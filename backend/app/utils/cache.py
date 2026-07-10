"""
Simple in-memory cache for LLM responses.
Keyed by (file_hash, language) — avoids re-analyzing identical documents.
No Redis required.
"""
import hashlib
import time
from typing import Any


class InMemoryCache:
    def __init__(self, default_ttl: int = 604800):  # 7 days default
        self._store: dict[str, tuple[Any, float]] = {}
        self.default_ttl = default_ttl

    def _is_expired(self, expires_at: float) -> bool:
        return time.time() > expires_at

    def get(self, key: str) -> Any | None:
        if key not in self._store:
            return None
        value, expires_at = self._store[key]
        if self._is_expired(expires_at):
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        expires_at = time.time() + (ttl or self.default_ttl)
        self._store[key] = (value, expires_at)

    def delete(self, key: str) -> None:
        self._store.pop(key, None)

    def clear_expired(self) -> None:
        now = time.time()
        expired = [k for k, (_, exp) in self._store.items() if now > exp]
        for k in expired:
            del self._store[k]

    def make_key(self, *parts: str) -> str:
        combined = ":".join(parts)
        return hashlib.md5(combined.encode()).hexdigest()


# Cache version — bump this to invalidate all cached results after prompt changes
CACHE_VERSION = "v3"

# Module-level singleton instances
analysis_cache = InMemoryCache(default_ttl=604800)   # 7 days for analysis
suggestions_cache = InMemoryCache(default_ttl=604800)  # 7 days for suggestions
classification_cache = InMemoryCache(default_ttl=86400)  # 24h for classification


def hash_file(file_bytes: bytes) -> str:
    """MD5 hash of file content for cache keying."""
    return hashlib.md5(file_bytes).hexdigest()
