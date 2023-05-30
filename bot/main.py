import asyncio
import atexit
from data import Data,config, TaskStatus,ImageOperationType
from . import DiscordUser
from .DiscordUser.values import Opcodes, Events,MJBotId


from .DiscordUser.utils import *
import concurrent.futures
pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)




class UserProxy:
    def __init__(self,  guild_id: str, channel_id: str, user: DiscordUser) -> None:
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.user = user
        self.loop = user.loop

    @property
    def ids(self) -> dict[str, str]:
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "application_id": MJBotId,
        }

    def check(self, guild_id, channel_id) -> bool:
        return self.guild_id == guild_id and self.channel_id == channel_id

    async def send_prompt(self, prompt):
        payload = {
            **self.ids,
            "type":2,
            "application_id": MJBotId,
            "session_id":"435b587a1db9552069d068c373c6f57a",
            "data":{
                "version":"1077969938624553050","id":"938956540159881230",
                "name":"imagine","type":1,"options":[{"type":3,"name":"prompt","value":prompt}],
                "application_command":{"id":"994261739745050684","application_id": MJBotId,"version":"994261739745050685","default_member_permissions": None,"type":1,"nsfw":False,"name":"ask","description":"Get an answer to a question.","dm_permission":True,"options":[{"type":3,"name":"question","description":"What is the question?","required":True}]},
                "attachments":[]
            }
        }
        response = await self.user.send_interactions(payload)
        return response

    async def send_upscale(self, taskId: str,  index : int, messageId : str, messageHash : str):
        pass


    async def send_variation(self, taskId: str, prompt: str,  index : int,messageId : str, messageHash : str):
        snowflake_id = generate_snowflake_id()
        payload = {
            **self.ids,
            "type":3, 
            "message_flags":0,
            "message_id": messageId,
            "session_id":"1f3dbdf09efdf93d81a3a6420882c92c",
            "data":{
                "component_type":2,
                "custom_id": f"MJ::JOB::variation::{index}::{messageHash}"
            },
            "nonce": snowflake_id
        }
        response = await self.user.send_interactions(payload)
    
        asyncio.sleep(10)


        # payload = {
        #     **self.ids,
        #     "type":5,
        #     "data":{
        #         "id": f"{snowflake_id}",
        #         "custom_id": f"MJ::RemixModal::{messageHash}::{index}",  #  "MJ::RemixModal::548034f0-49db-43fb-86f8-1ca09a72e786::1",
        #         "components":[
        #             {
        #                 "type":1,
        #                 "components":[
        #                     {
        #                         "type":4,
        #                         "custom_id":"MJ::RemixModal::new_prompt",
        #                         "value": prompt
        #                     }
        #                 ]
        #             }
        #         ]
        #     },
        #     "session_id":"1f3dbdf09efdf93d81a3a6420882c92c",
        #     # "nonce":"1108688258952331264"
        # }



        pass
    async def send_max_upscale(self, messageId : str, messageHash : str):
        pass
    async def re_roll(self):
        pass


    def create_prompt(self, prompt):

        self.loop.create_task(
            self.send_prompt(prompt)
        )
    def create_variation():
        pass

    def create_upscale():
        pass






class Users:
    def __init__(
            self,  
            proxy: str | None, 
            redis_url: str, 
            mysql_url: str, 
            s3config: dict
        ):
        self.proxy = proxy
        self.data = Data(
            redis_url = redis_url,
            mysql_url= mysql_url,
            proxy = proxy,
            s3config = s3config
        )
        self.loop = asyncio.new_event_loop()
        self.users: dict[
            str, UserProxy
        ] = {} 
        self.channels = {}
        atexit.register(self.data.close)

    async def messages_handler(self, events: Events, data: dict):
        print("🔔 new msg")    
        print(data)    
        if events.value == Events.INTERACTION_SUCCESS.value:
            self.data.add_interaction(data['nonce'], data['id'])
        elif events.value == Events.MESSAGE_CREATE.value:
            message_id =  data['id']
            channel_id = data['channel_id'] 
            guild_id = data['guild_id']
            content = data['content'] 
            author_id = get_dict_value(data, 'author.id') 
            reference_id = get_dict_value(data, 'message_reference.message_id')


            if self.channels[f'{guild_id},{channel_id}']:
                # print(f'{reference_id},{message_id},{author_id},{channel_id},{guild_id},{content}')
                taskId = get_taskId(content)
                print(f'==⏰== taskId {taskId}')
                task_is_committed = is_committed(content)
                if task_is_committed:
                    print("task committed")
                else:
                    curType = output_type(content)
                    print(curType)




    

    async def start(self) -> None:
        users =  self.data.get_discord_users()

        for user in users:
            uid = user['uid']
            token = user['authorization']
            guild_id= user['guild_id']
            channel_id=  user['channel_id']

            self.users[uid]  = UserProxy(
                guild_id= guild_id,
                channel_id= channel_id,
                user= DiscordUser(
                    token = token, 
                    proxy= self.proxy, 
                    msg_handler = self.messages_handler
                )
            )

            self.channels[f'{guild_id},{channel_id}'] = 1   

        print(self.users['a1'])

        #await  self.users['a1'].user.run()    
        # for uid in self.users:
        #     asyncio.run_coroutine_threadsafe( self.users[uid].user.run()  , loop= self.loop)

    def get_user_by_taskId(self, taskId) -> UserProxy | None:
        uid = get_uid_by_taskId(taskId)
        if self.users[uid] is not None:
            return  self.users[uid]
        else:
            return None


    def create_prompt(self, token_id, taskId, prompt, new_prompt) -> None:
        user  = self.get_user_by_taskId(taskId)
        if user is not None:
            self.loop.run_in_executor(pool, lambda: user.create_prompt(new_prompt))

    def send_variation(self, prompt: str, task: dict[str, str], index: str):
        user  = self.get_user_by_taskId(task['taskId'])
        if user is not None:
            self.loop.run_in_executor(pool, user.create_variation())

    def send_upscale(self, task: dict[str, str, str], index: str):
        user  = self.get_user_by_taskId(task['taskId'])
        if user is not None:
            self.loop.run_in_executor(pool, user.create_upscale())
