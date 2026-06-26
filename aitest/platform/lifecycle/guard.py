"""MemoryGuard + _GuardedTask — runtime GC enforcement. v2.7

Extracted from lifecycle.py (P2-1 split, 2026-06-25).
"""
from __future__ import annotations
import asyncio
import gc
import os
import sys
import time
import threading

from .registry import (
    LifecycleRegistry,
    _MEMORY_SOFT_LIMIT_MB, _MEMORY_HARD_LIMIT_MB, _MEMORY_CHECK_INTERVAL_S,
)

def _get_process_rss_mb() -> float:
    """Get current process RSS in MB. Tries psutil, then /proc, then resource.

    Returns 0 if all methods fail (graceful degradation on obscure platforms).
    """
    # Method 1: psutil (cross-platform, accurate)
    try:
        import psutil
        proc = psutil.Process()
        return proc.memory_info().rss / (1024 * 1024)
    except ImportError:
        pass
    except Exception:
        pass

    # Method 2: /proc/self/status (Linux)
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    # Format: "VmRSS:    123456 kB"
                    parts = line.split()
                    if len(parts) >= 2:
                        return float(parts[1]) / 1024  # kB → MB
    except Exception:
        pass

    # Method 3: resource module (Unix)
    try:
        import resource
        rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        # On macOS, ru_maxrss is in bytes; on Linux, it's in KB
        if sys.platform == "darwin":
            return rss / (1024 * 1024)
        else:
            return rss / 1024
    except Exception:
        pass

    return 0.0  # Unknown — guard won't trigger, but won't crash either


class MemoryGuard:
    """Memory enforcement — threshold monitoring + cascade disposal.

    Not observation. Control.

    Strategy:
      Soft limit (e.g., 500 MB): log warning, aggressive sweep, notify
      Hard limit (e.g., 800 MB): cascade dispose largest→oldest, force gc.collect()

    Config via env:
      MEMORY_SOFT_LIMIT_MB  — warning threshold (default 500)
      MEMORY_HARD_LIMIT_MB  — emergency threshold (default 800)
      MEMORY_CHECK_INTERVAL_S — check cadence (default 30)

    Usage:
        guard = MemoryGuard(registry)
        result = guard.check()  # → {rss_mb, level, actions_taken, ...}
    """

    def __init__(self, registry: LifecycleRegistry):
        self._registry = registry
        self._soft_limit_mb = _MEMORY_SOFT_LIMIT_MB
        self._hard_limit_mb = _MEMORY_HARD_LIMIT_MB
        self._last_check_ts = 0.0
        self._check_count = 0
        self._cascade_count = 0
        self._total_disposed_by_guard = 0

    @property
    def soft_limit_mb(self) -> float:
        return self._soft_limit_mb

    @soft_limit_mb.setter
    def soft_limit_mb(self, value: float):
        self._soft_limit_mb = max(0, value)

    @property
    def hard_limit_mb(self) -> float:
        return self._hard_limit_mb

    @hard_limit_mb.setter
    def hard_limit_mb(self, value: float):
        self._hard_limit_mb = max(0, value)

    def check(self) -> dict:
        """Check memory and enforce limits. Returns action report.

        Called periodically from the sweep loop (every 60s by default).
        Can also be called manually via /api/debug/memory/control.
        """
        self._check_count += 1
        self._last_check_ts = time.monotonic()
        rss_mb = _get_process_rss_mb()
        actions: list[str] = []

        if rss_mb <= 0:
            return {
                "rss_mb": rss_mb, "level": "unknown",
                "soft_limit_mb": self._soft_limit_mb,
                "hard_limit_mb": self._hard_limit_mb,
                "actions": ["rss_unavailable"],
            }

        level = "normal"

        # ── Soft limit: aggressive sweep + warning ──────────────────
        if rss_mb >= self._soft_limit_mb and rss_mb < self._hard_limit_mb:
            level = "warning"
            swept = self._registry.sweep()
            if swept > 0:
                actions.append(f"sweep_disposed_{swept}")
                self._total_disposed_by_guard += swept
            else:
                actions.append("sweep_no_effect")
            # Force Python GC as secondary measure
            collected = gc.collect()
            if collected > 0:
                actions.append(f"gc_collected_{collected}")

        # ── Hard limit: cascade dispose + gc ────────────────────────
        elif rss_mb >= self._hard_limit_mb:
            level = "critical"
            self._cascade_count += 1

            # Phase 1: Sweep TTL-expired
            swept = self._registry.sweep()
            if swept > 0:
                actions.append(f"sweep_disposed_{swept}")
                self._total_disposed_by_guard += swept

            # Phase 2: Dispose largest objects first
            disposed = self._dispose_largest(limit=10)
            if disposed > 0:
                actions.append(f"largest_disposed_{disposed}")
                self._total_disposed_by_guard += disposed

            # Phase 3: Dispose oldest objects
            disposed = self._dispose_oldest(limit=10)
            if disposed > 0:
                actions.append(f"oldest_disposed_{disposed}")
                self._total_disposed_by_guard += disposed

            # Phase 4: Force full GC
            collected = gc.collect()
            if collected > 0:
                actions.append(f"gc_collected_{collected}")

        return {
            "rss_mb": round(rss_mb, 1),
            "level": level,
            "soft_limit_mb": self._soft_limit_mb,
            "hard_limit_mb": self._hard_limit_mb,
            "actions": actions,
            "total_disposed_by_guard": self._total_disposed_by_guard,
            "cascade_events": self._cascade_count,
        }

    def _dispose_largest(self, limit: int) -> int:
        """Dispose the N largest alive objects. Returns count disposed."""
        now = time.monotonic()
        with self._registry._lock:
            sized = []
            for lid, entry in self._registry._objects.items():
                if entry.obj.ttl_s == 0:
                    continue  # Skip manual-only objects (consumers, etc.)
                size = _estimate_size(entry.wrapped_obj) if entry.wrapped_obj else 0
                sized.append((lid, size))
        sized.sort(key=lambda x: -x[1])
        count = 0
        for lid, _ in sized[:limit]:
            if self._registry.dispose(lid):
                count += 1
        return count

    def _dispose_oldest(self, limit: int) -> int:
        """Dispose the N oldest alive objects. Returns count disposed."""
        now = time.monotonic()
        with self._registry._lock:
            aged = []
            for lid, entry in self._registry._objects.items():
                if entry.obj.ttl_s == 0:
                    continue
                age = now - entry.registered_at
                aged.append((lid, age))
        aged.sort(key=lambda x: -x[1])
        count = 0
        for lid, _ in aged[:limit]:
            if self._registry.dispose(lid):
                count += 1
        return count


# ══════════════════════════════════════════════════════════════════════════
#  ★ v2.8: Task Guardrail — async tasks must bind to lifecycle
# ══════════════════════════════════════════════════════════════════════════

class _GuardedTask:
    """Wrapper around an asyncio.Task that registers itself in the LifecycleRegistry.

    On completion or cancellation, auto-unregisters. This prevents the
    fire-and-forget pattern from leaking unobservable tasks.
    """

    __slots__ = ("_task", "_lifecycle_id", "_done")

    def __init__(self, task: asyncio.Task, lifecycle_id: str, owner: str, ttl_s: float = 0):
        self._task = task
        self._lifecycle_id = lifecycle_id
        self._done = False

        # Register in lifecycle registry
        try:
            get_registry().register(_ObjectRef(
                lifecycle_id,
                owner,
                dispose_fn=self._cancel_and_cleanup,
                ttl_s=ttl_s,
            ))
        except Exception:
            pass

        # Auto-unregister on completion
        task.add_done_callback(self._on_done)

    def _on_done(self, _task: asyncio.Task) -> None:
        if self._done:
            return
        self._done = True
        try:
            get_registry().unregister(self._lifecycle_id)
        except Exception:
            pass

    def _cancel_and_cleanup(self) -> None:
        """Dispose callback: cancel the task if still running."""
        if not self._done and not self._task.done():
            self._task.cancel()
        self._on_done(self._task)

    @property
    def task(self) -> asyncio.Task:
        return self._task


def guarded_create_task(
    coro,
    *,
    owner: str,
    lifecycle_id: str = "",
    ttl_s: float = 0,
) -> asyncio.Task:
    """Create an asyncio.Task that is registered in the LifecycleRegistry.

    Unlike bare asyncio.create_task(), this:
      - Registers the task in the LifecycleRegistry (observable)
      - Auto-unregisters on completion (no leak)
      - Supports TTL-based auto-cancel (enforcement)
      - Survives fire-and-forget without losing track

    Args:
        coro: Coroutine to schedule
        owner: Who created this task (e.g., "onboarding:start", "chat:stream")
        lifecycle_id: Unique ID (auto-generated if empty)
        ttl_s: If > 0, task will be cancelled if it exceeds this duration

    Returns:
        The asyncio.Task (can be awaited or ignored)

    Usage:
        # Instead of:
        asyncio.create_task(self._run(...))

        # Use:
        guarded_create_task(self._run(...), owner="onboarding:start", ttl_s=7200)
    """
    import uuid as _uuid
    task = asyncio.create_task(coro)

    if not lifecycle_id:
        lifecycle_id = f"task:{owner}:{_uuid.uuid4().hex[:8]}"

    # _GuardedTask binds the task to the registry — auto-cleanup on done
    _GuardedTask(task, lifecycle_id, owner, ttl_s=ttl_s)
    return task


# ══════════════════════════════════════════════════════════════════════════
#  Singleton
# ══════════════════════════════════════════════════════════════════════════

_registry: Optional[LifecycleRegistry] = None
_registry_lock = threading.Lock()

_guard: Optional[MemoryGuard] = None
_guard_lock = threading.Lock()


def get_registry() -> LifecycleRegistry:
    global _registry
    with _registry_lock:
        if _registry is None:
            _registry = LifecycleRegistry()
        return _registry


def get_memory_guard() -> MemoryGuard:
    """Get or create the global MemoryGuard singleton.
    Requires get_registry() to have been called first."""
    global _guard
    with _guard_lock:
        if _guard is None:
            _guard = MemoryGuard(get_registry())
        return _guard
