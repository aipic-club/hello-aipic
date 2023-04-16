import os
import asyncio
from threading import Thread
import nextcord
import yaml
from bot.DiscordBot.Bot import Bot
from bot.DiscordBot.Selfbot import Selfbot
from bot.DiscordBot.Q import  imgresqueue
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

file = open( os.path.join( os.getcwd(), 'users.yaml') , 'r', encoding="utf-8")
file_data = file.read()
file.close()
users = yaml.safe_load(file_data)


class DiscordBot():
    def __init__(self,  proxy, redis_connection):
        self.proxy = proxy

        self.event_loop_a = asyncio.new_event_loop()
        self.event_loop_b = asyncio.new_event_loop()

    def __startBot(self, token):
        intents = nextcord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.message_content = True
        bot = Bot(intents=intents, proxy = self.proxy)
        self.userbot = Selfbot(users= users, proxy = self.proxy)
        
        
        event_loop_a = self.event_loop_a
        event_loop_a.create_task(bot.start(token))
        t1= Thread(target=event_loop_a.run_forever)
        t1.daemon = True
        t1.start()

      

        t2= Thread(target=self.userbot.keep_online)
        t2.daemon = True
        t2.start()



    def start(self, token):
        self.__startBot(token)    

        # loop = asyncio.get_event_loop()
        # loop.create_task(bot.start(token))
        # t1= Thread(target=loop.run_forever)
        # t1.daemon = True
        # t1.start()
    def sendPrompt(self, taskId,  prompt):
        # add task to redis first

        # send to discord
        loop = asyncio.get_event_loop()
        # loop.create_task(self.userbot.sendPrompt(prompt))
        loop.run_until_complete(self.userbot.sendPrompt(prompt))
        #self.userbot.sendPrompt(prompt)
        

    
        
if __name__ == '__main__':
    pass
    #selfbot.sendPrompt("a tiny cute Audi Racing Car RS 5 in grey color with a sheep on the road of New York Brooklyn Bridge")
