import asyncio
from threading import Thread
import nextcord
from .Bot import Bot, MJBotId
from .Selfbot import Selfbot
from .users import users, is_user_in_channel
from .utils import get_taskId, output_type, is_committed, OutputType
from data import Data




class DiscordBot():
    def __init__(self,  proxy: str | None, redis_url: str, mysql_url: str):
        self.proxy = proxy
        self.data = Data(redis_url = redis_url, mysql_url= mysql_url)
    async def __on_message (self, message):
        author_id = message.author.id
        channel_id = message.channel.id
        guild_id = message.guild.id
        if message.author == self.bot_user:
            return
        if message.content == 'ping':
            await message.channel.send('pong')
        if author_id == MJBotId and is_user_in_channel(guild_id , channel_id ):
            #print("-- new message form MJ --")
            #print(message.content)
            taskId = get_taskId(message.content)
            print(f'==⏰== new task taskId is {taskId}')
            curType = output_type(message.content)
            if curType != OutputType.UNKNOWN:
                loop = asyncio.get_event_loop()
                loop.run_in_executor(None, lambda: 
                    self.data.updateTask(
                        taskId = taskId, 
                        type= curType , 
                        message_id= message.id , 
                        url = message.attachments[0].url if  (
                            curType == OutputType.DRAFT or 
                            curType == OutputType.UPSCALE or 
                            curType == OutputType.VARIATION
                        ) else None
                    )
                )
        
        print(author_id)
    def __startBot(self, token):
        intents = nextcord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.message_content = True
        self.userbot = Selfbot(users= users, proxy = self.proxy)
        
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

    def sendPrompt(self, taskId, prompt, new_prompt):
        self.data.addTask(taskId, prompt) 
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.userbot.sendPrompt(new_prompt))


        
if __name__ == '__main__':
    pass
