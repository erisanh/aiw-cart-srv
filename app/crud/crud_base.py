import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

from aioredis import Redis


class CRUDBase:
    """
    Base class for Redis CRUD operations.
    
    This class provides basic Redis operations like get, set, delete, etc.
    It can be inherited by other classes that need Redis functionality.
    
    Attributes:
        prefix (str): Prefix for Redis keys to keep them organized
        expire_time (int): Default expiration time in seconds
    
    Author:
        GitHub Copilot
    """

    def __init__(self, prefix: str, expire_time: int = 3600):
        """
        Initialize CRUDBase with prefix and expiration time.
        
        Args:
            prefix (str): Prefix for all Redis keys
            expire_time (int): Default expiration time in seconds (default: 3600)
            
        Author:
            dev09@allyai.ai
        """
        self.prefix = prefix
        self.expire_time = expire_time

    def _get_key(self, key: str) -> str:
        """
        Generate a prefixed Redis key.
        
        Args:
            key (str): Original key
            
        Returns:
            str: Prefixed key (e.g., "prefix:key")
            
        Author:
            dev09@allyai.ai
        """
        return f"{self.prefix}:{key}"

    async def get(self, redis: Redis, key: str) -> Optional[Any]:
        """
        Retrieve a value from Redis.
        
        Args:
            redis (Redis): Redis connection instance
            key (str): Key to retrieve
            
        Returns:
            Optional[Any]: Decoded value if exists, None otherwise
            
        Example:
            >>> value = await crud.get(redis, "user:123")
        """
        value = await redis.get(self._get_key(key))
        return json.loads(value) if value else None

    async def set(
        self, 
        redis: Redis, 
        key: str, 
        value: Any, 
        expire_time: Optional[int] = None
    ) -> bool:
        """
        Set a value in Redis with optional expiration.
        
        Args:
            redis (Redis): Redis connection instance
            key (str): Key to set
            value (Any): Value to store
            expire_time (Optional[int]): Custom expiration time in seconds
            
        Returns:
            bool: True if successful
            
        Example:
            >>> success = await crud.set(redis, "user:123", {"name": "John"})
        """
        serialized = json.dumps(value)
        expiry = expire_time if expire_time is not None else self.expire_time
        return await redis.set(self._get_key(key), serialized, ex=expiry)

    async def delete(self, redis: Redis, key: str) -> bool:
        """
        Delete a key from Redis.
        
        Args:
            redis (Redis): Redis connection instance
            key (str): Key to delete
            
        Returns:
            bool: True if key was deleted, False if key didn't exist
            
        Example:
            >>> deleted = await crud.delete(redis, "user:123")
        """
        return bool(await redis.delete(self._get_key(key)))

    async def exists(self, redis: Redis, key: str) -> bool:
        """
        Check if a key exists in Redis.
        
        Args:
            redis (Redis): Redis connection instance
            key (str): Key to check
            
        Returns:
            bool: True if key exists, False otherwise
            
        Example:
            >>> exists = await crud.exists(redis, "user:123")
        """
        return bool(await redis.exists(self._get_key(key)))

    async def expire(self, redis: Redis, key: str, seconds: int) -> bool:
        """
        Set expiration time for a key.
        
        Args:
            redis (Redis): Redis connection instance
            key (str): Key to set expiration for
            seconds (int): Expiration time in seconds
            
        Returns:
            bool: True if expiration was set, False otherwise
            
        Example:
            >>> success = await crud.expire(redis, "user:123", 3600)
        """
        return await redis.expire(self._get_key(key), seconds)

    async def ttl(self, redis: Redis, key: str) -> int:
        """
        Get remaining time to live for a key.
        
        Args:
            redis (Redis): Redis connection instance
            key (str): Key to check TTL
            
        Returns:
            int: Remaining time in seconds, -2 if key doesn't exist, -1 if no expiry
            
        Example:
            >>> remaining = await crud.ttl(redis, "user:123")
        """
        return await redis.ttl(self._get_key(key))

    async def incr(self, redis: Redis, key: str) -> int:
        """
        Increment a numeric value.
        
        Args:
            redis (Redis): Redis connection instance
            key (str): Key to increment
            
        Returns:
            int: New value after increment
            
        Example:
            >>> new_value = await crud.incr(redis, "counter")
        """
        return await redis.incr(self._get_key(key))

    async def hset(self, redis: Redis, key: str, mapping: Dict[str, Any]) -> int:
        """
        Set multiple hash fields.
        
        Args:
            redis (Redis): Redis connection instance
            key (str): Hash key
            mapping (Dict[str, Any]): Field-value mapping to set
            
        Returns:
            int: Number of fields that were added
            
        Example:
            >>> count = await crud.hset(redis, "user:123", {"name": "John", "age": 30})
        """
        return await redis.hset(self._get_key(key), mapping=mapping)

    async def hget(self, redis: Redis, key: str, field: str) -> Optional[str]:
        """
        Get value of a hash field.
        
        Args:
            redis (Redis): Redis connection instance
            key (str): Hash key
            field (str): Field to get
            
        Returns:
            Optional[str]: Field value if exists, None otherwise
            
        Example:
            >>> value = await crud.hget(redis, "user:123", "name")
        """
        return await redis.hget(self._get_key(key), field)