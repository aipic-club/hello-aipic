import os
import random
import string
from typing import Annotated, Callable, Optional, Union
from pydantic import BaseModel, Json
from fastapi import FastAPI,APIRouter, HTTPException, Depends,  Header, Request, Response
from fastapi import BackgroundTasks
from fastapi.routing import APIRoute
from fastapi.responses import PlainTextResponse
from celery import Celery
from dotenv import load_dotenv, find_dotenv
from data import Data, TaskStatus, SysError, random_id, uids
load_dotenv(find_dotenv())

celery = Celery('tasks', broker=os.environ.get("CELERY.BROKER"))


async def get_token_id(authentication: str = Header(None)):
    temp = data.check_token_and_get_id(token= authentication)
    if type(temp) is SysError:
        raise HTTPException(401)
    else:
        return temp
    
async def validate_pagination(page: int = 1, size: int = 10,) -> dict[int, int]:
    page = 1 if page < 1 else page
    size = 10 if size < 10 else size
    return {'page':page,'size':size}

async def get_task():
    # task = data.get_task_by_id( token_id, task_id)
    # if task is None:
    #     raise HTTPException(404)  
    # return task  
    pass


app = FastAPI()
router = APIRouter(
    prefix="/api/v1.0",
    dependencies=[
        Depends(get_token_id),
        Depends(validate_pagination)
    ]
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


class Prompt(BaseModel):
    prompt: str
    raw: Union[str , None] = None
    execute: Union[bool , None] = None


@app.get("/ping")
async def ping():
    return PlainTextResponse(content="pong") 

@router.get("/prompts")
async def list_prompts( token_id: int = Depends(get_token_id), pagination = Depends(validate_pagination)):
    records = data.get_prompts_by_token_id(token_id=token_id, page= pagination['page'] , page_size= pagination['size'])
    return records

@router.get("/images/{taskId}")
async def prompt_detail(taskId: str, page: int = 1, size: int = 10, token_id: int = Depends(get_token_id)):
    if page < 1 or size < 10:
        raise HTTPException(500)
    records = data.get_tasks_by_taskId(token_id=token_id, taskId= taskId, page= page, page_size= size)
    return records

@router.post("/prompts")
async def send_prompt(item: Prompt, token_id: int = Depends(get_token_id) ):
    user = random.choice(uids)
    taskId = f'{user}.{random_id(10)}'    
    prompt = item.prompt
    data.add_task(
        token_id = token_id,
        prompt = prompt,
        raw= item.raw,
        taskId = taskId,
        status = TaskStatus.CONFIRMED if item.execute else TaskStatus.CREATED
    ) 

    if item.execute:
         celery.send_task('prompt',
            (
                token_id,
                taskId,
                prompt
            )
        )
    return {
        'id':  taskId
    }

@router.post("/images/{image_hash}/upscale")
async def upscale(image_hash:str, index: int, token_id: int = Depends(get_token_id)):
    task = data.get_task_by_messageHash(token_id , image_hash)
    if task is None:
        raise HTTPException(404)    
    else:
        res = celery.send_task('upscale',
            (
                task,
                index
            )
        )
    return {}

@router.post("/images/{image_hash}/variation")
async def variation(image_hash:str, index: int,  token_id: int = Depends(get_token_id)):
    task = data.get_task_by_messageHash(token_id , image_hash)
    if task is None:
        raise HTTPException(404)    
    else:
        res = celery.send_task('variation',
            (
                task,
                index
            )
        )
    return {}


@router.post("/sign")
async def get_sign(token_id: int = Depends(get_token_id)):
    sign = data.fileHandler.generate_presigned_url(f'temp/{token_id}/{random_id(10)}.jpg')  
    return   {'sign': sign}


app.include_router(router)
