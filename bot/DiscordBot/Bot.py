import os
import nextcord
from nextcord.ext import commands, tasks
from bot.DiscordBot.users import is_user_in_channel
from bot.DiscordBot.Q import imgqueue, imgresqueue

MJBotId= "936929561302675456"



class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # start the task to run in the background
        self.my_background_task.start()
    async def on_ready(self):
        print(self)
        print('Bot logged on as', self.user)
        self.is_ready = True

    async def on_message(self, message):
        # don't respond to ourselves
        print(message)
        #print(message.reference.resolved.author.id)

        author = message.author  
        channel_id = message.channel.id
        guild_id = message.guild.id
        if message.author == self.user:
            return
        if message.content == 'ping':
            await message.channel.send('pong')
        if author == MJBotId and is_user_in_channel(guild_id , channel_id ):
            print(message.content)
            pass


    @tasks.loop(seconds=1)  # task runs every 1 second
    async def my_background_task(self):
        print(1)
        # channel = self.get_channel(1084379543516749825)  # channel ID goes here
        # while not imgqueue.empty():
        #     id = imgqueue.get()
        #     file_path = os.path.join(
        #         os.getcwd(), 
        #         'tmp',
        #         f'{id}.jpg'
        #     )
        #     with open(file_path, 'rb') as f:
        #         picture = nextcord.File(f)
        #         res = await channel.send(file=picture)
        #         message = await channel.fetch_message(res.id)
        #         imgurl=message.attachments[0].url
        #         data = {'id': id , 'url': imgurl}
        #         dc = data.copy()
        #         print(dc)
        #         imgresqueue.put(dc)
        #         data.clear()
                
        #     os.unlink(file_path)
        pass
            

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in 