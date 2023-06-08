from abc import abstractmethod
from urllib.parse import urlparse
import mysql.connector.pooling
from mysql.connector import errorcode

class MySQLInterface:
    @abstractmethod
    def __init__(self, url: str) -> None:
        pass

class MySQLBase(MySQLInterface):
    def __init__(self, url: str) -> None:
        parsed = urlparse(url)
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
    def close(self):
        self.pool.close()

    def mysql_fetchall(self, sql, params: dict):
        cnx = self.pool.get_connection()
        cursor = cnx.cursor(dictionary=True)  
        records = None
        try:
            cursor.execute(sql,params)
            records = cursor.fetchall()
        finally:
            cursor.close()
            cnx.close()
        return records
    
    def mysql_fetchone(self, sql, params: dict, _cnx = None):
        cnx = self.pool.get_connection() if _cnx is None else _cnx
        cursor = cnx.cursor(dictionary=True)  
        record = None
        try:
            cursor.execute(sql,params)
            record = cursor.fetchone()
        finally:
            if _cnx is None:
                cursor.close()
                cnx.close()
        return record
    def mysql_execute(self, sql, params: dict, lastrowid: bool = False, _cnx = None):
        cnx = self.pool.get_connection() if _cnx is None else _cnx
        cursor = cnx.cursor(dictionary=True)  
        _id = None
        try:
            cursor.execute(sql,params)
            _id = cursor.lastrowid if lastrowid else None
            if _cnx is None:
                cnx.commit()
        finally:
            if _cnx is None:
                cursor.close()
                cnx.close()
        return _id