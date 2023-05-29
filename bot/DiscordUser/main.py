import enum
import json
import time
import asyncio
import aiohttp
import zlib
from .values import Opcodes, Events


class DiscordUser:
    WSSURL = "wss://gateway.discord.gg/?v=9&encoding=json&compress=zlib-stream"
    def __init__(self, token: str, proxy : str) -> None:
        self.token = token
        self.proxy = proxy
        self.session =  None
        self.ws = None
        self.hb = None
        self.loop = None
        self.sequence_number = None
    async def run(self) -> None:
        self.loop = asyncio.get_event_loop()
        self.session = aiohttp.ClientSession(loop= self.loop)

        self.ws = await  self.session.ws_connect(DiscordUser.WSSURL, proxy= self.proxy)

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
                print(data)
                op = data.get("op")
                d = data.get("d")
                s = data.get("s")
                t = data.get("t")
                await self.on_message(Opcodes(op), d , s, t)

        self.hb.cancel()
        await self.run()



    async def identify(self):
        identify_data = {
            "token": self.token,
            "properties": {
                "$os": "Windows 11",
                "$browser": "Google Chrome",
                "$device": "Windows",
            },
            "presence": {"status": "online", "afk": False},
        }
        await self.send(Opcodes.IDENTIFY ,  identify_data)

    async def on_message(self, op: Opcodes , data: dict, sequence_number: int, event_name: str):
        self.sequence_number = sequence_number
        if op is Opcodes.HELLO:
            self.hb = self.loop.create_task(self.send_heartbeat(data['heartbeat_interval']))
            await self.identify()
        elif op is Opcodes.INVALID_SESSION:
            await self.identify()
        
        if event_name is Events.INTERACTION_SUCCESS:
            print(data)
        
        pass

    async def send_heartbeat(self, heartbeat_interval):
        while True:
            await asyncio.sleep(heartbeat_interval / 1000)
            print("🔗 send heartbeat")
            await self.send(Opcodes.HEARTBEAT, self.sequence_number)

    async def send(self, op, data, *, sequences = None):
        ready_data = {
            "op": op.value,
            "d": data
        }

        if sequences is not None:
            ready_data["s"] = sequences
        await self.ws.send_json(ready_data)