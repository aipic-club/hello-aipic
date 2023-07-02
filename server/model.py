from pydantic import BaseModel
from typing import Annotated, Callable, Optional, Union


class Prompt(BaseModel):
    prompt: str
    raw: Union[str , None] = None
    execute: Union[bool , None] = None

class Space(BaseModel):
    name: str | None

class Describe(BaseModel):
    url: str
    
class Vary(BaseModel):
    type:  str

class Zoom(BaseModel):
    type: int
