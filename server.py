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
from wechatpy.events import SubscribeEvent

from bot.DiscordUser.values import MJ_VARY_TYPE


from data import Data,  SysCode, random_id
from data.values import DetailType, TaskStatus, output_type,image_hostname
from data.Snowflake import Snowflake
from config import *

Token = os.environ.get("MP.Token")
EncodingAESKey = os.environ.get("MP.EncodingAESKey")
AppID = os.environ.get("MP.AppID")


data = Data(
    redis_url = redis_url,
    mysql_url = mysql_url,
    proxy = None, 
    s3config= s3config
)

class Prompt(BaseModel):
    prompt: str
    raw: Union[str , None] = None
    execute: Union[bool , None] = None

class Task(BaseModel):
    name: str | None

class Upscale(BaseModel):
    index: int
class Remix(BaseModel):
    prompt: str
    index: int

class Describe(BaseModel):
    url: str


class Vary(BaseModel):
    type:  MJ_VARY_TYPE

class Zoom(BaseModel):
    type: int


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

def token_context(authorization: str = Header(None)):
    if authorization is None:
        #return {"error": "Authorization header is missing"}
        raise HTTPException(401)
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        #return {"error": "Authorization header is invalid"}
        raise HTTPException(401)
    token = parts[1]

    token_id, info , code = data.get_token_info(token= token)

    if code is SysCode.OK and id is not None:
        return (token, token_id, info)
    else:
        raise HTTPException(401)
    
    
def space_context(space_name: str = Path(...), context: tuple = Depends(token_context) ):
    token, token_id, _ = context
    space_id = data.get_space(
        token = token, 
        token_id= token_id, 
        space_name= space_name
    )
    if space_id is None:
        raise HTTPException(404) 
    return  (space_name, space_id, context )

def get_image(id:int = Path(...), context: tuple = Depends(token_context)) -> dict :
    _, token_id, _ = context
    record = data.get_detail_by_id(token_id=token_id, detail_id= id)
    if record is None:
        raise HTTPException(404) 
    if record['type'] in output_type:
        try:
            detail = json.loads(record['detail'])
            return {
                'id': id,
                'token_id': token_id,
                'type': record['type'],
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


    
def get_space_jobs(token_id: int, space_name: str):
    # status = data.redis_space_ongoing_prompt_status(token_id= token_id, space_name=space_name)
    # job = data.redis_task_job_status(space_name=space_name)
    # describe_data = data.redis_get_describe(space_name=space_name)
    # describe = describe_data.get("url") if describe_data is not None else None
    # return (status, job, describe,)
    pass

def is_busy(token_id: int, space_name: str):
    # status, job, describe  = get_space_jobs(token_id= token_id, space_name=space_name)
    # return status is not None or len(job) > 0 or describe is not None
    pass

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
        Depends(token_context)
    ]
)

@app.get("/ping")
async def ping(request: Request): 
    print(f'request header       : {dict(request.headers.items())}' )    
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
    if msg.type == 'event' and msg.event == SubscribeEvent.event:
        token,days = data.create_trial_token(msg.source) 
        template =  f'👏👏 欢迎关注 👏👏\n这里是一个充满创造力的空间，我们相信您将在这里找到灵感的源泉。'
        if days >= 0:
            template += '\n<a href="https://aipic.club/trial/{token}">👉👉 免费使用Midjourney 👈👈</a>'

        reply = create_reply(template , msg)
    elif msg.type == "text":
        lowercase_string = str(msg.content).lower()  # Convert string to lowercase
        no_spaces_string = lowercase_string.replace(" ", "")        
        if (no_spaces_string == "试用" or no_spaces_string == "aipic"):
            token,days = data.create_trial_token(msg.source) 
            if days < 0:
                template = "您的试用已过期，请点击菜单购买授权码后继续使用"
            else:
                template = f'{token}\n❗有效期小于一天，请及时备份' if days == 0 else f'{token}\n有效期剩余{days}天'
                template +=  f'\n<a href="https://aipic.club/trial/{token}">👉👉 试用https://AIPic.club 👈👈</a>'
            reply = create_reply(template , msg)

    return Response(content=reply.render(), media_type="application/xml")



@router.get("/spaces")
async def list_tasks( 
    context: tuple = Depends(token_context), 
    pagination = Depends(validate_pagination)
):
    _, token_id, _ = context
    return data.get_spaces_by_token_id(
        token_id=token_id, 
        page= pagination['page'], 
        page_size= pagination['size']
    )


@router.post("/spaces")
async def create_space(context: tuple = Depends(token_context)):
    _, token_id, _ = context
    name = random_id(11)
    data.create_space(token_id= token_id, name = name)
    return {
        'id':  name
    }

@router.put("/spaces/{space_name}")
async def update_task(task: Task, context: tuple  = Depends(space_context)):
    space_name, _ , _ = context
    name = task.name
    if name is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    
    data.update_space_topic(name=space_name, topic=name)

    return {
        'status': 'ok',
    }

@router.post("/spaces/{space_name}")
async def add_task_to_space(item: Prompt, context: tuple  = Depends(space_context) ):
    space_name, _ , token_context  = context
    _, token_id, info = token_context

    if is_busy(token_id= token_id, space_name= space_name):
        return Response(status_code=202)
     
    prompt = item.prompt
    execute = item.execute
    raw = item.raw

    token_type = info.get("type")


    data.update_status(space_name=space_name, status= TaskStatus.ACCEPTED)      


    celery.send_task('prompt',
        (
            token_id,
            token_type,
            space_name,
            prompt,
            raw,
            execute,
        ),
        queue= 'develop' if is_dev else 'celery'
    )
    return {
        "status": "ok"
    }


# @router.delete("/tasks/{taskId}")
# async def delete_task(task_context: tuple  = Depends(task_context) ):
#     taskId, _ , context  = task_context
#     _, token_id,_ = context
#     if is_busy(token_id= token_id, taskId= taskId):
#         return Response(status_code=202)    
#     cache_key = f'cache:{token_id}:{taskId}'
#     data.delete_task(taskId= taskId)
#     data.remove_cache(cache_key)
#     return {
#         'status': 'ok',
#         'detail': ''
#     }


# @router.post("/tasks/{taskId}/describe")
# def describe_a_img(describe:Describe, token_id_and_task_id = Depends(task_context) ):
#     taskId, _, _ = token_id_and_task_id 
#     url = describe.url
#     celery.send_task('describe',
#         (
#             taskId,
#             url
#         ),
#         queue= 'develop' if is_dev else 'celery'
#     ) 
#     return {
#         'status': 'ok',
#     }


# @router.get("/tasks/{taskId}/status")
# def get_task_status(token_id_and_task_id = Depends(task_context) ):
#     taskId, token_id, _ = token_id_and_task_id 
#     status, job,  describe  = get_task_jobs(token_id= token_id, taskId=taskId)
#     return{
#         'status': status,
#         'jobs': job,
#         'describing': describe
#     }
# @router.get("/tasks/{taskId}/detail")
# async def get_task_detail(
#     before: datetime = None,
#     after: datetime = None,    
#     token_id_and_task_id = Depends(task_context) , 
#     pagination = Depends(validate_pagination)
# ):
#     _,_,task_id  = token_id_and_task_id

#     detail = data.get_detail(
#         task_id=task_id, 
#         page= pagination['page'] , 
#         page_size= pagination['size'] ,
#         before = before,
#         after= after
#     )
#     return detail

# @router.post("/upscale/{id}")
# async def upscale( item: Upscale, detail: dict = Depends(get_image)):
#     if is_busy(token_id= detail.get('token_id'), taskId= detail.get('detail',{}).get('taskId')):
#         return Response(status_code=202)
#     broker_id , account_id = Snowflake.parse_snowflake_id(detail.get('id'))
#     celery.send_task('upscale',
#         (
#             {
#                 **detail.get('detail',{}),
#                 'ref_id': detail.get('id'),
#                 'broker_id': broker_id,
#                 'account_id' : account_id
#             },
#             item.index,
#         ),
#         queue= f"queue_{broker_id}"
#     )
#     return {
#         'status': 'ok'
#     }

# @router.post("/variation/{id}")
# async def upscale( item:  Remix,  detail: dict = Depends(get_image)):

#     if is_busy(token_id= detail.get('token_id'), taskId= detail.get('detail',{}).get('taskId')):
#         return Response(status_code=202)

#     broker_id , account_id = Snowflake.parse_snowflake_id(detail.get('id'))
#     celery.send_task('variation',
#         (
#             item.prompt,
#             {
#                 **detail.get('detail',{}),
#                 'ref_id': detail.get('id'),
#                 'broker_id': broker_id,
#                 'account_id' : account_id
#             },
#             item.index,
#         ),
#         queue= f"queue_{broker_id}"
#     )
#     return {
#         'status': 'ok'
#     }

# @router.post("/vary/{id}")
# async def vary(item: Vary, detail: dict = Depends(get_image)):
#     if detail.get('type') is not DetailType.OUTPUT_MJ_UPSCALE.value:
#          raise HTTPException(status_code=status.HTTP_406_NOT_ACCEPTABLE)
#     if is_busy(token_id= detail.get('token_id'), taskId= detail.get('detail',{}).get('taskId')):
#         return Response(status_code=202)
#     broker_id , account_id = Snowflake.parse_snowflake_id(detail.get('id'))
#     print(item.type)
#     celery.send_task('vary',
#         (
#             item.type,
#             {
#                 **detail.get('detail',{}),
#                 'ref_id': detail.get('id'),
#                 'broker_id': broker_id,
#                 'account_id' : account_id
#             }
#         ),
#         queue= f"queue_{broker_id}"
#     )
#     return {
#         'status': 'ok'
#     }

# @router.post("/zoom/{id}")
# async def zoom():
#     pass




# @router.get("/profile")
# async def get_profile(context: tuple = Depends(token_context)):
#     _, token_id, info = context
#     cost = data.redis_get_cost(token_id= token_id)
#     del info["id"]
#     return {
#         **info,
#         "cost": int(cost)
#     }

# @router.post("/sign")
# async def get_sign( context: tuple = Depends(token_context)):
#     _, token_id, _ = context
#     path = calculate_md5(f'aipic.{token_id}')
#     full_url = f'upload/{path}/{random_id(10)}.jpg'
#     sign = data.file_generate_presigned_url(full_url)  
#     return   {
#         'sign': sign,
#         'url': f'{image_hostname}/{full_url}'
#     }

app.include_router(router)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host='0.0.0.0', port=8000, log_level="info", reload= True)