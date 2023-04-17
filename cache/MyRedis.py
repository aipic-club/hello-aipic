import redis.asyncio as redis
import json
from .status import TaskStatus


class MyRedis():
    def __init__(self, url) -> None:
        self.r = redis.from_url(url)
    async def addTask(self, taskId, prompt):
        return await self.r.setex(taskId, 3 * 60 , json.dumps({
            'prompt': prompt,
            'type': TaskStatus.PENDING
        }))
    async def commitTask(self, taskId):
        pass

