"""
Unit tests for cache utilities.
"""
import pytest
import time
from app.utils.cache import InMemoryCache, hash_file


class TestInMemoryCache:
    def test_set_and_get(self):
        cache = InMemoryCache(default_ttl=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_nonexistent(self):
        cache = InMemoryCache()
        assert cache.get("nonexistent") is None

    def test_ttl_expiration(self):
        cache = InMemoryCache(default_ttl=1)  # 1 second TTL
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_custom_ttl(self):
        cache = InMemoryCache(default_ttl=60)
        cache.set("key1", "value1", ttl=1)  # Custom 1 second TTL
        assert cache.get("key1") == "value1"
        time.sleep(1.1)
        assert cache.get("key1") is None

    def test_delete(self):
        cache = InMemoryCache()
        cache.set("key1", "value1")
        cache.delete("key1")
        assert cache.get("key1") is None

    def test_make_key(self):
        cache = InMemoryCache()
        key = cache.make_key("part1", "part2", "part3")
        expected = "part1:part2:part3"
        # Should be MD5 hash
        import hashlib
        assert key == hashlib.md5(expected.encode()).hexdigest()

    def test_clear_expired(self):
        cache = InMemoryCache(default_ttl=1)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        time.sleep(1.1)
        cache.clear_expired()
        assert cache.get("key1") is None
        assert cache.get("key2") is None


class TestHashFile:
    def test_same_content_same_hash(self):
        data = b"test content"
        hash1 = hash_file(data)
        hash2 = hash_file(data)
        assert hash1 == hash2

    def test_different_content_different_hash(self):
        hash1 = hash_file(b"content1")
        hash2 = hash_file(b"content2")
        assert hash1 != hash2

    def test_empty_bytes(self):
        hash_val = hash_file(b"")
        import hashlib
        assert hash_val == hashlib.md5(b"").hexdigest()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])