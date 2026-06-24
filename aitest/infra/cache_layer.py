"""
Cache Layer — Runtime Performance for Alice v1.6.

Unified in-memory cache for RAG queries, LLM responses, and artifact content.
Thread-safe. TTL-based expiration. LRU eviction when max size exceeded.

Each cache type reports hit/miss/saved_tokens/saved_time to operational metrics.

Cache types:
  rag       — RAG query results (known issues, context search)
  llm       — LLM responses by (agent, prompt_hash)
  artifact  — Artifact file content by path

Usage:
    from aitest.infra.cache_layer import cache

    # RAG cache
    result = cache.get("rag", "el-dialog teleport")  # → None if miss
    cache.set("rag", "el-dialog teleport", issues_list, tokens_saved=1200)

    # LLM cache
    key = f"automation-agent:{hashlib.md5(prompt.encode()).hexdigest()[:12]}"
    result = cache.get("llm", key)

    # Auto-record metrics
    stats = cache.stats()  # → {rag: {hits, misses, saved_tokens, saved_time_ms}, ...}
"""

import hashlib
import threading
import time
from collections import OrderedDict
from typing import Optional, Any


class CacheStore:
    """Single cache store with TTL + LRU + metrics."""

    def __init__(self, max_size: int = 200, ttl_seconds: float = 300):
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._saved_tokens = 0
        self._saved_time_ms = 0.0

    def get(self, key: str) -> Optional[Any]:
        """Get cached value. Returns None if expired or missing."""
        with self._lock:
            if key not in self._store:
                self._misses += 1
                return None

            expiry, value = self._store[key]
            if time.monotonic() > expiry:
                del self._store[key]
                self._misses += 1
                return None

            # Move to end (LRU)
            self._store.move_to_end(key)
            self._hits += 1
            return value

    def set(self, key: str, value: Any, tokens_saved: int = 0, time_saved_ms: float = 0):
        """Store a value with TTL. Evicts oldest if max size exceeded."""
        with self._lock:
            # Evict if full
            while len(self._store) >= self._max_size:
                self._store.popitem(last=False)

            expiry = time.monotonic() + self._ttl
            self._store[key] = (expiry, value)
            self._saved_tokens += tokens_saved
            self._saved_time_ms += time_saved_ms

    def stats(self) -> dict:
        with self._lock:
            total = self._hits + self._misses
            return {
                "size": len(self._store),
                "max_size": self._max_size,
                "hits": self._hits,
                "misses": self._misses,
                "hit_rate": round(self._hits / total, 3) if total > 0 else 0,
                "saved_tokens": self._saved_tokens,
                "saved_time_ms": round(self._saved_time_ms, 1),
            }

    def clear(self):
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0
            self._saved_tokens = 0
            self._saved_time_ms = 0.0


class CacheLayer:
    """Unified cache manager with per-type stores."""

    def __init__(self):
        self._stores: dict[str, CacheStore] = {
            "rag": CacheStore(max_size=100, ttl_seconds=600),      # 10 min TTL
            "llm": CacheStore(max_size=50, ttl_seconds=300),       # 5 min TTL
            "artifact": CacheStore(max_size=200, ttl_seconds=1200), # 20 min TTL
        }
        self._lock = threading.Lock()

    def get(self, cache_type: str, key: str) -> Optional[Any]:
        store = self._stores.get(cache_type)
        if store is None:
            return None
        return store.get(key)

    def set(self, cache_type: str, key: str, value: Any,
            tokens_saved: int = 0, time_saved_ms: float = 0):
        store = self._stores.get(cache_type)
        if store is None:
            return
        store.set(key, value, tokens_saved, time_saved)

        # Sync to operational metrics
        try:
            from aitest.platform.operational_metrics import get_collector
            mc = get_collector()
            mc.record_memory(cache_type, hit=True)
            mc.record_capability(f"cache:{cache_type}", tokens_saved, time_saved_ms, True)
        except Exception:
            pass

    def stats(self) -> dict:
        return {
            cache_type: store.stats()
            for cache_type, store in self._stores.items()
        }

    def all_saved_tokens(self) -> int:
        return sum(s.stats()["saved_tokens"] for s in self._stores.values())

    def clear_all(self):
        for store in self._stores.values():
            store.clear()

    def get_or_set(self, cache_type: str, key: str, factory, **kwargs):
        """Get from cache or compute + store.

        Usage:
            result = cache.get_or_set("rag", query, lambda: chroma.query(query),
                                      tokens_saved=1200)
        """
        cached = self.get(cache_type, key)
        if cached is not None:
            return cached
        value = factory()
        self.set(cache_type, key, value, **kwargs)
        return value


# Singleton
cache = CacheLayer()
