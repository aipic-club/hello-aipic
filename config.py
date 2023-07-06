import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

is_dev = os.environ.get("MODE") == "DEV"
celery_id = os.environ.get("ID")
queue=os.environ.get("QUEUQE")
celery_broker =os.environ.get("CELERY.BROKER")
proxy =  os.environ.get("http_proxy")
redis_url = os.environ.get("REDIS")
mysql_url = os.environ.get("MYSQL")
s3config= {
    'aws_bucket_name': os.environ.get("AWS.BUCKET_NAME"),
    'aws_access_key_id' : os.environ.get("AWS.ACCESS_KEY_ID"),
    'aws_secret_access_key' : os.environ.get("AWS.SECRET_ACCESS_KEY"),
    'endpoint_url' : os.environ.get("AWS.ENDPOINT")
}

image_hostname = os.environ.get("IMG.HOSTNAME")

print(f'is dev mode : {is_dev}')