import asyncio
from nextcord.ext import commands, tasks
from .utils import get_taskId, output_type, is_committed
from data import Data,TaskStatus,OutputType,users, is_user_in_channel






MJBotId= 936929561302675456




class Bot(commands.Bot):
    def __init__(self, data: Data, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # start the task to run in the background
        self.data = data
        # self.my_background_task.start()
    async def on_ready(self):
        print(f' Logged in as {self.user} (ID: {self.user.id})')
    async def on_message(self, message):
        reference_id = getattr(message.reference, 'message_id', None) 
        message_id = message.id
        author_id = message.author.id
        channel_id = message.channel.id
        guild_id = message.guild.id
        content = message.content
        # print("===========")
        # print(message.application)
        # print("===========")
        # print(message.components)
        # print("===========")
        if message.author == self.user:
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

    # @tasks.loop(seconds=10)  # task runs every 10 seconds
    # async def my_background_task(self):
    #     ### TODO not work here
    #     pass

    # @my_background_task.before_loop
    # async def before_my_task(self):
    #     await self.wait_until_ready()  # wait until the bot logs in