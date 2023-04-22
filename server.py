import os
import random
import string
from typing import Annotated
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Header
from fastapi import BackgroundTasks
from celery import Celery
from dotenv import load_dotenv, find_dotenv
from data import Data, FileHandler, SysError, random_id, uids
load_dotenv(find_dotenv())

celery = Celery('tasks', broker=os.environ.get("CELERY.BROKER"))


app = FastAPI()


data = Data(
    redis_url = os.environ.get("REDIS"),
    mysql_url = os.environ.get("MYSQL"),
    proxy = None, 
    s3config= {
        'aws_access_key_id' : os.environ.get("AWS.ACCESS_KEY_ID"),
        'aws_secret_access_key' : os.environ.get("AWS.SECRET_ACCESS_KEY"),
        'endpoint_url' : os.environ.get("AWS.ENDPOINT")
    }
)


def random_id(length = 6) -> str:
    all = string.ascii_letters + string.digits
    # all = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.sample(all,length))

class Prompt(BaseModel):
    prompt: str

class Variation(BaseModel):
    id : int
    index: int

class Upscale(BaseModel):
    id : int
    index: int


@app.get("/")
def read_root():
    return "hello"

@app.post("/prompt")
async def send_prompt(item: Prompt, authentication: Annotated[str | None, Header()] = None):
    temp = data.check_token_and_get_id(token= authentication)
    if type(temp) is SysError:
        raise HTTPException(401,  temp.value)
    user = random.choice(uids)
    taskId = f'{user}.{random_id(10)}'    
    prompt = item.prompt
    res = celery.send_task('prompt',
        (
            temp,
            taskId,
            prompt
        )
    )
    return {
        'id':  taskId
    }

@app.post("/upscale")
async def upscale(item: Upscale, authentication: Annotated[str | None, Header()] = None):
    temp = data.check_token_and_get_id(token= authentication)
    if type(temp) is SysError:
        raise HTTPException(401,  temp.value)
    task = data.get_task_by_id(temp, item.id)
    if task is None:
        raise HTTPException(404,  "")    
    else:
        res = celery.send_task('upscale',
            (
                task,
                item.index
            )
        )
    return {}

@app.post("/variation")
async def variation(item: Variation, authentication: Annotated[str | None, Header()] = None):
    temp = data.check_token_and_get_id(token= authentication)
    if type(temp) is SysError:
        raise HTTPException(401,  temp.value)    
    task = data.get_task_by_id(temp, item.id)
    if task is None:
        raise HTTPException(404,  "")    
    else:
        res = celery.send_task('variation',
            (
                task,
                item.index
            )
        )
    return {}

@app.get("/sign")
async def get_sign():
    sign = data.fileHandler.generate_presigned_url(f'temp/{random_id(10)}.jpg')  
    return   {'sign': sign}

if __name__ == "__main__":
    pass