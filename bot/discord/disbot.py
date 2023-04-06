import nextcord
from nextcord.ext import commands, tasks


intents = nextcord.Intents.default()
intents.presences = True
intents.members = True
intents.message_content = True

proxy = 'http://127.0.0.1:7890'


BOT_TOKEN = 'MTA4NDM4OTk1NTc0MjIxNjIwNA.GkbgAv.frq88u03qNzcY2J0owCWRuhb59mWPLb7DbP-S8'

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # an attribute we can access from our task
        self.counter = 0

        # start the task to run in the background
        self.my_background_task.start()
    async def process_commands(self, message):
        """Override process_commands to listen to bots."""
        print(message)
        ctx = await self.get_context(message)
        await self.invoke(ctx)

    @tasks.loop(seconds=10)  # task runs every 60 seconds
    async def my_background_task(self):
        channel = self.get_channel(1084379543516749825)  # channel ID goes here
        print(channel)
        self.counter += 1
        await channel.send(1)

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready()  # wait until the bot logs in



bot = Bot(proxy = proxy, intents = intents)

# @bot.slash_command(description="Replies with pong!")
# async def ping(interaction: nextcord.Interaction):
#     print(interaction)
#     await interaction.send("Pong!", ephemeral=True)

@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')
@bot.event
async def on_message(message):
    print(f'Message from {message.author}: {message.content}')
@bot.event
async def on_presence_update(before, after):
    print(before)
@bot.event
async def on_interaction(interaction):
    print(interaction)
    

bot.run(BOT_TOKEN)