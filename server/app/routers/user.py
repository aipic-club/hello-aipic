from fastapi import Depends, APIRouter
from fastapi.security import OAuth2PasswordBearer

from .. import schemas
from ..dependencies import (
    check_user_token
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

router = APIRouter(
    prefix="/api/v1/user",
    tags=["users"],
    dependencies=[Depends(check_user_token)],
    responses={404: {"description": "Not found"}}
)

@router.get("/profile")
async def profile(profile = Depends(check_user_token)):
    return profile

