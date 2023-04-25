import redis
import asyncio
import logging
from urllib.parse import urlparse
import mysql.connector.pooling
from mysql.connector import errorcode
from .values import TaskStatus,OutputType,Cost, SysError
from .utils import current_time,is_expired
from .FileHandler import FileHandler

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


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
    def __insert_prompt(self, params: dict):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor()
        try:
            add_prompt = ("INSERT INTO `prompts` (`token_id`, `taskId`,`prompt`) VALUES( %(token_id)s, %(taskId)s, %(prompt)s)")
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
                add_task = (
                    "INSERT INTO `tasks` "
                    "(`taskID`,`type`,`reference`,`v_index`,`u_index`,`status`,`message_id`,`message_hash`,`url_global`,`url_cn`) "
                    "VALUES ( %(taskId)s, %(type)s, %(reference)s, %(v_index)s, %(u_index)s, %(status)s, %(message_id)s, %(message_hash)s, %(url_global)s, %(url_cn)s)"
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
            cnx.commit()

        except Exception as e:
            print(e)
            cnx.rollback()
        finally:
            cursor.close()
            cnx.close()
    def check_token_and_get_id(self, token: str) -> int | SysError:
        cnx = self.pool.get_connection()
        cursor = cnx.cursor()
        try:
            sql = "SELECT `id`,`expire_at` FROM `tokens` WHERE token = %s"
            val = (token,)
            cursor.execute(sql, val)
            record = cursor.fetchone()
            if record is not None:
                id = record[0]
                expire_at = record[1]
                if is_expired(expire_at):
                    return SysError.TOKEN_EXPIRED
                else:
                    return id
            else:
                return SysError.TOKEN_NOT_EXIST
        finally:
            cursor.close()
            cnx.close()
    def add_task(self, token_id,  taskId, prompt):
        self.r.setex(taskId, 10 * 60 , prompt )
        self.__insert_prompt({
            'token_id': token_id, 
            'taskId': taskId, 
            'prompt': prompt
        })
        self.__insert_task({
            'taskId': taskId,
            'type': None,
            'reference': None,
            'v_index': None,
            'u_index': None,
            'status': TaskStatus.CREATED.value,
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
        self.r.delete(taskId)
    def process_task(self, taskId: str ,  type: OutputType, reference: int | None,  message_id: str ,   url: str):
        # download file and upload image
        file_name = str(url.split("_")[-1])
        hash = str(file_name.split(".")[0])
        url_cn = f'/{taskId}/{file_name}'   
        self.r.delete(taskId)
        # copy to s3 bucket
        print("==🖼upload image ==")
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
            'reference': reference,
            'v_index': None,
            'u_index': None,
            'status': TaskStatus.FINISHED.value,
            'message_id': message_id if type is not OutputType.UPSCALE else '',
            'message_hash': hash if type is not OutputType.UPSCALE else '',
            'url_global': url,
            'url_cn': url_cn
        })
    def get_task_by_id(self, token_id: int, id: int) -> dict[str, str]:
        # https://stackoverflow.com/questions/29772337/python-mysql-connector-unread-result-found-when-using-fetchone
        cnx = self.pool.get_connection()
        cursor = cnx.cursor()
        try:
            ### check the id is belong to the token
            ### sql = "SELECT t1.taskId,t1.message_id,t1.message_hash FROM `tasks` t1 LEFT JOIN `prompts` t2  ON t1.taskId = t2.taskId WHERE t2.token_id = %s AND t1.id = %s LIMT 1"
            sql = " SELECT t1.taskId,t1.message_id,t1.message_hash FROM `tasks` t1 LEFT JOIN (SELECT taskId FROM `prompts` WHERE id = %s) t2 ON t1.taskId = t2.taskId WHERE t1.id = %s LIMIT 1"
            val = (token_id, id,)
            cursor.execute(sql, val)
            record = cursor.fetchone()
            print(record)
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
    def sum_costs_by_token_id(self):
        pass
    def sum_costs_by_taskID():
        # SELECT  t1.taskId, SUM(t2.cost) as cost FROM mj.tasks t1 LEFT JOIN mj.token_audit t2 ON t2.task_id = t1.id GROUP BY t1.taskId;
        pass
    def get_prompts_by_token_id(self, token_id,  page: int = 0, page_size: int = 10):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)
        records = None
        try:
            sql = "SELECT `id`,`taskId`,`prompt`,`create_at` FROM `prompts` WHERE `token_id` = %s ORDER BY `id` DESC LIMIT %s, %s"
            offset = (page - 1) * page_size
            val = (token_id, offset, page_size, )
            cursor.execute(sql, val)
            records = cursor.fetchall()
            print(records)
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
                sql = "SELECT * FROM `tasks` WHERE `taskId` = %s LIMIT %s, %s"
                offset = (page - 1) * page_size
                val = (taskId, offset, page_size, )
                cursor.execute(sql, val)
                records = cursor.fetchall()
        finally:
            cursor.close()
            cnx.close()
        return records









