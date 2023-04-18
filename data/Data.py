import json
import redis
from urllib.parse import urlparse
import mysql.connector
from mysql.connector import errorcode
from .status import TaskStatus


class Data():
    session = None
    client = None
    def __init__(self, redis_url: str, mysql_url:str) -> None:
        parsed = urlparse(mysql_url)
        try:
            self.cnx = mysql.connector.connect(
                user= parsed.username, 
                password=parsed.password,
                host=parsed.hostname,
                port=parsed.port,
                database=parsed.path.lstrip('/')
            )
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print("Database does not exist")
            else:
                print(err)
        self.r = redis.from_url(redis_url)
    def __del__(self):
        if self.session:
            self.session.close()
        if self.client:
            self.client.close()
    def add_task(self, taskId, prompt):
        self.r.setex(taskId, 10 * 60 , json.dumps({
            'prompt': prompt,
            'type': TaskStatus.PENDING.value
        }))
        # insert a blank record to db
        # https://dev.mysql.com/doc/connector-python/en/connector-python-example-cursor-transaction.html
        cursor = self.cnx.cursor()
        sql = f"INSERT INTO `tasks` (`id`,`taskID`,`prompt`) VALUES( NULL, %s, %s)"
        params = (taskId, prompt)
        cursor.execute(sql, params)
        self.cnx.commit()
        cursor.close()
    """
    remove task from redis
    """
    def remove_task(self, taskId):
        self.r.delete(taskId)
        pass
        
    def update_task(self, taskId: str , type: TaskStatus, message_id , url):
        print(taskId, type , message_id, url )        
        # download file



        # upload to bitiful

        # remove redis data

        # update mysql record
        if type == TaskStatus.COMMITTED:
            pass
        else:
            cursor = self.cnx.cursor()
            sql = f"INSERT INTO `tasks` (`id`,`taskID`,`prompt`, ) VALUES( NULL, %s, %s)"
            params = (taskId, '')
            cursor.execute(sql, params)
            self.cnx.commit()
            cursor.close()




