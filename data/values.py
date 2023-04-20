from enum import Enum

class TaskStatus(Enum):
    ABORTED = 0 
    CREATED = 1  # to db
    COMMITTED = 2 # to mj  
    FINISHED = 3 # 

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