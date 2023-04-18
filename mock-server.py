import os
import random
import string
from pydantic import BaseModel
from fastapi import FastAPI
from fastapi import BackgroundTasks
from celery import Celery
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

celery = Celery('tasks', broker=os.environ.get("CELERY.BROKER"))


app = FastAPI()


def random_id(length = 6) -> str:
    all = string.ascii_letters + string.digits
    # all = string.ascii_letters + string.digits + string.punctuation
    return "".join(random.sample(all,length))

class Prompt(BaseModel):
    prompt: str



@app.get("/")
def read_root():
    return {"Hello": "World"}




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
    res = celery.send_task('send_prompt',
        (
            taskId,
            prompt
        )
    )
    print(res)         
    return item





if __name__ == "__main__":
    pass