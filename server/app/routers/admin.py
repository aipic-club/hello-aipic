from typing import Annotated

from fastapi import Depends, APIRouter, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from sqlalchemy.orm import Session

from ..dependencies import (
    get_db, create_access_token,
    check_admin_token
)

from .. import crud, schemas

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(check_admin_token)],
    responses={404: {"description": "Not found"}}
)
    

@router.post("/user/create", response_model=schemas.UserToken)
async def create_user_with_token(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    expire_at: int, remaining: int, db: Session = Depends(get_db)
):
    user = crud.get_user(db, username=form.username)
    if user:
        raise HTTPException(status_code=400, detail="Username already created.")
    access_token = create_access_token(
        data={ "sub": form.username, "scopes": form.scopes }
    )
    user = schemas.CreateUser(username=form.username)
    token = schemas.UserToken(
        access_token=access_token, token_type="bearer", scopes=form.scopes, 
        expire_at=expire_at,ramaining=remaining
    )
    crud.create_user_with_token(db, user=user, token=token)
    return token
