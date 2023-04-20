import os
import random
import string
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi import BackgroundTasks
from celery import Celery
from dotenv import load_dotenv, find_dotenv
from data import FileHandler
load_dotenv(find_dotenv())

celery = Celery('tasks', broker=os.environ.get("CELERY.BROKER"))


app = FastAPI()

test_token = 'XDV9Z3uvQgVTsSYReuXk'
fileHandler = FileHandler(proxy = None, s3config= {
    'aws_access_key_id' : os.environ.get("AWS.ACCESS_KEY_ID"),
    'aws_secret_access_key' : os.environ.get("AWS.SECRET_ACCESS_KEY"),
    'endpoint_url' : os.environ.get("AWS.ENDPOINT")
})

def random_id(length = 6) -> str:
    all = string.ascii_letters + string.digits
    # all = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.sample(all,length))

class Prompt(BaseModel):
    prompt: str

@app.get("/")
def read_root():
    return {}

# @app.get("/items/{item_id}")
# def read_item(item_id: int, q: Union[str, None] = None):
#     res = celery.send_task('upload_img',
#         ('https://images.unsplash.com/photo-1681276311947-ebee32b4d4cc?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1374&q=80',
#         )
#     )
#     print(res)
#     return {"item_id": item_id, "q": q }

@app.post("/prompt")
async def send_prompt(item: Prompt):
    prompt = item.prompt
    taskId = random_id()
    res = celery.send_task('prompt',
        (
            test_token,
            taskId,
            prompt
        )
    )
    return {
        'taskId': taskId
    }

@app.post("/upscale/{id}/{index}")
async def upscale(id: int, index: int):
    res = celery.send_task('upscale',
        (
            test_token,
            id,
            index
        )
    )
    return {}

@app.post("/variation/{id}/{index}")
async def variation(id: int, index: int):
    res = celery.send_task('upscale',
        (
            test_token,
            id,
            index
        )
    )
    return {}

@app.get("/sign")
async def get_sign():
    sign = fileHandler.generate_presigned_url(f'temp/{random_id(10)}.jpg')  
    return   {'sign': sign}

if __name__ == "__main__":
    pass