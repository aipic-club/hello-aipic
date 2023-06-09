import os
import random
import string
import json

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
from data.values import output_type
from data.Snowflake import Snowflake
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
class Upscale(BaseModel):
    index: int
class Remix(BaseModel):
    prompt: str
    index: int

celery = Celery('tasks', broker=celery_broker)

def validate_pagination(page: int = 1, size: int = 10,) -> dict[int, int]:
    page = 1 if page < 1 else page
    size = 10 if size < 10 else size
    return {'page':page,'size':size}

def get_token_id(authorization: str = Header(None)):
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

def get_image_detail(id: int, token_id: int) -> dict[str, str]:
    record = data.get_detail_by_id(token_id=token_id, detail_id= id)
    if record is None:
        raise HTTPException(404) 
    if record['type'] in output_type:
        try:
            detail = json.loads(record['detail'])
            return {
                'taskId': record['taskId'],
                'id': detail['id'],
                'hash': detail['hash']
            }
        except:
            raise HTTPException(500)
    else:
        raise HTTPException(405) 

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
def create_task(token_id: int = Depends(get_token_id) ):
    taskId = random_id(11)
    data.create_task(token_id= token_id, taskId= taskId)
    return {
        'id':  taskId
    }

@router.post("/tasks/{taskId}")
def add_task_item(taskId: str, item: Prompt, token_id: int = Depends(get_token_id) ):
    if data.verify_task(token_id= token_id, taskId= taskId):
        raise HTTPException(404)   
    prompt = item.prompt
    execute = item.execute
    raw = item.raw
    
    celery.send_task('prompt',
        (
            token_id,
            taskId,
            prompt,
            raw,
            execute
        )
    )  
  
    return {
        "status": "ok"
    }
@router.delete("/tasks/{taskId}")
def delete_task(taskId: str,  token_id: int = Depends(get_token_id) ):
    record = data.get_task(taskId= taskId, token_id= token_id)
    if record is None:
        raise HTTPException(404)   
    else:
        data.delete_task(taskId= taskId, token_id= token_id)
        return {
            'status': 'ok',
            'detail': ""
        }

@router.get("/tasks/{taskId}/status")
def get_task_status(taskId: str,  token_id: int = Depends(get_token_id) ):
    pass
@router.get("/tasks/{taskId}/detail")
def get_task_detail(taskId: str, pagination = Depends(validate_pagination), token_id: int = Depends(get_token_id) ):
    record = data.get_task(taskId= taskId, token_id= token_id)
    if record is None:
        raise HTTPException(404)   

    else:
        detail = data.get_detail(task_id=record['id'], page= pagination['page'] , page_size= pagination['size'] )
        return detail
@router.post("/upscale/{id}")
def upscale( item: Upscale, id:int, token_id: int = Depends(get_token_id)):
    detail = get_image_detail(id=id, token_id=token_id)
    broker_id , account_id = Snowflake.parse_snowflake_id(id)
    celery.send_task('upscale',
        (
            item.prompt,
            {
                **detail,
                'ref_id': id,
                'broker_id': broker_id,
                'account_id' : account_id
            },
            item.index,
        ),
        queue= f"queue_{broker_id}"
    )
    return {
        'status': 'ok'
    }

@router.post("/variation/{id}")
def upscale( item:  Remix, id:int, token_id: int = Depends(get_token_id)):
    detail = get_image_detail(id=id, token_id=token_id)
    broker_id , account_id = Snowflake.parse_snowflake_id(id)
    celery.send_task('variation',
        (
            item.prompt,
            {
                **detail,
                'ref_id': id,
                'broker_id': broker_id,
                'account_id' : account_id
            },
            item.index,
        ),
        queue= f"queue_{broker_id}"
    )
    return {
        'status': 'ok'
    }


app.include_router(router)