from enum import Enum


class TaskStatus(Enum):
    
    ABORTED = 0 # 经过 server 的初筛，认为包含不合适的内容，不会向MJ 发送
    CREATED = 1 # 保存为草稿，但并不向MJ 发送
    CONFIRMED = 2 # 向MJ 发送
    COMMITTED = 3 # 已经送达至MJ 
    FINISHED = 4 # MJ 已经成功返回图像
    FAILED = 5 # 一定时间内没有收到 MJ 的响应， 标记为失败

class OutputType(Enum):
    DRAFT = 1
    VARIATION = 2
    UPSCALE = 3


class Cost(Enum):
    DRAFT = 4
    VARIATION = 4
    UPSCALE = 2
    @staticmethod
    def get_cost(output: OutputType):
        if output == OutputType.DRAFT.value:
            return Cost.DRAFT.value
        if output == OutputType.VARIATION.value:
            return Cost.VARIATION.value
        if output == OutputType.UPSCALE.value:
            return Cost.UPSCALE.value  
        return 0
    
class SysError(Enum):
    FATAL = 0
    TOKEN_NOT_EXIST = 1
    TOKEN_EXPIRED = 2


config = {
    'wait_time': 60 * 1
}
    
