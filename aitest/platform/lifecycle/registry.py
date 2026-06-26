"""
Lifecycle Contract Layer — unified runtime GC + Memory Observatory. v2.7

Stage 4: allocation traces, size tracking, memory diff, retain chain analysis.

Three layers:
  LifecycleObject   — Protocol every resource holder satisfies
  LifecycleRegistry — Thread-safe tracker: register → sweep → dispose_all
                       + snapshot / diff / retain_chain / leak_report
  LeakAnalyzer      — Top growing objects, type attribution, root cause

Usage:
    from aitest.platform.lifecycle import get_registry

    registry = get_registry()

    # Register (unchanged from v2.6):
    registry.register(_ObjectRef("metrics-consumer", "main:lifespan", consumer))

    # ★ Memory observability (new in v2.7):
    report = registry.leak_report()          # top leaks, by type, by age
    chain  = registry.retain_chain("chat-session:abc")  # who holds this object
    snap1  = registry.snapshot()             # full memory snapshot
    # ... time passes ...
    snap2  = registry.snapshot()
    diff   = registry.memory_diff(snap1, snap2)  # attributed growth

Design:
  - Allocation stack traces captured at register() time (traceback.format_stack)
  - Object size estimated via sys.getsizeof (shallow) — lower bound
  - gc.get_referrers() used on-demand (expensive) for retain chain analysis
  - Memory diff uses snapshot comparison — no continuous monitoring overhead
  - All diagnostic methods are read-only, thread-safe, no side effects
"""

from __future__ import annotations

import asyncio
import gc
import sys
import threading
import time
import traceback
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Protocol, Optional, Callable, Any


# ══════════════════════════════════════════════════════════════════════════
#  Protocol
# ══════════════════════════════════════════════════════════════════════════

class LifecycleObject(Protocol):
    """Single contract for all resource-holding platform objects."""

    @property
    def lifecycle_id(self) -> str: ...
    @property
    def owner(self) -> str: ...
    @property
    def ttl_s(self) -> float: ...
    @property
    def disposed(self) -> bool: ...
    def dispose(self) -> None: ...


# ══════════════════════════════════════════════════════════════════════════
#  Internal entry — upgraded with allocation trace + size tracking
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class _Entry:
    obj: LifecycleObject
    registered_at: float          # time.monotonic()
    last_touched: float           # time.monotonic() — refreshed on get()
    created_stack: str = ""       # ★ v2.7: allocation traceback (who created this)
    wrapped_obj: Any = None       # ★ v2.7: underlying object for size estimation


def _capture_stack(skip_frames: int = 3) -> str:
    """Capture allocation stack trace as a compact string.

    skip_frames: how many internal frames to skip (register → _ObjectRef → caller).
    """
    stack = traceback.extract_stack()[:-skip_frames] if len(traceback.extract_stack()) > skip_frames else traceback.extract_stack()
    if not stack:
        return "(stack unavailable)"
    lines = []
    for frame in stack[-8:]:  # last 8 frames — enough to find the allocation site
        fname = frame.filename.replace("\\", "/")
        parts = fname.split("/")
        short = "/".join(parts[-2:]) if len(parts) >= 2 else fname
        lines.append(f"  {short}:{frame.lineno} in {frame.name}")
    return "\n".join(lines) if lines else "(stack unavailable)"


def _estimate_size(obj: Any) -> int:
    """Estimate shallow memory size of an object. Lower bound only.
    Returns 0 for objects that don't support sys.getsizeof."""
    try:
        return sys.getsizeof(obj)
    except (TypeError, AttributeError):
        return 0


def _safe_referrers(obj: Any, max_depth: int = 5, max_total: int = 50) -> list[dict]:
    """Walk gc.get_referrers() to build a retain chain. Bounded.

    Returns list of {type, id, repr, size, frame} dicts.
    max_depth: how many levels of referrers to trace.
    max_total: max total referrers to collect (safety limit).
    """
    results: list[dict] = []
    seen_ids: set[int] = set()
    current_level = [obj]
    seen_ids.add(id(obj))

    for depth in range(max_depth):
        if not current_level or len(results) >= max_total:
            break
        next_level = []
        for item in current_level:
            try:
                refs = gc.get_referrers(item)
            except Exception:
                continue
            for ref in refs:
                rid = id(ref)
                if rid in seen_ids:
                    continue
                seen_ids.add(rid)
                if len(results) >= max_total:
                    break
                rtype = type(ref).__name__
                # Skip uninteresting referrer types
                if rtype in ("frame", "cell", "_Entry", "dict", "list", "tuple", "set"):
                    # Only include dict if it has meaningful keys
                    if rtype == "dict" and isinstance(ref, dict):
                        keys = list(ref.keys())[:5]
                        if not keys:
                            continue
                    elif rtype != "dict":
                        continue
                rrepr = repr(ref)[:120]
                rsize = _estimate_size(ref)
                try:
                    rframe = traceback.extract_stack()[-3:]
                    rframe_str = ":".join(f"{f.name}:{f.lineno}" for f in rframe)
                except Exception:
                    rframe_str = ""
                results.append({
                    "depth": depth,
                    "type": rtype,
                    "id": rid,
                    "repr": rrepr,
                    "size_bytes": rsize,
                    "frame": rframe_str,
                })
                next_level.append(ref)
        current_level = next_level

    return results[:max_total]


# ══════════════════════════════════════════════════════════════════════════
#  Wrappers
# ══════════════════════════════════════════════════════════════════════════

class _ObjectRef:
    """Wrap any object with stop/close/destroy → LifecycleObject."""

    __slots__ = ("_id", "_owner", "_ttl_s", "_disposed", "_dispose_fn", "_wrapped_obj")
    _PASSTHROUGH_MARKER = object()

    def __init__(
        self,
        lifecycle_id: str,
        owner: str,
        obj: Any = _PASSTHROUGH_MARKER,
        *,
        dispose_fn: Callable[[], None] = None,
        ttl_s: float = 0,
    ):
        self._id = lifecycle_id
        self._owner = owner
        self._ttl_s = ttl_s
        self._disposed = False

        if obj is not self._PASSTHROUGH_MARKER:
            self._wrapped_obj = obj
        else:
            self._wrapped_obj = None

        if dispose_fn is not None:
            self._dispose_fn = dispose_fn
        elif obj is not self._PASSTHROUGH_MARKER:
            self._dispose_fn = (
                getattr(obj, "stop", None)
                or getattr(obj, "close", None)
                or getattr(obj, "destroy", None)
                or getattr(obj, "shutdown", None)
                or getattr(obj, "dispose", None)   # ★ v2.9: discover dispose() method
            )
        else:
            self._dispose_fn = None

        # ★ v2.9: Attach Owned marker for OwnershipChecker enforcement
        if obj is not self._PASSTHROUGH_MARKER and obj is not None:
            try:
                from aitest.platform.ownership import Owned as _Owned
                obj.__owned__ = _Owned(
                    lifecycle_id=lifecycle_id,
                    owner=owner,
                    created_stack=_capture_stack(skip_frames=4),
                )
            except (TypeError, AttributeError):
                pass  # Some objects don't support __owned__ (builtins, C extensions)

    @property
    def lifecycle_id(self) -> str:
        return self._id

    @property
    def owner(self) -> str:
        return self._owner

    @property
    def ttl_s(self) -> float:
        return self._ttl_s

    @ttl_s.setter
    def ttl_s(self, value: float):
        self._ttl_s = value

    @property
    def disposed(self) -> bool:
        return self._disposed

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        fn = self._dispose_fn
        self._dispose_fn = None
        self._wrapped_obj = None  # release wrapped object reference
        if fn is not None:
            try:
                fn()
            except Exception:
                pass


class _AsyncObjectRef(_ObjectRef):
    """_ObjectRef variant for async dispose functions."""

    __slots__ = ()

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        fn = self._dispose_fn
        self._dispose_fn = None
        self._wrapped_obj = None
        if fn is None:
            return

        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # ★ v2.9: tracked task — won't leak, supports cancel, TTL-bounded
                from aitest.platform.lifecycle import guarded_create_task
                guarded_create_task(
                    fn(),
                    owner=f"lifecycle:dispose:{self._id}",
                    lifecycle_id=f"dispose-task:{self._id}",
                    ttl_s=300,  # 5 min max for shutdown coroutines
                )
                return
        except RuntimeError:
            pass

        try:
            fn()
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════
#  Registry — upgraded with memory observability
# ══════════════════════════════════════════════════════════════════════════

class LifecycleRegistry:
    """Central tracker for all LifecycleObjects. Thread-safe.

    v2.7 adds: snapshot, memory_diff, retain_chain, leak_report.
    """

    def __init__(self):
        self._objects: dict[str, _Entry] = {}
        self._lock = threading.Lock()
        self._total_disposed: int = 0
        # Previous snapshot for diff (updated by snapshot())
        self._prev_snapshot: dict | None = None
        self._prev_snapshot_ts: float = 0.0

    # ── CRUD ──────────────────────────────────────────────────────────

    def register(self, obj: LifecycleObject) -> None:
        """Register a LifecycleObject. Captures allocation stack trace automatically."""
        lid = obj.lifecycle_id
        if not lid:
            raise ValueError("lifecycle_id must be non-empty")
        now = time.monotonic()
        with self._lock:
            existing = self._objects.get(lid)
            if existing is not None:
                self._dispose_entry(lid, existing)
            # ★ v2.7: extract wrapped object for size estimation
            wrapped = getattr(obj, "_wrapped_obj", None)
            self._objects[lid] = _Entry(
                obj=obj,
                registered_at=now,
                last_touched=now,
                created_stack=_capture_stack(skip_frames=3),
                wrapped_obj=wrapped,
            )

    def unregister(self, lifecycle_id: str) -> Optional[LifecycleObject]:
        with self._lock:
            entry = self._objects.pop(lifecycle_id, None)
            return entry.obj if entry else None

    def get(self, lifecycle_id: str) -> Optional[LifecycleObject]:
        with self._lock:
            entry = self._objects.get(lifecycle_id)
            if entry is not None:
                entry.last_touched = time.monotonic()
                return entry.obj
            return None

    def touch(self, lifecycle_id: str) -> bool:
        with self._lock:
            entry = self._objects.get(lifecycle_id)
            if entry is not None:
                entry.last_touched = time.monotonic()
                return True
            return False

    # ── Disposal ───────────────────────────────────────────────────────

    def dispose(self, lifecycle_id: str) -> bool:
        with self._lock:
            entry = self._objects.pop(lifecycle_id, None)
            if entry is None:
                return False
            self._dispose_entry(lifecycle_id, entry)
            return True

    def sweep(self) -> int:
        now = time.monotonic()
        expired_ids: list[str] = []
        with self._lock:
            for lid, entry in self._objects.items():
                ttl = entry.obj.ttl_s
                if ttl > 0 and (now - entry.last_touched) > ttl:
                    expired_ids.append(lid)
        count = 0
        for lid in expired_ids:
            if self.dispose(lid):
                count += 1
        return count

    def dispose_all(self) -> int:
        with self._lock:
            ids = list(self._objects.keys())
        count = 0
        for lid in ids:
            if self.dispose(lid):
                count += 1
        return count

    def _dispose_entry(self, lifecycle_id: str, entry: _Entry) -> None:
        try:
            entry.obj.dispose()
        except Exception:
            pass
        finally:
            self._total_disposed += 1

    # ── ★ v2.7: Memory Snapshot ────────────────────────────────────────

    def snapshot(self) -> dict:
        """Full memory snapshot — all alive objects with sizes, ages, stacks.

        Returns a dict suitable for diff comparison. Stores as _prev_snapshot
        for subsequent memory_diff() calls.
        """
        now = time.monotonic()
        with self._lock:
            entries = {}
            by_type: dict[str, dict] = defaultdict(lambda: {"count": 0, "total_size": 0, "max_age": 0})
            total_size = 0

            for lid, entry in self._objects.items():
                age_s = now - entry.registered_at
                idle_s = now - entry.last_touched
                ttl = entry.obj.ttl_s
                size = _estimate_size(entry.wrapped_obj) if entry.wrapped_obj else 0

                # Owner type (first segment before :)
                otype = entry.obj.owner.split(":")[0] if entry.obj.owner else "unknown"

                entries[lid] = {
                    "owner": entry.obj.owner,
                    "type": otype,
                    "ttl_s": ttl,
                    "age_s": round(age_s, 1),
                    "idle_s": round(idle_s, 1),
                    "size_bytes": size,
                    "disposed": entry.obj.disposed,
                    "expired": ttl > 0 and idle_s > ttl,
                    "created_stack": entry.created_stack,
                }
                total_size += size
                by_type[otype]["count"] += 1
                by_type[otype]["total_size"] += size
                by_type[otype]["max_age"] = max(by_type[otype]["max_age"], age_s)

            snap = {
                "ts": time.time(),
                "monotonic_ts": now,
                "alive": len(self._objects),
                "total_disposed": self._total_disposed,
                "total_size_bytes": total_size,
                "by_type": dict(by_type),
                "entries": entries,
            }

        # Store for subsequent diff
        self._prev_snapshot = snap
        self._prev_snapshot_ts = now
        return snap

    def memory_diff(
        self, snap1: dict | None = None, snap2: dict | None = None
    ) -> dict:
        """Compare two snapshots and attribute memory growth.

        If snap1/snap2 not provided, uses current vs previous snapshot.
        Returns: {delta_size, delta_count, new_objects, disposed_objects, grew, shrank}
        """
        if snap1 is None:
            snap1 = self._prev_snapshot or {"entries": {}, "alive": 0, "total_size_bytes": 0}
        if snap2 is None:
            snap2 = self.snapshot()

        e1 = snap1.get("entries", {})
        e2 = snap2.get("entries", {})

        ids1 = set(e1.keys())
        ids2 = set(e2.keys())

        new_ids = ids2 - ids1
        gone_ids = ids1 - ids2
        common_ids = ids1 & ids2

        delta_size = snap2.get("total_size_bytes", 0) - snap1.get("total_size_bytes", 0)
        delta_count = snap2.get("alive", 0) - snap1.get("alive", 0)

        # Growth attribution: which types grew most?
        by_type_growth: dict[str, int] = defaultdict(int)
        for lid in common_ids:
            sz1 = e1[lid].get("size_bytes", 0)
            sz2 = e2[lid].get("size_bytes", 0)
            delta = sz2 - sz1
            if delta != 0:
                otype = e2[lid].get("type", "unknown")
                by_type_growth[otype] += delta
        for lid in new_ids:
            otype = e2[lid].get("type", "unknown")
            by_type_growth[otype] += e2[lid].get("size_bytes", 0)

        # Top contributors
        growth_items = sorted(by_type_growth.items(), key=lambda x: -x[1])[:10]

        # Objects that grew the most
        grew: list[dict] = []
        for lid in common_ids:
            sz1 = e1[lid].get("size_bytes", 0)
            sz2 = e2[lid].get("size_bytes", 0)
            if sz2 > sz1:
                grew.append({
                    "lifecycle_id": lid,
                    "type": e2[lid].get("type", ""),
                    "size_before": sz1,
                    "size_after": sz2,
                    "delta": sz2 - sz1,
                })
        grew.sort(key=lambda x: -x["delta"])

        return {
            "ts": snap2.get("ts", 0),
            "delta_size_bytes": delta_size,
            "delta_count": delta_count,
            "total_size_bytes": snap2.get("total_size_bytes", 0),
            "alive": snap2.get("alive", 0),
            "new_count": len(new_ids),
            "disposed_count": len(gone_ids),
            "new_objects": sorted(list(new_ids))[:20],
            "disposed_objects": sorted(list(gone_ids))[:20],
            "growth_by_type": [{"type": t, "delta_bytes": d} for t, d in growth_items],
            "top_growing": grew[:15],
        }

    # ── ★ v2.7: Retain Chain Analysis ──────────────────────────────────

    def retain_chain(self, lifecycle_id: str, max_depth: int = 5) -> dict:
        """Find what's keeping an object alive. Uses gc.get_referrers().

        Returns {object_info, referrers: [...]} or {error: "..."} if not found.
        """
        with self._lock:
            entry = self._objects.get(lifecycle_id)
            if entry is None:
                return {"error": f"Object '{lifecycle_id}' not found in registry"}

            obj_info = {
                "lifecycle_id": lifecycle_id,
                "owner": entry.obj.owner,
                "type": type(entry.wrapped_obj).__name__ if entry.wrapped_obj else "unknown",
                "size_bytes": _estimate_size(entry.wrapped_obj) if entry.wrapped_obj else 0,
                "age_s": round(time.monotonic() - entry.registered_at, 1),
                "created_stack": entry.created_stack,
            }

            # Get referrers of the wrapped object (if available)
            target = entry.wrapped_obj if entry.wrapped_obj else entry.obj

        # Run gc.get_referrers outside lock — it can be slow
        referrers = _safe_referrers(target, max_depth=max_depth)

        return {
            "object": obj_info,
            "referrers": referrers,
            "total_referrers_found": len(referrers),
        }

    # ── ★ v2.7: Leak Report ────────────────────────────────────────────

    def leak_report(self, top_n: int = 20) -> dict:
        """Generate a comprehensive leak report.

        Returns:
          - top_by_size: largest objects
          - top_by_age: oldest objects
          - by_type: count + size per owner type
          - expired_not_disposed: TTL-expired objects that haven't been swept yet
          - summary: one-line diagnosis
        """
        now = time.monotonic()
        with self._lock:
            items = []
            for lid, entry in self._objects.items():
                ttl = entry.obj.ttl_s
                age_s = now - entry.registered_at
                idle_s = now - entry.last_touched
                size = _estimate_size(entry.wrapped_obj) if entry.wrapped_obj else 0
                items.append({
                    "lifecycle_id": lid,
                    "owner": entry.obj.owner,
                    "type": entry.obj.owner.split(":")[0] if entry.obj.owner else "?",
                    "ttl_s": ttl,
                    "age_s": round(age_s, 1),
                    "idle_s": round(idle_s, 1),
                    "size_bytes": size,
                    "disposed": entry.obj.disposed,
                    "expired": ttl > 0 and idle_s > ttl,
                    "created_stack": entry.created_stack,
                })

        # Top by size
        by_size = sorted(items, key=lambda x: -x["size_bytes"])[:top_n]

        # Top by age
        by_age = sorted(items, key=lambda x: -x["age_s"])[:top_n]

        # By type aggregation
        by_type: dict[str, dict] = defaultdict(lambda: {"count": 0, "total_size": 0, "max_age": 0, "max_idle": 0})
        for it in items:
            t = it["type"]
            by_type[t]["count"] += 1
            by_type[t]["total_size"] += it["size_bytes"]
            by_type[t]["max_age"] = max(by_type[t]["max_age"], it["age_s"])
            by_type[t]["max_idle"] = max(by_type[t]["max_idle"], it["idle_s"])
        by_type_sorted = sorted(by_type.items(), key=lambda x: -x[1]["total_size"])

        # Expired but not yet swept
        expired = [it for it in items if it["expired"] and not it["disposed"]]
        expired.sort(key=lambda x: -x["idle_s"])
        expired = expired[:top_n]

        # Summary diagnosis
        total_size = sum(it["size_bytes"] for it in items)
        summary = (
            f"{len(items)} objects alive, {total_size:,} bytes total, "
            f"{len(expired)} TTL-expired pending sweep. "
            f"Top type: {by_type_sorted[0][0]} ({by_type_sorted[0][1]['count']} instances, "
            f"{by_type_sorted[0][1]['total_size']:,} bytes)"
            if by_type_sorted else f"{len(items)} objects alive, {total_size:,} bytes."
        )

        return {
            "ts": time.time(),
            "summary": summary,
            "alive": len(items),
            "total_size_bytes": total_size,
            "total_disposed": self._total_disposed,
            "top_by_size": by_size,
            "top_by_age": by_age,
            "by_type": [{"type": t, **d} for t, d in by_type_sorted],
            "expired_not_disposed": expired,
        }

    # ── Diagnostics (v2.6 compat) ──────────────────────────────────────

    def stats(self) -> dict:
        now = time.monotonic()
        with self._lock:
            expired_pending = 0
            by_owner: dict[str, int] = {}
            entries = {}
            for lid, entry in self._objects.items():
                ttl = entry.obj.ttl_s
                age_s = now - entry.registered_at
                idle_s = now - entry.last_touched
                is_expired = ttl > 0 and idle_s > ttl
                if is_expired:
                    expired_pending += 1
                owner = entry.obj.owner or "unknown"
                by_owner[owner] = by_owner.get(owner, 0) + 1
                entries[lid] = {
                    "owner": owner,
                    "ttl_s": ttl,
                    "age_s": round(age_s, 1),
                    "idle_s": round(idle_s, 1),
                    "disposed": entry.obj.disposed,
                    "expired": is_expired,
                }
            return {
                "total_registered": len(self._objects) + self._total_disposed,
                "alive": len(self._objects),
                "total_disposed": self._total_disposed,
                "expired_pending": expired_pending,
                "by_owner": by_owner,
                "entries": entries,
            }

    def list_alive(self) -> list[dict]:
        return [
            {"lifecycle_id": lid, "owner": e.obj.owner, "ttl_s": e.obj.ttl_s}
            for lid, e in self._objects.items()
        ]

    def __len__(self) -> int:
        with self._lock:
            return len(self._objects)


# ══════════════════════════════════════════════════════════════════════════
#  ★ v2.7: LeakAnalyzer — standalone diagnostic tool
# ══════════════════════════════════════════════════════════════════════════

class LeakAnalyzer:
    """Standalone leak analysis backed by a LifecycleRegistry.

    Can be used from CLI, API endpoints, or tests without holding the registry lock.
    """

    def __init__(self, registry: LifecycleRegistry):
        self._registry = registry

    def find_top_leaks(self, top_n: int = 20) -> dict:
        """Alias for registry.leak_report()."""
        return self._registry.leak_report(top_n=top_n)

    def find_retain_chain(self, lifecycle_id: str) -> dict:
        """Find what's keeping a specific object alive."""
        return self._registry.retain_chain(lifecycle_id)

    def compare_snapshots(self, snap1: dict, snap2: dict) -> dict:
        """Attribute memory growth between two snapshots."""
        return self._registry.memory_diff(snap1, snap2)

    def growth_attribution(self) -> dict:
        """Compare current state vs previous snapshot. Returns attributed growth."""
        return self._registry.memory_diff()

    @staticmethod
    def top_gc_objects(limit: int = 20) -> list[dict]:
        """Use gc.get_objects() to find largest objects in the entire process.
        This is a heavy operation — only for debugging."""
        objs = gc.get_objects()
        sized = []
        for o in objs[:50000]:  # safety cap
            try:
                sz = sys.getsizeof(o)
                if sz > 1024:  # only objects > 1KB
                    sized.append((type(o).__name__, sz, repr(o)[:80], id(o)))
            except Exception:
                pass
        sized.sort(key=lambda x: -x[1])
        return [
            {"type": t, "size_bytes": s, "repr": r, "id": i}
            for t, s, r, i in sized[:limit]
        ]


# ══════════════════════════════════════════════════════════════════════════
#  ★ v2.8: MemoryGuard — enforcement, not observation
# ══════════════════════════════════════════════════════════════════════════

# Default limits — override via env vars
_MEMORY_SOFT_LIMIT_MB = int(__import__('os').environ.get("MEMORY_SOFT_LIMIT_MB", "500"))
_MEMORY_HARD_LIMIT_MB = int(__import__('os').environ.get("MEMORY_HARD_LIMIT_MB", "800"))
_MEMORY_CHECK_INTERVAL_S = int(__import__('os').environ.get("MEMORY_CHECK_INTERVAL_S", "30"))
