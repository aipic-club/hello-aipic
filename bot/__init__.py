

import os
import io
import asyncio
# import requests
from PIL import Image
import tempfile
import redis
from celery import Celery
from celery.signals import worker_init
from dotenv import load_dotenv, find_dotenv
from bot.DiscordBot import DiscordBot
from bot.DiscordBot.utils import refine_prompt
load_dotenv(find_dotenv())


redis_connection = redis.from_url(os.environ.get("REDIS"))
celery = Celery('tasks', broker=os.environ.get("CELERY.BROKER"))
discordBot = DiscordBot( os.environ.get("DISCORD.PROXY"), redis_connection)


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

#  no need to upload image to discord first any more
# @celery.task(name='upload_img',bind=True, base=BaseTask)
# async def upload_img_task(self,  src ):
#     # download the image first
#     id = self.request.id
#     downloadImage(src, id)
#     discordBot.addImg(id)
#     return id

@celery.task(name='query_task',bind=True, base=BaseTask)
def query_task():
    # query the finished tasks
    pass


@celery.task(name='send_prompt',bind=True, base=BaseTask)
def query_task(self, taskId, prompt):
    new_prompt = refine_prompt(taskId, prompt)
    print(new_prompt)
    discordBot.sendPrompt(taskId, new_prompt)
    id = self.request.id
    return id

discordBot.start(os.environ.get("DISCORD.BOT.TOKEN"))

if __name__ == '__main__':
   pass
    
