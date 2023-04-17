
import json
import random
import aiohttp
import asyncio
from  .Bot import MJBotId


status = "online"
custom_status = ""
class Selfbot():
    def __init__(self, proxy: str = False, users: object = []):
        self.proxy = proxy
        self.users = users
    def run(self):
        asyncio.run(self.__keep_online())
    async def __sendInteractions(self, authorization, payload):
        
        headers = {
            'authorization' : authorization
        }
        # response = requests.post("https://discord.com/api/v9/interactions",json = payload, headers = header)
        # return response
        print("----sending prompt----")
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://discord.com/api/v9/interactions", 
                proxy= self.proxy,
                json = payload,
                headers= headers
            ) as response:
                status =  response.status
                # data = await response.text()
                # print(response)
                return status

    async def sendPrompt(self, prompt):
        user = random.choice(self.users)
        payload = {
            "type":2,
            "application_id": MJBotId,
            "guild_id": user['guild_id'],
            "channel_id":user['channel_id'],
            "session_id":"435b587a1db9552069d068c373c6f57a",
            "data":{
                "version":"1077969938624553050","id":"938956540159881230",
                "name":"imagine","type":1,"options":[{"type":3,"name":"prompt","value":prompt}],
                "application_command":{"id":"994261739745050684","application_id": MJBotId,"version":"994261739745050685","default_member_permissions": None,"type":1,"nsfw":False,"name":"ask","description":"Get an answer to a question.","dm_permission":True,"options":[{"type":3,"name":"question","description":"What is the question?","required":True}]},
                "attachments":[]
            }
        }
        response = await self.__sendInteractions(user['authorization'],  payload)
        return response
    def Upscale(index : int, messageId : str, messageHash : str):
        pass
    def MaxUpscale(messageId : str, messageHash : str):
        pass
    def Variation(index : int,messageId : str, messageHash : str):
        pass
    def ReRoll(self):
        pass