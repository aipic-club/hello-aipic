from enum import Enum


class TaskStatus(Enum):
    
    ABORTED = 0 # 经过 server 的初筛，认为包含不合适的内容，不会向MJ 发送
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
    ## MIDJOURNEY INPUT 
    INPUT_MJ_PROMPT = 11
    INPUT_MJ_VARIATION = 12
    INPUT_MJ_REMIX = 13
    INPUT_MJ_UPSCALE = 14
    INPUT_MJ_REROLL = 11
    ## MIDJOURNEY OUTPUT 
    OUTPUT_MJ_PROMPT = 11
    OUTPUT_MJ_VARIATION = 22
    OUTPUT_MJ_REMIX = 23
    OUTPUT_MJ_UPSCALE = 24
    OUTPUT_MJ_DESCRIBE = 24


    

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
    
class SysError(Enum):
    FATAL = 0
    TOKEN_NOT_EXIST_OR_EXPIRED = 1


config = {
    'wait_time': 60 * 10,  # 10 minutes
    'cache_time': 6 * 60 * 60  # half day
}
    
image_hostname = 'https://imgcdn.aipic.club'