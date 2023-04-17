import asyncio
from threading import Thread
import nextcord
from .Bot import Bot
from .Selfbot import Selfbot
from .users import users
from cache import MyRedis, resq



class DiscordBot():
    def __init__(self,  proxy, redis_url):
        self.proxy = proxy
        self.myRedis = MyRedis(url= redis_url)
    def __startBot(self, token):
        intents = nextcord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.message_content = True
        bot = Bot(intents=intents, proxy = self.proxy)
        self.userbot = Selfbot(users= users, proxy = self.proxy)




        loop = asyncio.get_event_loop()
        loop.create_task(bot.start(token))
        t1= Thread(target=loop.run_forever)
        t1.daemon = True
        t1.start()





    def __startHandler(self):
        loop2 = asyncio.get_event_loop()
        loop2.create_task(self.handleResult())
        t2= Thread(target=loop2.run_forever)
        t2.daemon = True
        t2.start()



    def start(self, token):
        self.__startBot(token) 
        self.__startHandler()

    async def __sendPrompt(self, taskId, prompt, new_prompt):
        return await asyncio.gather(*[
            self.myRedis.addTask(taskId, prompt) , 
            self.userbot.sendPrompt(new_prompt)
        ], return_exceptions=True)

    def sendPrompt(self, taskId, prompt, new_prompt):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.__sendPrompt(taskId, prompt, new_prompt))

    async def handleResult(self):
        while True:
            try:
                item = resq.get()
                print(item)
            except asyncio.QueueEmpty:
                # print('Consumer: got nothing, waiting a while...')
                await asyncio.sleep(1)

        

    
        
if __name__ == '__main__':
    pass
    #selfbot.sendPrompt("a tiny cute Audi Racing Car RS 5 in grey color with a sheep on the road of New York Brooklyn Bridge")
