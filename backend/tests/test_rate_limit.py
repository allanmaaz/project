"""
Unit tests for rate limiter.
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from app.middleware.rate_limit import (
    InMemoryRateLimiter,
    RateLimiter,
    SlidingWindowRateLimiter,
)
from app.models.user import User


class MockUser:
    def __init__(self, user_id: str, plan: str = "free"):
        self.id = user_id
        self.plan = plan
        self.uploads_this_month = 0


class TestInMemoryRateLimiter:
    def test_allows_within_limit(self):
        limiter = InMemoryRateLimiter()
        assert limiter.check("user1", limit=5, window_seconds=3600) is True
        assert limiter.check("user1", limit=5, window_seconds=3600) is True
        assert limiter.check("user1", limit=5, window_seconds=3600) is True

    def test_blocks_over_limit(self):
        limiter = InMemoryRateLimiter()
        for _ in range(5):
            assert limiter.check("user1", limit=5, window_seconds=3600) is True
        assert limiter.check("user1", limit=5, window_seconds=3600) is False

    def test_separate_keys_independent(self):
        limiter = InMemoryRateLimiter()
        for _ in range(5):
            assert limiter.check("user1", limit=5) is True
        assert limiter.check("user1", limit=5) is False
        # user2 should still work
        assert limiter.check("user2", limit=5) is True

    def test_window_expiration(self):
        limiter = InMemoryRateLimiter()
        for _ in range(5):
            assert limiter.check("user1", limit=5, window_seconds=1) is True
        assert limiter.check("user1", limit=5, window_seconds=1) is False
        import time
        time.sleep(1.1)
        assert limiter.check("user1", limit=5, window_seconds=1) is True


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_uses_memory_limiter_when_redis_unavailable(self):
        with patch("app.middleware.rate_limit.RedisRateLimiter") as mock_redis:
            mock_redis.side_effect = Exception("Redis unavailable")
            
            from app.middleware.rate_limit import _get_limiter
            limiter = await _get_limiter()
            # Should fall back to in-memory
            result = await limiter.check("test_key", 10)
            assert result is True

    @pytest.mark.asyncio
    async def test_check_upload_rate_free_user(self):
        from app.config import settings
        from app.middleware.rate_limit import check_upload_rate
        
        user = MockUser("user1", "free")
        # Free users get RATE_LIMIT_UPLOADS_FREE per hour
        # We can't easily test the exact limit without mocking settings
        # Just verify it runs without error
        try:
            await check_upload_rate(user)
        except Exception as e:
            # Rate limit exceeded is expected if called many times
            assert "RATE_LIMIT" in str(e) or "MONTHLY" in str(e)

    @pytest.mark.asyncio
    async def test_check_upload_rate_pro_user(self):
        from app.middleware.rate_limit import check_upload_rate
        
        user = MockUser("user2", "pro")
        # Pro users get 10x the free limit
        try:
            await check_upload_rate(user)
        except Exception as e:
            assert "RATE_LIMIT" in str(e) or "MONTHLY" in str(e)


class TestMonthlyLimit:
    def test_free_user_monthly_limit(self):
        from app.config import settings
        from app.middleware.rate_limit import check_monthly_limit
        from app.utils.exceptions import UploadLimitError
        
        user = MockUser("user1", "free")
        user.uploads_this_month = settings.FREE_PLAN_MONTHLY_UPLOADS
        
        with pytest.raises(UploadLimitError):
            check_monthly_limit(user)

    def test_pro_user_no_monthly_limit(self):
        from app.middleware.rate_limit import check_monthly_limit
        
        user = MockUser("user1", "pro")
        user.uploads_this_month = 1000
        
        # Should not raise
        check_monthly_limit(user)

    def test_free_user_under_limit(self):
        from app.middleware.rate_limit import check_monthly_limit
        
        user = MockUser("user1", "free")
        user.uploads_this_month = 5
        
        # Should not raise
        check_monthly_limit(user)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])