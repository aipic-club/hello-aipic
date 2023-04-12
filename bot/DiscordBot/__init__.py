import os
import asyncio
from threading import Thread
import nextcord
from bot.DiscordBot.Bot import Bot
from bot.DiscordBot.Bot import queue
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())


# selfbot = Selfbot(
#     os.environ.get("DISCORD.SELF.TOKEN"),
#     os.environ.get("DISCORD.GUILDID"),
#     os.environ.get("DISCORD.CHANNELID")
# )

class DiscordBot():
    def __init__(self):
        pass
        # while not self.__queue.empty():
        #     data = self.__queue.get()
        #     print('new data , {data}')
        #     bot.sendMsg(data)

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
        # t1 = threading.Thread(target=self.__startDisBot, args=[token,])
        # t1.daemon = True
        # t1.start()
    def addMsg(self, id):

        queue.put(id)
        
if __name__ == '__main__':
    pass
    #selfbot.sendPrompt("a tiny cute Audi Racing Car RS 5 in grey color with a sheep on the road of New York Brooklyn Bridge")
