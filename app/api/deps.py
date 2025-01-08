from aioredis import Redis
from app.core.config import settings


def get_redis() -> Redis:
    """
    Description:
        This function is a dependency for FastAPI routes. It provides an instance of Redis client.
        The Redis client is used to interact with the Redis database for caching purposes.
    Args: None
    Returns:
        Redis: An instance of the Redis client.
    Author:
        dev09@allyai.ai
    """
    return Redis.from_url(settings.REDIS_URL,  decode_responses=True)