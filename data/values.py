from enum import Enum


class TaskStatus(Enum):
    
    ABORTED = -1 # 经过 server 的初筛，认为包含不合适的内容，不会向MJ 发送
    ACCEPTED = 0 #
    CREATED = 1 # 已创建
    CONFIRMED = 2 # 向MJ 发送
    COMMITTED = 3 # 已经送达至MJ 
    FINISHED = 4 # MJ 已经成功返回图像
    FAILED = 5 # 一定时间内没有收到 MJ 的响应， 标记为失败


class OutputType(Enum):
    DRAFT = 1
    VARIATION = 2
    UPSCALE = 3
    REMIX = 4


class DetailType(Enum):
    ## SYSTEM MESSAGE
    SYS_ABORTED = 0
    SYS_WELCOME = 1
    SYS_FAILED = 5
    ## MIDJOURNEY INPUT 
    INPUT_MJ_IMAGINE = 11
    INPUT_MJ_VARIATION = 12
    INPUT_MJ_REMIX = 13
    INPUT_MJ_UPSCALE = 14
    INPUT_MJ_REROLL = 15
    INPUT_MJ_VARY = 16
    INPUT_MJ_ZOOM = 17
    ## MIDJOURNEY OUTPUT 
    OUTPUT_MJ_IMAGINE = 21
    OUTPUT_MJ_VARIATION = 22
    OUTPUT_MJ_REMIX = 23
    OUTPUT_MJ_UPSCALE = 24
    OUTPUT_MJ_DESCRIBE = 25
    OUTPUT_MJ_VARY = 28
    OUTPUT_MJ_ZOOM = 27
    ## MIDJOURNEY ERROR
    OUTPUT_MJ_TIMEOUT = 31
    OUTPUT_MJ_INVALID_PARAMETER = 32

mj_output_type = [
    DetailType.OUTPUT_MJ_IMAGINE.value,
    DetailType.OUTPUT_MJ_REMIX.value,
    DetailType.OUTPUT_MJ_UPSCALE.value,
    DetailType.OUTPUT_MJ_VARIATION.value,
    DetailType.OUTPUT_MJ_DESCRIBE.value,
    DetailType.OUTPUT_MJ_VARY.value,
    DetailType.OUTPUT_MJ_ZOOM.value
]

error_mj_output_type = [
    DetailType.OUTPUT_MJ_TIMEOUT,
    DetailType.OUTPUT_MJ_INVALID_PARAMETER
]



def get_cost(type: DetailType):
    if type is DetailType.OUTPUT_MJ_IMAGINE:
        return 4
    elif type is DetailType.OUTPUT_MJ_REMIX:
        return 4    
    elif type is DetailType.OUTPUT_MJ_UPSCALE:
        return 4       
    elif type is DetailType.OUTPUT_MJ_VARIATION:
        return 4        
    elif type is DetailType.OUTPUT_MJ_DESCRIBE:
        return 4        
    else:
        return 4

    

class ImageOperationType(Enum):
    VARIATION = 0
    UPSCALE = 1
    REROLL = 2
    DESCRIBE = 3

class Cost(Enum):
    DRAFT = 4
    VARIATION = 4
    UPSCALE = 4
    REMIX = 4
    VARY = 4
    ZOOM = 4
    @staticmethod
    def get_cost(output: OutputType):
        if output == OutputType.DRAFT.value:
            return Cost.DRAFT.value
        elif output == OutputType.VARIATION.value:
            return Cost.VARIATION.value
        elif output == OutputType.UPSCALE.value:
            return Cost.UPSCALE.value 
        elif output == OutputType.REMIX.value:
            return Cost.REMIX.value    
        else:
            return 0
    
class SysCode(Enum):
    OK = 0
    MAINTENACNCE = 1
    FATAL = 2
    TOKEN_NOT_EXIST_OR_EXPIRED = 11
    TOKEN_OUT_OF_BALANCE = 12


class TokenType(Enum):
    VIP = 0
    TRIAL = 1
    NORMAL = 2
    DEMO = 3


config = {
    'wait_time': 60 * 10,  # 10 minutes
    'cache_time': 24 * 60 * 60,  # one day
    'interaction_ttl': 60
}
    
image_hostname = 'https://imgcdn.aipic.club'