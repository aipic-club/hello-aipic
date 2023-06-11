import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

celery_broker_id = os.environ.get("ID")
celery_broker =os.environ.get("CELERY.BROKER")
proxy =  os.environ.get("http_proxy")
redis_url = os.environ.get("REDIS")
mysql_url = os.environ.get("MYSQL")
s3config= {
    'aws_access_key_id' : os.environ.get("AWS.ACCESS_KEY_ID"),
    'aws_secret_access_key' : os.environ.get("AWS.SECRET_ACCESS_KEY"),
    'endpoint_url' : os.environ.get("AWS.ENDPOINT")
}
