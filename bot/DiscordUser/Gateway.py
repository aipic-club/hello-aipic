
import asyncio
import concurrent.futures
from . import UserProxy
from .MessageHandler import MessageHandler
from .utils import *
from data import Data, config, ImageOperationType, Snowflake


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
        messageHandler = MessageHandler(id = self.id, data= self.data, pool= pool, loop= self.loop)
        if len(dbusers) == 0:
            raise Exception("not available users!!!")
        for user in dbusers:
            worker_id = user['worker_id']
            self.picked_worker_id = worker_id
            token = user['authorization']
            guild_id= user['guild_id']
            channel_id=  user['channel_id']
            self.users[worker_id] = UserProxy( 
                id = worker_id,
                token = token, 
                guild_id=guild_id,
                channel_id=channel_id,
                on_message= messageHandler.on_message,
                get_interaction_id = self.get_interaction_id,
                loop =  self.loop
            )

    def get_interaction_id(self, key) -> int | None:
        return self.data.get_interaction(key)

    def pick_a_worker_id(self) -> int:
        score = 0
        for id in self.users:
            if self.users[id].score >= score:
                score = self.users[id].score
                self.picked_worker_id = id
        return self.picked_worker_id
    
    def get_task_worker_id(self,  task: dict[str, str]) -> int | None:
        worker_id = task['worker_id']
        if worker_id is not None and self.users[worker_id] is not None:
            return worker_id
        else:
            return None

    def create_prompt(self, token_id, taskId, prompt, new_prompt) -> None:

        worker_id = self.pick_a_worker_id()
        if self.users[worker_id] is not None:
            self.data.prompt_task(token_id, taskId, TaskStatus.CONFIRMED, config['wait_time'])
            self.loop.create_task(self.users[worker_id].send_prompt(new_prompt))
            self.loop.create_task(self.check_task(taskId= taskId))

    def create_variation(self, prompt: str, task: dict[str, str], index: str):
        worker_id =  self.get_task_worker_id(task)
        if worker_id is not None:
            broker_id, _ =  Snowflake.parse_worker_id(worker_id)
            self.data.image_task(
                taskId=task['taskId'], 
                imageHash= task['message_hash'], 
                type= ImageOperationType.VARIATION, 
                index= index 
            )
            self.data.broker_task_status(
                broker_id=broker_id, 
                worker_id=worker_id, 
                taskId= task['taskId']
            )
            self.loop.create_task(
                self.users[worker_id].send_variation(
                    prompt = prompt,
                    index = index,
                    messageId = task['message_id'],
                    messageHash = task['message_hash'], 
                )
            )

    def create_upscale(self, task: dict[str, str], index: str):
        worker_id =  self.get_task_worker_id(task)
        if worker_id is not None:
            broker_id, _ =  Snowflake.parse_worker_id(worker_id)
            self.data.image_task(
                taskId=task['taskId'], 
                imageHash= task['message_hash'], 
                type= ImageOperationType.UPSCALE, 
                index= index 
            )
            self.data.broker_task_status(
                broker_id=broker_id, 
                worker_id=worker_id, 
                taskId= task['taskId']
            )
            self.loop.create_task(
                self.users[worker_id].send_upscale(
                    index = index,
                    messageId = task['message_id'],
                    messageHash = task['message_hash'], 
                )
            )

    async def check_task(self, taskId: str):
        await asyncio.sleep(config['wait_time'] - 10)
        self.data.check_task(taskId= taskId)