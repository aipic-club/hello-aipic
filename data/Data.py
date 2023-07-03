import asyncio
from datetime import datetime, timedelta, timezone
import json
from .Snowflake import Snowflake
from .utils import random_id
from .values import TaskStatus
from .MySQLBase import MySQLBase
from .RedisBase import RedisBase
from .FileBase import FileBase
from .Snowflake import Snowflake
from .values import DetailType,mj_output_type,get_cost, image_hostname, config,SysCode, TokenType

class Data(MySQLBase, RedisBase, FileBase):
    def __init__(self, 
            is_dev: bool,
            redis_url: str, 
            mysql_url:str, 
            proxy: str | None,
            s3config : dict
    ) -> None:
        MySQLBase.__init__(self, url = mysql_url)
        RedisBase.__init__(self, url = redis_url)
        FileBase.__init__(self, config= s3config, proxy= proxy)
        self.is_dev = is_dev
        self.snowflake = Snowflake(worker_id= 0, epoch= None)
    def close(self):
        self.mysql_close()
        self.redis_close()
    def set_cache(self, key, value):
        self.redis_set_cache_data(key=key, value=value)
    def get_cache(self, key):
        self.redis_get_cache_data(key=key)
    def remove_cache(self, key):
        self.redis.delete(key)

    def generate_unique_id(self):
        return self.redis.incr("unique_id_counter")

    def __insert_detail(self, id: int, space_id: int, type: DetailType, detail: dict, cnx):
        sql = (
            "INSERT INTO `detail` "
            "( `id`, `space_id`, `type`, `detail`, `create_at` )"
            "VALUES ( %(id)s, %(space_id)s, %(type)s, %(detail)s, %(create_at)s)"
        )
        new_params = {
            'id': id,
            'space_id': space_id,
            'type': type.value,
            'detail': json.dumps(detail),
            'create_at': datetime.now(timezone(offset= timedelta(hours= 0)))
        }
        self.mysql_execute(sql=sql, params= new_params, lastrowid= False, _cnx = cnx )
    
    def __insert_detail_and_audit(self, id: int, space_name: str, type: DetailType, detail: dict):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        try:
            cnx.start_transaction()
            ### 
            sql = "SELECT `id`,`token_id` FROM `space` WHERE name = %(space_name)s"
            new_params = {
                'space_name': space_name
            }
            record = self.mysql_fetchone(sql=sql, params= new_params, _cnx = cnx)
            if record is not None:
                token_id = record['token_id']
                self.__insert_detail(
                    id= id,
                    space_id= record['id'],
                    type= type,
                    detail= detail,
                    cnx= cnx
                )
                if type.value in mj_output_type:
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
    def get_token_info(self, token: str) -> tuple:
        id = None
        info = {}
        code = SysCode.OK
        try:
            # id = self.redis_get_token(token= token)
            data  = self.redis_get_token(token= token)
            cost = self.redis_get_cost(token_id= data.get("id")) if data is not None else None
            if data is None or cost is None:
                sql =(
                    "SELECT t.id,TIMESTAMPDIFF(SECOND, NOW(), t.expire_at ) as ttl, t.type, t.balance, t.expire_at, COALESCE(a.cost, 0) AS cost"
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
                        expire_at = record['expire_at'].strftime("%Y-%m-%dT%H:%M:%SZ")
                        info = {
                            'id': id,
                            'balance': record['balance'],
                            'type': record['type'],
                            'expire_at': expire_at
                        }

                        self.redis_set_token(token=token, ttl = ttl, data = info)
                        self.redis_init_cost(
                            token_id = id,
                            ttl = ttl,
                            cost = int(record['cost'])
                        )
                else:
                    code = SysCode.TOKEN_NOT_EXIST_OR_EXPIRED
            else:
                if int(cost) > data.get("balance"):
                    code = SysCode.TOKEN_OUT_OF_BALANCE
                else:
                    id = data.get("id")
                    info = data
        except Exception as e:
            print(e)
            code = SysCode.FATAL
        return (id, info, code, )
        

    def create_space(self, token_id: str, name: str, cnx = None) -> int:
        sql = ("INSERT INTO `space` (`token_id`, `name` ) VALUES( %(token_id)s, %(name)s)")
        id = self.mysql_execute(sql, params= {
            'token_id': token_id, 
            'name': name
        }, lastrowid= True, _cnx = cnx)
        return id
    
    def check_task(self, id: int, ref_id: int, space_name: str ):
        # status = self.redis_space_ongoing_prompt_status(token_id=None, taskId= taskId)
        # if status is not None:
        #     type = DetailType.OUTPUT_MJ_TIMEOUT
        #     self.cleanup(taskId=taskId, type= type)
        #     self.save_input(
        #         id=id,
        #         taskId=taskId,
        #         type=type,
        #         detail={
        #             'ref': str(ref_id),
        #         }
        #     )
        pass
            

    def get_space(self, token: str, token_id: int, space_name: str ):
        cache_key = f'cache:space_id:{token}:{space_name}'
        cache_data =  self.get_cache(cache_key)
        if cache_data is None:
            sql = (
                "SELECT id  FROM `space`  WHERE status = 1 AND name=%(name)s AND token_id=%(token_id)s" 
            )
            params = {
                'name': space_name,
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
        
    def clean_space(self, token: str, space_name: str):
        cache_key = f'cache:space_id:{token}:{space_name}'
        self.remove_cache(cache_key)
        self.__update_space_feild(space_name=space_name, field = 'status', value=0 )

    def get_detail(
            self, 
            space_id: int, 
            page: int = 0, 
            page_size: int = 10,
            before: str = None,
            after: str = None
        ):

        if after is not None:
            sql = (
                "SELECT  `id`, `type`, `detail`,`create_at` FROM detail"
                " WHERE `space_id`=%(space_id)s AND `create_at` >'{after}'"
                " LIMIT %(page_size)s OFFSET %(offset)s"
            ).format(after= after)
        else:
            sql = (
                "SELECT  `id`, `type`, `detail`,`create_at` FROM "
                " ( SELECT  * FROM detail"
                " WHERE `space_id`=%(space_id)s AND `create_at` <'{before}'"
                " ORDER BY `id` DESC"
                " LIMIT %(page_size)s OFFSET %(offset)s "
                " ) sub ORDER BY `id` ASC"
            ).format(before= before if before is not None else datetime.now(timezone(offset= timedelta(hours= 0))))
        offset = (page - 1) * page_size
        params = {
            'space_id': space_id,
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
            'type': DetailType.INPUT_MJ_IMAGINE.value
        }
        return self.mysql_fetchone(sql=sql, params=params)
    def save_input(self, id: int, space_name: str, type: DetailType , detail: dict ):
        self.__insert_detail_and_audit(
            id=id,
            space_name= space_name, 
            type= type, 
            detail= detail
        )
    def add_interaction(self, key, value ) -> bool:
        self.redis_set_interaction(key=key, value=value)
    def get_interaction(self, key)-> int:
        return self.redis_get_interaction(key=key)
    
    def update_status(self, space_name: str, status:TaskStatus ) -> None:
        self.redis_space_prompt(
            space_name= space_name, 
            status= status, 
            ttl= config['wait_time'] 
        )

    def space_job_add(self, space_name: str, id: int, type: DetailType):
        self.redis_add_job(
            space_name=space_name, 
            id= id, 
            type= type
        )
    

    def cleanup(self, space_name: str, inputType: DetailType = None, outputType : DetailType = None):
        print(f"🧹 clean  space {space_name}")
        if inputType is None and outputType is None:
            self.redis_jobs_cleanup(space_name=space_name)

        self.redis_clear_onwer(space_name=space_name, type= inputType)
        if outputType is DetailType.OUTPUT_MJ_IMAGINE : 
            self.redis_space_prompt_cleanup(space_name= space_name)
        elif outputType.value in [
            DetailType.OUTPUT_MJ_UPSCALE.value,
            DetailType.OUTPUT_MJ_VARIATION.value,
            DetailType.OUTPUT_MJ_REMIX.value,
            DetailType.OUTPUT_MJ_VARY.value,
            DetailType.OUTPUT_MJ_ZOOM.value
        ]:
            self.redis_jobs_cleanup(space_name=space_name)
              
    def process_error(
            self,
            id: int,
            space_name: str ,  
            type: DetailType, 
            detail: dict
    ):
        type = DetailType.OUTPUT_MJ_INVALID_PARAMETER
        self.save_input(
            id=id,
            space_name=space_name,
            type=type,
            detail= detail
        )
        self.cleanup(space_name=space_name)

    def process_output(
            self, 
            id: int,
            space_name: str ,  
            types: tuple[DetailType,DetailType], 
            reference: int | None,  
            message_id: str,  
            url: str
        ):
        curInputType, curOutputType = types
        file_name = str(url.split("_")[-1])
        hash = str(file_name.split(".")[0])
        url_cn = f'{image_hostname}/{space_name}/{file_name}' 
        # copy to s3 bucket
        if self.is_dev:
            print(f"🖼dev mode , output url is {url}")
            url_cn = url
        else:
            print("🖼upload image")
            loop = asyncio.new_event_loop()
            loop.run_until_complete(
                self.file_copy_url_to_bucket(
                    url = url,
                    path =  space_name,
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
        self.__insert_detail_and_audit(
            id=id,
            space_name= space_name, 
            type= curOutputType, 
            detail= detail
        )
        self.update_space_cover(
            space_name= space_name, 
            cover= url_cn
        )
        self.cleanup(
            space_name= space_name, 
            inputType= curInputType, 
            outputType = curOutputType
        )

    def get_detail_by_id(self, token_id: int, detail_id: int, types: list[DetailType] = None):
        sql = (
            "SELECT s.name, d.detail, d.type FROM detail d" 
            " LEFT JOIN space s ON d.space_id = s.id"
            " WHERE s.token_id = %(token_id)s AND  d.id=%(id)s"
        )
        if types is not None and len(types) > 0:
            if len(types) == 1:
                sql += f" AND `type`={types[0].value}"
            else:
                types_list = [t.value for t in types]
                types_sql = ','.join(map(str, types_list))
                sql += f" AND `type` in ({types_sql})"
        params = {
            'token_id': token_id,
            'id': detail_id,

        }
        return self.mysql_fetchone(sql=sql,params=params)

    def __update_space_feild(self, space_name: str , field: str, value: str| int, update_when_none : bool = False):
        sql = (
            "UPDATE `space` SET {field}=%(value)s  WHERE name=%(name)s"
        ).format(field=field)
        if update_when_none:
            sql += " AND {field}='' "
        params = {
            'name': space_name,
            'value': value
        }
        return self.mysql_execute(sql = sql, params= params, lastrowid= True)
    
    def update_space_topic(self,  space_name: str, topic: str, update_when_none : bool = False):
        self.__update_space_feild( space_name=space_name, field = 'topic', value=topic, update_when_none= update_when_none )

    def update_space_cover(self, space_name: str, cover: str):
        self.__update_space_feild(space_name=space_name,field = 'cover', value=cover )


    def get_spaces_by_token_id(self, token_id,  page: int = 0, page_size: int = 10):
        sql =(
            "SELECT s.name as id, s.topic, s.cover, s.create_at FROM space s"
            " WHERE s.token_id = %(token_id)s AND s.status != 0"
            " ORDER BY s.id DESC"                
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
        days = 15
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
                    sql = ("SELECT token,TIMESTAMPDIFF(DAY, NOW(), expire_at ) as days FROM `tokens` WHERE id=%(token_id)s AND type= %(type)s")
                    params = {
                        'token_id': token_id,
                        'type': TokenType.TRIAL.value
                    }
                    record = self.mysql_fetchone(sql=sql, params= params, _cnx = cnx)
                    if record is not None:
                        token = record['token']
                        days = record['days'] 


                    # token_id = record['token_id']
                    # sql = ("SELECT token,TIMESTAMPDIFF(DAY, NOW(), expire_at ) as days FROM `tokens` WHERE id=%(token_id)s AND type= %(type)s AND expire_at > NOW()")
                    # params = {
                    #     'token_id': token_id,
                    #     'type': TokenType.TRIAL.value
                    # }
                    # record = self.mysql_fetchone(sql=sql, params= params, _cnx = cnx)
                    # if record is not None:
                    #     token = record['token']
                    #     days = record['days'] 
                
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
                ### create default space and welcome msg for user
                taskId = random_id(11)
                task_id = self.create_task(token_id= token_id, taskId= taskId, cnx= cnx)
                # snowflake_id = self.snowflake.generate_id()
                # self.__insert_detail(
                #     id= snowflake_id,
                #     task_id= task_id,
                #     type= DetailType.SYS_WELCOME,
                #     detail= None,
                #     cnx= cnx
                # )

            cnx.commit()     
        except Exception as e:
            print(e)
            cnx.rollback()
        finally:
            cursor.close()
            cnx.close()
        return (token,days,)
        





