import asyncio
import json
from .Snowflake import Snowflake
from .utils import random_id
from .values import TaskStatus
from .MySQLBase import MySQLBase
from .RedisBase import RedisBase
from .FileBase import FileBase
from .values import DetailType,output_type,get_cost, image_hostname, config,SysCode, TokenType

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
    def close(self):
        self.mysql_close()
        self.redis_close()
    def set_cache(self, key, value):
        self.redis_set_cache_data(key=key, value=value)
    def get_cache(self, key):
        self.redis_get_cache_data(key=key)
    def remove_cache(self, key):
        self.redis.delete(key)
    
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
                self.mysql_execute(sql=sql, params= new_params, lastrowid= False, _cnx = cnx )
                if type.value in output_type:
                    print("add audit")
                    cost = get_cost(type= type)
                    sql = ("INSERT INTO `token_audit` (`token_id`, `task_id`, `cost`) VALUES (%(token_id)s, %(task_id)s,%(cost)s)")
                    new_params = {
                        'token_id' : token_id,
                        'task_id' : id,
                        'cost': cost
                    }
                    self.mysql_execute(sql=sql, params= new_params, _cnx = cnx )
                    self.redis_add_cost(token_id= token_id, cost= cost)
            cnx.commit()
        except Exception as e:
            print(e)
            cnx.rollback()

        finally:
            cursor.close()
            cnx.close()
    def get_token_id(self, token: str) -> tuple:
        id = None
        code = SysCode.OK
        try:
            temp = self.redis_get_token(token= token)
            if temp is None:
                sql =(
                    "SELECT t.id,TIMESTAMPDIFF(SECOND, NOW(), t.expire_at ) as ttl, t.balance, t.expire_at, COALESCE(a.cost, 0) AS cost"
                    " FROM tokens AS t"
                    " LEFT JOIN ("
                    "   SELECT token_id, SUM(cost) AS cost"
                    "   FROM token_audit"
                    "   GROUP BY token_id"
                    " ) AS a ON t.id = a.token_id"  
                    " WHERE t.token = %(token)s AND t.expire_at > current_timestamp()"
                )
                params = {
                    'token': token
                }
                record = self.mysql_fetchone(sql= sql, params= params)
                if record is not None:
                    if record['cost'] >= record['balance']:
                        code = SysCode.TOKEN_OUT_OF_BALANCE
                    else:
                        id = record['id']
                        ttl = record['ttl']
                        balance = record['balance']
                        cost = int(record['cost'])
                        expire_at = record['expire_at'].strftime("%Y-%m-%dT%H:%M:%SZ")
                        print(expire_at)
                        self.redis_set_token(token=token, ttl = ttl, id= id)
                        self.redis_init_cost(
                            token_id= id, 
                            balance = balance, 
                            cost= cost, 
                            expire_at= expire_at, 
                            ttl = ttl
                        )
                else:
                    code = SysCode.TOKEN_NOT_EXIST_OR_EXPIRED
            else:
                id = temp
                cost = self.redis_get_cost(token_id= id)
                if cost.get("cost") > cost.get("balance"):
                    code = SysCode.TOKEN_OUT_OF_BALANCE

        except Exception as e:
            print(e)
            code = SysCode.FATAL
        return (id, code, )
        

    def create_task(self, token_id: str, taskId: str):
        sql = ("INSERT INTO `task` (`token_id`, `taskId` ) VALUES( %(token_id)s, %(taskId)s)")
        self.mysql_execute(sql, params= {
            'token_id': token_id, 
            'taskId': taskId
        }, lastrowid= True)
    def check_task(self, id: int, ref_id: int, taskId: str ):
        status = self.redis_task_status(token_id=None, taskId= taskId)
        if status is not None:
            type = DetailType.OUTPUT_MJ_TIMEOUT
            self.cleanup(taskId=taskId, type= type)
            self.save_input(
                id=id,
                taskId=taskId,
                type=type,
                detail={
                    'ref': str(ref_id),
                }
            )
            

    def get_task(self, token_id: int, taskId: str ):
        cache_key = f'cache:{token_id}:{taskId}'
        cache_data =  self.get_cache(cache_key)
        if cache_data is None:
            sql = (
                "SELECT id  FROM `task`  WHERE status = 1 AND taskId=%(taskId)s AND token_id=%(token_id)s" 
            )
            params = {
                'taskId': taskId,
                'token_id': token_id
            }
            record =  self.mysql_fetchone(sql=sql, params= params)  
            if record is not None:
                id =  record['id']
                self.set_cache(cache_key, id)
                return  id
            else:
                return None
        else:
            return int(cache_data) 
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
    def get_fist_input_id(self, task_id: int):
        sql = (
            "SELECT  `id` FROM detail WHERE task_id=%(task_id)s AND type=%(type)s"
            " LIMIT 1"
        )
        params = {
            'task_id': task_id,
            'type': DetailType.INPUT_MJ_PROMPT.value
        }
        return self.mysql_fetchone(sql=sql, params=params)
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
    
    def update_status(self, taskId: str, status:TaskStatus , token_id = None) -> None:
        self.redis_task(token_id= token_id,  taskId=taskId, status= status, ttl= config['wait_time'] )
    def commit_task(self,  taskId: str ,  account_id: int):
        self.redis_set_onwer(account_id=account_id, taskId=taskId)
        self.update_status(taskId=taskId, status=TaskStatus.COMMITTED)
    def cleanup(self, taskId: str, type: DetailType):
        #if type is DetailType.OUTPUT_MJ_PROMPT or type is DetailType.OUTPUT_MJ_TIMEOUT:
        if type.value in [
            DetailType.OUTPUT_MJ_PROMPT.value,
            DetailType.OUTPUT_MJ_TIMEOUT.value,
            DetailType.OUTPUT_MJ_INVALID_PARAMETER.value
        ]:
            self.redis_task_cleanup(taskId= taskId)
        else:
            self.redis_task_job_cleanup(taskId= taskId)
        # elif type is DetailType.OUTPUT_MJ_REMIX:
        #     pass            
        # elif type is DetailType.OUTPUT_MJ_VARIATION:
        #     pass
        # elif type is DetailType.OUTPUT_MJ_UPSCALE:
        #     pass
        # elif type is DetailType.OUTPUT_MJ_REMIX:
        #     pass

    def is_task_onwer(self, account_id: int,  taskId: str) -> bool:
        print(self.redis_get_onwer(account_id= account_id, taskId= taskId))
        return self.redis_get_onwer(account_id= account_id, taskId= taskId) is not None


    def process_error(
            self,
            id: int,
            taskId: str ,  
            type: DetailType, 
            detail: dict
    ):
        type = DetailType.OUTPUT_MJ_INVALID_PARAMETER
        self.save_input(
            id=id,
            taskId=taskId,
            type=type,
            detail= detail
        )
        self.cleanup(taskId=taskId, type=type)


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
        self.update_task_cover(taskId= taskId, cover= url_cn)
        self.cleanup(taskId= taskId, type= type)

    def get_detail_by_id(self, token_id: int, detail_id: int):
        sql = (
            "SELECT t.taskId, d.detail, d.type FROM detail d LEFT JOIN task t ON d.task_id = t.id WHERE t.token_id = %(token_id)s AND  d.id=%(id)s"
        )
        params = {
            'token_id': token_id,
            'id': detail_id
        }
        return self.mysql_fetchone(sql=sql,params=params)

    def __update_task_feild(self, taskId: str , field: str, value: str| int):
        sql = (
            "UPDATE `task` SET {field}=%(value)s  WHERE taskId=%(taskId)s"
        ).format(field=field)
        params = {
            'taskId': taskId,
            'value': value
        }
        return self.mysql_execute(sql = sql, params= params, lastrowid= True)
    def update_task_topic(self,  taskId: str, topic: str):
        self.__update_task_feild( taskId=taskId, field = 'topic', value=topic )
    def update_task_cover(self, taskId: str, cover: str):
        self.__update_task_feild(taskId=taskId,field = 'cover', value=cover )
    def delete_task(self, taskId: str):
        self.__update_task_feild(taskId=taskId, field = 'status', value=0 )
    def get_tasks_by_token_id(self, token_id,  page: int = 0, page_size: int = 10):
        sql =(
            "SELECT t.taskId as id, t.topic, t.cover, t.create_at FROM task t"
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
        sql = ("SELECT worker_id,guild_id,channel_id,authorization FROM discord_users WHERE disabled = 0 AND worker_id >= %(start_id)s AND worker_id <= %(end_id)s")
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
                    sql = ("SELECT token,TIMESTAMPDIFF(DAY, NOW(), expire_at ) as days FROM `tokens` WHERE id=%(token_id)s AND type= %(type)s AND expire_at > NOW()")
                    params = {
                        'token_id': token_id,
                        'type': TokenType.TRIAL.value
                    }
                    record = self.mysql_fetchone(sql=sql, params= params, _cnx = cnx)
                    if record is not None:
                        token = record['token']
                        days = record['days'] 
            if token is None:
                token = random_id(20)
                sql = ("INSERT INTO `tokens` (`token`,`balance`,`type`,`expire_at`) VALUES( %(token)s, 100, %(type)s , DATE_ADD(NOW(), INTERVAL %(days)s DAY) )")
                params = {
                    'token': token,
                    'days': days,
                    'type': TokenType.TRIAL.value
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
        return (token,days,)
        





