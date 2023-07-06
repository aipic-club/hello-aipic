from pydantic import BaseModel
from typing import Annotated, Callable, Optional, Union
from data.values import MJ_VARY_TYPE, MJ_PAN_TYPE


class ImagineBody(BaseModel):
    prompt: str
    raw: Union[str , None] = None
    execute: Union[bool , None] = None

class RenameSpaceBody(BaseModel):
    name: str | None

class DescribeBody(BaseModel):
    url: str

class UpscaleBody(BaseModel):
    index: int   

class VariationBody(BaseModel):
    index: int    
    prompt: str

class VaryBody(BaseModel):
    type: MJ_VARY_TYPE
    prompt: str


class ZoomBody(BaseModel):
    zoom: float
    prompt: str = None

class PanBody(BaseModel):
    type: MJ_PAN_TYPE
    prompt: str
