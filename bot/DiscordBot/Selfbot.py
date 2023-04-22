
import json
import random
import aiohttp
import asyncio
from  .Bot import MJBotId
from data.users import users,get_user_by_taskId

class Selfbot():
    def __init__(self, proxy: str = False):
        self.proxy = proxy
        self.users = users
    def run(self):
        asyncio.run(self.__keep_online())
    async def __send_interactions(self, authorization, payload):
        
        headers = {
            'authorization' : authorization
        }
        # response = requests.post("https://discord.com/api/v9/interactions",json = payload, headers = header)
        # return response
        print("----sending __send_interactions----")
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

    async def send_prompt(self, prompt):
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
        response = await self.__send_interactions(user['authorization'],  payload)
        return response
    async def send_upscale(self, taskId: str,  index : int, messageId : str, messageHash : str):
        user = get_user_by_taskId(taskId)
        payload = {
            "type":3,
            "guild_id": user['guild_id'],
            "channel_id":user['channel_id'],
            "message_flags":0,
            "message_id": messageId,
            "application_id": MJBotId,
            "session_id":"45bc04dd4da37141a5f73dfbfaf5bdcf",
            "data":{
                "component_type":2,
                "custom_id":"MJ::JOB::upsample::{}::{}".format(index, messageHash)
            }
        } 
        response = await self.__send_interactions(user['authorization'],  payload)
        return response
    def send_max_upscale(self, messageId : str, messageHash : str):
        pass
    async def send_variation(self, taskId: str,  index : int,messageId : str, messageHash : str):
            user = get_user_by_taskId(taskId)
            payload = {
                "type":3, 
                "guild_id": user['guild_id'],
                "channel_id":user['channel_id'],
                "message_flags":0,
                "message_id": messageId,
                "application_id": MJBotId,
                "session_id":"1f3dbdf09efdf93d81a3a6420882c92c",
                "data":{
                    "component_type":2,
                    "custom_id":"MJ::JOB::variation::{}::{}".format(index, messageHash)
                }
            }
            response = await self.__send_interactions(user['authorization'],  payload)
            return response
    def ReRoll(self):
        pass