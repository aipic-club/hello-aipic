from aiohttp import web
import socketio
import uuid  # import uuid module to generate UUIDs

sio = socketio.AsyncServer(async_mode='aiohttp')
app = web.Application()
sio.attach(app)



async def send_heartbeat():
    while True:
        #data = {'id': '123123', 'prompt': ''}
        data = {
            "id": str(uuid.uuid4()),  # use uuid4() to generate a random UUID
            "data": {"name":"imagine","type":1,"options":[{"type":3,"name":"prompt","value":"https://s.mj.run/PzsU5JMviYg to create a 3d animate photo with jungle background.o --v 4"}]}
        }
        await  sio.sleep(10)
        await  sio.emit('mj', data)
        print("send command to mj")



@sio.event
def connect(sid, environ):
    print("connect ", sid)

@sio.event
async def chat_message(sid, data):
    print("message ", data)

@sio.event
def disconnect(sid):
    print('disconnect ', sid)



async def init_app():
    sio.start_background_task(send_heartbeat)
    return app


if __name__ == '__main__':
    web.run_app(init_app(), port=8089)