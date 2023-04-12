import os
from typing import Union
from fastapi import FastAPI
from fastapi import BackgroundTasks
from celery import Celery
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

celery = Celery('tasks', broker=os.environ.get("CELERY.BROKER"))


app = FastAPI()


@app.get("/")
def read_root():
    return {"Hello": "World"}


@app.get("/items/{item_id}")
def read_item(item_id: int, q: Union[str, None] = None):
    res = celery.send_task('upload_img', ('https://images.unsplash.com/photo-1681181840771-92f4ab1fddbc?ixlib=rb-4.0.3&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1430&q=80',))
    print(res)
    return {"item_id": item_id, "q": q }

if __name__ == "__main__":
    pass