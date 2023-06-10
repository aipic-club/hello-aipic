from abc import abstractmethod
import redis
import json
from .values import ImageOperationType, config, TaskStatus,DetailType

class RedisInterface:
    @abstractmethod
    def __init__(self, url: str) -> None:
        pass
    def test(slef):
        pass

class RedisBase(RedisInterface):
    def __init__(self, url: str) -> None:
        self.redis = redis.from_url(url)
    def __remove_keys(self, pattern: str):
        keys = self.redis.keys(pattern)
        self.redis.delete(*keys)
    def redis_close(self):
        self.redis.close()

    def redis_set_cache_data(self, key, value):
        self.redis.setex(key, config['cache_time'], value)
    def redis_get_cache_data(self, key):
        return self.redis.get(key)
    def redis_get_token(self, token: str):
        val = self.redis.get(f'token:{token}')
        return int(val) if val is not None else None
    def redis_set_token(self, token: str, ttl: int, id: int):
        self.redis.setex(f'token:{token}', ttl, id )
    def redis_set_task(self, taskId: str, worker_id: int | None):
        self.redis.setex(f'task:{taskId}', config['cache_time'], worker_id)
    def redis_get_task(self, taskId: str,):
        temp = self.redis.get(f'task:{taskId}')
        if temp is not None:
            return int(temp)
        return None
    def redis_task(self, token_id: int, taskId: str, status: TaskStatus, ttl: int = None) -> None:
        key = f'task:{token_id}:{taskId}'
        if token_id is None:
            keys = self.redis.keys(f'task:*:{taskId}')
            if len(keys) != 1:
                return
            key = keys[0]
        if ttl is not None:
            _ttl = ttl
        else:
            _ttl = self.redis.ttl(key) if  self.redis.exists(key) else config['wait_time'] 
        if _ttl > 0:
            self.redis.setex(key, _ttl , status.value )
    def redis_task_status(self, token_id, taskId: str) -> int | None:
        key = f'task:{token_id}:{taskId}' 
        val = self.redis.get(key)
        return int(val) if val else None
    def redis_task_cleanup(self, taskId):
        self.__remove_keys(f'task:*:{taskId}')
        
    # def redis_image(self,  taskId: str, imageHash: str, type: ImageOperationType, index: str):
    #     self.redis.setex(f'image:{taskId}:{imageHash}', config['wait_time'] ,  f'{imageHash}.{type.name}.{index}')

    def redis_task_job(self,  taskId: str, id: int, type: DetailType, index: int):
        self.redis.setex(f'job:{taskId}:{id}', config['wait_time'] ,  f'{id}.{type.name}.{index}')
    def redis_task_job_status(self,  taskId: str) -> list:
        keys = self.redis.keys(f'job:{taskId}:*')
        return self.redis.mget(keys)
    def redis_task_job_remove(self,  taskId: str, id: int) -> list:
        self.__remove_keys(f'job:{taskId}:{id}' )
    def redis_task_job_cleanup(self,  taskId: str,):
        self.__remove_keys(f'job:{taskId}:*' )

    # def redis_image_status(self, taskId) -> list:
    #     keys = self.redis.keys(f'image:{taskId}:*')
    #     return self.redis.mget(keys)
    # def redis_image_cleanup(self, taskId: str, imageHash: str, ):
    #     self.__remove_keys(f'image:{taskId}:{imageHash}' )

    def redis_broker(self, broker_id: int, worker_id: int, taskId: int):
        self.redis.setex(f'broker:{broker_id}:{worker_id}:{taskId}', config['wait_time']  , '')
    def redis_broker_cleanup(self, taskId):
        self.__remove_keys(f'broker:*:*:{taskId}')

    def redis_set_interaction(self, key: str | int, value: str | int  ) -> bool:
        return self.redis.setex(f'interaction:{key}', config['wait_time'] ,  value)
    def redis_get_interaction(self, key)-> int | None:
        value = self.redis.get(f'interaction:{key}')
        return int(value) if value is not None else None
