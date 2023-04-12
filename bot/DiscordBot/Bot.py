from queue import Queue
import nextcord
from nextcord.ext import commands, tasks

queue = Queue()

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # start the task to run in the background
        self.my_background_task.start()
    async def on_ready(self):
        print('Logged on as', self.user)
        self.is_ready = True

    async def on_message(self, message):
        # don't respond to ourselves
        print(message)
        #print(message.reference.resolved.author.id)
        if message.author == self.user:
            return
        if message.content == 'ping':
            await message.channel.send('pong')

    @tasks.loop(seconds=1)  # task runs every 60 seconds
    async def my_background_task(self):
        channel = self.get_channel(1084379543516749825)  # channel ID goes here
        msg = queue.get()
        if msg:
            await channel.send(msg)

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in 