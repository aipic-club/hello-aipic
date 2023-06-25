
import asyncio
import io
import concurrent.futures
import mimetypes
from . import UserProxy
from .MessageHandler import MessageHandler
from .utils import *
from data import Data_v2, config, DetailType,Snowflake


pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

class Gateway:
    def __init__(
            self,
            celery_id: int,
            data: Data_v2,
            pool: concurrent.futures.ProcessPoolExecutor
        ) -> None:
            self.celery_id = celery_id
            self.data = data
            self.loop = None
            self.users: dict[int, UserProxy] = {} 
            self.picked_worker_id = None
    


    async def create(self, loop: asyncio.AbstractEventLoop):
        
        self.loop = loop
        dbusers =  self.data.get_discord_users(self.celery_id)
        messageHandler = MessageHandler(data= self.data, pool= pool, loop= self.loop)
        if len(dbusers) == 0:
            raise Exception("not available users!!!")
        for user in dbusers:
            worker_id = user['worker_id']
            _, account_id = Snowflake.parse_worker_id(worker_id= worker_id)
            self.picked_worker_id = worker_id
            token = user['authorization']
            guild_id= user['guild_id']
            channel_id=  user['channel_id']

            print(f'current user: worker_id:{worker_id}, account_id: {account_id}')

            self.users[account_id] = UserProxy( 
                id = worker_id,
                token = token, 
                guild_id=guild_id,
                channel_id=channel_id,
                messageHandler = messageHandler,
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
        account_id = task['account_id']
        if account_id is not None and self.users[account_id] is not None:
            return account_id
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
                print(f"🚀 send prompt {new_prompt}, nonce: {id}")

                self.data.commit_task(taskId= taskId, account_id=_account_id, status= TaskStatus.CREATED )

                self.loop.create_task(self.users[_account_id].remove_suffix())
                self.loop.create_task(self.users[_account_id].send_prompt(new_prompt, id))
                self.data.update_status(taskId=taskId, status= TaskStatus.CONFIRMED, token_id= token_id)
                self.loop.create_task(self.check_task( account_id = _account_id, ref_id=id, taskId= taskId ))

    def create_variation(self, prompt: str, new_prompt: str,  task: dict[str, str], index: str):
        worker_id =  self.get_task_account_id(task)
        if worker_id is not None:
            id = self.users[worker_id].generate_id()
            broker_id  =  task['broker_id']
            input_type = DetailType.INPUT_MJ_REMIX
            detail = {
                'ref': str(task['ref_id']),
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
            detail = {
                'ref': str(task['ref_id']),
                'index': index
            }
            input_type = DetailType.INPUT_MJ_UPSCALE
            self.data.save_input(id=id, taskId= task['taskId'], type= input_type , detail= detail )
            self.data.redis_task_job(taskId=task['taskId'], id= task['ref_id'], type = input_type, index= index)
            self.loop.create_task(
                self.users[worker_id].send_upscale(
                    index = index,
                    messageId = task['id'],
                    messageHash = task['hash'], 
                )
            )
    def describe_a_image(self, taskId: str, url: str):
        _account_id = self.pick_a_worker_id() 
        if self.users[_account_id] is not None:
            self.loop.create_task(
                self.start_describe(
                    taskId= taskId,
                    account_id= _account_id,
                    url=url
                )
            )

    async def start_describe(self,taskId: int, account_id: int, url: str):
        file_resp = await self.data.file_download_a_file(url=url)
        file_id, filename, upload_url, upload_filename = await self.users[account_id].describe_get_upload_url(bytes=io.BytesIO(file_resp))
        mime_type, _ = mimetypes.guess_type(upload_filename)
        await self.data.upload_a_file(
            url= upload_url, 
            data= file_resp,
            mime_type= mime_type
        )

        self.data.redis_set_describe(
            account_id= account_id, 
            key= file_id, 
            taskId= taskId, 
            url = url
        )

        await self.users[account_id].describe_send(filename=filename, uploaded_filename= upload_filename)



    async def check_task(self, account_id: int, ref_id: int, taskId: str):
        await asyncio.sleep(config['wait_time'] - 10)
        id = self.users[account_id].generate_id()
        self.data.check_task(
            id = id, 
            ref_id= ref_id, 
            taskId= taskId
        )