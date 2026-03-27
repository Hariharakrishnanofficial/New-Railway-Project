"""
Cache Manager - TTL-based in-memory cache for CloudScale data.
Reduces repeated database calls for static/semi-static data.
"""

import logging
import threading
import time
from typing import Any, Optional, Callable
from functools import wraps

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Thread-safe TTL cache with namespace support.

    Usage:
        cache.set("stations:all", data, ttl=86400)
        data = cache.get("stations:all")
        cache.invalidate("trains:")  # invalidate all keys starting with "trains:"
    """

    def __init__(self):
        self._store: dict[str, tuple[Any, float]] = {}  # key -> (value, expire_at)
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0

    # ── Basic operations ───────────────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache. Returns None if key not found or expired."""
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                self._misses += 1
                return None
            value, expire_at = entry
            if time.monotonic() > expire_at:
                del self._store[key]
                self._misses += 1
                return None
            self._hits += 1
            return value

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """Set a value in cache with TTL (time to live) in seconds."""
        with self._lock:
            self._store[key] = (value, time.monotonic() + ttl)

    def delete(self, key: str) -> None:
        """Delete a specific key from cache."""
        with self._lock:
            self._store.pop(key, None)

    def invalidate(self, prefix: str) -> int:
        """Delete all keys that start with prefix. Returns count of deleted keys."""
        with self._lock:
            keys_to_delete = [k for k in self._store if k.startswith(prefix)]
            for k in keys_to_delete:
                del self._store[k]
            if keys_to_delete:
                logger.debug(f"Cache: invalidated {len(keys_to_delete)} keys with prefix '{prefix}'")
            return len(keys_to_delete)

    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0

    def stats(self) -> dict:
        """Get cache statistics."""
        with self._lock:
            now = time.monotonic()
            total = len(self._store)
            expired = sum(1 for _, exp in self._store.values() if now > exp)
            hit_rate = self._hits / (self._hits + self._misses) if (self._hits + self._misses) > 0 else 0
            return {
                "total_keys": total,
                "expired_keys": expired,
                "live_keys": total - expired,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": f"{hit_rate:.1%}",
            }

    # ── Decorator helper ───────────────────────────────────────────────────────

    def cached(self, key: str, ttl: int = 300):
        """Decorator that caches the return value of a function."""
        def decorator(fn: Callable):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                cached_val = self.get(key)
                if cached_val is not None:
                    logger.debug(f"Cache HIT: {key}")
                    return cached_val
                result = fn(*args, **kwargs)
                if result is not None:
                    self.set(key, result, ttl)
                    logger.debug(f"Cache SET: {key} (ttl={ttl}s)")
                return result
            return wrapper
        return decorator

    def cached_by_args(self, key_prefix: str, ttl: int = 300):
        """Decorator that caches with a key generated from arguments."""
        def decorator(fn: Callable):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                # Generate cache key from prefix + args
                arg_str = ":".join(str(a) for a in args)
                kwarg_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                cache_key = f"{key_prefix}:{arg_str}:{kwarg_str}".rstrip(":")

                cached_val = self.get(cache_key)
                if cached_val is not None:
                    logger.debug(f"Cache HIT: {cache_key}")
                    return cached_val
                result = fn(*args, **kwargs)
                if result is not None:
                    self.set(cache_key, result, ttl)
                    logger.debug(f"Cache SET: {cache_key} (ttl={ttl}s)")
                return result
            return wrapper
        return decorator


# ── TTL Constants ──────────────────────────────────────────────────────────────
TTL_STATIONS = 86400    # 24 hours  - station list rarely changes
TTL_TRAINS = 3600       # 1 hour    - train master data
TTL_FARES = 21600       # 6 hours   - fare matrix
TTL_INVENTORY = 300     # 5 minutes - seat availability per train+date+class
TTL_USER = 900          # 15 minutes - user profile (booking limit check)
TTL_ROUTES = 21600      # 6 hours   - route stops
TTL_OVERVIEW = 600      # 10 minutes - dashboard stats
TTL_SETTINGS = 3600     # 1 hour    - system settings


# ── Singleton ──────────────────────────────────────────────────────────────────
cache = CacheManager()
