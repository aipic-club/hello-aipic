

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
from bot.DiscordUser.utils import refine_prompt
from data import Data_v2
from config import *



pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

celery = Celery('tasks', broker= celery_broker)

data = Data_v2(
        redis_url = redis_url,
        mysql_url= mysql_url,
        proxy = proxy,
        s3config = s3config
)
atexit.register(data.close)


gateway = Gateway( 
    id = int(celery_broker_id) , 
    data = data, 
    pool = pool
)




loop = asyncio.new_event_loop()
loop.create_task(gateway.create(loop))

t= Thread(target= loop.run_forever)
t.daemon = True
t.start()


@worker_init.connect
def worker_start(sender, **kwargs):
    print('worker started')
    # discordBot.start(os.environ.get("DISCORD.BOT.TOKEN"))

class BaseTask(celery.Task):
    def __init__(self):
        pass
  
@celery.task(name='ping')
def ping():
    print('pong')


@celery.task(name='prompt',bind=True, base=BaseTask)
def add_task(
        self,
        broker_id: int | None, 
        account_id: int | None, 
        token_id: int , 
        taskId: str, 
        prompt: str, 
        raw: str, 
        execute: bool
    ):
    new_prompt = refine_prompt(taskId, prompt)
    gateway.loop.run_in_executor(
        pool, 
        lambda: gateway.create_prompt(
            broker_id,
            account_id,
            token_id,
            taskId, 
            prompt, 
            new_prompt,
            raw,
            execute
        )
    )
    return

@celery.task(name='variation', bind=True,  base=BaseTask)
def variation(self, prompt: str,  task: dict[str, str],  index: str):
    new_prompt = refine_prompt(task['taskId'], prompt)

    gateway.loop.run_in_executor(
        pool, 
        lambda: gateway.create_variation(prompt, new_prompt, task=task, index= index)
    )    
    return
@celery.task(name='upscale',bind=True, base=BaseTask)
def upscale(self,  task: dict[str, str], index: str):

    gateway.loop.run_in_executor(
        pool, 
        lambda: gateway.create_upscale( task=task, index= index)
    )   
    return

@celery.task(name='reroll',bind=True, base=BaseTask)
def reroll(self, task: dict[str, str, str]):
    return


@celery.task(name="describe",bind=True, base=BaseTask)
def describe(self, task: dict[str, str, str]):
    return


if __name__ == '__main__':
    celery.worker_main(argv=['worker', '--pool=solo',  '-l', 'info', '-Q' , f'queue_{celery_broker_id},celery'])