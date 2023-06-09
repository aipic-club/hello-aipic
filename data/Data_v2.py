import asyncio
import json
from .Snowflake import Snowflake
from .utils import random_id
from .values import TaskStatus
from .MySQLBase import MySQLBase
from .RedisBase import RedisBase
from .FileBase import FileBase
from .values import DetailType,output_type,get_cost, image_hostname, config

class Data_v2(MySQLBase, RedisBase, FileBase):
    def __init__(self, 
            redis_url: str, 
            mysql_url:str, 
            proxy: str | None,
            s3config : dict
    ) -> None:
        super().__init__(url = mysql_url)
        RedisBase.__init__(self, url = redis_url)
        FileBase.__init__(self, config= s3config, proxy= proxy)
    def __insert_detail(self, id: int, taskId: str, type: DetailType, detail: dict):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        try:
            cnx.start_transaction()
            sql = "SELECT `id`,`token_id` FROM `task` WHERE taskId = %(taskId)s"
            new_params = {
                'taskId': taskId
            }
            record = self.mysql_fetchone(sql=sql, params= new_params, _cnx = cnx)
            if record is not None:
                token_id = record['token_id']
                sql = (
                    "INSERT INTO `detail` "
                    "( `id`, `task_id`, `type`, `detail`) "
                    "VALUES ( %(id)s, %(task_id)s, %(type)s, %(detail)s)"
                )
                new_params = {
                    'id': id,
                    'task_id': record['id'],
                    'type': type.value,
                    'detail': json.dumps(detail)
                }
                insertd_detail_id = self.mysql_execute(sql=sql, params= new_params, lastrowid= True, _cnx = cnx )
                if type.value in output_type:
                    print("add audit")
                    sql = ("INSERT INTO `token_audit` (`token_id`, `task_id`, `cost`) VALUES (%(token_id)s, %(task_id)s,%(cost)s)")
                    new_params = {
                        'token_id' : token_id,
                        'task_id' : insertd_detail_id,
                        'cost': get_cost(type= type)
                    }
                    self.mysql_execute(sql=sql, params= new_params, _cnx = cnx )
            cnx.commit()
        except Exception as e:
            print(e)
            cnx.rollback()

        finally:
            cursor.close()
            cnx.close()


    def get_token_id(self, token: str):
        temp = self.redis_get_token(token= token)
        if temp is None:
            sql = "SELECT `id`,TIMESTAMPDIFF(SECOND, NOW(), expire_at ) as ttl FROM `tokens` WHERE token = %s and expire_at > current_timestamp()"
            val = (token,)
            recod = self.mysql_fetchone(sql= sql, params= val)

            if recod is None:
                return None
            else:
                self.redis_set_token(token= token, ttl= recod['ttl'], id= recod['id'])
                return recod['id']
        else:
            return temp
    def create_task(self, token_id: str, taskId: str):
        sql = ("INSERT INTO `task` (`token_id`, `taskId` ) VALUES( %(token_id)s, %(taskId)s)")
        self.mysql_execute(sql, params= {
            'token_id': token_id, 
            'taskId': taskId
        }, lastrowid= True)
    def verify_task(self, token_id: str, taskId: str) -> bool:
        sql = ("SELECT 1 FROM `task` WHERE token_id = %(token_id)s AND taskId = %(taskId)s")
        params= {
            'token_id': token_id, 
            'taskId': taskId
        }
        record = self.mysql_fetchone(sql=sql, params= params)
        return record is None
    def get_detail(self, task_id: int, page: int = 0, page_size: int = 10):
        sql = (
            "SELECT  `id`, `type`, `detail`,`create_at` FROM detail WHERE task_id=%(task_id)s"
            " LIMIT %(page_size)s OFFSET %(offset)s"
        )
        offset = (page - 1) * page_size
        params = {
            'task_id': task_id,
            'offset': offset,
            'page_size': page_size,
        }
        return self.mysql_fetchall(sql=sql, params= params)
    
    def save_input(self, id: int, taskId: int, type: DetailType , detail: dict ):
        self.__insert_detail(
            id=id,
            taskId= taskId, 
            type= type, 
            detail= detail
        )
    def add_interaction(self, key, value ) -> bool:
        self.redis_set_interaction(key=key, value=value)
    def get_interaction(self, key)-> int:
        return self.redis_get_interaction(key=key)
    
    def update_task_status(self, taskId: str, status:TaskStatus , token_id = None) -> None:
        self.redis_task(token_id= token_id,  taskId=taskId, status= status, ttl= config['wait_time'] )

    def commit_task(self,  taskId: str ,  worker_id: int):
        self.redis_set_task(taskId=taskId, worker_id=worker_id)
        self.update_task_status(taskId=taskId, status=TaskStatus.COMMITTED)

    def is_task_onwer(self, taskId: str ,  worker_id: int) -> bool:
        id = self.redis_get_task(taskId=taskId)
        return id is not None and id == worker_id
    def process_output(
            self, 
            id: int,
            taskId: str ,  
            type: DetailType, 
            reference: int | None,  
            message_id: str,  
            url: str
        ):
        file_name = str(url.split("_")[-1])
        hash = str(file_name.split(".")[0])
        url_cn = f'{image_hostname}/{taskId}/{file_name}' 
        # copy to s3 bucket
        print("🖼upload image")
        loop = asyncio.new_event_loop()
        loop.run_until_complete(
            self.file_copy_url_to_bucket(
                url = url,
                path =  taskId,
                file_name = file_name
            )
        )  
        loop.close()  
        
        detail = {
            'id': message_id,
            'hash': hash,
            'reference': reference,
            'url': url_cn
        }

        self.__insert_detail(
            id=id,
            taskId= taskId, 
            type= type, 
            detail= detail
        )
        self.redis_task_cleanup(taskId=taskId)
    def get_task(self, token_id: int, taskId: str ):
        sql = (
            "SELECT id  FROM `task`  WHERE status = 1 AND taskId=%(taskId)s AND token_id=%(token_id)s" 
        )
        params = {
            'taskId': taskId,
            'token_id': token_id
        }
        return self.mysql_fetchone(sql=sql, params= params)
    def get_detail_by_id(self, token_id: int, detail_id: int):
        sql = (
            "SELECT t.taskId, d.detail, d.type FROM detail d LEFT JOIN task t ON d.task_id = t.id WHERE t.token_id = %(token_id)s AND  d.id=%(id)s"
        )
        params = {
            'token_id': token_id,
            'id': detail_id
        }
        return self.mysql_fetchone(sql=sql,params=params)

    def delete_task(self, token_id: str, taskId: str):
        sql = (
            "UPDATE `task` SET status=0  WHERE taskId=%(taskId)s AND token_id=%(token_id)s"
        )
        params = {
            'taskId': taskId,
            'token_id': token_id
        }
        return self.mysql_execute(sql = sql, params= params, lastrowid= True)
    def get_tasks_by_token_id(self, token_id,  page: int = 0, page_size: int = 10):
        sql =(
            "SELECT t.taskId as id, t.create_at FROM task t"
            #"SELECT t.taskId, t.prompt, t.raw, d.url_cn,  t.create_at FROM task t"
            # " LEFT JOIN ("
            # "    SELECT d1.taskId, d1.type, d1.status, d1.url_cn"
            # "    FROM detail d1"
            # "    INNER JOIN ("
            # "        SELECT MAX(id) as id"
            # "        FROM tasks"
            # "        WHERE status = %(status)s"
            # "        GROUP BY taskId"
            # "    ) t2 ON t1.id = t2.id"
            # ") t ON p.taskId = t.taskId"
            " WHERE t.token_id = %(token_id)s AND t.status != 0"
            " ORDER BY t.id DESC"                
            " LIMIT %(page_size)s OFFSET %(offset)s"
        )
        offset = (page - 1) * page_size
        params = {
            'token_id': token_id,
            'offset': offset,
            'page_size': page_size,
            'status': TaskStatus.FINISHED.value
        }
        return self.mysql_fetchall(sql, params)
    def get_discord_users(self, broker_id: int):
        sql = ("SELECT worker_id,guild_id,channel_id,authorization FROM discord_users WHERE worker_id >= %(start_id)s AND worker_id <= %(end_id)s")
        params = {
            'start_id': Snowflake.generate_snowflake_worker_id(broker_id, 0),
            'end_id': Snowflake.generate_snowflake_worker_id(broker_id, 31),
        }
        return self.mysql_fetchall(sql, params)
    def create_trial_token(self, FromUserName):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)  
        token = None 
        days = 7
        try:
            sql = ("SELECT id FROM mp_users WHERE mp_user=%(user)s")
            params = {
                'user': FromUserName,
            }
            record = self.mysql_fetchone(sql = sql, params= params,  )
            if record is None:
                sql = ("INSERT INTO `mp_users` (`mp_user`) VALUES(%(user)s)")
                mp_userId = self.mysql_execute(sql= sql, params= params, lastrowid= True, _cnx = cnx)
            else:
                mp_userId = record['id']
                sql = ("SELECT id,mp_user_id,token_id FROM mp_trial_history WHERE mp_user_id=%(user_id)s ORDER BY id DESC LIMIT 1")
                params = {
                    'user_id': mp_userId
                }
                record = self.mysql_fetchone(sql= sql , params= params, _cnx = cnx)
                if record is not None:
                    token_id = record['token_id']
                    sql = ("SELECT token,TIMESTAMPDIFF(DAY, NOW(), expire_at ) as days FROM tokens WHERE id=%(token_id)s AND expire_at > NOW()")
                    params = {
                        'token_id': token_id
                    }
                    record = self.mysql_fetchone(sql=sql, params= params, _cnx = cnx)
                    if record is not None:
                        token = record['token']
                        days = record['days'] 
            if token is None:
                token = random_id(20)
                sql = ("INSERT INTO `tokens` (`token`,`blance`,`type`,`expire_at`) VALUES( %(token)s, 100, 1 , DATE_ADD(NOW(), INTERVAL %(days)s DAY) )")
                params = {
                   'token': token,
                    'days': days
                }
                token_id =  self.mysql_execute(sql=sql, params= params, lastrowid= True, _cnx = cnx )
                sql = ("INSERT INTO `mp_trial_history` (`mp_user_id`,`token_id`) VALUES( %(user_id)s, %(token_id)s) ")
                params = {
                    'user_id': mp_userId,
                    'token_id': token_id
                }
                self.mysql_execute(sql=sql, params=params, lastrowid= False, _cnx = cnx)
            cnx.commit()     
        except Exception as e:
            print(e)
            cnx.rollback()
        finally:
            cursor.close()
            cnx.close()
        return token,days
        





