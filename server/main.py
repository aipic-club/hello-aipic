import os
from typing import Annotated
from datetime import datetime, timedelta

from dotenv import find_dotenv, load_dotenv
load_dotenv(find_dotenv(".env"))

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.dependencies import (
    get_db, create_admin, 
    authenticate_admin, create_access_token
)

from app import schemas, crud

from app.routers import admin
from app.routers import user

app = FastAPI()

app.include_router(admin.router)
app.include_router(user.router)

@app.get("/api/")
def index():
    return "Hello World!"

@app.get("/api/admin")
def admin(db: crud.Session = Depends(get_db)):
    return create_admin(db, username="admin", password="admin")

@app.post("/api/admin/login", response_model=schemas.AdminToken)
async def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: crud.Session = Depends(get_db)
):
    admin = authenticate_admin(db, form.username, form.password)
    if not admin:
        raise HTTPException(status_code=400, detail="Username or password not correct.")
    ACCESS_TOKEN_EXPIRE_MINUTES = os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"]
    exp = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={ "sub": form.username, "scopes": form.scopes, "exp": exp }
    )
    return { "access_token": access_token, "token_type": "bearer" }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", port=8000, log_level="info")
