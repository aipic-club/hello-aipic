import os
import asyncio
from dotenv import load_dotenv, find_dotenv
from bot import Users, DiscordUser

from bot.DiscordUser.values import Events
load_dotenv(find_dotenv())


users = Users( 
    os.environ.get("http_proxy"), 
    redis_url = os.environ.get("REDIS"),
    mysql_url = os.environ.get("MYSQL"),
    s3config= {
        'aws_access_key_id' : os.environ.get("AWS.ACCESS_KEY_ID"),
        'aws_secret_access_key' : os.environ.get("AWS.SECRET_ACCESS_KEY"),
        'endpoint_url' : os.environ.get("AWS.ENDPOINT")
    }
)


def main():
    loop = asyncio.new_event_loop()
    user= DiscordUser(
        token = "MTAyMTYxMjYyODk4MTg0NjAzOA.GYfbDm.7WAlyPCSlemnPK6zSI1ZT2xBozEE_g2td9MeRw", 
        proxy= os.environ.get("http_proxy"),
        loop= loop
    )

    user2= DiscordUser(
        token = "MTAyMTYxMjYyODk4MTg0NjAzOA.GYfbDm.7WAlyPCSlemnPK6zSI1ZT2xBozEE_g2td9MeRw", 
        proxy= os.environ.get("http_proxy"),
        loop= loop
    )



    asyncio.run_coroutine_threadsafe(user.run(), loop)
    asyncio.run_coroutine_threadsafe(user2.run(), loop)

    loop.run_forever()
    #loop.run_forever()


asyncio.run(main())







