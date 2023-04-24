import asyncio
import atexit
from threading import Thread
import nextcord
from .Bot import Bot, MJBotId
from .Selfbot import Selfbot
from .utils import get_taskId, output_type, is_committed
from data import Data,TaskStatus,OutputType,users, is_user_in_channel




class DiscordBot():
    def __init__(self,  proxy: str | None, redis_url: str, mysql_url: str, s3config: dict):
        self.proxy = proxy
        self.data = Data(
            redis_url = redis_url,
            mysql_url= mysql_url,
            proxy = proxy,
            s3config = s3config
        )
        atexit.register(self.data.close)

    def __startBot(self, token):
        intents = nextcord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.message_content = True
        self.userbot = Selfbot( proxy = self.proxy)
        
        loop = asyncio.new_event_loop()
        bot = Bot(self.data , intents=intents, proxy = self.proxy, loop = loop)
        loop.create_task(bot.start(token))
        t= Thread(target=loop.run_forever)
        t.daemon = True
        t.start()


        

    def start(self, token: str) -> None:
        self.__startBot(token)

    def send_prompt(self, token_id, taskId, prompt, new_prompt):
        self.data.add_task(token_id, taskId, prompt) 
        loop = asyncio.new_event_loop()
        loop.run_until_complete(self.userbot.send_prompt(new_prompt))
        loop.close()
    def send_variation(self, task: dict[str, str, str], index: str):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(
            self.userbot.send_variation(
                task['taskId'],
                messageId = task['message_id'],
                messageHash = task['message_hash'], 
                index = index
            )
        )
        loop.close()
    def send_upscale(self, task: dict[str, str, str], index: str):
        loop = asyncio.new_event_loop()
        loop.run_until_complete(
            self.userbot.send_upscale(
                task['taskId'],
                messageId = task['message_id'],
                messageHash = task['message_hash'], 
                index = index
            )
        )
        loop.close()
    


        
if __name__ == '__main__':
    pass
