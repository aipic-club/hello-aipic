
import asyncio
import io
import concurrent.futures
import mimetypes
import random
from . import UserProxy
from .MessageHandler import MessageHandler
from .utils import *
from data import Data, config, DetailType,Snowflake


pool = concurrent.futures.ThreadPoolExecutor(max_workers=10)

class Gateway:
    def __init__(
            self,
            celery_id: int,
            data: Data,
            pool: concurrent.futures.ProcessPoolExecutor
        ) -> None:
            self.celery_id = celery_id
            self.data = data
            self.loop = None
            self.users: dict[int, UserProxy] = {} 

    
    async def create(self, loop: asyncio.AbstractEventLoop):
        
        self.loop = loop
        dbusers =  self.data.get_discord_users(self.celery_id)
        messageHandler = MessageHandler(data= self.data, pool= pool, loop= self.loop)
        if len(dbusers) == 0:
            raise Exception("no available users!!!")
        for user in dbusers:
            worker_id = user['worker_id']
  

            token = user['authorization']
            guild_id= user['guild_id']
            channel_id=  user['channel_id']

            print(f'current user: worker_id:{worker_id}')

            self.users[worker_id] = UserProxy( 
                worker_id = worker_id,
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
        temp = []
        for id in self.users:
            # if self.users[id].score >= score:
            #     score = self.users[id].score
            temp.append(id)
        print(temp)
        return random.choice(temp)        

    
    def get_task_worker_id(self,  task: dict[str, str]) -> int | None:
        worker_id = task['worker_id']
        if worker_id is not None and self.users[worker_id] is not None:
            return worker_id
        else:
            return None

    def create_prompt(
            self, 
            token_type: int,
            space_name: str, 
            prompt: str,
            new_prompt: str,
            raw: str, 
            execute: bool 
    ) -> None:
        worker_id = self.pick_a_worker_id()
        if self.users[worker_id] is not None:
            current_user = self.users[worker_id]
            id = current_user.generate_id()
            task_type = DetailType.INPUT_MJ_IMAGINE
            detail = {
                'prompt': prompt,
                'raw':  raw
            }
            


            self.data.save_input( 
                id=id, 
                space_name=space_name, 
                type= task_type ,
                detail= detail 
            )

            if execute:
                print(f" 🟢 receive prompt {new_prompt}, nonce: {id}")

                self.data.update_status(
                    space_name=space_name, 
                    status= TaskStatus.CREATED
                )

                self.data.redis_set_onwer(
                    worker_id= current_user.worker_id,
                    space_name= space_name,
                    type=task_type
                )

                self.loop.create_task(current_user.send_prompt(new_prompt, id))
                self.loop.create_task(
                        self.check_task( 
                        worker_id = worker_id, 
                        ref_id=id, 
                        space_name= space_name 
                    )
                )

    def create_variation(self, prompt: str, new_prompt: str,  task: dict[str, str], index: str):
        worker_id =  self.get_task_worker_id(task)
        print(worker_id)
        if worker_id is not None:
            current_user = self.users[worker_id]
            space_name = task['space_name']
            id = current_user.generate_id()
            task_type = DetailType.INPUT_MJ_REMIX
            detail = {
                'ref': str(task['ref_id']),
                'prompt': prompt,
                'index': index
            }
            self.data.save_input(
                id=id, 
                space_name= space_name, 
                type= task_type, 
                detail= detail 
            )
            self.data.redis_set_onwer(
                worker_id= current_user.worker_id,
                space_name= space_name,
                type=task_type
            )
            self.data.space_job_add(
                space_name= space_name,
                id=task['ref_id'],
                type= task_type
            )
            self.loop.create_task(
                current_user.send_variation(
                    prompt = new_prompt,
                    index = index,
                    messageId = task['id'],
                    messageHash = task['hash'], 
                )
            )

    def create_upscale(self, task: dict[str, str], index: str):
        worker_id =  self.get_task_worker_id(task)
        if worker_id is not None:
            current_user = self.users[worker_id]
            space_name = task['space_name']
            id = current_user.generate_id()
            detail = {
                'ref': str(task['ref_id']),
                'index': index
            }
            task_type = DetailType.INPUT_MJ_UPSCALE

            self.data.save_input(
                id=id, 
                space_name= space_name, 
                type= task_type, 
                detail= detail 
            )

            self.data.redis_set_onwer(
                worker_id= current_user.worker_id,
                space_name= space_name,
                type=task_type
            )

            self.loop.create_task(
                self.users[worker_id].send_upscale(
                    index = index,
                    messageId = task['id'],
                    messageHash = task['hash'], 
                )
            )
    
    def create_vary(self, prompt: str, new_prompt: str, task: dict[str, str], type_index: int):
        worker_id =  self.get_task_worker_id(task)
        if worker_id is not None:
            current_user = self.users[worker_id]
            id = current_user.generate_id()
            space_name = task['space_name']
            if type_index == 1:
                job_type = 'high_variation'
            else:
                job_type = 'low_variation'
            detail = {
                'ref': str(task['ref_id']),
                'type': type_index,
                'prompt': prompt
            }
            task_type = DetailType.INPUT_MJ_VARY
            self.data.save_input(
                id=id, 
                space_name= space_name, 
                type= task_type, 
                detail= detail 
            )

            self.data.redis_set_onwer(
                worker_id= current_user.worker_id,
                space_name= space_name,
                type=task_type
            )
            self.loop.create_task(
                self.users[worker_id].send_vary(
                    prompt = new_prompt,
                    job_type= job_type,
                    type_index = type_index,
                    messageId = task['id'],
                    messageHash = task['hash'], 
                )
            )            

        pass

    def create_zoom(self, prompt: str, new_prompt: str, zoom: float, task: dict[str, str]):
        worker_id =  self.get_task_worker_id(task)
        if worker_id is not None:
            current_user = self.users[worker_id]
            id = current_user.generate_id()
            space_name = task['space_name']
            task_type = DetailType.INPUT_MJ_ZOOM
            detail = {
                'ref': str(task['ref_id']),
                'zoom': zoom,
                'prompt': prompt
            }            
            self.data.save_input(
                id=id, 
                space_name= space_name, 
                type= task_type, 
                detail= detail 
            )

            self.data.redis_set_onwer(
                worker_id= current_user.worker_id,
                space_name= space_name,
                type=task_type
            )            
            self.loop.create_task(
                current_user.send_zoom(
                    prompt = new_prompt,
                    zoom= zoom,
                    messageId = task['id'],
                    messageHash = task['hash'], 
                )
            )   


    def describe_a_image(self, space_name: str, url: str):
        worker_id = self.pick_a_worker_id()
        if self.users[worker_id] is not None:
            current_user = self.users[worker_id]
            task_type = DetailType.INPUT_MJ_DESCRIBE
            id = current_user.generate_id()
            detail = {
                "url": url
            }            
            self.data.save_input(
                id=id, 
                space_name= space_name, 
                type= task_type, 
                detail= detail 
            )

            self.loop.create_task(
                self.start_describe(
                    space_name= space_name,
                    worker_id= worker_id,
                    url=url
                )
            )

    async def start_describe(self,space_name: int, worker_id: int, url: str):
        file_resp = await self.data.file_download_a_file(url=url)
        file_id, filename, upload_url, upload_filename = await self.users[worker_id].describe_get_upload_url(bytes=io.BytesIO(file_resp))
        mime_type, _ = mimetypes.guess_type(upload_filename)
        
        await self.data.upload_a_file(
            url= upload_url, 
            data= file_resp,
            mime_type= mime_type
        )

        self.data.redis_set_describe(
            worker_id= self.users[worker_id].worker_id, 
            key= file_id, 
            space_name= space_name, 
            url = url
        )

        await self.users[worker_id].describe_send(filename=filename, uploaded_filename= upload_filename)



    async def check_task(self, worker_id: int, ref_id: int, space_name: str):
        await asyncio.sleep(config['wait_time'] - 10)
        id = self.users[worker_id].generate_id()
        self.data.check_task(
            id = id, 
            ref_id= ref_id, 
            space_name= space_name
        )