import asyncio
import atexit
from threading import Thread
import nextcord
from .Bot import Bot, MJBotId
from .Selfbot import Selfbot
from .utils import get_taskId, output_type, is_committed
from data import Data,TaskStatus,OutputType
from data import users, is_user_in_channel




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
    async def __on_message (self, message):
 
        reference_id = getattr(message.reference, 'message_id', None) 
        message_id = message.id
        author_id = message.author.id
        channel_id = message.channel.id
        guild_id = message.guild.id
        content = message.content
        print("===========")
        print(message.application)
        print("===========")
        print(message.components)
        print("===========")
        if message.author == self.bot_user:
            return
        if content == 'ping':
            await message.channel.send('pong')
        if author_id == MJBotId and is_user_in_channel(guild_id , channel_id ):
            #print("-- new message form MJ --")
            #print(message.content)
            taskId = get_taskId(content)
            print(f'==⏰== taskId {taskId}')
            task_is_committed = is_committed(content)
            if task_is_committed:
                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, lambda: 
                    self.data.commit_task(
                        taskId = taskId
                    )
                )
            else:
                curType = output_type(content)
                if curType is not None:
                    attachment = message.attachments[0].url
                    loop = asyncio.get_event_loop()
                    loop.run_in_executor(None, lambda: 
                        self.data.process_task(
                            taskId = taskId, 
                            type= curType , 
                            reference= reference_id,
                            message_id= message_id , 
                            url = attachment
                        )
                    )
        
        # print(author_id)
    def __startBot(self, token):
        intents = nextcord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.message_content = True
        self.userbot = Selfbot( proxy = self.proxy)
        
        loop = asyncio.new_event_loop()
        bot = Bot(intents=intents, proxy = self.proxy, loop = loop)
        self.bot_user  = bot.user
        bot.on_message  = self.__on_message


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
