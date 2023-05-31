
import asyncio
import threading
import concurrent.futures
from . import UserProxy
from .MessageHandler import MessageHandler
from .utils import *
from data import Data


pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

class Gateway:
    def __init__(
            self,
            data: Data,
            pool: concurrent.futures.ProcessPoolExecutor
        ) -> None:
            self.data = data
            self.loop = None
            self.users: dict[str, UserProxy] = {} 
    
            
    def create(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        dbusers =  self.data.get_discord_users()
        messageHandler = MessageHandler(data= self.data, pool= pool, loop= loop)
        for user in dbusers:
            uid = user['uid']
            token = user['authorization']
            guild_id= user['guild_id']
            channel_id=  user['channel_id']
            self.users[uid] = UserProxy( 
                token = token, 
                guild_id=guild_id,
                channel_id=channel_id,
                on_message= messageHandler.on_message,
                loop = self.loop
            )
    def get_user_by_taskId(self, taskId) -> str:
        uid = get_uid_by_taskId(taskId)
        if self.users[uid] is not None:
            return  uid
        else:
            return None


    def create_prompt(self, token_id, taskId, prompt, new_prompt) -> None:
        uid  = self.get_user_by_taskId(taskId)
        if uid is not None:
            user = self.users[uid]
            self.loop.create_task(user.send_prompt(new_prompt))

    def send_variation(self, prompt: str, task: dict[str, str], index: str):
        uid  = self.get_user_by_taskId(task['taskId'])
        if uid is not None:
            pass

    def send_upscale(self, task: dict[str, str, str], index: str):
        uid  = self.get_user_by_taskId(task['taskId'])
        if uid is not None:
            pass