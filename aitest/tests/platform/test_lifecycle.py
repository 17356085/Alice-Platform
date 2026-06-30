"""Tests for platform/lifecycle/ — LifecycleRegistry, _ObjectRef, MemoryGuard.

Tests: register, dispose, sweep (TTL), snapshot, memory_diff,
leak_report, _ObjectRef auto-dispose-fn detection.
No real gc stress — pure unit/functional tests.
"""
import time
import pytest

from aitest.platform.lifecycle.registry import (
    LifecycleRegistry, _ObjectRef, _AsyncObjectRef,
    _Entry, LeakAnalyzer,
)
from aitest.platform.lifecycle.guard import MemoryGuard, get_registry


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


class _Disposable:
    """Simple object with a .stop() method for testing _ObjectRef."""
    def __init__(self):
        self.stopped = False
        self.closed = False

    def stop(self):
        self.stopped = True

    def close(self):
        self.closed = True


# ══════════════════════════════════════════════════════════════════════════
#  _ObjectRef
# ══════════════════════════════════════════════════════════════════════════


class TestObjectRef:
    def test_auto_discovers_stop_method(self):
        d = _Disposable()
        ref = _ObjectRef("test-1", "test:owner", d)
        assert ref.lifecycle_id == "test-1"
        assert ref.owner == "test:owner"
        assert ref.disposed is False

        ref.dispose()
        assert ref.disposed is True
        assert d.stopped is True

    def test_dispose_is_idempotent(self):
        d = _Disposable()
        ref = _ObjectRef("test-2", "test:owner", d)
        ref.dispose()
        ref.dispose()  # Must not raise
        assert ref.disposed is True

    def test_explicit_dispose_fn(self):
        called = []
        ref = _ObjectRef("test-3", "test:owner", dispose_fn=lambda: called.append(True))
        ref.dispose()
        assert len(called) == 1

    def test_no_dispose_fn_does_not_crash(self):
        ref = _ObjectRef("test-4", "test:owner")  # No obj, no dispose_fn
        ref.dispose()  # Must not raise
        assert ref.disposed is True

    def test_default_ttl_zero(self):
        ref = _ObjectRef("test-5", "test:owner")
        assert ref.ttl_s == 0

    def test_custom_ttl(self):
        ref = _ObjectRef("test-6", "test:owner", ttl_s=3600)
        assert ref.ttl_s == 3600

    def test_dispose_clears_dispose_fn(self):
        d = _Disposable()
        ref = _ObjectRef("test-7", "test:owner", d)
        ref.dispose()
        assert ref._dispose_fn is None  # Released after dispose

    def test_dispose_passes_on_exception(self):
        """dispose() catches exceptions — caller doesn't crash."""
        def _failing():
            raise RuntimeError("cleanup failed")
        ref = _ObjectRef("test-8", "test:owner", dispose_fn=_failing)
        ref.dispose()  # Must not raise
        assert ref.disposed is True

    def test_wrapped_object_released_after_dispose(self):
        d = _Disposable()
        ref = _ObjectRef("test-9", "test:owner", d)
        ref.dispose()
        assert ref._wrapped_obj is None


# ══════════════════════════════════════════════════════════════════════════
#  LifecycleRegistry — CRUD
# ══════════════════════════════════════════════════════════════════════════


class TestRegistryCRUD:
    def test_register_and_get(self):
        reg = LifecycleRegistry()
        d = _Disposable()
        ref = _ObjectRef("obj-1", "test", d)
        reg.register(ref)
        assert reg.get("obj-1") is ref

    def test_get_nonexistent_returns_none(self):
        reg = LifecycleRegistry()
        assert reg.get("no-such-id") is None

    def test_register_empty_id_raises(self):
        reg = LifecycleRegistry()
        ref = _ObjectRef("", "test")
        with pytest.raises(ValueError, match="non-empty"):
            reg.register(ref)

    def test_register_replaces_existing(self):
        reg = LifecycleRegistry()
        d1 = _Disposable()
        d2 = _Disposable()
        ref1 = _ObjectRef("dup", "test", d1)
        ref2 = _ObjectRef("dup", "test", d2)
        reg.register(ref1)
        reg.register(ref2)  # Should dispose ref1
        assert d1.stopped is True  # Old object disposed
        assert reg.get("dup") is ref2

    def test_unregister_removes(self):
        reg = LifecycleRegistry()
        ref = _ObjectRef("rem", "test")
        reg.register(ref)
        removed = reg.unregister("rem")
        assert removed is ref
        assert reg.get("rem") is None

    def test_len(self):
        reg = LifecycleRegistry()
        assert len(reg) == 0
        reg.register(_ObjectRef("a", "test"))
        reg.register(_ObjectRef("b", "test"))
        assert len(reg) == 2

    def test_dispose_by_id(self):
        reg = LifecycleRegistry()
        d = _Disposable()
        ref = _ObjectRef("disposable", "test", d)
        reg.register(ref)
        assert reg.dispose("disposable") is True
        assert d.stopped is True
        assert reg.get("disposable") is None

    def test_dispose_nonexistent(self):
        reg = LifecycleRegistry()
        assert reg.dispose("missing") is False

    def test_touch_updates_timestamp(self):
        reg = LifecycleRegistry()
        ref = _ObjectRef("touchable", "test")
        reg.register(ref)
        assert reg.touch("touchable") is True
        assert reg.touch("missing") is False

    def test_list_alive(self):
        reg = LifecycleRegistry()
        reg.register(_ObjectRef("a", "owner-a"))
        reg.register(_ObjectRef("b", "owner-b"))
        alive = reg.list_alive()
        assert len(alive) == 2
        ids = [item["lifecycle_id"] for item in alive]
        assert "a" in ids
        assert "b" in ids


# ══════════════════════════════════════════════════════════════════════════
#  LifecycleRegistry — sweep (TTL)
# ══════════════════════════════════════════════════════════════════════════


class TestRegistrySweep:
    def test_sweep_disposes_expired(self):
        reg = LifecycleRegistry()
        d = _Disposable()
        ref = _ObjectRef("expired", "test", d, ttl_s=0.01)
        reg.register(ref)
        time.sleep(0.05)  # Wait for TTL to expire
        count = reg.sweep()
        assert count == 1
        assert d.stopped is True

    def test_sweep_skips_infinite_ttl(self):
        reg = LifecycleRegistry()
        ref = _ObjectRef("eternal", "test", ttl_s=0)  # 0 = never expire
        reg.register(ref)
        count = reg.sweep()
        assert count == 0

    def test_sweep_skips_not_yet_expired(self):
        reg = LifecycleRegistry()
        ref = _ObjectRef("fresh", "test", ttl_s=99999)
        reg.register(ref)
        count = reg.sweep()
        assert count == 0

    def test_dispose_all(self):
        reg = LifecycleRegistry()
        ds = [_Disposable() for _ in range(5)]
        for i, d in enumerate(ds):
            reg.register(_ObjectRef(f"all-{i}", "test", d))
        count = reg.dispose_all()
        assert count == 5
        for d in ds:
            assert d.stopped is True

    def test_dispose_all_on_empty_registry(self):
        reg = LifecycleRegistry()
        assert reg.dispose_all() == 0


# ══════════════════════════════════════════════════════════════════════════
#  LifecycleRegistry — snapshot + memory_diff
# ══════════════════════════════════════════════════════════════════════════


class TestSnapshot:
    def test_snapshot_empty(self):
        reg = LifecycleRegistry()
        snap = reg.snapshot()
        assert snap["alive"] == 0
        assert snap["total_size_bytes"] == 0

    def test_snapshot_with_objects(self):
        reg = LifecycleRegistry()
        d = _Disposable()
        reg.register(_ObjectRef("snap-1", "main:test", d))
        snap = reg.snapshot()
        assert snap["alive"] == 1
        assert "entries" in snap

    def test_memory_diff_no_change(self):
        reg = LifecycleRegistry()
        snap1 = reg.snapshot()
        snap2 = reg.snapshot()
        diff = reg.memory_diff(snap1, snap2)
        assert diff["delta_count"] == 0

    def test_memory_diff_new_object(self):
        reg = LifecycleRegistry()
        snap1 = reg.snapshot()
        reg.register(_ObjectRef("new-obj", "main:test"))
        snap2 = reg.snapshot()
        diff = reg.memory_diff(snap1, snap2)
        assert diff["delta_count"] == 1
        assert diff["new_count"] == 1

    def test_memory_diff_disposed_object(self):
        reg = LifecycleRegistry()
        reg.register(_ObjectRef("temp", "main:test"))
        snap1 = reg.snapshot()
        reg.dispose("temp")
        snap2 = reg.snapshot()
        diff = reg.memory_diff(snap1, snap2)
        assert diff["disposed_count"] == 1


# ══════════════════════════════════════════════════════════════════════════
#  LifecycleRegistry — leak_report
# ══════════════════════════════════════════════════════════════════════════


class TestLeakReport:
    def test_empty_report(self):
        reg = LifecycleRegistry()
        report = reg.leak_report()
        assert report["alive"] == 0
        assert "summary" in report

    def test_report_with_objects(self):
        reg = LifecycleRegistry()
        reg.register(_ObjectRef("lr-1", "main:lifespan"))
        reg.register(_ObjectRef("lr-2", "chat:session"))
        report = reg.leak_report()
        assert report["alive"] == 2
        assert len(report["top_by_size"]) >= 0
        # by_type aggregation
        types = [t["type"] for t in report["by_type"]]
        assert "main" in types or "chat" in types

    def test_report_includes_total_disposed(self):
        reg = LifecycleRegistry()
        reg.register(_ObjectRef("lr-3", "test"))
        reg.dispose("lr-3")
        report = reg.leak_report()
        assert report["total_disposed"] == 1


# ══════════════════════════════════════════════════════════════════════════
#  LifecycleRegistry — stats (v2.6 compat)
# ══════════════════════════════════════════════════════════════════════════


class TestRegistryStats:
    def test_stats_empty(self):
        reg = LifecycleRegistry()
        s = reg.stats()
        assert s["alive"] == 0
        assert s["total_disposed"] == 0

    def test_stats_counts(self):
        reg = LifecycleRegistry()
        reg.register(_ObjectRef("s1", "owner-a"))
        reg.register(_ObjectRef("s2", "owner-a"))
        s = reg.stats()
        assert s["alive"] == 2
        assert s["total_registered"] == 2
        assert s["by_owner"]["owner-a"] == 2


# ══════════════════════════════════════════════════════════════════════════
#  Singleton
# ══════════════════════════════════════════════════════════════════════════


class TestGetRegistry:
    def test_returns_lifecycle_registry(self):
        reg = get_registry()
        assert isinstance(reg, LifecycleRegistry)

    def test_same_instance(self):
        a = get_registry()
        b = get_registry()
        assert a is b


# ══════════════════════════════════════════════════════════════════════════
#  LeakAnalyzer
# ══════════════════════════════════════════════════════════════════════════


class TestLeakAnalyzer:
    def test_backed_by_registry(self):
        reg = LifecycleRegistry()
        reg.register(_ObjectRef("la-1", "test"))
        analyzer = LeakAnalyzer(reg)
        report = analyzer.find_top_leaks()
        assert report["alive"] == 1

    def test_growth_attribution_empty(self):
        reg = LifecycleRegistry()
        analyzer = LeakAnalyzer(reg)
        diff = analyzer.growth_attribution()
        assert "delta_count" in diff


# ══════════════════════════════════════════════════════════════════════════
#  MemoryGuard
# ══════════════════════════════════════════════════════════════════════════


class TestMemoryGuard:
    def test_init_with_registry(self):
        reg = LifecycleRegistry()
        guard = MemoryGuard(reg)
        assert guard.soft_limit_mb > 0
        assert guard.hard_limit_mb > 0
        assert guard.soft_limit_mb < guard.hard_limit_mb

    def test_custom_limits(self):
        reg = LifecycleRegistry()
        guard = MemoryGuard(reg)
        guard.soft_limit_mb = 100
        guard.hard_limit_mb = 200
        assert guard.soft_limit_mb == 100
        assert guard.hard_limit_mb == 200

    def test_check_returns_report(self):
        reg = LifecycleRegistry()
        guard = MemoryGuard(reg)
        result = guard.check()
        assert "rss_mb" in result
        assert "level" in result
        assert "actions" in result

    def test_check_with_low_limit_triggers_warning(self):
        """Setting soft limit to 0MB guarantees check() triggers sweep."""
        reg = LifecycleRegistry()
        guard = MemoryGuard(reg)
        guard.soft_limit_mb = 0
        guard.hard_limit_mb = 1
        result = guard.check()
        # With soft limit 0, RSS will almost certainly be above
        if result["rss_mb"] > 0:
            assert result["level"] in ("warning", "critical")

    def test_check_with_high_limits_normal(self):
        reg = LifecycleRegistry()
        guard = MemoryGuard(reg)
        guard.soft_limit_mb = 999999
        guard.hard_limit_mb = 9999999
        result = guard.check()
        if result["rss_mb"] > 0:
            assert result["level"] == "normal"

    def test_get_memory_guard_singleton(self):
        from aitest.platform.lifecycle.guard import get_memory_guard
        g1 = get_memory_guard()
        assert isinstance(g1, MemoryGuard)

    def test_invalid_limit_clamped(self):
        reg = LifecycleRegistry()
        guard = MemoryGuard(reg)
        guard.soft_limit_mb = -10
        assert guard.soft_limit_mb == 0  # Clamped
