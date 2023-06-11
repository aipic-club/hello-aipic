
import asyncio
import concurrent.futures
from . import UserProxy
from .MessageHandler import MessageHandler
from .utils import *
from data import Data_v2, config, DetailType


pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

class Gateway:
    def __init__(
            self,
            id: int,
            data: Data_v2,
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
    
    def get_task_account_id(self,  task: dict[str, str]) -> int | None:
        worker_id = task['account_id']
        if worker_id is not None and self.users[worker_id] is not None:
            return worker_id
        else:
            return None

    def create_prompt(
            self, 
            broker_id: int | None, 
            account_id: int | None, 
            token_id: int , 
            taskId: str, 
            prompt: str,
            new_prompt: str,
            raw: str, 
            execute: bool 
    ) -> None:
        _account_id = self.pick_a_worker_id() if account_id is None else account_id
        if self.users[_account_id] is not None:
            id = self.users[_account_id].generate_id()
            detail = {
                'prompt': prompt,
                'raw':  raw
            }
            self.data.update_task_topic(taskId=taskId, topic= prompt)
            self.data.update_status(taskId=taskId, status= TaskStatus.CREATED, token_id= token_id)
            self.data.save_input(id=id, taskId= taskId, type= DetailType.INPUT_MJ_PROMPT , detail= detail )
            if execute:
                self.loop.create_task(self.users[_account_id].send_prompt(new_prompt, id))
                self.data.update_status(taskId=taskId, status= TaskStatus.CONFIRMED, token_id= token_id)
                # self.loop.create_task(self.check_task(taskId= taskId))

    def create_variation(self, prompt: str, new_prompt: str,  task: dict[str, str], index: str):
        worker_id =  self.get_task_account_id(task)
        if worker_id is not None:
            id = self.users[worker_id].generate_id()
            broker_id  =  task['broker_id']
            # self.data.image_task(
            #     taskId=task['taskId'], 
            #     imageHash= task['message_hash'], 
            #     type= ImageOperationType.VARIATION, 
            #     index= index 
            # )
            # self.data.broker_task_status(
            #     broker_id=broker_id, 
            #     worker_id=worker_id, 
            #     taskId= task['taskId']
            # )
            input_type = DetailType.INPUT_MJ_REMIX
            detail = {
                'ref': task['ref_id'],
                'prompt': prompt,
                'index': index
            }
            self.data.save_input(id=id, taskId= task['taskId'], type= input_type , detail= detail )
            self.data.redis_task_job(taskId=task['taskId'], id= task['ref_id'], type = input_type, index= index)
            self.loop.create_task(
                self.users[worker_id].send_variation(
                    prompt = new_prompt,
                    index = index,
                    messageId = task['id'],
                    messageHash = task['hash'], 
                )
            )

    def create_upscale(self, task: dict[str, str], index: str):
        worker_id =  self.get_task_account_id(task)
        if worker_id is not None:
            id = self.users[worker_id].generate_id()
            broker_id  =  task['broker_id']
            # self.data.image_task(
            #     taskId=task['taskId'], 
            #     imageHash= task['message_hash'], 
            #     type= ImageOperationType.UPSCALE, 
            #     index= index 
            # )
            # self.data.broker_task_status(
            #     broker_id=broker_id, 
            #     worker_id=worker_id, 
            #     taskId= task['taskId']
            # )
            detail = {
                'ref': task['ref_id'],
                'index': index
            }
            input_type = DetailType.INPUT_MJ_VARIATION
            self.data.save_input(id=id, taskId= task['taskId'], type= input_type , detail= detail )
            self.data.redis_task_job(taskId=task['taskId'], id= task['ref_id'], type = input_type, index= index)
            self.loop.create_task(
                self.users[worker_id].send_upscale(
                    index = index,
                    messageId = task['id'],
                    messageHash = task['hash'], 
                )
            )

    async def check_task(self, taskId: str):
        await asyncio.sleep(config['wait_time'] - 10)
        self.data.check_task(taskId= taskId)