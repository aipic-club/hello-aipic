from enum import Enum

class TaskStatus(Enum):
    ABORTED = 0
    PENDING = 1
    COMMITTED = 2
    FINISHED = 3

class OutputType(Enum):
    GRID = 1
    UPSCALE = 2
    VARIATION = 3
