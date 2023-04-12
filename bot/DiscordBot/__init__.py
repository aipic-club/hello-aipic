import os
import threading
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
    def __init__(self, proxy):
        intents = nextcord.Intents.default()
        intents.presences = True
        intents.members = True
        intents.message_content = True
        self.bot = Bot(intents=intents, proxy= proxy)
        # while not self.__queue.empty():
        #     data = self.__queue.get()
        #     print('new data , {data}')
        #     bot.sendMsg(data)
    def __startDisBot(self, token):
        self.bot.run(token)
    def run(self, token):
        t1 = threading.Thread(target=self.__startDisBot, args=[token,])
        t1.daemon = True
        t1.start()
    def addMsg(self, msg):
        print('message')
        print(msg)
        queue.put(msg)
        
    


if __name__ == '__main__':
    pass
    #selfbot.sendPrompt("a tiny cute Audi Racing Car RS 5 in grey color with a sheep on the road of New York Brooklyn Bridge")
    # bot.run(os.environ.get("DISCORD.BOT.TOKEN"))
