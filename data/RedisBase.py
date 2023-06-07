from abc import abstractmethod

class RedisInterface:
    @abstractmethod
    def __init__(self) -> None:
        pass

class RedisBase(RedisInterface):
    def __init__(self) -> None:
        pass