import redis, hashlib
from src.core.config import settings

class RedisMemory:
    def __init__(self):
        self.client = redis.from_url(settings.REDIS_URL)

    def get_cache(self, query: str):
        res = self.client.get(hashlib.md5(query.encode()).hexdigest())
        return res.decode() if res else None

    def set_cache(self, query: str, response: str):
        self.client.setex(hashlib.md5(query.encode()).hexdigest(), 3600, response)