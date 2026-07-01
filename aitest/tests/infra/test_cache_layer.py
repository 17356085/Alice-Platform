"""Tests for infra/cache_layer.py — unified in-memory cache.

Tests: CacheStore (get/set/TTL/LRU/metrics), CacheLayer (multi-type).
Pure in-memory — no external dependencies.
"""
import time
import threading
import pytest

from aitest.infra.cache_layer import CacheStore, CacheLayer


# ══════════════════════════════════════════════════════════════════════════
#  CacheStore
# ══════════════════════════════════════════════════════════════════════════


class TestCacheStore:
    def test_get_miss(self):
        store = CacheStore()
        assert store.get("nonexistent") is None

    def test_set_and_get(self):
        store = CacheStore()
        store.set("key1", "value1")
        assert store.get("key1") == "value1"

    def test_ttl_expiration(self):
        store = CacheStore(ttl_seconds=0.01)
        store.set("key1", "value1")
        time.sleep(0.05)
        assert store.get("key1") is None

    def test_lru_eviction(self):
        store = CacheStore(max_size=3)
        store.set("a", 1)
        store.set("b", 2)
        store.set("c", 3)
        store.set("d", 4)  # Should evict "a"
        assert store.get("a") is None
        assert store.get("d") == 4

    def test_lru_access_refreshes(self):
        store = CacheStore(max_size=3)
        store.set("a", 1)
        store.set("b", 2)
        store.set("c", 3)
        store.get("a")  # Access "a" to refresh
        store.set("d", 4)  # Should evict "b" (oldest unused)
        assert store.get("a") == 1
        assert store.get("b") is None

    def test_metrics_hit(self):
        store = CacheStore()
        store.set("key1", "value1")
        store.get("key1")
        stats = store.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 0

    def test_metrics_miss(self):
        store = CacheStore()
        store.get("nonexistent")
        stats = store.stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 1

    def test_metrics_hit_rate(self):
        store = CacheStore()
        store.set("key1", "value1")
        store.get("key1")  # hit
        store.get("key1")  # hit
        store.get("nonexistent")  # miss
        stats = store.stats()
        assert stats["hit_rate"] == pytest.approx(0.667, abs=0.01)

    def test_saved_tokens(self):
        store = CacheStore()
        store.set("key1", "value1", tokens_saved=100)
        stats = store.stats()
        assert stats["saved_tokens"] == 100

    def test_clear(self):
        store = CacheStore()
        store.set("key1", "value1")
        store.clear()
        assert store.get("key1") is None
        assert store.stats()["size"] == 0

    def test_overwrite(self):
        store = CacheStore()
        store.set("key1", "old")
        store.set("key1", "new")
        assert store.get("key1") == "new"

    def test_stats_structure(self):
        store = CacheStore()
        stats = store.stats()
        assert "size" in stats
        assert "max_size" in stats
        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "saved_tokens" in stats
        assert "saved_time_ms" in stats


# ══════════════════════════════════════════════════════════════════════════
#  CacheLayer
# ══════════════════════════════════════════════════════════════════════════


class TestCacheLayer:
    def test_rag_cache(self):
        layer = CacheLayer()
        layer.set("rag", "query1", ["result1", "result2"])
        assert layer.get("rag", "query1") == ["result1", "result2"]

    def test_llm_cache(self):
        layer = CacheLayer()
        layer.set("llm", "key1", "response")
        assert layer.get("llm", "key1") == "response"

    def test_artifact_cache(self):
        layer = CacheLayer()
        layer.set("artifact", "path/to/file", "content")
        assert layer.get("artifact", "path/to/file") == "content"

    def test_unknown_type_returns_none(self):
        layer = CacheLayer()
        assert layer.get("nonexistent", "key") is None

    def test_unknown_type_set_noop(self):
        layer = CacheLayer()
        layer.set("nonexistent", "key", "value")  # Should not raise

    def test_stats_all_types(self):
        layer = CacheLayer()
        stats = layer.stats()
        assert "rag" in stats
        assert "llm" in stats
        assert "artifact" in stats

    def test_different_types_independent(self):
        layer = CacheLayer()
        layer.set("rag", "key1", "rag-value")
        layer.set("llm", "key1", "llm-value")
        assert layer.get("rag", "key1") == "rag-value"
        assert layer.get("llm", "key1") == "llm-value"


# ══════════════════════════════════════════════════════════════════════════
#  Thread safety
# ══════════════════════════════════════════════════════════════════════════


class TestThreadSafety:
    def test_concurrent_access(self):
        store = CacheStore(max_size=1000)
        errors = []

        def read_write(n):
            try:
                for i in range(n):
                    store.set(f"key-{i}", f"value-{i}")
                    store.get(f"key-{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=read_write, args=(50,)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
