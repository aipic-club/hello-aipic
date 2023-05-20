

import os
# import requests
import asyncio
import concurrent.futures
from PIL import Image
from celery import Celery
from celery.signals import worker_init
from dotenv import load_dotenv, find_dotenv
from bot import DiscordBot
from bot.DiscordBot import refine_prompt

load_dotenv(find_dotenv())

pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)
celery = Celery('tasks', broker=os.environ.get("CELERY.BROKER"))


discordBot = DiscordBot( 
    os.environ.get("http_proxy"), 
    redis_url = os.environ.get("REDIS"),
    mysql_url = os.environ.get("MYSQL"),
    s3config= {
        'aws_access_key_id' : os.environ.get("AWS.ACCESS_KEY_ID"),
        'aws_secret_access_key' : os.environ.get("AWS.SECRET_ACCESS_KEY"),
        'endpoint_url' : os.environ.get("AWS.ENDPOINT")
    }
)



@worker_init.connect
def worker_start(sender, **kwargs):
    print('worker started')
    # discordBot.start(os.environ.get("DISCORD.BOT.TOKEN"))


#https://stackoverflow.com/questions/37751877/downloading-image-with-pil-and-requests
# def downloadImage(img_url, id):
#     buffer = tempfile.SpooledTemporaryFile(max_size=1e9)
#     r = requests.get(img_url, stream=True)
#     if r.status_code == 200:
#         downloaded = 0
#         filesize = int(r.headers['content-length'])
#         for chunk in r.iter_content(chunk_size=1024):
#             downloaded += len(chunk)
#             buffer.write(chunk)
#             print(downloaded/filesize)
#         buffer.seek(0)
#         i = Image.open(io.BytesIO(buffer.read()))
#         i.save(os.path.join(
#             os.getcwd(), 
#             'tmp',
#             f'{id}.jpg'
#         ), quality=100)
#     buffer.close() 
class BaseTask(celery.Task):
    def __init__(self):
        pass
  
@celery.task(name='ping')
def ping():
    print('pong')


@celery.task(name='prompt',bind=True, base=BaseTask)
def add_task(self, token_id , taskId, prompt):
        
        new_prompt = refine_prompt(taskId, prompt)
        loop = asyncio.get_event_loop()
        loop.run_in_executor(pool, discordBot.send_prompt(token_id, taskId, prompt, new_prompt))

        # id = self.request.id
        return taskId

@celery.task(name='variation',bind=True, base=BaseTask)
def variation(self, task: dict[str, str, str], prompt: str, index: str):
    discordBot.send_variation(task, index)
@celery.task(name='upscale',bind=True, base=BaseTask)
def upscale(self,  task: dict[str, str, str], index: str):
    discordBot.send_upscale(task, index)



discordBot.start(os.environ.get("DISCORD.BOT.TOKEN"))

if __name__ == '__main__':
   pass
    
