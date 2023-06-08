import json
from data import Snowflake
from .utils import random_id
from .values import TaskStatus
from .MySQLBase import MySQLBase
from .RedisBase import RedisBase
from .FileBase import FileBase
from .values import DetailType,output_type,get_cost

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
    def __insert_task(self, params: dict) -> int | None:
        sql = ("INSERT INTO `task` (`token_id`, `taskId` ,`prompt`, `raw`) VALUES( %(token_id)s, %(taskId)s,%(prompt)s, %(raw)s)")
        return self.mysql_execute(sql, params= params, lastrowid= None)
    def __insert_detail(self, type: DetailType, params: dict):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        try:
            cnx.start_transaction()
            sql = "SELECT `id`,`token_id` FROM `task` WHERE taskId = %s"
            new_params = (params['taskId'],)
            record = self.mysql_fetchone(sql=sql, params= new_params, _cnx = cnx)
            if record is not None:
                token_id = record['token_id']
                sql = (
                    "INSERT INTO `detail` "
                    "( `id`, `task_id`, `type`,  `prompt`,`detail`) "
                    "VALUES ( %{id}%, %{task_id}s, %{type}s,  %(prompt)s, %(detail)s)"
                )
                new_params = {
                    **params,
                    'task_id': record['id'],
                }
                insertd_detail_id = self.mysql_execute(sql=sql, params= new_params, lastrowid= True, _cnx = cnx )
                if output_type.index(type.value) > -1:
                    sql = ("INSERT INTO `token_audit` (`token_id`, `task_id`, `cost`) VALUES (%(token_id)s, %(task_id)s,%(cost)s)")
                    new_params = {
                        'token_id' : token_id,
                        'task_id' : insertd_detail_id,
                        'cost': get_cost(type= type)
                    }
                    self.mysql_execute(sql=sql, params= new_params, _cnx = cnx )
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
    def save_task(self, token_id: str, prompt: str, raw: str, taskId: str):
        prompt_id = self.__insert_task({
            'token_id': token_id, 
            'taskId': taskId,
            'prompt': prompt,
            'raw': raw
        })
        self.redis_set_task(taskId= taskId, prompt_id= prompt_id, worker_id= None)
    def save_input(self, id: int, task_id: int, type: DetailType , prompt: str ):
        self.__insert_detail({
            'id': id,
            'task_id': task_id,
            'type': type.value,
            'prompt': prompt,
            'detail': None
        })
    def save_output(self, id: int, task_id: int, type: DetailType , detail: dict):
       self.__insert_detail({
            'id': id,
            'task_id': task_id,
            'type': type.value,
            'detail': json.dumps(detail)
        })
    def get_task(self, token_id: str, taskId: str ):
        sql = (
            "SELECT 1  FROM `task`  WHERE status = 1 AND taskId=%(taskId)s AND token_id=%(token_id)s" 
        )
        params = {
            'taskId': taskId,
            'token_id': token_id
        }
        return self.mysql_fetchone(sql=sql, params= params)
    def delete_task(self, token_id: str, taskId: str):
        sql = (
            "UPDATE `task` SET status=0  WHERE taskId=%(taskId)s AND token_id=%(token_id)s"
        )
        params = {
            'taskId': taskId,
            'token_id': token_id
        }
        return self.mysql_execute(sql = sql, params= params, lastrowid= True)
    def get_detail_by_task_id(self):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        try:
            pass
        finally:
            cursor.close()
            cnx.close()
    def get_tasks_by_token_id(self, token_id,  page: int = 0, page_size: int = 10):
        sql =(
            "SELECT t.taskId as id, t.prompt as topic, t.raw, t.create_at FROM task t"
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
    def get_discord_users(self, celery_worker_id: int):
        sql = ("SELECT worker_id,guild_id,channel_id,authorization FROM discord_users WHERE worker_id >= %(start_id)s AND worker_id <= %(end_id)s")
        params = {
            'start_id': Snowflake.snowflake_worker_id(celery_worker_id, 0),
            'end_id': Snowflake.snowflake_worker_id(celery_worker_id, 31),
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
        





