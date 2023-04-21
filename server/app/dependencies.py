import os
from datetime import datetime

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, SecurityScopes

from jose import jwt, JWTError
from passlib.context import CryptContext
from pydantic import ValidationError

from . import models, schemas, database, crud

models.Base.metadata.create_all(bind=database.engine)

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_admin(
    db: crud.Session,
    username: str, password: str
):
    admin = schemas.CreateAdmin(
        username=username, 
        hashed_password=get_hashed_password(password)
    )
    return crud.create_admin(db, admin=admin)

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"])

db_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/admin/create",
    scopes={ "database": "read & write database" }
)

users_oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/admin/user/create",
    scopes={ "users": "read & write users" }
)

def create_access_token(data: dict):
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)

def get_hashed_password(password):
    return pwd_context.hash(password)

def authenticate_admin(
    db: crud.Session,
    username: str, password: str
):
    admin = crud.get_admin(db, username=username)
    if not admin:
        return False
    if not pwd_context.verify(password, admin.hashed_password):
        return False
    return admin

async def check_admin_token(
    security_scopes: SecurityScopes,
    access_token: str = Depends(db_oauth2_scheme),
    db: crud.Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"Authorization": "Bearer"}
    )
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes")
        expire = payload.get("exp")
    except (JWTError, ValidationError):
        raise credentials_exception
    admin = crud.get_admin(db, username=username)
    if admin is None:
        raise credentials_exception

    utcnow = datetime.utcnow()
    expire_at = datetime.fromtimestamp(expire)

    print("compare---->", utcnow, expire_at, expire)

    if utcnow >= expire_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credentials expired",
            headers={"Authorization": "Bearer"}
        )
    for scope in security_scopes.scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No permissions",
                headers={"Authorization": "Bearer"}
            )
    return admin  

async def check_user_token(
    access_token: str = Depends(users_oauth2_scheme),
    db: crud.Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"Authorization": "Bearer"}
    )
    try:
        payload = jwt.decode(access_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_scopes = payload.get("scopes")
    except (JWTError, ValidationError):
        raise credentials_exception
    user = crud.get_user(db, username=username)
    if user is None:
        raise credentials_exception

    utcnow = datetime.utcnow()
    db_expire_at = user.token.expire_at

    if utcnow >= db_expire_at:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credentials expired",
            headers={"Authorization": "Bearer"}
        )
    db_scopes = user.token.scopes.split(",")
    for scope in db_scopes:
        if scope not in token_scopes:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No permissions",
                headers={"Authorization": "Bearer"}
            )
    return user
