
import random
import aiohttp
import asyncio
MJAppID = "936929561302675456"





class Selfbot():
    def __init__(self, proxy: str = False, users: object = []):
        self.proxy = proxy
        self.users = users
    def __testPromptOut(self, payload):
        print(payload)
    async def __sendInteractions(self, authorization, payload):
        
        headers = {
            'authorization' : authorization
        }
        # response = requests.post("https://discord.com/api/v9/interactions",json = payload, headers = header)
        # return response
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://discord.com/api/v9/interactions", 
                proxy= self.proxy,
                json = payload,
                headers= headers
            ) as response:
                status =  response.status
                # print(status, data)
                return status

    def sendPrompt(self, prompt):
        user = random.choice(self.users)
        payload = {
            "type":2,
            "application_id":MJAppID,
            "guild_id": user['guild_id'],
            "channel_id":user['channel_id'],
            "session_id":"435b587a1db9552069d068c373c6f57a",
            "data":{
                "version":"1077969938624553050","id":"938956540159881230",
                "name":"imagine","type":1,"options":[{"type":3,"name":"prompt","value":prompt}],
                "application_command":{"id":"994261739745050684","application_id":MJAppID,"version":"994261739745050685","default_member_permissions": None,"type":1,"nsfw":False,"name":"ask","description":"Get an answer to a question.","dm_permission":True,"options":[{"type":3,"name":"question","description":"What is the question?","required":True}]},
                "attachments":[]
            }
        }
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__sendInteractions(user['authorization'],  payload))
        # response = self.__sendInteractions(user['authorization'],  payload)
    def Upscale(index : int, messageId : str, messageHash : str):
        pass
    def MaxUpscale(messageId : str, messageHash : str):
        pass
    def Variation(index : int,messageId : str, messageHash : str):
        pass
    def ReRoll(self):
        pass