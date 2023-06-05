import os
import random
import string
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


from celery import Celery
from dotenv import load_dotenv, find_dotenv
from data import Data, TaskStatus, SysError, random_id
load_dotenv(find_dotenv())

celery = Celery('tasks', broker=os.environ.get("CELERY.BROKER"))



Token = os.environ.get("MP.Token")
EncodingAESKey = os.environ.get("MP.EncodingAESKey")
AppID = os.environ.get("MP.AppID")




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
    

async def get_token_id(authorization: str = Header(None)):
    if authorization is None:
        #return {"error": "Authorization header is missing"}
        raise HTTPException(401)
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        #return {"error": "Authorization header is invalid"}
        raise HTTPException(401)
    token = parts[1]
    temp = data.check_token_and_get_id(token= token)
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
        Depends(get_token_id)
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

class Upscale(BaseModel):
    index: int
class Remix(BaseModel):
    prompt: str
    index: int


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
            token = data.create_trial_token(msg.source)         
            reply = create_reply(token , msg)
       
    return Response(content=reply.render(), media_type="application/xml")

@router.get("/prompts")
async def list_prompts( token_id: int = Depends(get_token_id), pagination = Depends(validate_pagination)):
    records = data.get_prompts_by_token_id(token_id=token_id, page= pagination['page'] , page_size= pagination['size'])
    return records


@router.post("/prompts")
async def send_prompt(item: Prompt, token_id: int = Depends(get_token_id) ):
    taskId = random_id(11)
    prompt = item.prompt
    data.save_prompt(token_id= token_id, prompt=prompt, raw= item.raw, taskId= taskId)
    if item.execute:
         celery.send_task('prompt',
            (
                token_id,
                taskId,
                prompt
            ),
            task_id= taskId,
            # queue="queue_1"
        )
         
    return {
        'id':  taskId
    }

@router.get("/prompts/{taskId}")
async def send_prompt(taskId: str, token_id: int = Depends(get_token_id) ):

    imageStatus = data.image_task_status(taskId)
    if len(imageStatus) > 0:
        return  {
            'status': TaskStatus.FINISHED.value,
            'images': imageStatus
        }
    
    status = data.prompt_task_status(token_id, taskId)
    return {
        'status': int(status) if status else None,
        'images': []
    }

@router.get("/images/{taskId}")
async def prompt_detail(taskId: str, page: int = 1, size: int = 10, token_id: int = Depends(get_token_id)):
    if page < 1 or size < 10:
        raise HTTPException(500)
    records = data.get_tasks_by_taskId(token_id=token_id, taskId= taskId, page= page, page_size= size)
    return records      

@router.post("/images/{image_hash}/upscale")
async def upscale( item: Upscale, image_hash:str,token_id: int = Depends(get_token_id)):
    task = data.get_task_by_messageHash(token_id , image_hash)
    if task is None:
        raise HTTPException(404)    
    else:
        broker_id = data.get_broker_id(task['worker_id'])
        res = celery.send_task('upscale',
            (
                task,
                item.index
            ),
            queue= f"queue_{broker_id}"
        )
    return {}

@router.post("/images/{image_hash}/variation")
async def variation( item: Remix,  image_hash:str,  token_id: int = Depends(get_token_id)):
    task = data.get_task_by_messageHash(token_id , image_hash)
    if task is None:
        raise HTTPException(404)    
    else:
        broker_id = data.get_broker_id(task['worker_id'])
        print(broker_id)
        res = celery.send_task('variation',
            (
                item.prompt,
                task,
                item.index,
            ),
            queue= f"queue_{broker_id}"
        )
    return {}

@router.get("/profile")
async def get_profile(token_id: int = Depends(get_token_id)):
    count = data.sum_costs_by_tokenId(token_id)
    info =  data.get_token_info_by_id(token_id)
    return {
        'cost': count['cost'],
        'blance': info['blance'],
        'expire_at': info['expire_at']
    }

@router.post("/sign")
async def get_sign(content_type :str, token_id: int = Depends(get_token_id)):
    sign = data.fileHandler.generate_presigned_url(content_type, f'temp/{token_id}/{random_id(10)}.jpg')  
    return   {'sign': sign}


app.include_router(router)
