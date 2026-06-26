"""Lifecycle Contract Layer — unified runtime GC + Memory Observatory. v2.7

Split from lifecycle.py (P2-1, 2026-06-25). Original 1,043 lines → 3 files.
"""
from .registry import (
    LifecycleObject, _Entry, _ObjectRef, _AsyncObjectRef,
    LifecycleRegistry, LeakAnalyzer,
    _capture_stack, _estimate_size, _safe_referrers,
    get_registry,
)
from .guard import (
    _get_process_rss_mb, MemoryGuard, get_memory_guard,
    _GuardedTask, guarded_create_task,
)

__all__ = [
    "LifecycleObject",
    "_Entry",
    "_ObjectRef",
    "_AsyncObjectRef",
    "LifecycleRegistry",
    "LeakAnalyzer",
    "_capture_stack",
    "_estimate_size",
    "_safe_referrers",
    "get_registry",
    "_get_process_rss_mb",
    "MemoryGuard",
    "get_memory_guard",
    "_GuardedTask",
    "guarded_create_task",
]
