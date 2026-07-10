"""
Rate limiter with Redis backend (production) and in-memory fallback (development).
"""
import time
from collections import defaultdict, deque
from threading import Lock
from typing import Optional

from app.models.user import User
from app.utils.exceptions import RateLimitError, UploadLimitError
from app.config import settings


class InMemoryRateLimiter:
    """Fallback in-memory rate limiter for development without Redis."""
    
    def __init__(self):
        self._windows: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int = 3600) -> bool:
        now = time.time()
        with self._lock:
            window = self._windows[key]
            while window and window[0] < now - window_seconds:
                window.popleft()
            if len(window) >= limit:
                return False
            window.append(now)
            return True


class RateLimiter:
    """Unified rate limiter with Redis backend and in-memory fallback."""
    
    def __init__(self):
        self._redis_limiter: Optional["RedisRateLimiter"] = None
        self._memory_limiter = InMemoryRateLimiter()
        self._use_redis = settings.APP_ENV != "development"
    
    async def _get_redis_limiter(self) -> Optional["RedisRateLimiter"]:
        if self._redis_limiter is None and self._use_redis:
            try:
                from app.services.rate_limiter import RedisRateLimiter
                self._redis_limiter = RedisRateLimiter()
                # Test connection
                await self._redis_limiter._get_client()
            except Exception as e:
                print(f"WARNING: Redis unavailable, falling back to in-memory rate limiter: {e}")
                self._use_redis = False
                self._redis_limiter = None
        return self._redis_limiter
    
    async def check(self, key: str, limit: int, window_seconds: int = 3600) -> bool:
        """Check if request is allowed under rate limit."""
        redis_limiter = await self._get_redis_limiter()
        if redis_limiter:
            return await redis_limiter.check(key, limit, window_seconds)
        return self._memory_limiter.check(key, limit, window_seconds)


# Module-level singleton
_limiter = RateLimiter()


async def check_upload_rate(user: User) -> None:
    """Raise if user exceeds upload rate limit."""
    limit = (
        settings.RATE_LIMIT_UPLOADS_FREE
        if user.plan == "free"
        else settings.RATE_LIMIT_UPLOADS_FREE * 10
    )
    if not await _limiter.check(f"upload:{user.id}", limit):
        raise RateLimitError(upgrade=(user.plan == "free"))


def check_monthly_limit(user: User) -> None:
    """Raise if free-tier user has hit their monthly upload limit."""
    if user.plan == "free" and user.uploads_this_month >= settings.FREE_PLAN_MONTHLY_UPLOADS:
        raise UploadLimitError(settings.FREE_PLAN_MONTHLY_UPLOADS)


async def check_chat_rate(user: User) -> None:
    """Raise if user exceeds chat message rate limit."""
    limit = (
        settings.RATE_LIMIT_CHAT_FREE
        if user.plan == "free"
        else settings.RATE_LIMIT_CHAT_FREE * 4
    )
    if not await _limiter.check(f"chat:{user.id}", limit):
        raise RateLimitError(upgrade=(user.plan == "free"))