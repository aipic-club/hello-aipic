import os
import random
import string
import hashlib
import json
from datetime import datetime

from celery import Celery

from functools import partial
from typing import Annotated, Callable, Optional, Union
from pydantic import BaseModel, Json
from fastapi import FastAPI,APIRouter, HTTPException, Depends,  Header, Request, Response, status, Path
from fastapi import BackgroundTasks
from fastapi.routing import APIRoute
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException


from data import Data_v2,  SysCode, random_id
from data.values import output_type,image_hostname
from data.Snowflake import Snowflake
from config import *

Token = os.environ.get("MP.Token")
EncodingAESKey = os.environ.get("MP.EncodingAESKey")
AppID = os.environ.get("MP.AppID")


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

class Describe(BaseModel):
    url: str

celery = Celery('tasks', broker=celery_broker)




def check_wechat_signature(request: Request):
    params = request.query_params._dict
    signature = params["signature"]
    timestamp = params["timestamp"]
    nonce = params["nonce"]
    try:
        check_signature(Token, signature, timestamp, nonce)
    except InvalidSignatureException:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invalid signature"
        )

def calculate_md5(data):
    md5_hash = hashlib.md5()
    md5_hash.update(data.encode('utf-8'))  # Assuming 'data' is a string, encode it to bytes
    return md5_hash.hexdigest()

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
    id,code = data.get_token_id(token= token)
    if code is SysCode.OK and id is not None:
        return id
    else:
        raise HTTPException(401)
    
def get_token_id_and_task_id(taskId: str = Path(...), token_id: int = Depends(get_token_id) ):
    task_id = data.get_task(taskId= taskId, token_id= token_id)
    if task_id is None:
        raise HTTPException(404) 
    return  (taskId, token_id, task_id, )

def get_image(id:int = Path(...), token_id: int = Depends(get_token_id)) -> dict :
    record = data.get_detail_by_id(token_id=token_id, detail_id= id)
    if record is None:
        raise HTTPException(404) 
    if record['type'] in output_type:
        try:
            detail = json.loads(record['detail'])
            return {
                'id': id,
                'token_id': token_id,
                'detail': {
                    'taskId': record.get('taskId'),
                    'id': detail.get('id'),
                    'hash': detail.get('hash')
                }
            }
        except:
            raise HTTPException(500)
    else:
        raise HTTPException(405) 
    
def get_task_jobs(token_id: int, taskId: str):
    status = data.redis_task_status(token_id= token_id, taskId=taskId)
    job = data.redis_task_job_status(taskId=taskId)
    return status, job

def is_busy(token_id: int, taskId: str):
    status, job  = get_task_jobs(token_id= token_id, taskId=taskId)
    return status is not None or len(job) > 0

app = FastAPI()


origins = [
    "http://127.0.0.1:5173",
    "http://localhost:5173",
    "https://aipic.club",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


router = APIRouter(
    prefix="/api/v1.0",
    dependencies=[
        Depends(get_token_id)
    ]
)

@app.get("/ping")
async def ping():    
    return PlainTextResponse(content="pong") 

@app.get("/mp",  dependencies=[Depends(check_wechat_signature)])
def mp(echostr: int):
    return echostr


@app.post("/mp", dependencies=[Depends(check_wechat_signature)])
async def mp(request: Request):
    #params = request.query_params._dict
    body = await request.body()
    msg = parse_message(body)
    reply = create_reply(None, msg)
    if msg.type == "text":
        if (msg.content == "试用" or msg.content == "aipic"):
            token,days = data.create_trial_token(msg.source) 
            expire = '{token}\n❗有效期小于一天，请及时备份' if days == 0 else f'{token}\n有效期剩余{days}天'
            template =  f'{expire}\n有效期后可继续获取试用 \n电脑访问https://aipic.club/或<a href="https://aipic.club/trial/{token}">在微信中</a>试用AIPic'
            reply = create_reply(template , msg)
    return Response(content=reply.render(), media_type="application/xml")



@router.get("/tasks")
async def list_tasks( 
    token_id: int = Depends(get_token_id), 
    pagination = Depends(validate_pagination)
):
    return data.get_tasks_by_token_id(
        token_id=token_id, 
        page= pagination['page'], 
        page_size= pagination['size']
    )


@router.post("/tasks")
async def create_task(token_id: int = Depends(get_token_id) ):
    taskId = random_id(11)
    data.create_task(token_id= token_id, taskId= taskId)
    return {
        'id':  taskId
    }

@router.post("/tasks/{taskId}")
async def add_task_item(item: Prompt, token_id_and_task_id: int = Depends(get_token_id_and_task_id) ):
    taskId, token_id, task_id  = token_id_and_task_id
    if is_busy(token_id= token_id, taskId= taskId):
        return Response(status_code=202)
     
    prompt = item.prompt
    execute = item.execute
    raw = item.raw

    #record = data.get_fist_input_id(task_id=task_id)
    
    #queue = 'celery'
    # queue = 'queue_1'
    broker_id = None
    account_id = None
    # if record is not None:
    #     first_id = int(record.get('id'))
    #     broker_id , account_id = Snowflake.parse_snowflake_id(first_id)
    #     queue = f"queue_{broker_id}"
        
    celery.send_task('prompt',
        (
            broker_id,
            account_id,
            token_id,
            taskId,
            prompt,
            raw,
            execute,
        )
    )  
  
    return {
        "status": "ok"
    }
@router.delete("/tasks/{taskId}")
async def delete_task(token_id_and_task_id: int = Depends(get_token_id_and_task_id) ):
    taskId, token_id, _  = token_id_and_task_id
    cache_key = f'cache:{token_id}:{taskId}'
    data.delete_task(taskId= taskId)
    data.remove_cache(cache_key)
    return {
        'status': 'ok',
        'detail': ""
    }


@router.post("/tasks/{taskId}/describe")
def describe_a_img(describe:Describe, token_id_and_task_id: int = Depends(get_token_id_and_task_id) ):
    taskId, _, _ = token_id_and_task_id 
    url = describe.url
    celery.send_task('describe',
        (
            taskId,
            url
        )
    ) 
    return {
        'status': 'ok',
    }


@router.get("/tasks/{taskId}/status")
def get_task_status(token_id_and_task_id: int = Depends(get_token_id_and_task_id) ):
    taskId, token_id, _ = token_id_and_task_id 
    status, job  = get_task_jobs(token_id= token_id, taskId=taskId)
    return{
        'status': status,
        'jobs': job
    }
@router.get("/tasks/{taskId}/detail")
async def get_task_detail(
    token_id_and_task_id: int = Depends(get_token_id_and_task_id) , 
    pagination = Depends(validate_pagination)
):
    _,_,task_id  = token_id_and_task_id
    detail = data.get_detail(task_id=task_id, page= pagination['page'] , page_size= pagination['size'] )
    return detail
@router.post("/upscale/{id}")
async def upscale( item: Upscale,detail: dict = Depends(get_image)):
    print(detail)
    if is_busy(token_id= detail.get('token_id'), taskId= detail.get('detail',{}).get('taskId')):
        return Response(status_code=202)
    broker_id , account_id = Snowflake.parse_snowflake_id(detail.get('id'))
    celery.send_task('upscale',
        (
            {
                **detail.get('detail',{}),
                'ref_id': detail.get('id'),
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
async def upscale( item:  Remix,  detail: dict = Depends(get_image)):

    if is_busy(token_id= detail.get('token_id'), taskId= detail.get('detail',{}).get('taskId')):
        return Response(status_code=202)

    broker_id , account_id = Snowflake.parse_snowflake_id(detail.get('id'))
    celery.send_task('variation',
        (
            item.prompt,
            {
                **detail.get('detail',{}),
                'ref_id': detail.get('id'),
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

@router.get("/profile")
async def get_profile(token_id: int = Depends(get_token_id)):
    temp = data.redis_get_cost(token_id= token_id)
    return temp


@router.post("/sign")
async def get_sign( token_id: int = Depends(get_token_id)):
    path = calculate_md5(f'aipic.{token_id}')
    full_url = f'upload/{path}/{random_id(10)}.jpg'
    sign = data.file_generate_presigned_url(full_url)  
    return   {
        'sign': sign,
        'url': f'{image_hostname}/{full_url}'
    }

app.include_router(router)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", port=8000, log_level="info", reload= True)