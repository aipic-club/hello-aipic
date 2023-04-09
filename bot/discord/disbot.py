import discord
from nextcord.ext import commands, tasks


# intents = nextcord.Intents.default()
# intents.presences = True
# intents.members = True
# intents.message_content = True

proxy = 'http://127.0.0.1:7890'

BOT_TOKEN = 'MTA4NDM4OTk1NTc0MjIxNjIwNA.GkbgAv.frq88u03qNzcY2J0owCWRuhb59mWPLb7DbP-S8'


class DisBot(discord.Client):
    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == 'ping':
            await message.channel.send('pong')





# class DisBot(commands.Bot):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # start the task to run in the background
#         self.my_background_task.start()
#     async def process_commands(self, message):
#         """Override process_commands to listen to bots."""
#         print(message)
#         ctx = await self.get_context(message)
#         await self.invoke(ctx)

#     @tasks.loop(seconds=10)  # task runs every 60 seconds
#     async def my_background_task(self):
#         channel = self.get_channel(1084379543516749825)  # channel ID goes here
#         print(channel)
#         self.counter += 1
#         await channel.send(1)

#     @my_background_task.before_loop
#     async def before_my_task(self):
#         await self.wait_until_ready()  # wait until the bot logs in
#     @commands.Cog.event()
#     async def on_message(self, message: nextcord.Message):
#         # do something with the message here
#         pass        
    # @commands.Cog.event
    # async def on_ready():
    #     print(f'We have logged in as {bot.user}')
    # @commands.Cog.event
    # async def on_message(message):
    #     print(f'Message from {message.author}: {message.content}')
    # @commands.Cog.event
    # async def on_presence_update(before, after):
    #     print(before)
    # @commands.Cog.event
    # async def on_interaction(interaction):
    #     print(interaction)        



# bot = Bot(proxy = proxy, intents = intents)

# @bot.slash_command(description="Replies with pong!")
# async def ping(interaction: nextcord.Interaction):
#     print(interaction)
#     await interaction.send("Pong!", ephemeral=True)


    

# bot.run(BOT_TOKEN)