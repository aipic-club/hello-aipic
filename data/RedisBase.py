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
        if keys:
            self.redis.delete(*keys)
    def redis_close(self):
        self.redis.close()

    def redis_set_cache_data(self, key, value):
        self.redis.setex(key, config['cache_time'], value)
    def redis_get_cache_data(self, key):
        return self.redis.get(key)
    # def redis_get_token(self, token: str):
    #     val = self.redis.get(f'token:{token}')
    #     return int(val) if val is not None else None
    # def redis_set_token(self, token: str, ttl: int, id: int):
    #     self.redis.setex(f'token:{token}', ttl, id )

    # def redis_init_cost(self,  token_id: str, ttl: int , data: dict   ):
    #     self.redis.setex(f'tokenId:{token_id}', ttl, json.dumps(data))
    # def redis_add_cost(self, token_id: str, cost ):
    #     key = f'tokenId:{token_id}'
    #     current = self.redis_get_cost(token_id=token_id)
    #     if current is not None:
    #         data = {
    #             **current,
    #             'cost': current.get("cost") + cost, 
    #         }
    #         _ttl = self.redis.ttl(key)
    #         self.redis.setex(key , _ttl, json.dumps(data))

    # def redis_get_cost(self, token_id: str | None):
    #     if token_id is None:
    #         return None
    #     val = self.redis.get(f'tokenId:{token_id}')
    #     return json.loads(val) if val is not None else None
    ### 



    def redis_set_token(self, token: str, ttl: int, data: dict):
        self.redis.setex(f'token:{token}', ttl, json.dumps(data))

    def redis_get_token(self, token: str):
        val = self.redis.get(f'token:{token}')
        return json.loads(val) if val is not None else None


    """
        cost
    """
    def redis_init_cost(self, token_id: str, ttl: int, cost: int ):
        key = f'cost:{token_id}'
        self.redis.setex(key, ttl, cost)
    def redis_add_cost(self, token_id: str, cost: int ):
        key = f'cost:{token_id}'
        self.redis.incrby(key, cost)
    def redis_get_cost(self, token_id: str ):
        key = f'cost:{token_id}'
        return self.redis.get(key)


    
    def redis_set_onwer(self, worker_id: int, taskId: str):
        self.redis.setex(f'onwer:{taskId}:{worker_id}', config['wait_time'], str(worker_id))
    def redis_get_onwer(self, worker_id: int, taskId: str,):
        return self.redis.get(f'onwer:{taskId}:{worker_id}')
    

    


    def redis_set_owner(self, worker_id: int, space_name: str, type: DetailType):
        key = f'onwer:{space_name}:{type.value}'
        self.redis.setex(key, config['wait_time'], worker_id)

    def redis_is_onwer(self, worker_id: int, space_name: str, type: DetailType ):
        key = f'onwer:{space_name}:{type.value}'
        temp = self.redis.get(key)
        print(key)
        print(temp)
        return temp is not None and int(temp) == worker_id
    
    def redis_clear_onwer(self, space_name: str, type: DetailType):
        key = f'onwer:{space_name}:{type.value}'
        self.__remove_keys(key)

 


    def redis_space_prompt(self, space_name: str, status: TaskStatus, ttl: int = None) -> None:
        key = f'space:{space_name}:prompt'
        if ttl is not None:
            _ttl = ttl
        else:
            _ttl = self.redis.ttl(key) if  self.redis.exists(key) else config['wait_time'] 
        if _ttl > 0:
            self.redis.setex(key, _ttl , status.value )

    def redis_space_prompt_status(self, space_name: str) -> int | None:
        key = f'space:{space_name}:prompt'
        val = self.redis.get(key)
        return int(val) if val else None
    
    def redis_space_prompt_cleanup(self, space_name: str) -> int | None:
        self.__remove_keys(f'space:{space_name}:prompt') 


    def redis_add_job(self, space_name: str, id: int, data: dict):
        self.redis.setex(f'space:{space_name}:job:{id}', config['wait_time'] ,  json.dumps(data))
  
    def redis_ongoing_jobs(self,  space_name: str) -> list:
        keys = self.redis.keys(f'space:{space_name}:job:*')
        return self.redis.mget(keys)
    
    def redis_space_cleanup(self, space_name: str):
        self.__remove_keys(f'space:{space_name}:job:*')
        
    # def redis_image(self,  taskId: str, imageHash: str, type: ImageOperationType, index: str):
    #     self.redis.setex(f'image:{taskId}:{imageHash}', config['wait_time'] ,  f'{imageHash}.{type.name}.{index}')



    def redis_space_job(self, space_name: str,):
        key = f'space:{space_name}:job' 
        pass




    def redis_task_job(self,  taskId: str, id: int, type: DetailType, index: int):
        self.redis.setex(f'job:{taskId}:{id}', config['wait_time'] ,  f'{id}.{type.name}.{index}')
        
    def redis_task_job_status(self,  taskId: str) -> list:
        keys = self.redis.keys(f'job:{taskId}:*')
        return self.redis.mget(keys)
    def redis_task_job_remove(self,  taskId: str, id: int) -> list:
        self.__remove_keys(f'job:{taskId}:{id}' )
    def redis_task_job_cleanup(self,  taskId: str,):
        self.__remove_keys(f'job:{taskId}:*' )

    def redis_set_interaction(self, key: str | int, value: str | int  ) -> bool:
        return self.redis.setex(f'interaction:{key}', config['wait_time'] ,  value)
    def redis_get_interaction(self, key)-> int | None:
        value = self.redis.get(f'interaction:{key}')
        return int(value) if value is not None else None
    
    def redis_set_describe(self, worker_id: int, key: str, taskId: str, url: str) -> bool:
        data = {
            'taskId': taskId,
            'url': url
        }
        # print(json.dumps(data))
        return self.redis.setex(f'describe:{taskId}:{worker_id}:{key}', config['wait_time'] ,  json.dumps(data))
    def redis_get_describe(
            self,
            taskId: str = None,
            worker_id: int = None, 
            key: str = None
        ) -> dict| None:
        if taskId is None and worker_id is not None:
            keys = self.redis.keys(f'describe:*:{worker_id}:{key}')
        
        if taskId is not None and worker_id is None and key is None:
            keys = self.redis.keys(f'describe:{taskId}:*:*')
        if len(keys) != 1:
            return
        print(keys)
        data = self.redis.get(keys[0])
        return json.loads(data) if data is not None else None
    def redis_describe_cleanup(self, taskId = None, key = None):
        if taskId is not None:
            self.__remove_keys(f'describe:{taskId}:*:*' )
        if key is not None:
            self.__remove_keys(f'describe:*:*:{key}' )

