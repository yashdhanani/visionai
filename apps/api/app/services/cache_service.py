from __future__ import annotations

import json
import logging
import time
from typing import Any

from app.config.settings import settings
from app.core.logging import logger


class MemoryCache:
    """Process-local fallback used when Redis is not configured (dev/test only)."""

    def __init__(self) -> None:
        self._data: dict[str, tuple[Any, float]] = {}

    def _purged_get(self, key: str) -> Any:
        item = self._data.get(key)
        if not item:
            return None
        value, expires = item
        if expires and time.monotonic() > expires:
            del self._data[key]
            return None
        return value

    def get(self, key: str) -> Any:
        return self._purged_get(key)

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        self._data[key] = (value, (time.monotonic() + ttl) if ttl else 0)

    def delete(self, *keys: str) -> None:
        for k in keys:
            self._data.pop(k, None)

    def incr(self, key: str) -> int:
        current = self._purged_get(key) or 0
        current = int(current) + 1
        self.set(key, current)
        return current

    def expire(self, key: str, ttl: int) -> None:
        item = self._data.get(key)
        if item:
            self._data[key] = (item[0], time.monotonic() + ttl)

    def publish(self, channel: str, message: str) -> int:
        return 0

    def close(self) -> None:
        self._data.clear()


_redis_client = None
_memory_cache = MemoryCache()


def get_redis():
    """Return a Redis client if REDIS_URL is configured and reachable, else None."""
    global _redis_client
    if _redis_client is not None:
        return _redis_client
    if not settings.REDIS_URL:
        return None
    try:
        import redis as redis_lib

        client = redis_lib.Redis.from_url(
            settings.REDIS_URL, socket_connect_timeout=1.0, socket_timeout=1.0, decode_responses=True
        )
        client.ping()
        _redis_client = client
        logger.info("redis connected", extra={"endpoint": settings.REDIS_URL.split("@")[-1]})
        return _redis_client
    except Exception as exc:
        logger.warning(f"Redis unavailable ({exc.__class__.__name__}); using in-process cache fallback")
        settings.REDIS_URL = ""
        return None


def cache() -> Any:
    """Return the active cache backend (Redis if available, otherwise memory)."""
    return get_redis() or _memory_cache


def cache_get_json(key: str) -> Any | None:
    raw = cache().get(key)
    if raw is None:
        return None
    if isinstance(raw, bytes):
        raw = raw.decode()
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return raw


def cache_set_json(key: str, value: Any, ttl: int = 60) -> None:
    cache().set(key, json.dumps(value), ttl)


def cache_delete(*keys: str) -> None:
    cache().delete(*keys)
