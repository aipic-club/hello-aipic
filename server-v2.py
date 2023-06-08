import os
import random
import string

from celery import Celery

from typing import Annotated, Callable, Optional, Union
from pydantic import BaseModel, Json
from fastapi import FastAPI,APIRouter, HTTPException, Depends,  Header, Request, Response, status
from fastapi import BackgroundTasks
from fastapi.routing import APIRoute
from fastapi.responses import PlainTextResponse
from fastapi.security import OAuth2PasswordBearer

from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException


from data import Data_v2, SysError, random_id
from config import *


data = Data_v2(
    redis_url = redis_url,
    mysql_url = mysql_url,
    proxy = None, 
    s3config= s3config
)

class Prompt(BaseModel):
    prompt: str
    raw: Union[str , None] = None
    execute: Union[bool , None] = None


celery = Celery('tasks', broker=celery_broker)

async def validate_pagination(page: int = 1, size: int = 10,) -> dict[int, int]:
    page = 1 if page < 1 else page
    size = 10 if size < 10 else size
    return {'page':page,'size':size}

async def get_token_id(authorization: str = Header(None)):
    if authorization is None:
        #return {"error": "Authorization header is missing"}
        raise HTTPException(401)
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        #return {"error": "Authorization header is invalid"}
        raise HTTPException(401)
    token = parts[1]
    temp = data.get_token_id(token= token)
    if type(temp) is SysError:
        raise HTTPException(401)
    else:
        return temp

app = FastAPI()
router = APIRouter(
    prefix="/api/v1.0",
    dependencies=[
        Depends(get_token_id)
    ]
)

@app.get("/ping")
async def ping():
    return PlainTextResponse(content="pong") 


@router.get("/tasks")
def list_tasks( 
    token_id: int = Depends(get_token_id), 
    pagination = Depends(validate_pagination)
):
    return data.get_tasks_by_token_id(
        token_id=token_id, 
        page= pagination['page'], 
        page_size= pagination['size']
    )

@router.post("/tasks")
def send_task(item: Prompt, token_id: int = Depends(get_token_id) ):
    taskId = random_id(11)
    prompt = item.prompt
    data.save_task(token_id= token_id, prompt=prompt, raw= item.raw, taskId= taskId)
    if item.execute:
         celery.send_task('prompt',
            (
                token_id,
                taskId,
                prompt
            ),
            queue="develop"
        )    
    return {
        'id':  taskId
    }
@router.delete("/tasks/{taskId}")
def send_task(taskId: str,  token_id: int = Depends(get_token_id) ):
    record = data.get_task(taskId= taskId, token_id= token_id)
    if record is None:
        raise HTTPException(404)   
    else:
        data.delete_task(taskId= taskId, token_id= token_id)
        return {
            'status': 'ok',
            'detail': ""
        }

app.include_router(router)