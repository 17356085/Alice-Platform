"""Redis utilities — distributed lock + persistent rate limiting.

P3+P4 (2026-06-25): Adds distributed coordination primitives.
All auto-detect Redis. All fall back gracefully when unavailable.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Optional

logger = logging.getLogger("redis_utils")

_REDIS_AVAILABLE = False
try:
    import redis as _redis
    _REDIS_AVAILABLE = True
except ImportError:
    pass


def _get_redis() -> Optional[_redis.Redis]:
    if not _REDIS_AVAILABLE:
        return None
    try:
        r = _redis.Redis(host="localhost", port=6379, socket_connect_timeout=1)
        r.ping()
        return r
    except Exception:
        return None


# ══════════════════════════════════════════════════════════════════════
#  P3: Distributed Lock
# ══════════════════════════════════════════════════════════════════════

class RedisLock:
    """Redis-based distributed lock using SETNX + TTL.

    Prevents duplicate SOP runs, concurrent mutations on same module.

    Usage:
        lock = RedisLock("sop:run:equipment", ttl=3600)
        if lock.acquire():
            try:
                run_sop("equipment")
            finally:
                lock.release()
    """

    def __init__(self, resource: str, ttl: int = 3600):
        self._key = f"tlo:lock:{resource}"
        self._ttl = ttl
        self._token = uuid.uuid4().hex
        self._redis = _get_redis()
        self._acquired = False

    def acquire(self) -> bool:
        """Try to acquire lock. Returns True if successful."""
        if not self._redis:
            return True  # No Redis → allow always (single-machine mode)
        ok = self._redis.set(self._key, self._token, nx=True, ex=self._ttl)
        if ok:
            self._acquired = True
            logger.debug("lock_acquired", resource=self._key, ttl=self._ttl)
        return bool(ok)

    def release(self):
        """Release lock (only if we own it)."""
        if not self._redis or not self._acquired:
            return
        # Lua script: release only if token matches
        script = """
        if redis.call("GET", KEYS[1]) == ARGV[1] then
            return redis.call("DEL", KEYS[1])
        else
            return 0
        end
        """
        self._redis.eval(script, 1, self._key, self._token)
        self._acquired = False
        logger.debug("lock_released", resource=self._key)

    def extend(self, ttl: int = None):
        """Extend lock TTL without releasing."""
        if not self._redis or not self._acquired:
            return
        self._redis.expire(self._key, ttl or self._ttl)

    @property
    def is_locked(self) -> bool:
        if not self._redis:
            return False
        return bool(self._redis.exists(self._key))

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, *args):
        self.release()


# ══════════════════════════════════════════════════════════════════════
#  P4: Persistent Rate Limiting
# ══════════════════════════════════════════════════════════════════════

class RedisRateLimiter:
    """Redis sliding-window rate limiter. Persists across restarts.

    Usage:
        limiter = RedisRateLimiter()
        if limiter.check("api:127.0.0.1", max_req=60, window=60):
            process_request()
        else:
            return 429
    """

    def __init__(self):
        self._redis = _get_redis()

    def check(self, key: str, max_requests: int = 60,
              window_seconds: int = 60) -> bool:
        """Check if request is within rate limit. Returns True if allowed."""
        if not self._redis:
            # Fallback: always allow (in-memory rate limit handles this)
            return True

        now = time.time()
        window_start = now - window_seconds
        rkey = f"tlo:ratelimit:{key}"

        # Atomic sliding window via Lua
        script = """
        local now = tonumber(ARGV[1])
        local window = tonumber(ARGV[2])
        local max_req = tonumber(ARGV[3])
        local member = ARGV[4]

        -- Remove expired entries
        redis.call("ZREMRANGEBYSCORE", KEYS[1], 0, now - window)

        -- Check count
        local count = redis.call("ZCARD", KEYS[1])
        if count >= max_req then
            return 0
        end

        -- Add current request
        redis.call("ZADD", KEYS[1], now, member)
        redis.call("EXPIRE", KEYS[1], window + 10)
        return 1
        """
        member = f"{now}:{uuid.uuid4().hex[:8]}"
        allowed = self._redis.eval(
            script, 1, rkey, now, window_seconds, max_requests, member)
        return bool(allowed)

    def remaining(self, key: str, max_requests: int = 60,
                  window_seconds: int = 60) -> int:
        """Return remaining requests in current window."""
        if not self._redis:
            return max_requests
        now = time.time()
        rkey = f"tlo:ratelimit:{key}"
        self._redis.zremrangebyscore(rkey, 0, now - window_seconds)
        used = self._redis.zcard(rkey)
        return max(0, max_requests - used)

    def stats(self) -> dict:
        if not self._redis:
            return {"backend": "memory", "status": "redis_unavailable"}
        return {
            "backend": "redis",
            "active_limiters": len(self._redis.keys("tlo:ratelimit:*")),
        }


# ── Singletons ────────────────────────────────────────────────────────

redis_limiter = RedisRateLimiter()
