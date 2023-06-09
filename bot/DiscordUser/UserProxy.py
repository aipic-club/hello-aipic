import asyncio
from typing import Callable
from .DiscordUser import DiscordUser
from .payloads import payloads
from .values import Events, MJBotId
from data import  Snowflake


accept_events = [Events.INTERACTION_SUCCESS.value, Events.MESSAGE_CREATE.value]


class UserProxy:
    def __init__(
            self, 
            id : int,
            token: str , 
            guild_id: str,
            channel_id: str, 
            on_message: Callable | None,
            get_interaction_id: Callable | None,
            loop: asyncio.AbstractEventLoop 
        ) -> None:
        self.id = id
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.on_mesage  = on_message
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
            if self.on_mesage is not None:
                message_worker_id = None
                if event.value == Events.MESSAGE_CREATE.value:
              
                    channel_id = data.get('channel_id', None) 
                    guild_id = data.get('guild_id', None)
                    nonce = data.get('nonce', None)
                    message_worker_id = self.snowflake.get_worker_id(int(nonce)) if nonce else None
                    if self.channel_id != channel_id or self.guild_id != guild_id:
                        return
                id = self.generate_id()   
                self.on_mesage(id, self.id, message_worker_id ,  event, data)
        # except Exception as e:
        #     print("error when handle message", e)

    async def send_prompt(self, prompt, nonce):
        payload = payloads.prompt(self.ids, prompt, nonce)
        try:
            await self.user.send_interactions(payload)
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

