import asyncio
import json
import io
import os
from PIL import Image
from typing import Callable
from .DiscordUser import DiscordUser
from .payloads import payloads
from .values import Events, MJBotId
from .MessageHandler import MessageHandler
from .utils import get_taskId
from data import  Snowflake, random_id


accept_events = [Events.INTERACTION_SUCCESS.value, Events.MESSAGE_CREATE.value]


class UserProxy:
    def __init__(
            self, 
            id : int,
            token: str , 
            guild_id: str,
            channel_id: str, 
            #on_message: Callable | None,
            messageHandler: MessageHandler,
            get_interaction_id: Callable | None,
            loop: asyncio.AbstractEventLoop 
        ) -> None:
        self.id = id
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.messageHandler = messageHandler
        self.get_interaction_id = get_interaction_id
        self.score = 100
        self.snowflake = Snowflake(id, None)
        self.user = DiscordUser( token= token, on_message= self.__on_message, loop= loop)
        loop.create_task(self.user.run())
    @property
    def ids(self) -> dict[str, str]:
        return {
            "guild_id": self.guild_id,
            "channel_id": self.channel_id,
            "application_id": MJBotId
        }
    def generate_id(self) -> int:
        return self.snowflake.generate_id()
    def __on_message(self, event: Events, data: dict) -> None:
        # try:
            if event is Events.MESSAGE_CREATE:
                message_account_id = None            
                if event is  Events.MESSAGE_CREATE:

                    channel_id = data.get('channel_id', None) 
                    guild_id = data.get('guild_id', None)
                    nonce = data.get('nonce', None)
                    #if self.channel_id != channel_id or self.guild_id != guild_id:
                    if self.channel_id != channel_id:
                        return    
                    message_account_id = self.snowflake.get_worker_id(int(nonce)) if nonce else None
                    embeds = data.get("embeds", [])
                    if len(embeds) > 0:
                            title = embeds[0].get("title")
                            description = embeds[0].get("description")
                            print(title, description)
                            if title == 'Job queued':
                                return
                            elif title == 'Invalid parameter':
                                taskId = get_taskId(embeds[0].get('footer',{}).get('text'))
                                id = self.generate_id()
                                self.messageHandler.on_invalid_parameter(
                                    id,
                                    taskId,
                                    detail= {
                                        'ref': str(nonce),
                                        'title': title,
                                        'description': description
                                    }
                                )
                                return
                id = self.generate_id()   
                self.messageHandler.on_message(id, self.id, message_account_id ,  event, data)
            elif event is Events.MESSAGE_UPDATE:

                #print(data)
                embeds = data.get("embeds", [])
                components = data.get("components", [])

                # print(embeds)
                # print(components)

                if len(embeds) > 0 and len(components) > 0  and len(components[0].get('components')) > 0:
                    custom_id = components[0].get('components')[0].get('custom_id')
                    if custom_id == 'MJ::Job::PicReader::1':
                        id = self.generate_id()   
                        self.messageHandler.on_receive_describe(id, self.id, embeds[0])

                        # # is describe
                        # url = embeds[0].get('image').get('url')
                        # filename = os.path.basename(url)
                        # name_without_extension = os.path.splitext(filename)[0]
                        # print(name_without_extension)
                        
                        # ###




                pass
        # except Exception as e:
        #     print("error when handle message", e)
    async def remove_prefix(self, nonce):
        payload = payloads.prefer_suffix(self.ids, nonce=nonce)
        payload_str = json.dumps(payload)
        try:
            await self.user.send_form_interactions(payload=payload_str)
        except Exception as e:
            print("error when handle message", e)

    async def remove_suffix(self):
        await self.remove_prefix(nonce=self.generate_id())
    async def send_prompt(self, prompt, nonce):
        payload = payloads.prompt_v1118961510123847772(self.ids, prompt, nonce)
        payload_str = json.dumps(payload)
        try:
            await self.user.send_form_interactions(payload=payload_str)
        except Exception as e:
            print("error when handle message", e)
    
    async def send_variation(self,  prompt: str,  index : int, messageId : str, messageHash : str):
        nonce = self.snowflake.generate_id()
        payload = payloads.variation(self.ids, messageId= messageId, messageHash=messageHash, index=index, nonce=nonce)
        try:
            await self.user.send_interactions(payload)
            await asyncio.sleep(3)
            data_id = self.get_interaction_id(nonce)
            if data_id is not None:
                payload = payloads.remix(self.ids, prompt= prompt,data_id= str(data_id), messageHash= messageHash, index= index )
                await self.user.send_interactions(payload)
            
        except Exception as e:
            print("error when variation message", e)
    async def send_upscale(self, index : int, messageId : str, messageHash : str):
        nonce = self.snowflake.generate_id()
        payload = payloads.upscale(self.ids, messageId= messageId, messageHash=messageHash, index=index, nonce=nonce)
        try:
            await self.user.send_interactions(payload)
        except Exception as e:
            print("error when upscale message", e)


    async def describe_get_upload_url(self, bytes: io.BytesIO):
        image = Image.open(bytes)
        image_format = image.format
        image_size = bytes.getbuffer().nbytes
        file_id= random_id(10)
        filename = f'{file_id}.{image_format.lower()}'
        payload = {
            'files': [
                {
                    'file_size': image_size,
                    'filename': filename,
                    'id': '1'
                }
            ]
        }
        response =  await self.user.get_upload_url(channel_id=self.channel_id, payload=payload)
        data = await response.json()
        upload_url = data.get("attachments")[0].get("upload_url")
        upload_filename = data.get("attachments")[0].get("upload_filename")
        return (file_id, filename, upload_url, upload_filename,)
    
    async def describe_send(self, filename: str, uploaded_filename: str,):
        nonce = self.snowflake.generate_id()
        payload = payloads.describe(self.ids, filename, uploaded_filename, nonce=nonce)
        payload_str = json.dumps(payload)
        try:
            await self.user.send_form_interactions(payload=payload_str)
        except Exception as e:
            print("error when handle message", e)