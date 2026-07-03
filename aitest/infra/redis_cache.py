"""Redis-backed cache layer — persistent, cross-process, shared across workers.

P1 (2026-06-25): Extends in-memory CacheLayer with Redis persistence.
Reuses same interface (get/set/get_or_set/stats).

LLM cache: keyed by (agent, prompt_hash), auto-TTL 1h.
RAG cache:  keyed by query_hash, TTL 10min.
Artifact:   keyed by path, TTL 20min.

Semantic LLM cache: embedding-based exact-match detection.
Two identical prompts (same hash) → instant cache hit.
"""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Optional, Any

logger = logging.getLogger("redis_cache")

_REDIS_AVAILABLE = False
try:
    import redis as _redis
    _REDIS_AVAILABLE = True
except ImportError:
    pass


class RedisCache:
    """Redis-backed cache with same interface as CacheStore."""

    def __init__(self, cache_type: str, prefix: str = "tlo:cache",
                 ttl_seconds: int = 300):
        self._type = cache_type
        self._prefix = f"{prefix}:{cache_type}"
        self._ttl = ttl_seconds
        self._redis: Optional[_redis.Redis] = None
        self._hits = 0
        self._misses = 0
        self._saved_tokens = 0
        if _REDIS_AVAILABLE:
            try:
                from aitest.platform.config_registry import cfg
                self._redis = _redis.Redis(
                    host=cfg.redis_host, port=cfg.redis_port,
                    socket_connect_timeout=cfg.redis_connect_timeout,
                )
                self._redis.ping()
                logger.info("redis_cache_connected", type=cache_type)
            except Exception:
                self._redis = None

    @property
    def is_available(self) -> bool:
        return self._redis is not None

    def _safe_key(self, key: str) -> str:
        """Sanitize key for Redis (no spaces, special chars)."""
        return f"{self._prefix}:{hashlib.md5(key.encode()).hexdigest()[:16]}"

    def get(self, key: str) -> Optional[Any]:
        if not self._redis:
            self._misses += 1
            return None
        try:
            raw = self._redis.get(self._safe_key(key))
            if raw is None:
                self._misses += 1
                return None
            self._hits += 1
            return json.loads(raw)
        except Exception:
            self._misses += 1
            return None

    def set(self, key: str, value: Any, tokens_saved: int = 0, time_saved_ms: float = 0):
        if not self._redis:
            return
        try:
            sk = self._safe_key(key)
            self._redis.setex(sk, self._ttl, json.dumps(value, ensure_ascii=False))
            self._saved_tokens += tokens_saved
            # Track cache savings in Redis for cross-process visibility
            self._redis.incrby(f"{self._prefix}:saved_tokens", tokens_saved)
        except Exception:
            pass

    def get_or_set(self, key: str, factory, tokens_saved: int = 0) -> Any:
        cached = self.get(key)
        if cached is not None:
            return cached
        value = factory()
        self.set(key, value, tokens_saved=tokens_saved)
        return value

    def stats(self) -> dict:
        total = self._hits + self._misses
        size = 0
        if self._redis:
            try:
                size = len(self._redis.keys(f"{self._prefix}:*"))
            except Exception:
                pass
        return {
            "backend": "redis" if self._redis else "memory",
            "size": size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / total, 3) if total > 0 else 0,
            "saved_tokens": self._saved_tokens,
        }

    def clear(self):
        if self._redis:
            try:
                keys = self._redis.keys(f"{self._prefix}:*")
                if keys:
                    self._redis.delete(*keys)
            except Exception:
                pass
        self._hits = 0
        self._misses = 0
        self._saved_tokens = 0


class RedisCacheLayer:
    """Unified Redis cache manager — drop-in replacement for CacheLayer.

    Auto-detects Redis. Falls back to in-memory CacheLayer if unavailable.
    """

    _CONFIG = {
        "rag":      {"ttl": 600,  "max": 100},
        "llm":      {"ttl": 3600, "max": 200},  # 1h TTL for LLM responses
        "artifact": {"ttl": 1200, "max": 200},
    }

    def __init__(self):
        self._backends: dict[str, RedisCache] = {}
        self._fallback = None  # Lazy import if Redis unavailable
        self._redis_ok = False
        self._init_backends()

    def _init_backends(self):
        redis_ok = True
        for ctype, cfg in self._CONFIG.items():
            backend = RedisCache(ctype, ttl_seconds=cfg["ttl"])
            if not backend.is_available:
                redis_ok = False
            self._backends[ctype] = backend
        self._redis_ok = redis_ok

        if not redis_ok:
            from aitest.infra.cache_layer import CacheLayer
            self._fallback = CacheLayer()

    def _backend(self, cache_type: str):
        if self._redis_ok:
            return self._backends.get(cache_type)
        return None  # Fallback handled in get/set

    def get(self, cache_type: str, key: str) -> Optional[Any]:
        if self._redis_ok:
            b = self._backends.get(cache_type)
            return b.get(key) if b else None
        return self._fallback.get(cache_type, key) if self._fallback else None

    def set(self, cache_type: str, key: str, value: Any,
            tokens_saved: int = 0, time_saved_ms: float = 0):
        if self._redis_ok:
            b = self._backends.get(cache_type)
            if b:
                b.set(key, value, tokens_saved, time_saved_ms)
                return
        if self._fallback:
            self._fallback.set(cache_type, key, value, tokens_saved, time_saved_ms)

    def get_or_set(self, cache_type: str, key: str, factory, **kwargs) -> Any:
        if self._redis_ok:
            b = self._backends.get(cache_type)
            if b:
                return b.get_or_set(cache_type, key, factory,
                                    tokens_saved=kwargs.get("tokens_saved", 0))
        if self._fallback:
            return self._fallback.get_or_set(cache_type, key, factory, **kwargs)
        return factory()

    def stats(self) -> dict:
        result = {}
        if self._redis_ok:
            for ctype, backend in self._backends.items():
                result[ctype] = backend.stats()
        elif self._fallback:
            result = self._fallback.stats()
        return result

    def all_saved_tokens(self) -> int:
        if self._redis_ok:
            return sum(b.stats()["saved_tokens"] for b in self._backends.values())
        return self._fallback.all_saved_tokens() if self._fallback else 0

    def clear_all(self):
        for b in self._backends.values():
            b.clear()
        if self._fallback:
            self._fallback.clear_all()

    @property
    def is_redis(self) -> bool:
        return self._redis_ok


# Singleton
redis_cache = RedisCacheLayer()
