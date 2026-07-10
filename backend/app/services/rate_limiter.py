"""
Redis-backed sliding window rate limiter for production use.
"""
import time
import redis.asyncio as redis
from typing import Optional
from app.config import settings


class RedisRateLimiter:
    """Redis-backed sliding window rate limiter."""
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
    
    async def _get_client(self) -> redis.Redis:
        if self._client is None:
            self._client = redis.from_url(settings.REDIS_URL, decode_responses=True)
        return self._client
    
    async def check(self, key: str, limit: int, window_seconds: int = 3600) -> bool:
        """
        Check if request is allowed under rate limit using sliding window.
        Returns True if allowed, False if limit exceeded.
        """
        client = await self._get_client()
        now = time.time()
        window_start = now - window_seconds
        
        # Use a sorted set with timestamps as scores
        pipe = client.pipeline()
        # Remove expired entries
        pipe.zremrangebyscore(key, 0, window_start)
        # Count current entries
        pipe.zcard(key)
        # Add current request
        pipe.zadd(key, {str(now): now})
        # Set expiry on key
        pipe.expire(key, window_seconds + 1)
        results = await pipe.execute()
        
        current_count = results[1]
        return current_count < limit
    
    async def close(self):
        if self._client:
            await self._client.close()
            self._client = None