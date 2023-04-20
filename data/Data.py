import json
import redis
import asyncio
from urllib.parse import urlparse
import mysql.connector
from mysql.connector import errorcode
from .values import TaskStatus,OutputType,Cost
from .FileHandler import FileHandler


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
            self.cnx = mysql.connector.connect(
                user = parsed.username, 
                password = parsed.password,
                host = parsed.hostname,
                port = parsed.port,
                database = parsed.path.lstrip('/')
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
    def __del__(self):
        if self.session:
            self.session.close()
        if self.client:
            self.client.close()
    def __insert_prompt(self, params: dict):
        cursor = self.cnx.cursor()
        add_prompt = ("INSERT INTO `prompts` (`token_id`, `taskId`,`prompt`) VALUES( %(token_id)s, %(taskId)s, %(prompt)s)")
        cursor.execute(add_prompt, params)
        self.cnx.commit()
        cursor.close()
    def __insert_task(self, params: dict):
        cursor = self.cnx.cursor()
        try:
            self.cnx.start_transaction()
            #### get token_id ###
            sql = "SELECT `token_id` FROM `prompts` WHERE taskId = %s"
            val = (params['taskId'],)
            cursor.execute(sql, val)
            record = cursor.fetchone()
            if record is not None:
                token_id = record[0]
                add_task = (
                    "INSERT INTO `tasks` "
                    "(`taskID`,`type`,`parent`,`v_index`,`u_index`,`status`,`message_id`,`image_hash`,`url_global`,`url_cn`) "
                    "VALUES ( %(taskId)s, %(type)s, %(parent)s, %(v_index)s, %(u_index)s, %(status)s, %(message_id)s, %(image_hash)s, %(url_global)s, %(url_cn)s)"
                )
                cursor.execute(add_task, params)
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
            self.cnx.commit()

        except Exception as e:
            print(e)
            self.cnx.rollback()
        finally:
            cursor.close()         
    def add_task(self, tokenId,  taskId, prompt):
        self.r.setex(taskId, 10 * 60 , prompt )
        self.__insert_prompt({
            'token_id': tokenId, 
            'taskId': taskId, 
            'prompt': prompt
        })
        self.__insert_task({
            'taskId': taskId,
            'type': None,
            'parent': None,
            'v_index': None,
            'u_index': None,
            'status': TaskStatus.CREATED.value,
            'message_id': None,
            'image_hash': None,
            'url_global': None,
            'url_cn': None
        })
    def commit_task(self, taskId: str ):
        self.__insert_task({
            'taskId': taskId,
            'type': None,
            'parent': None,
            'v_index': None,
            'u_index': None,
            'status': TaskStatus.COMMITTED.value,
            'message_id': None,
            'image_hash': None,
            'url_global': None,
            'url_cn': None
        })
        self.r.delete(taskId)
    def process_task(self, taskId: str ,  type: OutputType,  message_id: str ,   url: str):
        # download file and upload image
        file_name = str(url.split("_")[-1])
        hash = str(file_name.split(".")[0])
        url_cn = f'{taskId}/{file_name}'   
        # copy to s3 bucket
        print("== 🖼 upload image ==")
        loop = asyncio.new_event_loop() 
        asyncio.set_event_loop(loop)
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
            'parent': None,
            'v_index': None,
            'u_index': None,
            'status': TaskStatus.FINISHED.value,
            'message_id': message_id if type is not OutputType.UPSCALE else '',
            'image_hash': hash if type is not OutputType.UPSCALE else '',
            'url_global': url,
            'url_cn': url_cn
        })









