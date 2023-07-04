
from enum import Enum


class MJ_VARY_TYPE(str, Enum):
    STRONG = 'strong'
    SUBTLE = 'subtle'
    # LOW_VARIATION = 'low_variation'
    # HIGH_VARIATION = 'high_variation'

class MJ_PAN_TYPE(str, Enum):
    LEFT = 'left'
    RIGHT = 'right'
    UP = 'up'
    DOWN = 'down'


def get_vary_type(type: MJ_VARY_TYPE) -> int:
    #low_variation , subtle
    if type is MJ_VARY_TYPE.SUBTLE:
        return 0
    #high_variation, strong
    if type is MJ_VARY_TYPE.STRONG:
        return 1
    return None
    

class MJ_OUTPAINT_VALUE(int, Enum):
    ZOOMOUT2X = 50
    ZOOMOUT1_5X =  75