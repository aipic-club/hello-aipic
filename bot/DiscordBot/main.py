import asyncio
import atexit
from threading import Thread
import nextcord

from nextcord.ext import commands
from .pool import pool
from .Bot import Bot
from .Selfbot import Selfbot
from data import Data,config, TaskStatus,ImageOperationType



class DiscordBot():
    def __init__(self,  proxy: str | None, redis_url: str, mysql_url: str, s3config: dict):
        self.proxy = proxy
        self.data = Data(
            redis_url = redis_url,
            mysql_url= mysql_url,
            proxy = proxy,
            s3config = s3config
        )
        self.loop = asyncio.new_event_loop()
        atexit.register(self.data.close)



    async def __startBot(self, token):
        intents = nextcord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.message_content = True

        discord_users = self.data.get_discord_users()
        
        self.userbot = Selfbot( proxy = self.proxy)
        self.userbot.register_discord_users(discord_users)

        bot = Bot( self.data , command_prefix='/', intents=intents, proxy = self.proxy)



        @bot.command()
        async def test(ctx):
            print(12344444)
            await ctx.send("some random text")



        await bot.start(token)
   



    async def check(self, taskId):
        await asyncio.sleep(config['wait_time'] - 10)
        self.data.check_task(taskId)


    async def send_prompt_with_check(self, token_id, taskId, prompt, new_prompt):
        print(f"==🔖== prompt {prompt}")
        self.data.prompt_task(token_id, taskId, TaskStatus.CONFIRMED )
        await self.userbot.send_prompt(new_prompt)
        self.loop.create_task(self.check(taskId))

    
    async def send_variation_with_check(self, prompt,  task: dict[str, str, str], index: str):
        print(f"==🔖== variation {task['taskId']}")
        self.data.image_task(task['taskId'], task['message_hash'], ImageOperationType.VARIATION, index)
        await self.userbot.send_variation(
            task['taskId'],
            prompt=prompt,
            messageId = task['message_id'],
            messageHash = task['message_hash'], 
            index = index
        )
    
    async def send_upscale_with_check(self, task: dict[str, str, str], index: str):
        self.data.image_task(task['taskId'], task['message_hash'], ImageOperationType.UPSCALE)
        self.userbot.send_upscale(
            task['taskId'],
            messageId = task['message_id'],
            messageHash = task['message_hash'], 
            index = index
        )  



    async def start(self, token: str) -> None:
        await self.__startBot(token)


    def send_prompt(self, token_id, taskId, prompt, new_prompt) -> None:
        self.loop.create_task(
            self.send_prompt_with_check(token_id, taskId, prompt, new_prompt)
        )


    def send_variation(self, prompt: str, task: dict[str, str, str], index: str):
        self.loop.create_task(
            self.send_variation_with_check(prompt, task, index)
        )
    def send_upscale(self, task: dict[str, str, str], index: str):
        self.loop.create_task(
            self.send_upscale_with_check(task, index)
        )
    


        
if __name__ == '__main__':
    pass
