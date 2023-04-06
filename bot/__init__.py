import yaml
from celery import Celery

file = open("./config.yaml", 'r', encoding="utf-8")
file_data = file.read()
file.close()
conf = yaml.safe_load(file_data)

celery = Celery('tasks', broker=conf['celery']['broker'], backend=conf['celery']['backend'])

class BaseTask(celery.Task):
    def __init__(self):
        pass
    
@celery.task(name='ping')
def ping():
    print('pong')
@celery.task(name='add_task',bind=True, base=BaseTask)
def add_task(self,  id ,  prompt):
    print(id, prompt)
