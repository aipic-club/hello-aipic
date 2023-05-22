import asyncio
import atexit
from threading import Thread
import nextcord
from .pool import pool
from .Bot import Bot
from .Selfbot import Selfbot
from data import Data,config



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

        discord_users = self.data.get_discord_users()
        
        self.userbot = Selfbot( proxy = self.proxy)
        self.userbot.register_discord_users(discord_users)

        loop = asyncio.new_event_loop()
        bot = Bot(self.data , intents=intents, proxy = self.proxy, loop = loop)
        loop.create_task(bot.start(token))
        t= Thread(target=loop.run_forever)
        t.daemon = True
        t.start()




    async def send_prompt_with_check(self, token_id, taskId, prompt, new_prompt):
        print(f"==🔖== prompt {prompt}")
        self.data.cache_task(taskId, prompt )
        await self.userbot.send_prompt(new_prompt)
        # await asyncio.sleep(config['wait_time'] - 10)
        # self.data.check_task(taskId)
    
    async def send_variation_with_check(self, task: dict[str, str, str], index: str):
        pass
    
    async def send_variation_with_check(self, task: dict[str, str, str], index: str):
        pass  



    def start(self, token: str) -> None:
        self.__startBot(token)


    def send_prompt(self, token_id, taskId, prompt, new_prompt):
        loop = asyncio.get_event_loop()
        loop.call_soon(self.send_prompt_with_check(token_id, taskId, prompt, new_prompt))


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
