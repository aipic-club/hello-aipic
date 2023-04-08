import yaml
import time
from celery import Celery

file = open("./config.yaml", 'r', encoding="utf-8")
file_data = file.read()
file.close()
conf = yaml.safe_load(file_data)

#celery = Celery('tasks', broker=conf['celery']['broker'], backend=conf['celery']['backend'])
celery = Celery('tasks', broker=conf['celery']['broker'])

class BaseTask(celery.Task):
    def __init__(self):
        pass
    
@celery.task(name='ping')
def ping():
    print('pong')
@celery.task(name='add_mj_task',bind=True, base=BaseTask)
def add_task(self,arg1, arg2, *args, **kwargs):
    print(arg1, arg2)
    # parse data to mj prompt and send it to discord bot
@celery.task(name='query_task',bind=True, base=BaseTask)
def query_task():
    # query the finished tasks
    pass