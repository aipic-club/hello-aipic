from pydantic import BaseModel

class AdminBase(BaseModel):
    username: str

class CreateAdmin(AdminBase):
    hashed_password: str

class UserBase(BaseModel):
    username: str

class CreateUser(UserBase):
    pass

class TokenBase(BaseModel):
    access_token: str
    token_type: str

class AdminToken(TokenBase):
    pass

class UserToken(TokenBase):
    expire_at: int
    ramaining: int
    scopes: list[str] = []
    pass

class CreatePrompt(BaseModel):
    prompt: str

