import os
import asyncio
from dotenv import load_dotenv, find_dotenv
from bot import DiscordUser

from bot.DiscordUser.values import Events
load_dotenv(find_dotenv())


token = "MTAyMTYxMjYyODk4MTg0NjAzOA.GdtMD6.mPHb_iBXl7-oGAQD6A_Bhhj3nvrhWiWGowPOfw"

user = DiscordUser(proxy= os.environ.get("http_proxy"), token = token)

asyncio.run(
    user.run()
)


# def main():
#     print(Events)
#     pass

# print(__name__)
# if __name__ == "__main__":
#     main()




