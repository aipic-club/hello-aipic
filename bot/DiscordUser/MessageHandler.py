import asyncio
import os
import concurrent.futures
from .utils import *
from .values import Events
from data import Data
from data import Snowflake

class MessageHandler:
    def __init__(
            self, 
            data: Data, 
            pool: concurrent.futures.ProcessPoolExecutor,
            loop: asyncio.AbstractEventLoop
        ):
        self.data = data
        self.pool = pool
        self.loop = loop
        pass

    def on_invalid_parameter(self, id: int, space_name: str, detail: dict ):
        self.loop.run_in_executor(self.pool, lambda: 
            self.data.process_error(
                id=id,
                space_name=space_name,
                type=DetailType.OUTPUT_MJ_INVALID_PARAMETER,
                detail= detail
            )
        )
    def on_job_queued(self,  space_name: str):
        if self.data.space_prompt_status(space_name=space_name) is not None:
            self.data.space_prompt(
                space_name=space_name, 
                status= TaskStatus.COMMITTED
            )
    def on_receive_describe(self,id: int, worker_id: int, embed):
        # # is describe


        url = embed.get('image').get('url')
        filename = os.path.basename(url)
        name_without_extension = os.path.splitext(filename)[0]

        data = self.data.redis_get_describe(worker_id= worker_id, key=name_without_extension )
        
        print(f"describe . {worker_id}, {name_without_extension}")

        
        if data is not None:
            detail = {
                'url': data.get('url', ''),
                'description':  embed.get('description', '')
            }        

            self.data.save_input(
                id=id,
                space_name=data.get('space_name'),
                type= DetailType.OUTPUT_MJ_DESCRIBE,
                detail = detail
            )

            self.data.redis_describe_cleanup(key= name_without_extension)
    def on_interaction(self, data: dict):
        if data.get('nonce') is not None and data.get('id') is not None:
            self.data.add_interaction(data.get('nonce'), data.get('id'))

    def on_message(self, id: int, worker_id: int,  message_worker_id: int, event: Events, data: dict):
        if  event is Events.MESSAGE_CREATE:
            message_id =  data.get("id")
            content = data.get('content', None)
            if content is None:
                return
            reference_id = get_dict_value(data, 'message_reference.message_id')
            space_name = get_space_name(content)
   

            if space_name is None:
                return
            
            print(f'⏰ Space Name {space_name}')

            task_committed = is_committed(content)

            if task_committed:
                #### check the worker id
                if  worker_id == message_worker_id and self.data.space_prompt_status(space_name=space_name) is not None:
                    self.data.space_prompt(
                        space_name=space_name, 
                        status= TaskStatus.COMMITTED
                    )
            else:
                types  = input_output_type(content)
                if types is None:
                    return

                curInputType, curOutputType = types

                print(f'output: {worker_id}, {space_name}, {curInputType.value}')
                print(types)

                print(data)



                if self.data.redis_is_onwer(
                    worker_id=worker_id, 
                    space_name= space_name, 
                    type= curInputType
                ):
                    attachments =  data.get('attachments',[])
                    data_components = data.get('components', [])
                    new_components = []
                    to_exclude = ['❤️', 'Web','🔄']
                    #print(data_components)
                    for item in data_components:
                        components = item.get('components', [])
                        for component in components:
                            emoji = component.get('emoji', {}).get('name', None)
                            label = component.get('label', None)
                            if (emoji or label) and emoji not in  to_exclude and label not in to_exclude:
                                new_components.append({'emoji': emoji, 'label': label})
                    
                    # print(new_components)
                    content =  data.get('content', '')
                    prompt = get_prompt_from_content(content = content, space_name=space_name) if content else ''
                    url =  attachments[0].get("url") if len(attachments) > 0  else None
                    
                    self.loop.run_in_executor(self.pool, lambda: 
                        self.data.process_output(
                            id = id,
                            space_name = space_name, 
                            types= types , 
                            reference= reference_id,
                            message_id= message_id , 
                            prompt = prompt,
                            components = new_components,
                            url = url
                        )
                    )
        elif  event is Events.MESSAGE_UPDATE:
            pass

