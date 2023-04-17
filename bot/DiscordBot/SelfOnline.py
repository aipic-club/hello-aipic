"""
Keep all users online
"""
import json
import time
import websocket
import threading


class SelfOnline():
    def __init__(self,  users: object = []):
        self.users = users    
    def onliner(self, token):
        print("-- keep all users online --")
        status = "online"
        custom_status = ""
        ws = websocket.WebSocket()
        ws.connect("wss://gateway.discord.gg/?v=9&encoding=json")
        start = json.loads(ws.recv())
        heartbeat = start["d"]["heartbeat_interval"]
        auth = {
            "op": 2,
            "d": {
                "token": token,
                "properties": {
                    "$os": "Windows 11",
                    "$browser": "Google Chrome",
                    "$device": "Windows",
                },
                "presence": {"status": status, "afk": False},
            },
            "s": None,
            "t": None,
        }
        ws.send(json.dumps(auth))
        cstatus = {
            "op": 3,
            "d": {
                "since": 0,
                "activities": [
                    {
                        "type": 4,
                        "state": custom_status,
                        "name": "Custom Status",
                        "id": "custom",
                        #Uncomment the below lines if you want an emoji in the status
                        #"emoji": {
                            #"name": "emoji name",
                            #"id": "emoji id",
                            #"animated": False,
                        #},
                    }
                ],
                "status": status,
                "afk": False,
            },
        }
        ws.send(json.dumps(cstatus))
        online = {"op": 1, "d": "None"}
        time.sleep(heartbeat / 1000)
        ws.send(json.dumps(online))
    def run_onliner(self, token):
        while True:
            self.onliner(token)
            time.sleep(30)  
    def run(self):
        for u in self.users:
            token = u['authorization']
            t = threading.Thread(self.run_onliner(token))
            t.daemon = True
            t.start()    