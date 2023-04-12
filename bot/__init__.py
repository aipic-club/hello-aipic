

import os
import discord
from celery import Celery
from celery.signals import worker_init
from dotenv import load_dotenv, find_dotenv
from bot.DiscordBot import DiscordBot

load_dotenv(find_dotenv())

intents = discord.Intents.default()
intents.message_content = True



celery = Celery('tasks', broker=os.environ.get("CELERY.BROKER"))
discordBot = DiscordBot(os.environ.get("DISCORD.PROXY"))


@worker_init.connect
def worker_start(sender, **kwargs):
    print('worker started')
    discordBot.run(os.environ.get("DISCORD.BOT.TOKEN"))



class BaseTask(celery.Task):
    def __init__(self):
        pass
    
@celery.task(name='ping')
def ping():
    print('pong')
@celery.task(name='upload_img',bind=True, base=BaseTask)
def upload_img_task(self,  src ):
    print(src)
    discordBot.addMsg(src)
    return src

@celery.task(name='query_task',bind=True, base=BaseTask)
def query_task():
    # query the finished tasks
    pass

if __name__ == '__main__':
   pass
    
