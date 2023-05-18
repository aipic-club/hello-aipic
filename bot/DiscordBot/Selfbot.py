
import random
import aiohttp
from  .Bot import MJBotId
from data import DiscordUsers

class Selfbot():
    def __init__(self, proxy: str = False):
        self.proxy = proxy

    def register_discord_users(self, discordUsers : DiscordUsers = None):
        self.discordUsers = discordUsers
    async def __send_interactions(self, authorization, payload):
        
        headers = {
            'authorization' : authorization
        }
        # response = requests.post("https://discord.com/api/v9/interactions",json = payload, headers = header)
        # return response
        print("===🚀sending to user bot===")
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
        user = random.choice(self.discordUsers.users)
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
        user = self.discordUsers.get_user_by_taskId(taskId) 
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
            user = self.discordUsers.get_user_by_taskId(taskId)
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

            # payload = {
            #     "type":5,
            #     "application_id":"936929561302675456",
            #     "channel_id":"1096333900273426535",
            #     "guild_id":"1096333899778490380",
            #     "data":{
            #         "id":"1108688218611789904",
            #         "custom_id":"MJ::RemixModal::548034f0-49db-43fb-86f8-1ca09a72e786::1",
            #         "components":[
            #             {
            #                 "type":1,
            #                 "components":[
            #                     {
            #                         "type":4,
            #                         "custom_id":"MJ::RemixModal::new_prompt",
            #                         "value":"A serene waterfall in a lush tropical forest, with sunlight filtering through the canopy, painted in the style of Claude Monet. ::2 [Waterfall]::1 [Sunlight]::1 --ar 1:1 --v 5 --no a1.8zOPrRv0Q3 --v 5.1 --s 50"
            #                     }
            #                 ]
            #             }
            #         ]
            #     },
            #     "session_id":"cba2441e167d8aec7945844727bcb11f",
            #     # "nonce":"1108688258952331264"
            # }
            

            return response
    def ReRoll(self):
        pass