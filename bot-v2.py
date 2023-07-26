

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
from bot.DiscordUser.utils import refine_prompt, add_zoom
from data import Data
from config import *
from data.values import MJ_VARY_TYPE



pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

celery = Celery('tasks', broker= celery_broker)

data = Data(
    is_dev= is_dev,
    redis_url = redis_url,
    mysql_url= mysql_url,
    proxy = proxy,
    s3config = s3config
)
atexit.register(data.close)


gateway = Gateway( 
    celery_id = int(celery_id) , 
    data = data, 
    pool = pool
)




loop = asyncio.new_event_loop()
loop.create_task(gateway.create(loop))

t= Thread(target= loop.run_forever)
t.daemon = True
t.start()


# @worker_init.connect
# def worker_start(sender, **kwargs):
#     print('worker started')
#     # discordBot.start(os.environ.get("DISCORD.BOT.TOKEN"))

class BaseTask(celery.Task):
    def __init__(self):
        pass
  
@celery.task(name='ping')
def ping():
    print('pong')


@celery.task(name='imagine',bind=True, base=BaseTask)
def imagine(
        self,
        token_type: int,
        space_name: str, 
        prompt: str, 
        raw: str, 
        execute: bool
    ):
    new_prompt = refine_prompt(space_name, prompt)
    print(new_prompt)
    gateway.loop.run_in_executor(
        pool, 
        lambda: gateway.create_prompt(
            token_type,
            space_name, 
            prompt, 
            new_prompt,
            raw,
            execute
        )
    )
    return

@celery.task(name='variation', bind=True,  base=BaseTask)
def variation(self, prompt: str,  task: dict[str, str],  index: str):
    new_prompt = refine_prompt(task['space_name'], prompt)
    gateway.loop.run_in_executor(
        pool, 
        lambda: gateway.create_variation(
            prompt,
            new_prompt, 
            task=task, 
            index= index
        )
    )    
    return

@celery.task(name='vary',bind=True, base=BaseTask)
def vary(self, prompt: str, task: dict[str, str], type: str ):
    vary_type = MJ_VARY_TYPE(type)
    new_prompt = refine_prompt(task['space_name'], prompt)
    gateway.loop.run_in_executor(
        pool, 
        lambda: gateway.create_vary( 
            prompt, 
            new_prompt, 
            task=task, 
            type = vary_type
        )
    )   
    return

@celery.task(name='upscale',bind=True, base=BaseTask)
def upscale(self,  task: dict[str, str], index: str):
    gateway.loop.run_in_executor(
        pool, 
        lambda: gateway.create_upscale( 
            task=task, 
            index= index
        )
    )   
    return

@celery.task(name='zoom',bind=True, base=BaseTask)
def zoom(self, prompt: str, zoom:float, task: dict[str, str]):
    new_prompt = refine_prompt(task['space_name'], prompt) if prompt is not None else None
    new_prompt = add_zoom(prompt= new_prompt, zoom=zoom)
    gateway.loop.run_in_executor(
        pool, 
        lambda: gateway.create_zoom( 
            prompt=prompt,
            new_prompt=new_prompt,
            zoom= zoom,
            task=task
        )
    )   
    return

@celery.task(name='pan',bind=True, base=BaseTask)
def pan(self, prompt: str, type: str, task: dict[str, str]):
    new_prompt = refine_prompt(task['space_name'], prompt) if prompt is not None else None
    gateway.loop.run_in_executor(
        pool, 
        lambda: gateway.create_pan( 
            prompt=prompt,
            new_prompt=new_prompt,
            type=type,
            task=task
        )
    )   
    return

@celery.task(name='square',bind=True, base=BaseTask)
def square(self, task: dict[str, str, str]):
    gateway.loop.run_in_executor(
        pool,
        lambda: gateway.make_square(
            task=task
        )
    )
    return

@celery.task(name='reroll',bind=True, base=BaseTask)
def reroll(self, task: dict[str, str, str]):
    return

@celery.task(name="describe",bind=True, base=BaseTask)
def describe(self, space_name: str, url: str):
    gateway.loop.run_in_executor(
        pool, 
        lambda: gateway.describe_a_image( space_name=space_name, url= url)
    )  
    return

if __name__ == '__main__':
    celery.worker_main(
        argv=[
            'worker', 
            '--pool=solo',  
            '-l', 
            'info', 
            '-Q' , 
            ",".join([f'queue_{celery_id}',  'develop' if is_dev else 'celery'])
        ]
    )