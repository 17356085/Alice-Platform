"""Tests for platform/ttl_set.py — bounded, time-aware idempotency tracker.

Tests: add (dedup), contains, eviction (max_size + TTL),
cleanup, thread safety, clear, edge cases.
"""
import time
import threading
import pytest

from aitest.platform.ttl_set import TTLSet


# ══════════════════════════════════════════════════════════════════════════
#  add — first-time vs duplicate
# ══════════════════════════════════════════════════════════════════════════


class TestAdd:
    def test_first_time_returns_true(self):
        s = TTLSet(max_age_s=999999)
        assert s.add("key-1") is True

    def test_duplicate_returns_false(self):
        s = TTLSet(max_age_s=999999)
        s.add("key-1")
        assert s.add("key-1") is False

    def test_multiple_unique_keys(self):
        s = TTLSet(max_age_s=999999)
        assert s.add("a") is True
        assert s.add("b") is True
        assert s.add("c") is True
        assert len(s) == 3

    def test_expired_key_treated_as_new(self):
        s = TTLSet(max_age_s=0.01)  # 10ms TTL
        s.add("key-1")
        time.sleep(0.05)
        assert s.add("key-1") is True  # Expired → new


# ══════════════════════════════════════════════════════════════════════════
#  contains
# ══════════════════════════════════════════════════════════════════════════


class TestContains:
    def test_contains_existing(self):
        s = TTLSet(max_age_s=999999)
        s.add("key-1")
        assert "key-1" in s

    def test_contains_missing(self):
        s = TTLSet(max_age_s=999999)
        assert "nonexistent" not in s

    def test_contains_expired_returns_false(self):
        s = TTLSet(max_age_s=0.01)
        s.add("key-1")
        time.sleep(0.05)
        assert "key-1" not in s


# ══════════════════════════════════════════════════════════════════════════
#  eviction — max_size
# ══════════════════════════════════════════════════════════════════════════


class TestEviction:
    def test_evicts_oldest_when_full(self):
        s = TTLSet(max_size=3, max_age_s=999999)
        s.add("a")
        s.add("b")
        s.add("c")
        assert len(s) == 3
        s.add("d")  # Should evict "a" (oldest)
        assert len(s) == 3
        assert "a" not in s
        assert "b" in s
        assert "c" in s
        assert "d" in s

    def test_fifo_eviction_order(self):
        s = TTLSet(max_size=2, max_age_s=999999)
        s.add("first")
        s.add("second")
        s.add("third")  # Evicts "first"
        assert "first" not in s
        assert "second" in s
        assert "third" in s

    def test_len_reflects_current_size(self):
        s = TTLSet(max_size=100, max_age_s=999999)
        for i in range(50):
            s.add(f"key-{i}")
        assert len(s) == 50


# ══════════════════════════════════════════════════════════════════════════
#  cleanup
# ══════════════════════════════════════════════════════════════════════════


class TestCleanup:
    def test_removes_expired(self):
        s = TTLSet(max_age_s=0.01)
        s.add("expired")
        time.sleep(0.05)
        removed = s.cleanup()
        assert removed >= 1
        assert len(s) == 0

    def test_keeps_fresh(self):
        s = TTLSet(max_age_s=999999)
        s.add("fresh")
        assert s.cleanup() == 0
        assert len(s) == 1

    def test_mixed_cleanup(self):
        s = TTLSet(max_age_s=0.01)
        s.add("old")
        time.sleep(0.05)  # "old" expires
        s.add("keep")     # Still fresh
        removed = s.cleanup()
        assert removed >= 1
        assert "old" not in s
        assert "keep" in s


# ══════════════════════════════════════════════════════════════════════════
#  clear
# ══════════════════════════════════════════════════════════════════════════


class TestClear:
    def test_clear_empties_set(self):
        s = TTLSet(max_age_s=999999)
        s.add("a")
        s.add("b")
        s.clear()
        assert len(s) == 0
        assert "a" not in s

    def test_clear_then_reuse(self):
        s = TTLSet(max_age_s=999999)
        s.add("a")
        s.clear()
        assert s.add("a") is True  # Same key works after clear


# ══════════════════════════════════════════════════════════════════════════
#  Construction + Properties
# ══════════════════════════════════════════════════════════════════════════


class TestConstruction:
    def test_defaults(self):
        s = TTLSet()
        assert s.max_size == 10_000
        assert s.max_age_s == 86_400.0

    def test_custom_limits(self):
        s = TTLSet(max_size=500, max_age_s=3600)
        assert s.max_size == 500
        assert s.max_age_s == 3600

    def test_max_size_must_be_positive(self):
        with pytest.raises(ValueError, match="max_size"):
            TTLSet(max_size=0)


# ══════════════════════════════════════════════════════════════════════════
#  Thread safety
# ══════════════════════════════════════════════════════════════════════════


class TestThreadSafety:
    def test_concurrent_adds(self):
        s = TTLSet(max_size=10_000, max_age_s=999999)
        errors = []

        def add_keys(start: int, count: int):
            try:
                for i in range(start, start + count):
                    s.add(f"key-{i}")
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=add_keys, args=(i * 100, 100))
            for i in range(5)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0
        assert len(s) == 500
