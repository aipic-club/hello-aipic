

import os
import atexit
# import requests
from threading import Thread
import concurrent.futures
import asyncio
from PIL import Image
from celery import Celery
from celery.signals import worker_init
from bot.DiscordUser.Gateway import Gateway
from bot.DiscordBot import refine_prompt, pool
from data import Data
from config import *



pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

celery = Celery('tasks', broker= celery_broker)
data = Data(
        redis_url = redis_url,
        mysql_url= mysql_url,
        proxy = proxy,
        s3config = s3config
)
atexit.register(data.close)

gateway = Gateway( data = data , pool = pool)

loop = asyncio.new_event_loop()
gateway.create(loop = loop)
t= Thread(target=loop.run_forever)
t.daemon = True
t.start()



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
    
    loop.run_in_executor(pool, lambda: gateway.create_prompt(token_id, taskId, prompt, new_prompt))

    return taskId

@celery.task(name='variation',bind=True, base=BaseTask)
def variation(self, prompt: str,  task: dict[str, str, str],  index: str):
    #discordBot.loop.run_in_executor(pool, lambda: discordBot.send_variation( prompt, task, index))
    
    return
@celery.task(name='upscale',bind=True, base=BaseTask)
def upscale(self,  task: dict[str, str, str], index: str):
    #discordBot.loop.run_in_executor(pool, lambda: discordBot.send_upscale(task, index))
    
    return



if __name__ == '__main__':
    celery.worker_main(argv=['worker', '-l', 'info', '--pool=solo'])
