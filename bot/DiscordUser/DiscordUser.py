import enum
import json
import time
import asyncio
import aiohttp
import zlib
from typing import Callable
from .utils import get_dict_value
from .values import Opcodes, Events, browser, MJBotId
from config import proxy


class DiscordUser:
    APIURL = "https://discord.com/api/v9/interactions"
    WSSURL = "wss://gateway.discord.gg/?v=9&encoding=json&compress=zlib-stream"
    def __init__(
            self, 
            token: str, 
            on_message: Callable | None,
            loop: asyncio.AbstractEventLoop
        ) -> None:
        self.token = token
        self.proxy = proxy
        self.on_message = on_message
        self.session =  None
        self.ws = None
        self.hb = None
        self.loop = loop
        self.sequence_number = None

    @property
    def header(self):
        return {
            'authorization' : self.token,
            'User-Agent': browser["browser_user_agent" ]
        }


    async def run(self) -> None:
        await asyncio.sleep(5)
        self.session = aiohttp.ClientSession(loop = self.loop)

        self.ws = await self.session.ws_connect(DiscordUser.WSSURL, proxy= self.proxy )

        buffer = bytearray()
        inflator = zlib.decompressobj()

        if self.hb is not None:
            self.hb.cancel()

        async for message in self.ws:
            if message.type in (aiohttp.WSMsgType.error, aiohttp.WSMsgType.closed):
                break
            if message.type is aiohttp.WSMsgType.binary:
                buffer.extend(message.data)
                if len(message.data) < 4 or not message.data[-4:] == b"\x00\x00\xff\xff":
                    continue
                data = inflator.decompress(buffer)
                buffer.clear()
                data = json.loads(data)
                op = data.get("op")
                d = data.get("d")
                s = data.get("s")
                t = data.get("t")
                await self.__on_message(Opcodes(op), d , s, t)
    

        self.hb.cancel()
        await self.run()




    async def __identify(self):
        identify_data = {
            "token": self.token,
            "properties": browser,
            "presence": {"status": "online", "afk": False},
        }

        await self.__send(Opcodes.IDENTIFY ,  identify_data)

  

    async def __on_message(self, op: Opcodes , data: dict, sequence_number: int, event_name: str | None):
        # print(op, data, event_name)
        self.sequence_number = sequence_number
        if op is Opcodes.HELLO:
            self.hb = self.loop.create_task(self.__send_heartbeat(data['heartbeat_interval']))
            await self.__identify()
        elif op is Opcodes.INVALID_SESSION:
            await self.__identify()
        
        # print("=====")
        # print(op, event_name, data)
        # print("=====")
        ##########
        if self.on_message is not None:
            if event_name == Events.READY.value:
                self.session_id = data['session_id']
            elif event_name == Events.INTERACTION_SUCCESS.value:
                self.on_message(Events.INTERACTION_SUCCESS, data)
            elif event_name == Events.MESSAGE_CREATE.value:
                if get_dict_value(data, 'author.id')  == str(MJBotId):
                    self.on_message(Events.MESSAGE_CREATE, data)
            elif event_name == Events.MESSAGE_UPDATE.value:
                if get_dict_value(data, 'author.id')  == str(MJBotId) :
                    self.on_message(Events.MESSAGE_UPDATE, data)                
            else:
                pass
            # elif event_name == Events.MESSAGE_UPDATE.value:
            #     embeds = data.get("embeds")
            #     if len(embeds) > 0:
            #         title = embeds[0].get("title")
            #         print(title)




    
    async def __send_heartbeat(self, heartbeat_interval):
        while True:
            print("♥️ send heartbeat")
            await asyncio.sleep(heartbeat_interval / 1000)
            await self.__send(Opcodes.HEARTBEAT, self.sequence_number)

    async def __send(self, op, data, *, sequences = None):
        ready_data = {
            "op": op.value,
            "d": data
        }

        if sequences is not None:
            ready_data["s"] = sequences
        await self.ws.send_json(ready_data)

################

    async  def send_interactions(self, payload)  -> aiohttp.ClientResponse :
        response = await self.session.post(
            DiscordUser.APIURL,
            proxy= self.proxy,
            json = payload,
            headers= self.header
        )

        return response
    
    async def send_form_interactions(self, payload: str) -> aiohttp.ClientResponse :

        form_data = aiohttp.FormData()
        form_data.add_field('payload_json', payload)

        response = await self.session.post(
            DiscordUser.APIURL,
            proxy= self.proxy,
            data= form_data,
            headers= self.header
        )

        return response
    async def get_upload_url(self,channel_id: str,  payload: str) -> aiohttp.ClientResponse :
        response = await self.session.post(
            f'https://discord.com/api/v9/channels/{channel_id}/attachments',
            proxy= self.proxy,
            json = payload,
            headers= self.header
        )
        return response



