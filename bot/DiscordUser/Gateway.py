
import asyncio
import threading
import concurrent.futures
from . import UserProxy
from .MessageHandler import MessageHandler
from .utils import *
from data import Data,Snowflake


pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

class Gateway:
    def __init__(
            self,
            id: int,
            data: Data,
            pool: concurrent.futures.ProcessPoolExecutor
        ) -> None:
            self.id = id
            self.data = data
            self.loop = None
            self.users: dict[str, UserProxy] = {} 
            self.picked_worker_id = None
    


    async def create(self, loop: asyncio.AbstractEventLoop):
        
        self.loop = loop
        dbusers =  self.data.get_discord_users(self.id)
        messageHandler = MessageHandler(data= self.data, pool= pool, loop= self.loop)
        for user in dbusers:
            worker_id = user['worker_id']
            self.picked_worker_id = worker_id
            token = user['authorization']
            guild_id= user['guild_id']
            channel_id=  user['channel_id']
            self.users[worker_id] = UserProxy( 
                token = token, 
                id = worker_id,
                guild_id=guild_id,
                channel_id=channel_id,
                on_message= messageHandler.on_message,
                loop =  self.loop
            )
 

    def pick_a_worker_id(self) -> int:
        score = 0
        for id in self.users:
            if self.users[id].score >= score:
                score = self.users[id].score
                self.picked_worker_id = id
        return self.picked_worker_id


    def get_user_by_taskId(self, taskId) -> str:
        uid = get_uid_by_taskId(taskId)
        if self.users[uid] is not None:
            return  uid
        else:
            return None

    async def test(self):
        while True:
            print(1)
            asyncio.sleep(1)


    def create_prompt(self, token_id, taskId, prompt, new_prompt) -> None:
        
        # uid  = self.get_user_by_taskId(taskId)

        # if uid is not None:
        #     user = self.users[uid]
        #     self.loop.create_task(user.send_prompt(new_prompt))
        worker_id = self.pick_a_worker_id()

        print(worker_id, self.users[worker_id])
        user = self.users[worker_id]
        print(user.channel_id)
        if user is not None:
            print(asyncio.current_task(self.loop))
            print(self.loop.is_running())
            for item in asyncio.all_tasks(self.loop):
                print(item)
            self.loop.create_task(self.test())
            #self.loop.create_task(user.send_prompt(new_prompt))


    def send_variation(self, prompt: str, task: dict[str, str], index: str):
        uid  = self.get_user_by_taskId(task['taskId'])
        if uid is not None:
            pass

    def send_upscale(self, task: dict[str, str, str], index: str):
        uid  = self.get_user_by_taskId(task['taskId'])
        if uid is not None:
            pass