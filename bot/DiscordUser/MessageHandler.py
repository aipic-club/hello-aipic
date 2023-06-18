import asyncio
import os
import concurrent.futures
from .utils import *
from .values import Events
from data import Data_v2
from data import Snowflake

class MessageHandler:
    def __init__(
            self, 
            id: int,
            data: Data_v2, 
            pool: concurrent.futures.ProcessPoolExecutor,
            loop: asyncio.AbstractEventLoop
        ):
        self.id = id
        self.data = data
        self.pool = pool
        self.loop = loop
        pass

    def on_invalid_parameter(self,id: int, taskId: str, detail: dict ):
        self.loop.run_in_executor(self.pool, lambda: 
            self.data.process_error(
                id=id,
                taskId=taskId,
                type=DetailType.OUTPUT_MJ_INVALID_PARAMETER,
                detail= detail
            )
        )
    def on_receive_describe(self,id: int, account_id: int, embed):
                                # # is describe


        url = embed.get('image').get('url')
        filename = os.path.basename(url)
        name_without_extension = os.path.splitext(filename)[0]
        data = self.data.redis_get_describe(account_id= account_id, key=name_without_extension )
        
        if data is not None:
            detail = {
                'url': data.get('url', ''),
                'description':  embed.get('description', '')
            }        

            self.data.save_input(
                id=id,
                taskId=data.get('taskId'),
                type= DetailType.OUTPUT_MJ_DESCRIBE,
                detail = detail
            )
    def on_message(self, id: int, account_id: int,  message_account_id: int, event: Events, data: dict):
        #print(event, data)
        
        if event is Events.INTERACTION_SUCCESS:
            if data.get('nonce') is not None and data.get('id') is not None:
                self.data.add_interaction(data.get('nonce'), data.get('id'))
        elif  event is Events.MESSAGE_CREATE:
            message_id =  data.get("id")
            content = data.get('content', None)
            if content is None:
                return
            reference_id = get_dict_value(data, 'message_reference.message_id')
            taskId = get_taskId(content)
   

            if taskId is None:
                return
            print(f'⏰ taskId {taskId}')
            task_is_committed = is_committed(content)
            if task_is_committed:
                #### check the worker id
                if  account_id == message_account_id:
                        self.data.commit_task(
                            taskId = taskId,
                            account_id= account_id
                        )

            else:
                curType = output_type(content)
                if curType is not None and self.data.is_task_onwer(account_id= account_id, taskId = taskId):
                    attachments =  data.get('attachments',[])
                    url =  attachments[0].get("url") if len(attachments) > 0  else None
                    self.loop.run_in_executor(self.pool, lambda: 
                        self.data.process_output(
                            id = id,
                            taskId = taskId, 
                            type= curType , 
                            reference= reference_id,
                            message_id= message_id , 
                            url = url
                        )
                    )
        elif  event is Events.MESSAGE_UPDATE:
            pass

