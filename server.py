import os
import random
import string
from typing import Annotated, Callable
from pydantic import BaseModel
from fastapi import FastAPI,APIRouter, HTTPException, Depends,  Header, Request, Response
from fastapi import BackgroundTasks
from fastapi.routing import APIRoute
from celery import Celery
from dotenv import load_dotenv, find_dotenv
from data import Data, FileHandler, SysError, random_id, uids
load_dotenv(find_dotenv())

celery = Celery('tasks', broker=os.environ.get("CELERY.BROKER"))


async def get_token_id(authentication: str = Header(None)):
    # if x_token != "fake-super-secret-token":
    #     raise HTTPException(status_code=400, detail="X-Token header invalid")
    temp = data.check_token_and_get_id(token= authentication)
    if type(temp) is SysError:
        raise HTTPException(401)
    else:
        return temp
        


app = FastAPI()
router = APIRouter(
    prefix="/api/v1.0",
    dependencies=[Depends(get_token_id)]
)


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






@app.get("/ping")
async def ping():
    return "pong"

@router.get("/prompts")
async def variation( page: int = 1, size: int = 10, token_id: int = Depends(get_token_id)):
    pass

@router.get("/prompts/{prompt_id}")
async def variation(prompt_id: int,  token_id: int = Depends(get_token_id)):
    pass

@router.post("/prompts")
async def send_prompt(item: Prompt, token_id: int = Depends(get_token_id) ):
    user = random.choice(uids)
    taskId = f'{user}.{random_id(10)}'    
    prompt = item.prompt
    res = celery.send_task('prompt',
        (
            token_id,
            taskId,
            prompt
        )
    )
    return {
        'id':  taskId
    }

@router.post("/upscale")
async def upscale(item: Upscale, token_id: int = Depends(get_token_id)):
    task = data.get_task_by_id( token_id, item.id)
    if task is None:
        raise HTTPException(404)    
    else:
        res = celery.send_task('upscale',
            (
                task,
                item.index
            )
        )
    return {}

@router.post("/variation")
async def variation(item: Variation,  token_id: int = Depends(get_token_id)):
    task = data.get_task_by_id(token_id , item.id)
    if task is None:
        raise HTTPException(404)    
    else:
        res = celery.send_task('variation',
            (
                task,
                item.index
            )
        )
    return {}






@router.post("/sign")
async def get_sign():
    sign = data.fileHandler.generate_presigned_url(f'temp/{random_id(10)}.jpg')  
    return   {'sign': sign}


app.include_router(router)
