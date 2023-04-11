# import os
# import asyncio
# import discord
# from myDiscord.Bot import Bot
# from myDiscord.Selfbot import  Selfbot
# from dotenv import load_dotenv, find_dotenv
# load_dotenv(find_dotenv())
# intents = discord.Intents.default()
# intents.message_content = True
# proxy = os.environ.get("DISCORD.PROXY")
# bot = Bot(intents=intents, proxy= proxy)
# selfbot = Selfbot(
#     os.environ.get("DISCORD.SELF.TOKEN"),
#     os.environ.get("DISCORD.GUILDID"),
#     os.environ.get("DISCORD.CHANNELID")
# )



# if __name__ == '__main__':
#     selfbot.sendPrompt("a tiny cute Audi Racing Car RS 5 in grey color with a sheep on the road of New York Brooklyn Bridge")
#     # bot.run(os.environ.get("DISCORD.BOT.TOKEN"))


import os
import discord
from celery import Celery
from dotenv import load_dotenv, find_dotenv
from bot.myDiscord.Bot import Bot
from bot.myDiscord.Selfbot import  Selfbot

load_dotenv(find_dotenv())

intents = discord.Intents.default()
intents.message_content = True
proxy = os.environ.get("DISCORD.PROXY")


celery = Celery('tasks', broker=os.environ.get("CELERY_BROKER"))
bot = Bot(intents=intents, proxy= proxy)
selfbot = Selfbot(
    os.environ.get("DISCORD.SELF.TOKEN"),
    os.environ.get("DISCORD.GUILDID"),
    os.environ.get("DISCORD.CHANNELID")
)


class BaseTask(celery.Task):
    def __init__(self):
        bot.run(os.environ.get("DISCORD.BOT.TOKEN"))
        pass
    
@celery.task(name='ping')
def ping():
    print('pong')
@celery.task(name='upload_img',bind=True, base=BaseTask)
def upload_img_task(self, src , *args, **kwargs):
    print(src)

@celery.task(name='query_task',bind=True, base=BaseTask)
def query_task():
    # query the finished tasks
    pass


bot.run(os.environ.get("DISCORD.BOT.TOKEN"))
if __name__ == '__main__':
    pass
