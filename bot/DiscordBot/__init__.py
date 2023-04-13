import os
import asyncio
from threading import Thread
import nextcord
from bot.DiscordBot.Bot import Bot
from bot.DiscordBot.Q import imgqueue, imgresqueue
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


# selfbot = Selfbot(
#     os.environ.get("DISCORD.SELF.TOKEN"),
#     os.environ.get("DISCORD.GUILDID"),
#     os.environ.get("DISCORD.CHANNELID")
# )

def handle_img_res():
    while True:
        res = imgresqueue.get()
        if res:
            print(res)


class DiscordBot():
    def __init__(self, redis_connection):
        pass
        
    def start(self, token, proxy):
        intents = nextcord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.message_content = True
        bot = Bot(intents=intents, proxy = proxy)
        loop = asyncio.get_event_loop()
        loop.create_task(bot.start(token))
        t1= Thread(target=loop.run_forever)
        t1.daemon = True
        t1.start()
        # t2 = Thread(target=handle_img_res, args=[])
        # t2.daemon = True
        # t2.start()
    def addMsg(self, id):
        imgqueue.put(id)
        
if __name__ == '__main__':
    pass
    #selfbot.sendPrompt("a tiny cute Audi Racing Car RS 5 in grey color with a sheep on the road of New York Brooklyn Bridge")
