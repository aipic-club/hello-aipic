import nextcord
from nextcord.ext import commands
from nextcord.ui import Button
from nextcord import ButtonStyle

TESTING_GUILD_ID = 1101146791925256294  # Replace with your guild ID

intents = nextcord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='$', proxy="http://127.0.0.1:7890", intents=intents)



@bot.event
async def on_ready():
    print(f'We have logged in as {bot.user}')


@bot.event
async def on_interaction(interaction):
    print(interaction.id)    

@bot.event
async def on_message(message):
    if message.content == "!button":
        button = nextcord.ui.Button(label="Click me!", style=nextcord.ButtonStyle.green)
        view = nextcord.ui.View()
        view.add_item(button)
        await message.channel.send("Click the button below!", view=view)



@bot.command()
async def test(ctx):
    await ctx.send(123)








bot.run("MTA4NDM4OTk1NTc0MjIxNjIwNA.GkbgAv.frq88u03qNzcY2J0owCWRuhb59mWPLb7DbP-S8")