
import json
import random
import aiohttp
import asyncio
# from websockets.sync.client import connect

import websockets
# from  bot.DiscordBot.Bot import MJBotId
MJBotId= "936929561302675456"

status = "online"
custom_status = ""
class Selfbot():
    def __init__(self, proxy: str = False, users: object = []):
        self.proxy = proxy
        self.users = users
    # def run(self):
    #     asyncio.run(self.__keep_online())
    # async def onliner(self, token):
    #     async for ws in websockets.connect("wss://gateway.discord.gg/?v=9&encoding=json") :
    #         try:
    #             data = await ws.recv()
    #             start = json.loads(data)
        
    #             heartbeat = start["d"]["heartbeat_interval"]

    #             auth = {
    #                 "op": 2,
    #                 "d": {
    #                     "token": token,
    #                     "properties": {
    #                         "$os": "Windows 11",
    #                         "$browser": "Google Chrome",
    #                         "$device": "Windows",
    #                     },
    #                     "presence": {"status": status, "afk": False},
    #                 },
    #                 "s": None,
    #                 "t": None,
    #             }
    #             await ws.send(json.dumps(auth))
    #             cstatus = {
    #                 "op": 3,
    #                 "d": {
    #                     "since": 0,
    #                     "activities": [
    #                         {
    #                             "type": 4,
    #                             "state": custom_status,
    #                             "name": "Custom Status",
    #                             "id": "custom",
    #                             #Uncomment the below lines if you want an emoji in the status
    #                             #"emoji": {
    #                                 #"name": "emoji name",
    #                                 #"id": "emoji id",
    #                                 #"animated": False,
    #                             #},
    #                         }
    #                     ],
    #                     "status": status,
    #                     "afk": False,
    #                 },
    #             }
    #             await ws.send(json.dumps(cstatus))
    #             online = {"op": 1, "d": "None"}
    #             await asyncio.sleep(heartbeat / 1000)
    #             await ws.send(json.dumps(online))
    #         except websockets.ConnectionClosed:
    #             continue                
    # """
    # keep all user bot acconts online
    # """
    # async def keep_online(self):
    #     await self.onliner("MTA3NjAyNjcwNDE0MjgxNTI0Mg.Gn-i3m.0cKlkMdDnxuc4tSuc9ngKNXjp0sRZR5PkPn2AY")

    #     # tasks = []
    #     # for u in self.users:
    #     #     self.onliner(u['authorization'])
    #     #     task = asyncio.create_task(self.onliner(u['authorization']))
    #     #     tasks.append(task)
    #     # await asyncio.gather(*tasks, return_exceptions=True)

    # def __testPromptOut(self, payload):
    #     print(payload)
    # async def __sendInteractions(self, authorization, payload):
        
    #     headers = {
    #         'authorization' : authorization
    #     }
    #     # response = requests.post("https://discord.com/api/v9/interactions",json = payload, headers = header)
    #     # return response
    #     print("----sending prompt----")
    #     async with aiohttp.ClientSession() as session:
    #         async with session.post(
    #             "https://discord.com/api/v9/interactions", 
    #             proxy= self.proxy,
    #             json = payload,
    #             headers= headers
    #         ) as response:
    #             status =  response.status
    #             data = await response.text()
    #             print(response)
    #             return status

    # async def sendPrompt(self, prompt):
    #     user = random.choice(self.users)
    #     payload = {
    #         "type":2,
    #         "application_id": MJBotId,
    #         "guild_id": user['guild_id'],
    #         "channel_id":user['channel_id'],
    #         "session_id":"435b587a1db9552069d068c373c6f57a",
    #         "data":{
    #             "version":"1077969938624553050","id":"938956540159881230",
    #             "name":"imagine","type":1,"options":[{"type":3,"name":"prompt","value":prompt}],
    #             "application_command":{"id":"994261739745050684","application_id": MJBotId,"version":"994261739745050685","default_member_permissions": None,"type":1,"nsfw":False,"name":"ask","description":"Get an answer to a question.","dm_permission":True,"options":[{"type":3,"name":"question","description":"What is the question?","required":True}]},
    #             "attachments":[]
    #         }
    #     }
    #     response = await self.__sendInteractions(user['authorization'],  payload)
    #     return response
    # def Upscale(index : int, messageId : str, messageHash : str):
    #     pass
    # def MaxUpscale(messageId : str, messageHash : str):
    #     pass
    # def Variation(index : int,messageId : str, messageHash : str):
    #     pass
    # def ReRoll(self):
    #     pass