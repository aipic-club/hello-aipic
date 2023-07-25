from datetime import datetime
import os
import hashlib
import json

from functools import partial

from typing import Annotated, Callable, Optional, Union
from pydantic import BaseModel, Json
from fastapi import Body, FastAPI,APIRouter, HTTPException, Depends,  Header, Request, Response, status, Path
from fastapi import BackgroundTasks
from fastapi.routing import APIRoute
from fastapi.responses import PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware

from celery import Celery

from wechatpy import parse_message, create_reply
from wechatpy.utils import check_signature
from wechatpy.exceptions import InvalidSignatureException, InvalidAppIdException
from wechatpy.events import SubscribeEvent


from data import Data,  SysCode, random_id
from data.values import DetailType, TaskStatus
from data.Snowflake import Snowflake
from config import *
from .model import *

Token = os.environ.get("MP.Token")
EncodingAESKey = os.environ.get("MP.EncodingAESKey")
AppID = os.environ.get("MP.AppID")


data = Data(
    is_dev=is_dev,
    redis_url = redis_url,
    mysql_url = mysql_url,
    proxy = None, 
    s3config= s3config
)


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
    token_id, info, cost , code = data.get_token_info(token= token)
    #spaces = data.get_all_spaces(token_id= token_id)
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


class ImageContext:
    def __init__(self, allowed_types: list[DetailType] =[]):
        self.allowed_types= allowed_types
    def __call__(
            self,
            id:int = Path(...),
            context: tuple = Depends(token_context)            
        ):
        _, token_id, _ = context
        record = data.get_detail_by_id(token_id=token_id, detail_id= id, types= self.allowed_types)

        if record is None:
            raise HTTPException(404) 
        try:
            detail = json.loads(record['detail'])
            return {
                'id': id,
                'token_id': token_id,
                'type': record['type'],
                'detail': {
                    'space_name': record.get('name'),
                    'id': detail.get('id'),
                    'hash': detail.get('hash')
                }
            }
        except:
            raise HTTPException(500)


    
def get_space_jobs( space_name: str):
    status = data.space_prompt_status(space_name=space_name)
    jobs = data.spaces_jobs(space_name=space_name)
    describe_data = data.redis_get_describe(space_name=space_name)
    describe = describe_data.get("url") if describe_data is not None else None
    return status, jobs, describe

def is_busy( space_name: str):
    status, jobs, describe  = get_space_jobs( space_name=space_name)
    return status is not None or len(jobs) > 0 or describe is not None
def withhold(space_name: str):
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
    # print(f'request header : {dict(request.headers.items())}' )    
    celery.send_task('ping', queue= 'develop' if is_dev else 'celery')
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
            template += f'\n<a href="https://aipic.club/trial/{token}">👉👉 免费使用Midjourney 👈👈</a>'

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
async def update_space(space: RenameSpaceBody, context: tuple  = Depends(space_context)):
    space_name, _ , _ = context
    name = space.name
    if name is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    
    data.update_space_topic(space_name=space_name, topic=name)

    return {
        'status': 'ok',
    }

@router.post("/spaces/{space_name}")
async def add_task_to_space(body: ImagineBody, context: tuple  = Depends(space_context) ):
    space_name, _ , token_context  = context
    _, token_id, info = token_context

    if is_busy(space_name= space_name):
        return Response(status_code=202)

    token_type = info.get("type")
    data.space_prompt(space_name=space_name, status= TaskStatus.ACCEPTED) 
    celery.send_task('imagine',
        (
            token_type,
            space_name,
            body.prompt,
            body.raw,
            body.execute,
        ),
        queue= 'develop' if is_dev else 'celery'
    )
    return {
        "status": "ok"
    }



@router.delete("/spaces/{space_name}")
async def delete_space(context: tuple  = Depends(space_context) ):
    space_name, _ , token_context  = context
    token, _, _ = token_context
    if is_busy(space_name= space_name):
        return Response(status_code=202)   
    data.clean_space(token=token,  space_name=space_name) 
    return {
        'status': 'ok',
        'detail': ''
    }    


@router.post("/spaces/{space_name}/describe")
def describe(
    body: DescribeBody,
    context: tuple  = Depends(space_context) 
):
    space_name, _ , _  = context
    if is_busy(space_name= space_name):
        return Response(status_code=status.HTTP_202_ACCEPTED)
    celery.send_task('describe',
        (
            space_name,
            body.url
        ),
        queue= 'develop' if is_dev else 'celery'
    ) 
    return {
        'status': 'ok',
    }


@router.get("/spaces/{space_name}/status")
def get_space_status( context: tuple  = Depends(space_context),):
    space_name, _ , _  = context
    status, jobs,  describe  = get_space_jobs(space_name=space_name)
    return {
        'status': status,
        'jobs': jobs,
        'describing': describe
    }


@router.get("/spaces/{space_name}/detail")
async def get_space_detail(
    before: datetime = None,
    after: datetime = None,    
    context: tuple  = Depends(space_context),
    pagination = Depends(validate_pagination)
):
    _, space_id , _  = context
    detail = data.get_detail(
        space_id=space_id, 
        page= pagination['page'] , 
        page_size= pagination['size'] ,
        before = before,
        after= after
    )
    return detail


@router.post("/upscale/{id}")
async def upscale( 
    body: UpscaleBody,
    context: dict = Depends(
        ImageContext(
            allowed_types =[
                DetailType.OUTPUT_MJ_IMAGINE,
                DetailType.OUTPUT_MJ_REMIX,
                DetailType.OUTPUT_MJ_VARIATION,
                DetailType.OUTPUT_MJ_VARY,
                DetailType.OUTPUT_MJ_PAN,
                DetailType.OUTPUT_MJ_ZOOM
            ]
        )
    )
):
    detail = context.get('detail',{})
    if is_busy(space_name= detail.get("space_name")):
        return Response(status_code=status.HTTP_202_ACCEPTED)
    worker_id = Snowflake.parse_snowflake_worker_id(snowflake_id = context.get('id'))
    broker_id , _ = Snowflake.parse_worker_id(worker_id = worker_id)
    celery.send_task('upscale',
        (
            {
                **detail,
                'ref_id': context.get('id'),
                'worker_id': worker_id
            },
            body.index,
        ),
        queue= f"queue_{broker_id}"
    )
    return {
        'status': 'ok'
    }

@router.post("/variation/{id}")
async def upscale( 
    body: VariationBody,
    context: dict = Depends(
        ImageContext(
            allowed_types =[
                DetailType.OUTPUT_MJ_IMAGINE,
                DetailType.OUTPUT_MJ_REMIX,
                DetailType.OUTPUT_MJ_VARIATION,
                DetailType.OUTPUT_MJ_VARY,
                DetailType.OUTPUT_MJ_PAN,
                DetailType.OUTPUT_MJ_ZOOM
            ]
        )
    )
):
    
    detail = context.get('detail',{})
    if is_busy(space_name= detail.get("space_name")):
        return Response(status_code=status.HTTP_202_ACCEPTED)
    worker_id = Snowflake.parse_snowflake_worker_id(snowflake_id = context.get('id'))
    broker_id , _ = Snowflake.parse_worker_id(worker_id = worker_id)
    celery.send_task('variation',
        (
            body.prompt,
            {
                **detail,
                'ref_id': context.get('id'),
                'worker_id': worker_id
            },
            body.index,
        ),
        queue= f"queue_{broker_id}"
    )
    return {
        'status': 'ok'
    }



@router.post("/vary/{id}")
async def vary(
    body: VaryBody,
    context: dict = Depends(
        ImageContext(
            allowed_types =[
                DetailType.OUTPUT_MJ_UPSCALE
            ]
        )
    )
):
    detail = context.get('detail',{})
    if is_busy(space_name= detail.get("space_name")):
        return Response(status_code=status.HTTP_202_ACCEPTED)
    worker_id = Snowflake.parse_snowflake_worker_id(snowflake_id = context.get('id'))
    broker_id , _ = Snowflake.parse_worker_id(worker_id = worker_id)

    celery.send_task('vary',
        (
            body.prompt,
            {
                **detail,
                'ref_id': context.get('id'),
                'worker_id': worker_id
            },
            body.type
        ),
        queue= f"queue_{broker_id}"
    )

    return {
        'status': 'ok'
    }
@router.post("/zoom/{id}")
async def zoom(
    body: ZoomBody,
    context: dict = Depends(
        ImageContext(
            allowed_types =[
                DetailType.OUTPUT_MJ_UPSCALE
            ]
        )
    )
):
    detail = context.get('detail',{})
    if is_busy(space_name= detail.get("space_name")):
        return Response(status_code=status.HTTP_202_ACCEPTED)    
    zoom = body.zoom
    prompt = body.prompt
    if (zoom < 1 or zoom > 2):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    if prompt is None and zoom not in [1.5, 2]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST)
    
    
    worker_id = Snowflake.parse_snowflake_worker_id(snowflake_id = context.get('id'))
    broker_id , _ = Snowflake.parse_worker_id(worker_id = worker_id)

    celery.send_task('zoom',
        (
            prompt,
            zoom,
            {
                **detail,
                'ref_id': context.get('id'),
                'worker_id': worker_id
            }
        ),
        queue= f"queue_{broker_id}"
    )

    return {
        'status': 'ok'
    }



@router.post("/pan/{id}")
async def pan(
    body: PanBody,
    context: dict = Depends(
        ImageContext(          
            allowed_types =[
                DetailType.OUTPUT_MJ_UPSCALE
            ]
        )
    )
):
    detail = context.get('detail',{})
    if is_busy(space_name= detail.get("space_name")):
        return Response(status_code=status.HTTP_202_ACCEPTED)    
    worker_id = Snowflake.parse_snowflake_worker_id(snowflake_id = context.get('id'))
    broker_id , _ = Snowflake.parse_worker_id(worker_id = worker_id)
    celery.send_task('pan',
        (
            body.prompt,
            body.type,
            {
                **detail,
                'ref_id': context.get('id'),
                'worker_id': worker_id
            }
        ),
        queue= f"queue_{broker_id}"
    )

    return {
        'status': 'ok'
    }


@router.post("/square/{id}")
async def square():
    pass


@router.get("/profile")
async def get_profile(context: tuple = Depends(token_context)):
    _, token_id, info = context
    cost = data.redis_get_cost(token_id= token_id)

    del info["id"]
    return {
        **info,
        "cost": int(cost),
        "withhold": 0
    }

@router.post("/sign")
async def get_sign( context: tuple = Depends(token_context)):
    _, token_id, _ = context
    path = calculate_md5(f'aipic.{token_id}')
    full_url = f'upload/{path}/{random_id(10)}.jpg'
    sign = data.file_generate_presigned_url(full_url)  
    return   {
        'sign': sign,
        'url': f'{image_hostname}/{full_url}'
    }

app.include_router(router)
