from __future__ import annotations

import time
from typing import Protocol

from app.core.exceptions import RateLimitError


class Backend(Protocol):
    def incr_with_ttl(self, key: str, ttl_seconds: int) -> int: ...


class RedisBackend:
    def __init__(self, client):
        self.client = client

    def incr_with_ttl(self, key: str, ttl_seconds: int) -> int:
        count = self.client.incr(key)
        if count == 1:
            self.client.expire(key, ttl_seconds)
        return int(count)


class MemoryBackend:
    def __init__(self) -> None:
        self._store: dict[str, tuple[int, float]] = {}

    def incr_with_ttl(self, key: str, ttl_seconds: int) -> int:
        now = time.monotonic()
        count, expires = self._store.get(key, (0, 0.0))
        if now >= expires:
            count, expires = 0, now + ttl_seconds
        count += 1
        self._store[key] = (count, expires)
        if len(self._store) > 50_000:
            cutoff = now
            self._store = {k: v for k, v in self._store.items() if v[1] > cutoff}
        return count


_backend: Backend | None = None


def get_rate_limit_backend() -> Backend:
    global _backend
    if _backend is None:
        from app.services.cache_service import get_redis
        redis = get_redis()
        _backend = RedisBackend(redis) if redis is not None else MemoryBackend()
    return _backend


def rate_limit(name: str, limit: int, window_seconds: int = 60, key_by: str = "ip"):
    def dependency(request=None, identifier: str | None = None):
        from fastapi import Request as FastAPIRequest

        req: FastAPIRequest | None = request
        if req is None:
            raise RuntimeError("rate_limit requires a Request")
        if key_by == "ip":
            subject = req.client.host if req.client else "unknown"
        else:
            subject = identifier or "anonymous"
        backend = get_rate_limit_backend()
        bucket = f"rl:{name}:{subject}"
        count = backend.incr_with_ttl(bucket, window_seconds)
        if count > limit:
            raise RateLimitError(f"Rate limit exceeded ({limit} requests / {window_seconds}s)")

    return dependency
