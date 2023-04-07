import yaml
import socketio
import asyncio
from celery import Celery


file = open("./config.yaml", 'r', encoding="utf-8")
file_data = file.read()
file.close()
conf = yaml.safe_load(file_data)

celery = Celery('tasks', broker=conf['celery']['broker'])
#sio = socketio.AsyncClient(logger=True, engineio_logger=True)
sio = socketio.AsyncClient()

@sio.event
async def connect():
    print('connection established')

# @sio.event
# async def my_message(data):
#     print('message received with ', data)
#     await sio.emit('my response', {'response': 'my response'})

@sio.event
async def disconnect():
    print('disconnected from server')

@sio.on('mj')
async def on_message(data):
    print(f'received mj command: {data}')
    res = celery.send_task('add_mj_task', (data['id'], data['data']) )



async def main():
    await sio.connect(conf['socket'])
    await sio.wait()

if __name__ == '__main__':
    asyncio.run(main())
