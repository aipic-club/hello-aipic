import asyncio
import concurrent.futures
from .utils import *
from .values import Events
from data import Data
from data import Snowflake

class MessageHandler:
    def __init__(
            self, 
            id: int,
            data: Data, 
            pool: concurrent.futures.ProcessPoolExecutor,
            loop: asyncio.AbstractEventLoop
        ):
        self.id = id
        self.data = data
        self.pool = pool
        self.loop = loop
        pass

    def on_message(self, worker_id: int, message_worker_id: int, event: Events, data: dict):
        print(event, data)
        if event.value == Events.INTERACTION_SUCCESS.value:
            if data['nonce'] is not None:
                self.data.add_interaction(data['nonce'], data['id'])
        elif  event.value == Events.MESSAGE_CREATE.value:
            message_id =  data.get("id")
            content = data.get('content', None)
            if content is None:
                return
            reference_id = get_dict_value(data, 'message_reference.message_id')
            taskId = get_taskId(content)
            print(f'==⏰== taskId {taskId}')
            task_is_committed = is_committed(content)
            if task_is_committed:
                #### check the worker id
      
                if  worker_id == message_worker_id:
                        self.data.commit_task(
                            taskId = taskId,
                            broker_id= self.id,
                            worker_id= worker_id
                        )
            else:
                curType = output_type(content)

                if curType is not None and self.data.check_task_ower( taskId = taskId, worker_id= worker_id):
                    attachments =  data.get('attachments',[])
                    url =  attachments[0].get("url") if len(attachments) > 0  else None
                    self.loop.run_in_executor(self.pool, lambda: 
                        self.data.process_task(
                            taskId = taskId, 
                            type= curType , 
                            reference= reference_id,
                            message_id= message_id , 
                            url = url
                        )
                    )