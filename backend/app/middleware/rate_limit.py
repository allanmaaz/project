"""
Simple in-memory rate limiter (no Redis required).
Uses sliding window algorithm per user_id.
"""
import time
from collections import defaultdict, deque
from threading import Lock
from app.models.user import User
from app.utils.exceptions import RateLimitError, UploadLimitError
from app.config import settings


class SlidingWindowRateLimiter:
    def __init__(self):
        self._windows: dict[str, deque] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_seconds: int = 3600) -> bool:
        """
        Returns True if allowed, raises RateLimitError if limit exceeded.
        key: unique identifier (e.g., f"upload:{user_id}")
        """
        now = time.time()
        with self._lock:
            window = self._windows[key]
            # Remove timestamps outside the window
            while window and window[0] < now - window_seconds:
                window.popleft()
            if len(window) >= limit:
                return False
            window.append(now)
            return True


# Module-level singleton
_limiter = SlidingWindowRateLimiter()


def check_upload_rate(user: User) -> None:
    """Raise if user exceeds upload rate limit."""
    limit = (
        settings.RATE_LIMIT_UPLOADS_FREE
        if user.plan == "free"
        else settings.RATE_LIMIT_UPLOADS_FREE * 10
    )
    if not _limiter.check(f"upload:{user.id}", limit):
        raise RateLimitError(upgrade=(user.plan == "free"))


def check_monthly_limit(user: User) -> None:
    """Raise if free-tier user has hit their monthly upload limit."""
    if user.plan == "free" and user.uploads_this_month >= settings.FREE_PLAN_MONTHLY_UPLOADS:
        raise UploadLimitError(settings.FREE_PLAN_MONTHLY_UPLOADS)


def check_chat_rate(user: User) -> None:
    """Raise if user exceeds chat message rate limit."""
    limit = (
        settings.RATE_LIMIT_CHAT_FREE
        if user.plan == "free"
        else settings.RATE_LIMIT_CHAT_FREE * 4
    )
    if not _limiter.check(f"chat:{user.id}", limit):
        raise RateLimitError(upgrade=(user.plan == "free"))
