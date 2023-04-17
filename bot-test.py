import os
import time
import asyncio
import yaml
# from threading import Thread
# from bot.DiscordBot.Selfbot import Selfbot
from bot import SelfOnline
from dotenv import load_dotenv, find_dotenv
# from bot.DiscordBot import DiscordBot
# from bot.DiscordBot.users import users, is_user_in_channel




file = open( os.path.join( os.getcwd(), 'users.yaml') , 'r', encoding="utf-8")
file_data = file.read()
file.close()
users = yaml.safe_load(file_data)

proxy =  os.environ.get("http_proxy")


# selfbot = Selfbot(proxy = proxy, users= users)


print('bot test')

selfOnline = SelfOnline( users )

selfOnline.run()




# loop.run_in_executor(None, selfbot.keep_online())



# # good
# response  = selfbot.sendPrompt("an Asian girl jumps into a river, full body --v 5 --no .1qwsdf")
# print(response)
# #bad 
# response  = selfbot.sendPrompt("a nude Asian girl jumps into a river, full body --v 5 --no .1dflxe")
# print(response)


# response  = selfbot.sendPrompt("nikon RAW photo,8 k,Fujifilm XT3,masterpiece, best quality, 1girl,solo,realistic, photorealistic,ultra detailed, diamond stud earrings, long straight black hair, hazel eyes, serious expression, slender figure, wearing a black blazer and white blouse, standing against a city skyline at night iu1, <lora:iu_v35:1><lora:lightAndShadow_v10:0.7>, --v 5")
# print(response)
