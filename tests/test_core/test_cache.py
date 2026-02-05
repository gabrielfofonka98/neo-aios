"""Tests for cache module."""

import time
from pathlib import Path

import pytest

from aios.core.cache import Cache
from aios.core.cache import CacheEntry
from aios.core.cache import FileCache
from aios.core.cache import cached
from aios.core.cache import clear_default_cache
from aios.core.cache import get_default_cache


class TestCacheEntry:
    """Tests for CacheEntry dataclass."""

    def test_entry_not_expired_when_no_expiration(self) -> None:
        """Entry without expires_at should never expire."""
        entry: CacheEntry[str] = CacheEntry(value="test")
        assert not entry.is_expired()

    def test_entry_not_expired_before_time(self) -> None:
        """Entry should not be expired before expires_at."""
        entry: CacheEntry[str] = CacheEntry(
            value="test",
            expires_at=time.time() + 100,
        )
        assert not entry.is_expired()

    def test_entry_expired_after_time(self) -> None:
        """Entry should be expired after expires_at."""
        entry: CacheEntry[str] = CacheEntry(
            value="test",
            expires_at=time.time() - 1,  # Already expired
        )
        assert entry.is_expired()

    def test_entry_tracks_hits(self) -> None:
        """Entry should track access hits."""
        entry: CacheEntry[int] = CacheEntry(value=42)
        assert entry.hits == 0
        entry.hits += 1
        assert entry.hits == 1


class TestCache:
    """Tests for Cache class."""

    def test_basic_get_set(self) -> None:
        """Test basic get/set operations."""
        cache: Cache[str] = Cache()
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_get_returns_default_for_missing_key(self) -> None:
        """Get should return default for missing key."""
        cache: Cache[str] = Cache()
        assert cache.get("missing") is None
        assert cache.get("missing", "default") == "default"

    def test_delete_removes_entry(self) -> None:
        """Delete should remove entry and return True."""
        cache: Cache[str] = Cache()
        cache.set("key", "value")
        assert cache.delete("key") is True
        assert cache.get("key") is None
        assert cache.delete("key") is False

    def test_clear_removes_all_entries(self) -> None:
        """Clear should remove all entries."""
        cache: Cache[str] = Cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.size == 0

    def test_has_returns_correct_status(self) -> None:
        """Has should return True only for existing entries."""
        cache: Cache[str] = Cache()
        assert not cache.has("key")
        cache.set("key", "value")
        assert cache.has("key")

    def test_ttl_expiration(self) -> None:
        """Entry should expire after TTL."""
        cache: Cache[str] = Cache()
        cache.set("key", "value", ttl=0.01)  # 10ms TTL
        assert cache.get("key") == "value"
        time.sleep(0.02)  # Wait for expiration
        assert cache.get("key") is None

    def test_default_ttl(self) -> None:
        """Entries should use default TTL if not specified."""
        cache: Cache[str] = Cache(default_ttl=0.01)
        cache.set("key", "value")
        assert cache.get("key") == "value"
        time.sleep(0.02)
        assert cache.get("key") is None

    def test_max_size_eviction(self) -> None:
        """Cache should evict LRU entries when max_size exceeded."""
        cache: Cache[str] = Cache(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1
        assert cache.get("key1") is None
        assert cache.get("key2") == "value2"
        assert cache.get("key3") == "value3"

    def test_lru_eviction_order(self) -> None:
        """Most recently used entries should be kept."""
        cache: Cache[str] = Cache(max_size=2)
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.get("key1")  # Access key1, making key2 LRU
        cache.set("key3", "value3")  # Should evict key2
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"

    def test_get_or_set_returns_existing(self) -> None:
        """get_or_set should return existing value."""
        cache: Cache[str] = Cache()
        cache.set("key", "existing")
        result = cache.get_or_set("key", lambda: "new")
        assert result == "existing"

    def test_get_or_set_creates_new(self) -> None:
        """get_or_set should create value if missing."""
        cache: Cache[str] = Cache()
        called = False

        def factory() -> str:
            nonlocal called
            called = True
            return "created"

        result = cache.get_or_set("key", factory)
        assert result == "created"
        assert called

    def test_invalidate_pattern(self) -> None:
        """invalidate_pattern should remove matching keys."""
        cache: Cache[str] = Cache()
        cache.set("user:1", "alice")
        cache.set("user:2", "bob")
        cache.set("post:1", "hello")
        count = cache.invalidate_pattern("user:")
        assert count == 2
        assert cache.get("user:1") is None
        assert cache.get("user:2") is None
        assert cache.get("post:1") == "hello"

    def test_cleanup_expired(self) -> None:
        """cleanup_expired should remove expired entries."""
        cache: Cache[str] = Cache()
        cache.set("key1", "value1", ttl=0.01)
        cache.set("key2", "value2")  # No TTL
        time.sleep(0.02)
        count = cache.cleanup_expired()
        assert count == 1
        assert cache.get("key2") == "value2"

    def test_stats(self) -> None:
        """stats should return cache statistics."""
        cache: Cache[str] = Cache(default_ttl=60, max_size=100)
        cache.set("key", "value")
        cache.get("key")
        cache.get("key")
        stats = cache.stats()
        assert stats["size"] == 1
        assert stats["max_size"] == 100
        assert stats["default_ttl"] == 60
        assert stats["total_hits"] == 2

    def test_contains_operator(self) -> None:
        """Test 'in' operator."""
        cache: Cache[str] = Cache()
        cache.set("key", "value")
        assert "key" in cache
        assert "missing" not in cache

    def test_len_operator(self) -> None:
        """Test len() function."""
        cache: Cache[str] = Cache()
        assert len(cache) == 0
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert len(cache) == 2


class TestFileCache:
    """Tests for FileCache class."""

    def test_basic_get_set(self, tmp_path: Path) -> None:
        """Test basic get/set operations."""
        cache = FileCache(tmp_path / "cache")
        cache.set("key1", {"data": "value1"})
        result = cache.get("key1")
        assert result == {"data": "value1"}

    def test_get_returns_default_for_missing(self, tmp_path: Path) -> None:
        """Get should return default for missing key."""
        cache = FileCache(tmp_path / "cache")
        assert cache.get("missing") is None
        assert cache.get("missing", "default") == "default"

    def test_delete_removes_entry(self, tmp_path: Path) -> None:
        """Delete should remove entry and files."""
        cache = FileCache(tmp_path / "cache")
        cache.set("key", "value")
        assert cache.delete("key") is True
        assert cache.get("key") is None
        assert cache.delete("key") is False

    def test_clear_removes_all(self, tmp_path: Path) -> None:
        """Clear should remove all entries."""
        cache = FileCache(tmp_path / "cache")
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.clear()
        assert cache.size == 0

    def test_ttl_expiration(self, tmp_path: Path) -> None:
        """Entry should expire after TTL."""
        cache = FileCache(tmp_path / "cache")
        cache.set("key", "value", ttl=0.01)
        assert cache.get("key") == "value"
        time.sleep(0.02)
        assert cache.get("key") is None

    def test_default_ttl(self, tmp_path: Path) -> None:
        """Entries should use default TTL."""
        cache = FileCache(tmp_path / "cache", default_ttl=0.01)
        cache.set("key", "value")
        assert cache.get("key") == "value"
        time.sleep(0.02)
        assert cache.get("key") is None

    def test_persistence(self, tmp_path: Path) -> None:
        """Values should persist across cache instances."""
        cache_dir = tmp_path / "cache"
        cache1 = FileCache(cache_dir)
        cache1.set("key", {"data": 123})

        # Create new cache instance
        cache2 = FileCache(cache_dir)
        assert cache2.get("key") == {"data": 123}

    def test_has_returns_correct_status(self, tmp_path: Path) -> None:
        """Has should return True only for existing entries."""
        cache = FileCache(tmp_path / "cache")
        assert not cache.has("key")
        cache.set("key", "value")
        assert cache.has("key")

    def test_cleanup_expired(self, tmp_path: Path) -> None:
        """cleanup_expired should remove expired entries."""
        cache = FileCache(tmp_path / "cache")
        cache.set("key1", "value1", ttl=0.01)
        cache.set("key2", "value2")
        time.sleep(0.02)
        count = cache.cleanup_expired()
        assert count == 1
        assert cache.has("key2")

    def test_stats(self, tmp_path: Path) -> None:
        """stats should return cache statistics."""
        cache = FileCache(tmp_path / "cache", default_ttl=60)
        cache.set("key", "value")
        stats = cache.stats()
        assert stats["entries"] == 1
        assert stats["default_ttl"] == 60
        assert "total_size_bytes" in stats

    def test_complex_values(self, tmp_path: Path) -> None:
        """Cache should handle complex Python objects."""
        cache = FileCache(tmp_path / "cache")
        data = {
            "list": [1, 2, 3],
            "nested": {"a": {"b": "c"}},
            "tuple": (1, 2),
            "set": {1, 2, 3},
        }
        cache.set("complex", data)
        result = cache.get("complex")
        assert result["list"] == [1, 2, 3]
        assert result["nested"]["a"]["b"] == "c"
        assert result["tuple"] == (1, 2)
        assert result["set"] == {1, 2, 3}


class TestCachedDecorator:
    """Tests for @cached decorator."""

    def test_basic_caching(self) -> None:
        """Decorator should cache function results."""
        clear_default_cache()
        call_count = 0

        @cached
        def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        assert expensive_function(5) == 10
        assert expensive_function(5) == 10
        assert call_count == 1

    def test_different_args_cached_separately(self) -> None:
        """Different arguments should be cached separately."""
        clear_default_cache()
        call_count = 0

        @cached
        def func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x

        assert func(1) == 1
        assert func(2) == 2
        assert func(1) == 1
        assert call_count == 2

    def test_ttl_expiration(self) -> None:
        """Cached values should expire after TTL."""
        clear_default_cache()
        call_count = 0

        @cached(ttl=0.01)
        def func() -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        assert func() == 1
        assert func() == 1
        time.sleep(0.02)
        assert func() == 2

    def test_cache_clear(self) -> None:
        """cache_clear should clear function cache."""
        clear_default_cache()
        call_count = 0

        @cached(key_prefix="test_func_")
        def func() -> int:
            nonlocal call_count
            call_count += 1
            return call_count

        assert func() == 1
        assert func() == 1
        func.cache_clear()  # type: ignore[attr-defined]
        assert func() == 2

    def test_custom_cache_instance(self) -> None:
        """Decorator should work with custom cache."""
        custom_cache: Cache[int] = Cache()
        call_count = 0

        @cached(cache=custom_cache)
        def func(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 2

        assert func(5) == 10
        assert func(5) == 10
        assert call_count == 1
        assert custom_cache.size == 1

    def test_kwargs_in_cache_key(self) -> None:
        """Keyword arguments should affect cache key."""
        clear_default_cache()
        call_count = 0

        @cached
        def func(a: int, b: int = 0) -> int:
            nonlocal call_count
            call_count += 1
            return a + b

        assert func(1, b=2) == 3
        assert func(1, b=3) == 4
        assert func(1, b=2) == 3
        assert call_count == 2


class TestDefaultCache:
    """Tests for default cache utilities."""

    def test_get_default_cache(self) -> None:
        """get_default_cache should return same instance."""
        cache1 = get_default_cache()
        cache2 = get_default_cache()
        assert cache1 is cache2

    def test_clear_default_cache(self) -> None:
        """clear_default_cache should clear the cache."""
        cache = get_default_cache()
        cache.set("test_key", "value")
        assert cache.has("test_key")
        clear_default_cache()
        assert not cache.has("test_key")
