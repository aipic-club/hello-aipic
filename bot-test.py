import os
from bot.DiscordBot.Selfbot import Selfbot
from dotenv import load_dotenv, find_dotenv
from bot.DiscordBot import DiscordBot

proxy =  os.environ.get("DISCORD.PROXY")
selfbot = Selfbot(proxy)
# good
response  = selfbot.sendPrompt("an Asian girl jumps into a river, full body --v 5 --no .1qwsdf")
print(response)
#bad 
response  = selfbot.sendPrompt("a nude Asian girl jumps into a river, full body --v 5 --no .1dflxe")
print(response)
