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