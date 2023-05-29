# import asyncio
# import websockets
# import json



# token = "MTAyMTYxMjYyODk4MTg0NjAzOA.GdtMD6.mPHb_iBXl7-oGAQD6A_Bhhj3nvrhWiWGowPOfw"

# class DiscordWebSocketClient:
#     def __init__(self, token: str):
#         self.auth_string = json.dumps({
#             "op": 2,
#             "d": {
#                 "token": token,
#                 "properties": {
#                     "$os": "Windows 11",
#                     "$browser": "Google Chrome",
#                     "$device": "Windows",
#                 },
#                 "presence": {"status": "online", "afk": False},
#             },
#             "s": None,
#             "t": None,
#         })
#         self.websocket = None
#         self.heartbeat = 0
#     async def connect(self):

#         loop = asyncio.get_event_loop()

#         async for websocket in websockets.connect('wss://gateway.discord.gg/?v=9&encoding=json'):
#             try:
#                 self.websocket = websocket
#                 start = await self.websocket.recv()
#                 start = json.loads(start)
#                 self.heartbeat = start["d"]["heartbeat_interval"]
#                 await asyncio.sleep(10)
#                 await self.websocket.send(self.auth_string)
#                 print(self.heartbeat)
#                 # loop.create_task(self.send_heartbeat())
#                 # loop.create_task(self.receive_messsages())
#                 # asyncio.sleep(float('inf'))
#             except websockets.ConnectionClosed:
#                 print(1)
#                 continue
        
#         print(1)


#     async def send_heartbeat(self):
#         while True:
#             await asyncio.sleep(self.heartbeat / 1000)
#             print("send heart beat")
#             online_str = json.dumps({"op": 1, "d": None})
#             try:
#                 await self.websocket.send(online_str)
#             except:
#                 pass
#     async def receive_messsages(self):
#         while True:
#             try:
#                 message = await self.websocket.recv()
#                 print('msg', message)
#             except:

#                 print(3)
#                 pass







# async def handle_messages():
#     loop = asyncio.get_running_loop()
#     uri = 'wss://gateway.discord.gg/?v=9&encoding=json'  # Replace with your WebSocket server URI
#     auth_string = json.dumps(auth)  # Replace with your authentication string
    
#     while True:
#         try:
#             async with websockets.connect(uri) as websocket:
#                 start = await websocket.recv()
#                 heartbeat = start["d"]["heartbeat_interval"]
#                 print(message)

#                 # Send authentication string
#                 await websocket.send(auth_string)
                
#                 while True:
#                     message = await websocket.recv()
             
#                     #print("Received message:", message)
#         except websockets.exceptions.ConnectionClosed:
#             print("Connection closed, attempting to reconnect in 5 seconds...")
#             asyncio.sleep(10)




# asyncio.run(handle_messages())

# discordWebSocketClient = DiscordWebSocketClient(token)

# asyncio.run(discordWebSocketClient.connect())



# token = "MTAyMTYxMjYyODk4MTg0NjAzOA.GdtMD6.mPHb_iBXl7-oGAQD6A_Bhhj3nvrhWiWGowPOfw"

# client = SelfClient()

# client.run(token)


