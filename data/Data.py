import redis
import asyncio
import json
import time
# import logging
from urllib.parse import urlparse
import mysql.connector.pooling
from mysql.connector import errorcode
from .values import  TaskStatus,ImageOperationType,OutputType,Cost, SysError,config,image_hostname
from .utils import random_id,current_time,is_expired
from .FileHandler import FileHandler
from .Snowflake import Snowflake

# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)


class Data():
    session = None
    client = None
    def __init__(self, 
            redis_url: str, 
            mysql_url:str, 
            proxy: str | None,
            s3config : dict
    ) -> None:
        parsed = urlparse(mysql_url)
        try:
            dbconfig = {
                'user' : parsed.username, 
                'password' : parsed.password,
                'host' : parsed.hostname,
                'port' : parsed.port,
                'database' : parsed.path.lstrip('/')
            }
            self.pool = mysql.connector.pooling.MySQLConnectionPool(
                pool_name = "mypool",
                pool_size = 5,
                buffered = True,
                **dbconfig
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        self.r = redis.from_url(redis_url)
        self.fileHandler = FileHandler(proxy= proxy, s3config=s3config)

    def close(self):
        if self.session:
            self.session.close()
        if self.client:
            self.client.close()
    def __insert_prompt(self, params: dict) -> int | None:
        cnx = self.pool.get_connection()
        cursor = cnx.cursor()
        insertd_prompt_id = None
        try:
            add_prompt = ("INSERT INTO `prompts` (`token_id`, `taskId`,`prompt`, `raw`) VALUES( %(token_id)s, %(taskId)s, %(prompt)s, %(raw)s)")
            cursor.execute(add_prompt, params)
            insertd_prompt_id = cursor.lastrowid
            cnx.commit()
        finally:
            cursor.close()
            cnx.close()
        return insertd_prompt_id
    
    def __set_task_cache(self, taskId: str, prompt_id: int,  worker_id: int | None):
        json_data = json.dumps({
            'prompt_id': prompt_id,
            'worker_id': worker_id
        })
        self.r.setex(f'task:{taskId}', config['cache_time'], json_data)

    def __get_task_cache(self, taskId: str):
        temp = self.r.get(f'task:{taskId}')
        data = None
        if temp is not None:
            data = json.loads(temp.decode('utf-8'))
        return data
    
    ### TODO rename table names


    def __insert_task(self, params: dict):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        try:
            cnx.start_transaction()
            #### get token_id ###
            sql = "SELECT `id`,`token_id` FROM `prompts` WHERE taskId = %s"
            val = (params['taskId'],)
            cursor.execute(sql, val)
            record = cursor.fetchone()
            if record is not None:
                token_id = record['token_id']
                add_sql = (
                    "INSERT INTO `tasks` "
                    "( `taskId`, `prompt_id`, `prompt`, `type`,`reference`,`v_index`,`u_index`,`status`,`message_id`,`message_hash`,`url_global`,`url_cn`) "
                    "VALUES ( %{taskId}%, %{prompt_id}s, %{prompt}s,  %(type)s, %(reference)s, %(v_index)s, %(u_index)s, %(status)s, %(message_id)s, %(message_hash)s, %(url_global)s, %(url_cn)s)"
                )
                cursor.execute(add_sql, {
                    **params,
                    'prompt_id': record['id']
                })
                insertd_task_id = cursor.lastrowid
                ##### add the cost ####
                if params['status'] == TaskStatus.FINISHED.value:
                    cost_sql = ("INSERT INTO `token_audit` (`token_id`, `task_id`, `cost`) VALUES (%(token_id)s, %(task_id)s,%(cost)s)")
                    cost_row = {
                        'token_id' : token_id,
                        'task_id' : insertd_task_id,
                        'cost': Cost.get_cost(params['type'])
                    }
                    cursor.execute(cost_sql, cost_row)
            cnx.commit()

        except Exception as e:
            print(e)
            cnx.rollback()
        finally:
            cursor.close()
            cnx.close()
    def check_token_and_get_id(self, token: str) -> int | SysError:
        id = None
        temp = self.r.get(f'token:{token}')
        if temp:
            return temp.decode('utf-8')
        cnx = self.pool.get_connection()
        cursor = cnx.cursor()
        try:
            sql = "SELECT `id`,TIMESTAMPDIFF(SECOND, NOW(), expire_at ) as ttl FROM `tokens` WHERE token = %s and expire_at > current_timestamp()"
            val = (token,)
            cursor.execute(sql, val)
            record = cursor.fetchone()
            if record is not None:
                id = record[0]
                ttl = record[1]
                self.r.setex(f'token:{token}', ttl, id )
        finally:
            cursor.close()
            cnx.close()
        return id if id is not None else SysError.TOKEN_NOT_EXIST_OR_EXPIRED
    def prompt_task(self, token_id, taskId: str, status: TaskStatus, ttl: int = None ) -> None:
        key = f'prompt:{token_id}:{taskId}'
        if token_id is None:
            keys = self.r.keys(f'prompt:*:{taskId}')
            if len(keys) != 1:
                return
            key = keys[0]
        if ttl is not None:
            _ttl = ttl
        else:
            _ttl = self.r.ttl(key) if  self.r.exists(key) else config['wait_time'] 
        if _ttl > 0:
            self.r.setex(key, _ttl , status.value )

    def prompt_task_status(self, token_id, taskId: str):
        key = f'prompt:{token_id}:{taskId}' 
        return self.r.get(key)
    
    def prompt_task_cleanup(self, taskId):
        keys = self.r.keys(f'prompt:*:{taskId}')
        self.r.delete(*keys)

    ### 
    def image_task(self, taskId: str, imageHash: str, type: ImageOperationType, index: str):
        self.r.setex(f'image:{taskId}:{imageHash}', config['wait_time'] ,  f'{imageHash}.{type.name}.{index}')

    def image_task_status(self, taskId) -> list:
        keys = self.r.keys(f'image:{taskId}:*')
        return self.r.mget(keys)
    
    def image_task_cleanup(self, taskId: str, imageHash: str, ):
        self.r.delete(f'image:{taskId}:{imageHash}' )
    
    def broker_task_status(self, broker_id: int, worker_id: int, taskId: int):
        self.r.setex(f'broker:{broker_id}:{worker_id}:{taskId}', config['wait_time']  , '')

    def broker_task_cleanup(self, taskId):
        keys = self.r.keys(f'broker:*:*:{taskId}')
        self.r.delete(*keys)

    def add_interaction(self, key, value ) -> bool:

        return self.r.setex(f'interaction:{key}', config['wait_time'] ,  value)
    
    def get_interaction(self, key)-> int:
        value = self.r.get(f'interaction:{key}')
        return int(value) if value is not None else None

    def check_task(self, taskId: str):
        print(f'✔️ check task {taskId}')
        if TaskStatus.CONFIRMED == self.r.get(f'prompt*:{taskId}'):
            self.__insert_task({
                'taskId': taskId,
                'prompt': None,
                'type': None,
                'reference': None,
                'v_index': None,
                'u_index': None,
                'status': TaskStatus.FAILED.value,
                'message_id': None,
                'message_hash': None,
                'url_global': None,
                'url_cn': None
            })
            self.prompt_task_cleanup(taskId=taskId)
            image_status = self.image_task_status(taskId=taskId)
            if len(image_status) == 0:
                self.broker_task_cleanup(taskId= taskId)

    def save_prompt(self, token_id: str,  prompt: str, raw: str,taskId: str  ):
        prompt_id = self.__insert_prompt({
            'token_id': token_id, 
            'taskId': taskId, 
            'prompt': prompt,
            'raw': raw
        })
        self.__set_task_cache(taskId=taskId, prompt_id=prompt_id, worker_id= None)
        self.prompt_task(token_id , taskId, TaskStatus.CREATED )

    def get_prompt_by_taskId(self, taskId: str):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        record = None
        try:
            select_sql = "SELECT id, worker_id FROM `prompts` WHERE taskId=%(taskId)s"
            cursor.execute(select_sql, {
                'taskId': taskId
            })
            record = cursor.fetchone()
        finally:
            cursor.close()
            cnx.close()
        return record

    def update_prompt_worker_id(self, taskId: str , worker_id: int):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor()
        try:
            task_data = self.__get_task_cache(taskId=taskId)
            if task_data is not None:
                id = task_data['prompt_id']
            else:
                item = self.get_prompt_by_taskId(taskId)
                id = item['id']
            update_sql = "UPDATE `prompts` SET worker_id=%(worker_id)s  WHERE id=%(id)s"
            cursor.execute(update_sql, {
                'worker_id': worker_id, 
                'id': id
            })
            cnx.commit()
            self.__set_task_cache(taskId=taskId, prompt_id= id, worker_id= worker_id)
        finally:
            cursor.close()
            cnx.close()
    def get_task_worker_id(self, taskId: str):
        worker_id = None
        task_data = self.__get_task_cache(taskId=taskId)
        if task_data is not None:
            worker_id = task_data['worker_id']
        if worker_id is None:
            item = self.get_prompt_by_taskId(taskId)
            worker_id = item['worker_id']
        return worker_id
    def get_broker_id(self, worker_id: int):
        broker_id , _ = Snowflake.parse_worker_id(worker_id=worker_id)
        return broker_id

    def commit_task(self, taskId: str , broker_id: int,  worker_id: int ):
        self.r.setex(f'worker:{broker_id}:{worker_id}:{taskId}', config['wait_time']  , '')
        self.update_prompt_worker_id(taskId, worker_id)
        self.prompt_task(None , taskId, TaskStatus.COMMITTED )

    def is_task_onwer(self, taskId: str, worker_id: int) -> bool:
        print("check task onwer")
        data =  self.__get_task_cache(taskId=taskId)

        if data is not None and data.get('worker_id') == worker_id:
            return True
        data =  self.get_prompt_by_taskId(taskId=taskId)
        
        if data is not None and worker_id == data['worker_id']:
            self.__set_task_cache(taskId=taskId, prompt_id= data['id'], worker_id=worker_id)
            return True
        
        return False



    def process_task(self, taskId: str ,  type: OutputType, reference: int | None,  message_id: str ,   url: str):
        

        # download file and upload image
        file_name = str(url.split("_")[-1])
        hash = str(file_name.split(".")[0])
        url_cn = f'{image_hostname}/{taskId}/{file_name}'   

        # copy to s3 bucket
        print("🖼upload image")
        loop = asyncio.new_event_loop()
        loop.run_until_complete(
            self.fileHandler.copy_discord_img_to_bucket(
                path= taskId, 
                file_name= file_name,
                url = url 
            )
        )  
        loop.close()  
        # update mysql record
        self.__insert_task({
            'taskId': taskId,
            'prompt': None,
            'type': type.value,
            'reference': reference,
            'v_index': None,
            'u_index': None,
            'status': TaskStatus.FINISHED.value,
            'message_id': message_id if type is not OutputType.UPSCALE else '',
            'message_hash': hash if type is not OutputType.UPSCALE else '',
            'url_global': url,
            'url_cn': url_cn
        })
        #### clean up
        if type is OutputType.DRAFT:
            self.prompt_task_cleanup(taskId = taskId)
        else:
            self.image_task_cleanup(taskId=taskId, imageHash= hash)
        self.broker_task_cleanup(taskId= taskId)

    def get_task_by_messageHash(self, token_id: int, id: int) -> dict[str, str]:
        cnx = self.pool.get_connection()
        cursor = cnx.cursor()
        try:
            ### check the id is belong to the token
            ### sql = "SELECT t1.taskId,t1.message_id,t1.message_hash FROM `tasks` t1 LEFT JOIN `prompts` t2  ON t1.taskId = t2.taskId WHERE t2.token_id = %s AND t1.id = %s LIMT 1"
            sql = " SELECT t2.worker_id,t1.taskId,t1.message_id,t1.message_hash FROM `tasks` t1 LEFT JOIN (SELECT worker_id,taskId FROM `prompts` WHERE token_id = %s) t2 ON t1.taskId = t2.taskId WHERE t1.message_hash = %s LIMIT 1"
            val = (token_id, id,)
            cursor.execute(sql, val)
            record = cursor.fetchone()
            if record is not None: 
                return {
                    'worker_id': record[0],
                    'taskId': record[1],
                    'message_id' : record[2],
                    'message_hash' : record[3]
                }
            else:
                return None
        finally:
            cursor.close()
            cnx.close()
    def sum_costs_by_tokenId(self, token_id):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        records = None
        try:
            sql = ("SELECT SUM(cost) as cost  FROM token_audit WHERE token_id=%(token_id)s")
            cursor.execute(sql, {
                'token_id': token_id
            })
            records = cursor.fetchone()
        finally:
            cursor.close()
            cnx.close()
        return records
    def get_token_info_by_id(self, token_id):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        records = None
        try:
            sql = ("SELECT blance,expire_at FROM tokens where id = %(token_id)s")
            cursor.execute(sql, {
                'token_id': token_id
            })
            records = cursor.fetchone()
        finally:
            cursor.close()
            cnx.close()
        return records
    def sum_costs_by_taskID():
        # SELECT  t1.taskId, SUM(t2.cost) as cost FROM mj.tasks t1 LEFT JOIN mj.token_audit t2 ON t2.task_id = t1.id GROUP BY t1.taskId;
        pass
    def get_prompts_by_token_id(self, token_id,  page: int = 0, page_size: int = 10):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        records = None
        try:
            # sql = "SELECT `taskId`,`prompt`,`raw`,`create_at` FROM `prompts` WHERE `token_id` = %s ORDER BY `id` DESC LIMIT %s, %s"
            sql =(
                "SELECT p.taskId, p.prompt, p.raw, t.url_cn,  p.create_at FROM prompts p"
                " LEFT JOIN ("
                "    SELECT t1.taskId, t1.type, t1.status, t1.url_cn"
                "    FROM tasks t1"
                "    INNER JOIN ("
                "        SELECT MAX(id) as id"
                "        FROM tasks"
                "        WHERE status = %(status)s"
                "        GROUP BY taskId"
                "    ) t2 ON t1.id = t2.id"
                ") t ON p.taskId = t.taskId"
                " WHERE p.token_id = %(token_id)s "
                " ORDER BY p.id DESC"                
                " LIMIT %(page_size)s OFFSET %(offset)s"
            )
            offset = (page - 1) * page_size
            cursor.execute(sql, {
                'token_id': token_id,
                'offset': offset,
                'page_size': page_size,
                'status': TaskStatus.FINISHED.value
            })
            records = cursor.fetchall()
        finally:
            cursor.close()
            cnx.close()
        return records
    def get_tasks_by_taskId(self, token_id,  taskId, page: int = 0, page_size: int = 10):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        records = None
        try:
            ### check token id first 
            check_sql = "SELECT 1 FROM `prompts` WHERE token_id =%s AND taskId = %s LIMIT 1"
            val = (token_id,  taskId,)
            cursor.execute(check_sql, val)
            record = cursor.fetchone()
            if record is not None:
                sql = "SELECT v_index,u_index,type,status,reference,message_id,message_hash,url_cn,create_at FROM `tasks` WHERE `taskId` = %s LIMIT %s, %s"
                offset = (page - 1) * page_size
                val = (taskId, offset, page_size, )
                cursor.execute(sql, val)
                records = cursor.fetchall()
        finally:
            cursor.close()
            cnx.close()
        return records
    def get_discord_users(self, celery_worker_id: int):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)  
        records = None
        try:
            sql = ("SELECT worker_id,guild_id,channel_id,authorization FROM discord_users WHERE worker_id >= %(start_id)s AND worker_id <= %(end_id)s")
            cursor.execute(sql,{
                'start_id': Snowflake.snowflake_worker_id(celery_worker_id, 0),
                'end_id': Snowflake.snowflake_worker_id(celery_worker_id, 31),
            })
            records = cursor.fetchall()
        finally:
            cursor.close()
            cnx.close()
        return records

    def create_trial_token(self, FromUserName):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)  
        token = None 
        days = 7     
        try:
            # first check user exist or not
            user_sql = ("SELECT id FROM mp_users WHERE mp_user=%(user)s")
            cursor.execute(user_sql, {
                'user': FromUserName,
            })
            record = cursor.fetchone()
            record2 = None
            record3 = None
            mp_userId = None
            if record is None:
                create_mpUser_sql = ("INSERT INTO `mp_users` (`mp_user`) VALUES(%(user)s)")
                cursor.execute(create_mpUser_sql, {
                    'user': FromUserName,
                })
                mp_userId = cursor.lastrowid
            else:
                mp_userId = record['id']
                trial_sql = ("SELECT id,mp_user_id,token_id FROM mp_trial_history WHERE mp_user_id=%(user_id)s ORDER BY id DESC LIMIT 1")
                cursor.execute(trial_sql, {
                    'user_id': mp_userId
                })
                record2 = cursor.fetchone()
                if record2 is not None:
                    token_id = record2['token_id']
                    token_sql = ("SELECT token,TIMESTAMPDIFF(DAY, NOW(), expire_at ) as days FROM tokens WHERE id=%(token_id)s AND expire_at > NOW()")
                    cursor.execute(token_sql, {
                        'token_id': token_id
                    })
                    record3 = cursor.fetchone()
                    if record3 is not None:
                        token = record3['token']
                        days = record3['days'] 
            if token is None:
                token = random_id(20)
                create_token_sql = ("INSERT INTO `tokens` (`token`,`blance`,`type`,`expire_at`) VALUES( %(token)s, 100, 1 , DATE_ADD(NOW(), INTERVAL %(days)s DAY) )")
                cursor.execute(create_token_sql, {
                    'token': token,
                    'days': days
                })
                token_id = cursor.lastrowid
                create_trial_sql = ("INSERT INTO `mp_trial_history` (`mp_user_id`,`token_id`) VALUES( %(user_id)s, %(token_id)s) ")
                cursor.execute(create_trial_sql, {
                    'user_id': mp_userId,
                    'token_id': token_id
                })
            cnx.commit()       
        except Exception as e:
            print(e)
            cnx.rollback()
        finally:
            cursor.close()
            cnx.close()
        expire = '一天内到期' if days == 0 else f'{token}\n有效期剩余{days}天'
        return f'{expire}\n有效期后可继续获取试用 \n点击下方链接\n<a href="https://aipic.club/trial/{token}">在微信中试用AIPic</a>'



    


        def __create_input():


            pass
        def __create_output():
            pass







