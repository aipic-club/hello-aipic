import os
import asyncio
import discord
from myDiscord.Bot import Bot
from myDiscord.Selfbot import  Selfbot
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())
intents = discord.Intents.default()
intents.message_content = True
proxy = os.environ.get("DISCORD.PROXY")
bot = Bot(intents=intents, proxy= proxy)
selfbot = Selfbot(
    os.environ.get("DISCORD.SELF.TOKEN"),
    os.environ.get("DISCORD.GUILDID"),
    os.environ.get("DISCORD.CHANNELID")
)



if __name__ == '__main__':
    selfbot.sendPrompt("a tiny cute Audi Racing Car RS 5 in grey color with a sheep on the road of New York Brooklyn Bridge")
    # bot.run(os.environ.get("DISCORD.BOT.TOKEN"))


