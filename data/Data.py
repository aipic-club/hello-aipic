import redis
import asyncio
import time
# import logging
from urllib.parse import urlparse
import mysql.connector.pooling
from mysql.connector import errorcode
from .DiscordUsers import DiscordUsers
from .values import  TaskStatus,ImageOperationType,OutputType,Cost, SysError,config
from .utils import random_id,current_time,is_expired
from .FileHandler import FileHandler

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
        self.discordUsers = None
        self.get_discord_users()

    def close(self):
        if self.session:
            self.session.close()
        if self.client:
            self.client.close()
    def __insert_prompt(self, params: dict):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor()
        try:
            add_prompt = ("INSERT INTO `prompts` (`token_id`, `taskId`,`prompt`, `raw`) VALUES( %(token_id)s, %(taskId)s, %(prompt)s, %(raw)s)")
            cursor.execute(add_prompt, params)
            cnx.commit()
        finally:
            cursor.close()
            cnx.close()
    def __insert_task(self, params: dict):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor()
        try:
            cnx.start_transaction()
            #### get token_id ###
            sql = "SELECT `token_id` FROM `prompts` WHERE taskId = %s"
            val = (params['taskId'],)
            cursor.execute(sql, val)
            record = cursor.fetchone()
            if record is not None:
                token_id = record[0]
                add_sql = (
                    "INSERT INTO `tasks` "
                    "(`taskID`,`type`,`reference`,`v_index`,`u_index`,`status`,`message_id`,`message_hash`,`url_global`,`url_cn`) "
                    "VALUES ( %(taskId)s, %(type)s, %(reference)s, %(v_index)s, %(u_index)s, %(status)s, %(message_id)s, %(message_hash)s, %(url_global)s, %(url_cn)s)"
                )
                cursor.execute(add_sql, params)
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
    def prompt_task(self, token_id, taskId: str, status: TaskStatus) -> None:
        key = f'prompt:{token_id}:{taskId}'
        if token_id is None:
            keys = self.r.keys(f'prompt:*:{taskId}')
            if len(keys) != 1:
                return
            key = keys[0]
        ttl = self.r.ttl(key) if  self.r.exists(key) else config['wait_time'] 
        # if ttl > 0:
        self.r.setex(key, ttl , status.value )
        
    def prompt_task_status(self, token_id, taskId: str) -> bool:
        return self.r.get(f'prompt:{token_id}:{taskId}')
    
    ### 
    def image_task(self, taskId: str, imageHash: str, type: ImageOperationType, index: str):
        self.r.setex(f'image:{taskId}:{imageHash}', config['wait_time'] ,  f'{imageHash}.{type.value}.{index}')

    def image_task_status(self, taskId) -> list:
        keys = self.r.keys(f'image:{taskId}:*')
        return self.r.mget(keys)
    

    def add_interaction(self, key, value ) -> bool:

        return self.r.setex(f'interaction:{key}', 60,  value)



    def check_task(self, taskId: str):
        print("==check==")
        if TaskStatus.CONFIRMED == self.prompt_task_status(None, taskId):
            self.__insert_task({
                'taskId': taskId,
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
            self.r.delete(f'prompt:*:{taskId}')

    def add_task(self, 
            token_id: str,  
            prompt: str, 
            raw: str,
            taskId: str , 
            status: TaskStatus = TaskStatus.CREATED 
        ):
        self.__insert_prompt({
            'token_id': token_id, 
            'taskId': taskId, 
            'prompt': prompt,
            'raw': raw
        })
        self.__insert_task({
            'taskId': taskId,
            'type': None,
            'reference': None,
            'v_index': None,
            'u_index': None,
            'status': status.value,
            'message_id': None,
            'message_hash': None,
            'url_global': None,
            'url_cn': None
        })
    def commit_task(self, taskId: str ):
        self.__insert_task({
            'taskId': taskId,
            'type': None,
            'reference': None,
            'v_index': None,
            'u_index': None,
            'status': TaskStatus.COMMITTED.value,
            'message_id': None,
            'message_hash': None,
            'url_global': None,
            'url_cn': None
        })
        self.prompt_task(None , taskId, TaskStatus.COMMITTED )
    def process_task(self, taskId: str ,  type: OutputType, reference: int | None,  message_id: str ,   url: str):
        # download file and upload image
        file_name = str(url.split("_")[-1])
        hash = str(file_name.split(".")[0])
        url_cn = f'/{taskId}/{file_name}'   
        # copy to s3 bucket
        print("==🖼upload image ==")
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
        self.prompt_task(None , taskId, TaskStatus.FINISHED )
    def get_task_by_messageHash(self, token_id: int, id: int) -> dict[str, str]:
        # https://stackoverflow.com/questions/29772337/python-mysql-connector-unread-result-found-when-using-fetchone
        cnx = self.pool.get_connection()
        cursor = cnx.cursor()
        try:
            ### check the id is belong to the token
            ### sql = "SELECT t1.taskId,t1.message_id,t1.message_hash FROM `tasks` t1 LEFT JOIN `prompts` t2  ON t1.taskId = t2.taskId WHERE t2.token_id = %s AND t1.id = %s LIMT 1"
            sql = " SELECT t1.taskId,t1.message_id,t1.message_hash FROM `tasks` t1 LEFT JOIN (SELECT taskId FROM `prompts` WHERE id = %s) t2 ON t1.taskId = t2.taskId WHERE t1.message_hash = %s LIMIT 1"
            val = (token_id, id,)
            cursor.execute(sql, val)
            record = cursor.fetchone()
            if record is not None: 
                return {
                    'taskId': record[0],
                    'message_id' : record[1],
                    'message_hash' : record[2]
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
    def get_discord_users(self) :
        if self.discordUsers is not None:
            return self.discordUsers
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)  
        records = None
        try:
            sql = ("SELECT uid,guild_id,channel_id,authorization FROM discord_users")
            cursor.execute(sql)
            records = cursor.fetchall()
        finally:
            cursor.close()
            cnx.close()
        return records
        #self.discordUsers = DiscordUsers(records)
        #return self.discordUsers

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
        return f'{token}\n有效期剩余{days}天\n有效期后可继续获取试用'
        # \n回复【教程】获取试用帮助\n您也可以点击下方链接\n<a href="https://cnjourney.pancrasxox.xyz/trial/{token}">在微信中试用AIPic</a>









