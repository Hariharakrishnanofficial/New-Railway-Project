"""
Cache Manager — TTL-based in-memory cache for CloudScale data.
Reduces repeated database calls for static/semi-static data.
"""

import logging
import threading
import time
from typing import Any, Optional

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
        self._store: dict[str, tuple[Any, float]] = {}   # key -> (value, expire_at)
        self._lock  = threading.Lock()

    # ── Basic operations ─────────────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if not entry:
                return None
            value, expire_at = entry
            if time.monotonic() > expire_at:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        with self._lock:
            self._store[key] = (value, time.monotonic() + ttl)

    def delete(self, key: str) -> None:
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
        with self._lock:
            self._store.clear()

    def stats(self) -> dict:
        with self._lock:
            now = time.monotonic()
            total   = len(self._store)
            expired = sum(1 for _, exp in self._store.values() if now > exp)
            return {"total_keys": total, "expired_keys": expired, "live_keys": total - expired}

    # ── Decorator helper ─────────────────────────────────────────────────────

    def cached(self, key: str, ttl: int = 300):
        """Decorator that caches the return value of a function."""
        def decorator(fn):
            from functools import wraps
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


# ── TTL Constants ────────────────────────────────────────────────────────────
TTL_STATIONS  = 86400   # 24 hours  — station list rarely changes
TTL_TRAINS    = 3600    # 1 hour    — train master data
TTL_FARES     = 21600   # 6 hours   — fare matrix
TTL_INVENTORY = 300     # 5 minutes — seat availability per train+date+class
TTL_USER      = 900     # 15 minutes — user profile (booking limit check)
TTL_ROUTES    = 21600   # 6 hours   — route stops
TTL_OVERVIEW  = 600     # 10 minutes — dashboard stats


# Singleton
cache = CacheManager()
