"""Cache system for NEO-AIOS.

Provides in-memory and file-based caching with TTL support,
invalidation strategies, and decorators for easy integration.

Note: FileCache uses pickle for serialization of arbitrary Python objects.
This is safe for local caching where the cache files are not exposed to
external/untrusted sources. For network-based caching, use JSON serialization.

Example:
    >>> from aios.core.cache import Cache, cached, FileCache
    >>>
    >>> # In-memory cache with TTL
    >>> cache = Cache(default_ttl=300)  # 5 minutes
    >>> cache.set("key", "value")
    >>> cache.get("key")
    'value'
    >>>
    >>> # Cached function
    >>> @cached(ttl=60)
    ... def expensive_computation(x: int) -> int:
    ...     return x * 2
    >>>
    >>> # File-based persistent cache
    >>> file_cache = FileCache(".cache/my_cache")
    >>> file_cache.set("data", {"complex": "object"})
"""

from __future__ import annotations

import functools
import hashlib
import json
import pickle  # nosec B403 - used for local cache only, not external data
import threading
import time
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Any
from typing import cast
from typing import overload

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass
class CacheEntry[T]:
    """A single cache entry with value and metadata.

    Attributes:
        value: The cached value.
        created_at: Unix timestamp when entry was created.
        expires_at: Unix timestamp when entry expires (None = never).
        hits: Number of times this entry was accessed.
    """

    value: T
    created_at: float = field(default_factory=time.time)
    expires_at: float | None = None
    hits: int = 0

    def is_expired(self) -> bool:
        """Check if this entry has expired.

        Returns:
            True if expired, False otherwise.
        """
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at


class Cache[T]:
    """Thread-safe in-memory cache with TTL support.

    Provides a simple key-value cache with optional TTL (time-to-live)
    for automatic expiration. Thread-safe for concurrent access.

    Attributes:
        default_ttl: Default TTL in seconds (None = no expiration).
        max_size: Maximum number of entries (None = unlimited).

    Example:
        >>> cache: Cache[str] = Cache(default_ttl=60)
        >>> cache.set("user_123", "John Doe")
        >>> cache.get("user_123")
        'John Doe'
    """

    def __init__(
        self,
        default_ttl: float | None = None,
        max_size: int | None = None,
    ) -> None:
        """Initialize cache.

        Args:
            default_ttl: Default TTL in seconds for entries without explicit TTL.
            max_size: Maximum entries before LRU eviction kicks in.
        """
        self._entries: dict[str, CacheEntry[T]] = {}
        self._lock = threading.RLock()
        self.default_ttl = default_ttl
        self.max_size = max_size
        self._access_order: list[str] = []

    def get(self, key: str, default: T | None = None) -> T | None:
        """Get value from cache.

        Args:
            key: Cache key.
            default: Value to return if key not found or expired.

        Returns:
            Cached value or default.
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return default
            if entry.is_expired():
                self._remove_entry(key)
                return default
            entry.hits += 1
            self._update_access_order(key)
            return entry.value

    def set(
        self,
        key: str,
        value: T,
        ttl: float | None = None,
    ) -> None:
        """Set value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
            ttl: TTL in seconds (None = use default_ttl).
        """
        with self._lock:
            effective_ttl = ttl if ttl is not None else self.default_ttl
            expires_at = time.time() + effective_ttl if effective_ttl else None

            self._entries[key] = CacheEntry(
                value=value,
                created_at=time.time(),
                expires_at=expires_at,
            )
            self._update_access_order(key)
            self._enforce_max_size()

    def delete(self, key: str) -> bool:
        """Delete entry from cache.

        Args:
            key: Cache key to delete.

        Returns:
            True if key existed and was deleted.
        """
        with self._lock:
            return self._remove_entry(key)

    def clear(self) -> None:
        """Clear all entries from cache."""
        with self._lock:
            self._entries.clear()
            self._access_order.clear()

    def has(self, key: str) -> bool:
        """Check if key exists and is not expired.

        Args:
            key: Cache key to check.

        Returns:
            True if key exists and is valid.
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return False
            if entry.is_expired():
                self._remove_entry(key)
                return False
            return True

    def get_or_set(
        self,
        key: str,
        factory: Callable[[], T],
        ttl: float | None = None,
    ) -> T:
        """Get value or compute and cache it.

        Atomic operation that returns cached value if exists,
        otherwise computes using factory and caches result.

        Args:
            key: Cache key.
            factory: Callable to produce value if not cached.
            ttl: TTL for new entry.

        Returns:
            Cached or newly computed value.
        """
        with self._lock:
            value = self.get(key)
            if value is not None:
                return value
            new_value = factory()
            self.set(key, new_value, ttl)
            return new_value

    def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern.

        Uses simple prefix matching.

        Args:
            pattern: Prefix pattern to match.

        Returns:
            Number of keys invalidated.
        """
        with self._lock:
            keys_to_delete = [k for k in self._entries if k.startswith(pattern)]
            for key in keys_to_delete:
                self._remove_entry(key)
            return len(keys_to_delete)

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed.
        """
        with self._lock:
            expired_keys = [
                k for k, v in self._entries.items() if v.is_expired()
            ]
            for key in expired_keys:
                self._remove_entry(key)
            return len(expired_keys)

    def stats(self) -> dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics.
        """
        with self._lock:
            total_hits = sum(e.hits for e in self._entries.values())
            return {
                "size": len(self._entries),
                "max_size": self.max_size,
                "default_ttl": self.default_ttl,
                "total_hits": total_hits,
                "keys": list(self._entries.keys()),
            }

    def _remove_entry(self, key: str) -> bool:
        """Internal: Remove entry by key.

        Args:
            key: Key to remove.

        Returns:
            True if removed.
        """
        if key in self._entries:
            del self._entries[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return True
        return False

    def _update_access_order(self, key: str) -> None:
        """Internal: Update LRU access order."""
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def _enforce_max_size(self) -> None:
        """Internal: Evict LRU entries if over max_size."""
        if self.max_size is None:
            return
        while len(self._entries) > self.max_size and self._access_order:
            lru_key = self._access_order[0]
            self._remove_entry(lru_key)

    @property
    def size(self) -> int:
        """Current number of entries."""
        with self._lock:
            return len(self._entries)

    def __contains__(self, key: str) -> bool:
        """Check if key is in cache."""
        return self.has(key)

    def __len__(self) -> int:
        """Number of entries in cache."""
        return self.size

    def __repr__(self) -> str:
        """String representation."""
        return f"Cache(size={self.size}, default_ttl={self.default_ttl})"


class FileCache:
    """Persistent file-based cache.

    Stores cache entries as files on disk for persistence across restarts.
    Uses pickle for serialization (local cache only, not for external data).

    Security Note:
        This cache is intended for local use only. The pickle module is used
        for serialization which can execute arbitrary code during deserialization.
        Do NOT use this cache with files from untrusted sources.

    Attributes:
        cache_dir: Directory for cache files.
        default_ttl: Default TTL in seconds.

    Example:
        >>> cache = FileCache(".cache/validators")
        >>> cache.set("validator_results", results, ttl=3600)
        >>> # Later, even after restart:
        >>> results = cache.get("validator_results")
    """

    def __init__(
        self,
        cache_dir: str | Path,
        default_ttl: float | None = None,
    ) -> None:
        """Initialize file cache.

        Args:
            cache_dir: Directory to store cache files.
            default_ttl: Default TTL in seconds.
        """
        self.cache_dir = Path(cache_dir)
        self.default_ttl = default_ttl
        self._lock = threading.RLock()
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _key_to_path(self, key: str) -> Path:
        """Convert key to file path.

        Uses hash for filesystem-safe names.

        Args:
            key: Cache key.

        Returns:
            Path to cache file.
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.cache_dir / f"{key_hash}.cache"

    def _metadata_path(self, key: str) -> Path:
        """Get path for metadata file.

        Args:
            key: Cache key.

        Returns:
            Path to metadata file.
        """
        key_hash = hashlib.sha256(key.encode()).hexdigest()[:16]
        return self.cache_dir / f"{key_hash}.meta"

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from file cache.

        Args:
            key: Cache key.
            default: Value if not found or expired.

        Returns:
            Cached value or default.
        """
        with self._lock:
            cache_path = self._key_to_path(key)
            meta_path = self._metadata_path(key)

            if not cache_path.exists():
                return default

            # Check metadata for expiration
            if meta_path.exists():
                try:
                    meta = json.loads(meta_path.read_text())
                    expires_at = meta.get("expires_at")
                    if expires_at and time.time() > expires_at:
                        self.delete(key)
                        return default
                except (json.JSONDecodeError, OSError):
                    pass

            try:
                # nosec B301 - pickle used for local cache only
                return pickle.loads(cache_path.read_bytes())
            except (pickle.PickleError, OSError):
                return default

    def set(
        self,
        key: str,
        value: Any,
        ttl: float | None = None,
    ) -> None:
        """Set value in file cache.

        Args:
            key: Cache key.
            value: Value to cache (must be picklable).
            ttl: TTL in seconds.
        """
        with self._lock:
            cache_path = self._key_to_path(key)
            meta_path = self._metadata_path(key)

            effective_ttl = ttl if ttl is not None else self.default_ttl
            expires_at = time.time() + effective_ttl if effective_ttl else None

            # Write value
            cache_path.write_bytes(pickle.dumps(value))

            # Write metadata
            meta = {
                "key": key,
                "created_at": time.time(),
                "expires_at": expires_at,
            }
            meta_path.write_text(json.dumps(meta))

    def delete(self, key: str) -> bool:
        """Delete entry from file cache.

        Args:
            key: Cache key.

        Returns:
            True if deleted.
        """
        with self._lock:
            cache_path = self._key_to_path(key)
            meta_path = self._metadata_path(key)
            deleted = False

            if cache_path.exists():
                cache_path.unlink()
                deleted = True
            if meta_path.exists():
                meta_path.unlink()

            return deleted

    def clear(self) -> None:
        """Clear all entries from file cache."""
        with self._lock:
            for path in self.cache_dir.glob("*.cache"):
                path.unlink()
            for path in self.cache_dir.glob("*.meta"):
                path.unlink()

    def has(self, key: str) -> bool:
        """Check if key exists and is not expired.

        Args:
            key: Cache key.

        Returns:
            True if valid entry exists.
        """
        return self.get(key, default=None) is not None

    def cleanup_expired(self) -> int:
        """Remove all expired entries.

        Returns:
            Number of entries removed.
        """
        with self._lock:
            removed = 0
            for meta_path in self.cache_dir.glob("*.meta"):
                try:
                    meta = json.loads(meta_path.read_text())
                    expires_at = meta.get("expires_at")
                    if expires_at and time.time() > expires_at:
                        key = meta.get("key", "")
                        if key and self.delete(key):
                            removed += 1
                except (json.JSONDecodeError, OSError):
                    continue
            return removed

    def stats(self) -> dict[str, Any]:
        """Get file cache statistics.

        Returns:
            Dictionary with statistics.
        """
        with self._lock:
            cache_files = list(self.cache_dir.glob("*.cache"))
            total_size = sum(f.stat().st_size for f in cache_files)
            return {
                "entries": len(cache_files),
                "total_size_bytes": total_size,
                "cache_dir": str(self.cache_dir),
                "default_ttl": self.default_ttl,
            }

    @property
    def size(self) -> int:
        """Number of entries in cache."""
        with self._lock:
            return len(list(self.cache_dir.glob("*.cache")))

    def __contains__(self, key: str) -> bool:
        """Check if key is in cache."""
        return self.has(key)

    def __len__(self) -> int:
        """Number of entries."""
        return self.size

    def __repr__(self) -> str:
        """String representation."""
        return f"FileCache(dir={self.cache_dir}, size={self.size})"


def _make_cache_key(
    func: Callable[..., Any],
    args: tuple[Any, ...],
    kwargs: dict[str, Any],
) -> str:
    """Create cache key from function call.

    Args:
        func: Function being cached.
        args: Positional arguments.
        kwargs: Keyword arguments.

    Returns:
        Unique cache key string.
    """
    key_parts = [func.__module__, func.__qualname__]

    # Add args
    for arg in args:
        try:
            key_parts.append(repr(arg))
        except Exception:
            key_parts.append(str(id(arg)))

    # Add kwargs (sorted for consistency)
    for k, v in sorted(kwargs.items()):
        try:
            key_parts.append(f"{k}={v!r}")
        except Exception:
            key_parts.append(f"{k}={id(v)}")

    key_string = "|".join(key_parts)
    return hashlib.sha256(key_string.encode()).hexdigest()


# Global cache instance for @cached decorator
_default_cache: Cache[Any] = Cache()


@overload
def cached[F: Callable[..., Any]](func: F) -> F: ...


@overload
def cached[F: Callable[..., Any]](
    *,
    ttl: float | None = None,
    cache: Cache[Any] | None = None,
    key_prefix: str | None = None,
) -> Callable[[F], F]: ...


def cached[F: Callable[..., Any]](
    func: F | None = None,
    *,
    ttl: float | None = None,
    cache: Cache[Any] | None = None,
    key_prefix: str | None = None,
) -> F | Callable[[F], F]:
    """Decorator to cache function results.

    Can be used with or without arguments:

        @cached
        def simple_function(x):
            return x * 2

        @cached(ttl=60, key_prefix="my_func")
        def function_with_options(x):
            return expensive_computation(x)

    Args:
        func: Function to wrap (when used without parens).
        ttl: Time-to-live in seconds.
        cache: Cache instance to use (defaults to global cache).
        key_prefix: Prefix for cache keys.

    Returns:
        Decorated function or decorator.
    """
    def decorator(fn: F) -> F:
        target_cache = cache if cache is not None else _default_cache
        prefix = key_prefix or ""

        @functools.wraps(fn)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            cache_key = prefix + _make_cache_key(fn, args, kwargs)

            # Check cache
            cached_value = target_cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Compute and cache
            result = fn(*args, **kwargs)
            target_cache.set(cache_key, result, ttl)
            return result

        # Add cache management methods to wrapper
        def _cache_clear() -> int:
            return target_cache.invalidate_pattern(prefix)

        wrapper.cache_clear = _cache_clear  # type: ignore[attr-defined]
        wrapper.cache_info = target_cache.stats  # type: ignore[attr-defined]

        return cast("F", wrapper)

    if func is not None:
        # Called without arguments: @cached
        return decorator(func)

    # Called with arguments: @cached(ttl=60)
    return decorator


def get_default_cache() -> Cache[Any]:
    """Get the global default cache instance.

    Returns:
        Default cache used by @cached decorator.
    """
    return _default_cache


def clear_default_cache() -> None:
    """Clear the global default cache."""
    _default_cache.clear()
