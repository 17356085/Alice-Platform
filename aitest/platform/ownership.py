"""
Ownership Enforcement Layer — single-owner guarantee. v1.0

Core invariant: every platform object has exactly ONE owner → LifecycleRegistry.
No external strong reference may survive owner disposal.

Rules enforced at runtime:
  1. Owned objects: registry is sole strong holder
  2. Module-level dicts: must use OwnedDict, not bare dict
  3. Event subscriptions: bind to owner lifecycle → auto-unsubscribe on dispose
  4. asyncio Tasks: tracked + cancellable + bound to lifecycle
  5. OwnershipChecker: periodic scan → alarm on external refs

Usage:
    from aitest.platform.ownership import OwnedDict, BoundSubscription, OwnershipChecker

    # Instead of: sessions = {}
    sessions = OwnedDict("chat-sessions", owner="chat:module", ttl_s=1800)

    # Instead of: bus.subscribe(et, callback)
    sub = BoundSubscription(bus, et, callback, owner_id="chat-session:abc")
    # ... when owner disposed, sub.dispose() auto-unsubscribes

    # Periodic check:
    checker = OwnershipChecker()
    violations = checker.scan()  # → list of {object, external_refs, location}
"""

from __future__ import annotations

import gc
import sys
import threading
import time
import traceback
import weakref
from dataclasses import dataclass, field
from typing import Any, Callable, Generic, Optional, Protocol, TypeVar
from aitest.infra.logging import get_logger
_log = get_logger(__name__)


# ══════════════════════════════════════════════════════════════════════════
#  Owned — declare single ownership
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class Owned:
    """Marker + metadata for an object owned by LifecycleRegistry.

    Attach to any object to declare: 'only the registry holds a strong ref to me.'
    OwnershipChecker will flag any external strong reference.

    Usage:
        obj = SomeLargeObject()
        obj.__owned__ = Owned(
            lifecycle_id="chat-session:abc",
            owner="chat:create_session",
            created_stack=traceback.format_stack(),
        )
        get_registry().register(_ObjectRef("chat-session:abc", "chat:create_session", obj))
    """

    lifecycle_id: str
    owner: str
    created_at: float = field(default_factory=time.monotonic)
    created_stack: str = ""
    _disposed: bool = False

    def dispose(self):
        self._disposed = True


# Sentinel for "not owned"
_NOT_OWNED = Owned(lifecycle_id="", owner="", created_at=0)


def _get_owned(obj: Any) -> Owned | None:
    """Extract Owned metadata from an object. Returns None if not owned."""
    owned = getattr(obj, "__owned__", None)
    if owned is not None and not owned._disposed:
        return owned
    return None


# ══════════════════════════════════════════════════════════════════════════
#  OwnedDict — dict whose values are lifecycle-tracked
# ══════════════════════════════════════════════════════════════════════════

K = TypeVar("K")
V = TypeVar("V")


class OwnedDict(Generic[K, V]):
    """Mutable mapping whose values are owned by LifecycleRegistry.

    Replaces bare module-level `sessions = {}` patterns.
    Every value is auto-registered on insert. Every key removal triggers dispose.
    On dispose_all(), all values are disposed and internal dict is cleared.

    Usage:
        sessions = OwnedDict("chat-sessions", owner="chat:module", ttl_s=1800)

        sessions["abc"] = ChatSession(...)      # auto-registered
        sid = sessions["abc"]                    # normal access, refreshes TTL
        del sessions["abc"]                      # dispose + unregister
        sessions.dispose_all()                   # shutdown: dispose all + clear
    """

    def __init__(
        self,
        name: str,
        *,
        owner: str,
        ttl_s: float = 0,
        max_size: int = 0,
    ):
        self._name = name
        self._owner = owner
        self._ttl_s = ttl_s
        self._max_size = max_size  # 0 = unbounded
        self._lock = threading.Lock()
        self._data: dict[str, Any] = {}

    # ── Dict interface ─────────────────────────────────────────────────

    def __getitem__(self, key: str) -> Any:
        with self._lock:
            val = self._data[key]
            self._touch(key)
            return val

    def __setitem__(self, key: str, value: Any):
        with self._lock:
            # Dispose old value if key exists
            old = self._data.get(key)
            if old is not None:
                self._dispose_value(key, old)

            # Enforce max_size
            if self._max_size > 0 and len(self._data) >= self._max_size:
                oldest = next(iter(self._data))
                old_val = self._data.pop(oldest)
                self._dispose_value(oldest, old_val)

            self._data[key] = value
            self._register_value(key, value)

    def __delitem__(self, key: str):
        with self._lock:
            val = self._data.pop(key)
            self._dispose_value(key, val)

    def __contains__(self, key: str) -> bool:
        with self._lock:
            return key in self._data

    def __len__(self) -> int:
        with self._lock:
            return len(self._data)

    def __iter__(self):
        with self._lock:
            return iter(list(self._data.keys()))

    def get(self, key: str, default=None) -> Any:
        try:
            return self[key]
        except KeyError:
            return default

    def pop(self, key: str, default=None) -> Any:
        with self._lock:
            val = self._data.pop(key, default)
            if val is not default:
                self._dispose_value(key, val)
            return val

    def items(self):
        with self._lock:
            return list(self._data.items())

    def values(self):
        with self._lock:
            return list(self._data.values())

    def keys(self):
        with self._lock:
            return list(self._data.keys())

    # ── Lifecycle ──────────────────────────────────────────────────────

    def _register_value(self, key: str, value: Any):
        """Register value in LifecycleRegistry. Auto-discovers dispose method.
        Uses _AsyncObjectRef if dispose_fn is a coroutine function."""
        import asyncio as _asyncio

        try:
            from aitest.platform.lifecycle import (
                get_registry, _ObjectRef, _AsyncObjectRef,
            )

            lifecycle_id = f"{self._name}:{key}"
            owner = f"{self._owner}:{key}"

            # Find dispose method (sync or async)
            dispose_fn = (
                getattr(value, "destroy", None)
                or getattr(value, "dispose", None)
                or getattr(value, "stop", None)
                or getattr(value, "close", None)
                or getattr(value, "shutdown", None)
                or getattr(value, "_release_resources", None)  # ProjectOnboardingAgent pattern
            )

            # Attach ownership marker
            try:
                value.__owned__ = Owned(
                    lifecycle_id=lifecycle_id,
                    owner=owner,
                    created_stack="".join(
                        traceback.format_list(traceback.extract_stack()[-6:-1])
                    ),
                )
            except (TypeError, AttributeError):
                pass  # Some objects don't support __owned__ (builtins)

            # Use _AsyncObjectRef for coroutine dispose functions
            if _asyncio.iscoroutinefunction(dispose_fn):
                get_registry().register(_AsyncObjectRef(
                    lifecycle_id,
                    owner,
                    obj=value,
                    dispose_fn=dispose_fn,
                    ttl_s=self._ttl_s,
                ))
            else:
                get_registry().register(_ObjectRef(
                    lifecycle_id,
                    owner,
                    obj=value,
                    dispose_fn=dispose_fn,
                    ttl_s=self._ttl_s,
                ))
        except Exception:
            pass

    def _dispose_value(self, key: str, value: Any):
        """Dispose a value: mark owned as disposed, call lifecycle dispose."""
        # Mark ownership as disposed
        owned = _get_owned(value)
        if owned:
            owned.dispose()

        # Call lifecycle dispose (pops from registry + calls dispose_fn)
        try:
            from aitest.platform.lifecycle import get_registry
            get_registry().dispose(f"{self._name}:{key}")
        except Exception:
            pass

    def _touch(self, key: str):
        """Refresh TTL in lifecycle registry."""
        try:
            from aitest.platform.lifecycle import get_registry
            get_registry().touch(f"{self._name}:{key}")
        except Exception:
            pass

    def dispose_all(self):
        """Dispose all values. Called at shutdown."""
        with self._lock:
            for key in list(self._data.keys()):
                val = self._data.pop(key)
                self._dispose_value(key, val)

    @property
    def name(self) -> str:
        return self._name


# ══════════════════════════════════════════════════════════════════════════
#  BoundSubscription — event sub that binds to owner lifecycle
# ══════════════════════════════════════════════════════════════════════════

class BoundSubscription:
    """Event subscription that auto-unsubscribes when owner is disposed.

    Bridges EventBus/ObservationBus with LifecycleRegistry.
    When the owner (identified by lifecycle_id) is disposed, the subscription
    is automatically unsubscribed — no manual cleanup needed.

    Usage:
        sub = BoundSubscription(
            bus=observation_bus,
            event_type=EventType.SKILL_COMPLETE,
            callback=my_handler,
            owner_id="agent:my-agent:run-abc",
        )
        sub.activate()   # subscribes
        # ... later, when owner disposed:
        sub.dispose()    # unsubscribes (idempotent)
    """

    def __init__(
        self,
        bus: Any,
        event_type: Any,
        callback: Callable,
        *,
        owner_id: str,
    ):
        self._bus = bus
        self._event_type = event_type
        self._callback = callback
        self._owner_id = owner_id
        self._active = False

        # Register in LifecycleRegistry so that when owner is swept,
        # this subscription is disposed too
        try:
            from aitest.platform.lifecycle import get_registry, _ObjectRef
            get_registry().register(_ObjectRef(
                f"subscription:{owner_id}:{_safe_event_name(event_type)}",
                f"subscription:{owner_id}",
                dispose_fn=self.dispose,
                ttl_s=0,  # Manual — disposed when owner is disposed
            ))
        except Exception:
            pass

    def activate(self):
        """Subscribe to the event bus. Idempotent."""
        if self._active:
            return
        self._active = True
        try:
            self._bus.subscribe(self._event_type, self._callback)
        except Exception:
            pass

    def dispose(self):
        """Unsubscribe from the event bus. Idempotent."""
        if not self._active:
            return
        self._active = False
        try:
            self._bus.unsubscribe(self._event_type, self._callback)
        except Exception:
            pass
        # Unregister self from lifecycle
        try:
            from aitest.platform.lifecycle import get_registry
            get_registry().unregister(
                f"subscription:{self._owner_id}:{_safe_event_name(self._event_type)}"
            )
        except Exception:
            pass


def _safe_event_name(event_type: Any) -> str:
    """Normalize event type to a safe string for lifecycle IDs."""
    if hasattr(event_type, "value"):
        return str(event_type.value)[:40]
    return str(event_type)[:40]


# ══════════════════════════════════════════════════════════════════════════
#  OwnershipChecker — runtime scanner for external strong references
# ══════════════════════════════════════════════════════════════════════════

# Known-safe referrer types — these are internal to lifecycle system
_SAFE_REFERRER_TYPES = frozenset({
    "_Entry", "_ObjectRef", "_AsyncObjectRef", "OwnedDict",
    "LifecycleRegistry", "dict",
    "Handle", "TimerHandle",  # asyncio event loop callbacks
})

# Known-safe referrer modules (prefix match)
_SAFE_REFERRER_MODULES = (
    "aitest.platform.lifecycle",
    "aitest.platform.ownership",
    "_ctypes", "ctypes",
    "gc", "sys", "threading",
    "asyncio",  # event loop internals (Handle, closures from create_task)
)


def _is_safe_referrer(ref: Any) -> bool:
    """Check if a referrer is internal/expected — not a leak."""
    rtype = type(ref).__module__ + "." + type(ref).__qualname__

    # Safe types
    if type(ref).__name__ in _SAFE_REFERRER_TYPES:
        # dict is safe only if it's the lifecycle _objects dict
        if type(ref).__name__ == "dict":
            if len(ref) > 100:
                return True  # Likely lifecycle._objects
            # Check if it looks like an internal dict
            for k in list(ref.keys())[:3]:
                if isinstance(k, str) and (
                    k.startswith("chat-session:")
                    or k.startswith("onboarding:")
                    or k.startswith("agent:")
                    or k.startswith("task:")
                    or k.startswith("subscription:")
                ):
                    return True
            return False
        return True

    # Safe modules
    for prefix in _SAFE_REFERRER_MODULES:
        if rtype.startswith(prefix):
            return True

    return False


# Known-safe source file paths (substring match).
# Closures defined in these files are internal asyncio/cpython mechanics,
# not leaks — even if they hold references to lifecycle objects.
_SAFE_LOCATION_SUBSTRINGS = (
    "asyncio" + "\\",
    "asyncio" + "/",
    "asyncio" + ".py",
    "lib\\threading",
    "lib/threading",
    "lib\\multiprocessing",
    "lib/multiprocessing",
)


def _is_safe_location(location: str) -> bool:
    """Check if a referrer's source file is a known-safe internal location."""
    if not location:
        return False
    loc_lower = location.lower()
    return any(sub in loc_lower for sub in _SAFE_LOCATION_SUBSTRINGS)


def _find_file_location(ref: Any) -> str:
    """Best-effort find where a referrer was defined."""
    try:
        if hasattr(ref, "__file__"):
            return str(ref.__file__)
        if hasattr(type(ref), "__module__"):
            mod = sys.modules.get(type(ref).__module__)
            if mod and hasattr(mod, "__file__"):
                return str(mod.__file__)
    except Exception:
        pass
    # Try to find via traceback
    try:
        frame = traceback.extract_stack()[-5]
        return f"{frame.filename}:{frame.lineno}"
    except Exception:
        pass
    return "(unknown)"


class OwnershipChecker:
    """Periodic runtime scanner: finds objects with external strong references.

    Walks all LifecycleRegistry-tracked objects, calls gc.get_referrers() on each,
    and flags any referrer that is NOT the registry or other internal structure.

    Usage:
        checker = OwnershipChecker()
        violations = checker.scan()
        for v in violations:
            _log.info(f"LEAK: {v['lifecycle_id']} held by {v['external_refs']}")
    """

    def __init__(self):
        self._scan_count = 0
        self._last_scan_ts = 0.0
        self._total_violations_found = 0
        self._known_false_positives: set[int] = set()  # object ids to skip

    @property
    def scan_count(self) -> int:
        """Public accessor for scan count. Used by sweep loop."""
        return self._scan_count

    def scan(self, max_objects: int = 50, max_depth: int = 3) -> dict:
        """Scan for ownership violations.

        Args:
            max_objects: Max lifecycle objects to check (safety limit)
            max_depth: How many referrer levels to trace

        Returns:
            {
                "scan_id": int,
                "violations": [...],
                "total_checked": int,
                "total_external_refs": int,
                "duration_ms": float,
            }
        """
        self._scan_count += 1
        started = time.monotonic()
        violations: list[dict] = []
        total_checked = 0
        total_external_refs = 0

        try:
            from aitest.platform.lifecycle import get_registry
            registry = get_registry()
        except Exception:
            return {
                "scan_id": self._scan_count,
                "error": "LifecycleRegistry not available",
                "violations": [],
                "total_checked": 0,
                "total_external_refs": 0,
                "duration_ms": (time.monotonic() - started) * 1000,
            }

        with registry._lock:
            entries = list(registry._objects.items())[:max_objects]

        for lid, entry in entries:
            total_checked += 1
            target = entry.wrapped_obj if entry.wrapped_obj else entry.obj

            try:
                refs = gc.get_referrers(target)
            except Exception:
                continue

            external_refs: list[dict] = []
            for ref in refs:
                rid = id(ref)

                # Skip known false positives
                if rid in self._known_false_positives:
                    continue

                # Skip self
                if rid == id(target) or rid == id(entry) or rid == id(registry):
                    continue

                # Check if safe (by type or module)
                if _is_safe_referrer(ref):
                    continue

                rtype = type(ref).__qualname__
                rmodule = type(ref).__module__ or ""

                # Check if defined in a safe internal file (e.g. asyncio closures
                # captured by event loop handles). The type module might not match
                # (closures are generic `function` type), so check the source file.
                location = _find_file_location(ref)
                if _is_safe_location(location):
                    continue
                rrepr = repr(ref)[:200]
                rsize = sys.getsizeof(ref) if hasattr(ref, "__sizeof__") else 0

                # Classify violation severity
                severity = "warning"
                if rtype == "dict" and not _is_safe_referrer(ref):
                    # Module-level dict holding owned objects
                    keys = list(ref.keys())[:5] if isinstance(ref, dict) else []
                    if any(
                        isinstance(k, str) and (
                            "session" in k or "agent" in k or "task" in k
                        )
                        for k in keys
                    ):
                        severity = "critical"
                        location += f" [module_dict keys={keys}]"

                elif rtype in ("function", "method", "cell"):
                    severity = "high"  # Closure capturing owned object
                    location += " [closure_capture]"

                elif rtype == "list":
                    severity = "high" if len(ref) > 10 else "warning"

                external_refs.append({
                    "type": rtype,
                    "module": rmodule,
                    "repr": rrepr[:150],
                    "size_bytes": rsize,
                    "location": location,
                    "severity": severity,
                })

            if external_refs:
                total_external_refs += len(external_refs)
                owned_meta = _get_owned(target)
                violations.append({
                    "lifecycle_id": lid,
                    "owner": entry.obj.owner,
                    "age_s": round(time.monotonic() - entry.registered_at, 1),
                    "created_stack": entry.created_stack,
                    "external_refs": external_refs,
                    "max_severity": max(
                        (r["severity"] for r in external_refs),
                        key=lambda s: {"critical": 3, "high": 2, "warning": 1}.get(s, 0),
                    ) if external_refs else "warning",
                })

        self._last_scan_ts = time.monotonic()
        self._total_violations_found += len(violations)

        return {
            "scan_id": self._scan_count,
            "violations": violations,
            "total_checked": total_checked,
            "total_external_refs": total_external_refs,
            "total_violations": len(violations),
            "duration_ms": round((time.monotonic() - started) * 1000, 1),
        }

    def whitelist(self, obj_id: int):
        """Add a false positive to whitelist."""
        self._known_false_positives.add(obj_id)

    @property
    def stats(self) -> dict:
        return {
            "scan_count": self._scan_count,
            "total_violations_found": self._total_violations_found,
            "last_scan_ts": self._last_scan_ts,
            "whitelist_size": len(self._known_false_positives),
        }


# ══════════════════════════════════════════════════════════════════════════
#  TaskGuard — asyncio.create_task replacement that prevents escape
# ══════════════════════════════════════════════════════════════════════════

class TaskGuard:
    """Replacement for asyncio.create_task that prevents task escape.

    Every task created through TaskGuard is:
      1. Registered in LifecycleRegistry (observable)
      2. Auto-unregistered on completion (no leak)
      3. TTL-bounded (enforcement)
      4. Cancellable via owner dispose

    Also tracks all created tasks for OwnershipChecker compatibility.

    Usage:
        guard = TaskGuard()
        task = guard.create_task(my_coro(), owner="chat:stream", ttl_s=300)
    """

    def __init__(self):
        self._active_task_ids: set[str] = set()
        self._lock = threading.Lock()
        self._total_created = 0
        self._total_completed = 0
        self._total_cancelled = 0

    def create_task(
        self,
        coro,
        *,
        owner: str,
        lifecycle_id: str = "",
        ttl_s: float = 0,
    ) -> "asyncio.Task":
        """Create a tracked asyncio.Task. Never escapes.

        Args:
            coro: Coroutine to schedule
            owner: Who created this task (e.g., "chat:stream", "onboarding:start")
            lifecycle_id: Unique ID (auto-generated if empty)
            ttl_s: If > 0, task is cancelled if it exceeds this duration

        Returns:
            The asyncio.Task
        """
        import asyncio
        import uuid as _uuid

        task = asyncio.create_task(coro)

        if not lifecycle_id:
            lifecycle_id = f"task:{owner}:{_uuid.uuid4().hex[:8]}"

        tid = lifecycle_id

        with self._lock:
            self._active_task_ids.add(tid)
            self._total_created += 1

        def _on_done(t: asyncio.Task):
            with self._lock:
                self._active_task_ids.discard(tid)
                self._total_completed += 1
                if t.cancelled():
                    self._total_cancelled += 1
            # Unregister from lifecycle
            try:
                from aitest.platform.lifecycle import get_registry
                get_registry().unregister(tid)
            except Exception:
                pass

        def _cancel_task():
            """Dispose callback: cancel the task if still running."""
            if not task.done():
                task.cancel()
                with self._lock:
                    self._total_cancelled += 1
            _on_done(task)

        # Register in lifecycle
        try:
            from aitest.platform.lifecycle import get_registry, _ObjectRef
            get_registry().register(_ObjectRef(
                tid,
                owner,
                dispose_fn=_cancel_task,
                ttl_s=ttl_s,
            ))
        except Exception:
            pass

        task.add_done_callback(_on_done)
        return task

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._active_task_ids)

    @property
    def stats(self) -> dict:
        with self._lock:
            return {
                "active": len(self._active_task_ids),
                "total_created": self._total_created,
                "total_completed": self._total_completed,
                "total_cancelled": self._total_cancelled,
            }

    def cancel_all(self) -> int:
        """Cancel all active tasks. Returns count cancelled."""
        with self._lock:
            ids = list(self._active_task_ids)
        count = 0
        for tid in ids:
            try:
                from aitest.platform.lifecycle import get_registry
                if get_registry().dispose(tid):
                    count += 1
            except Exception:
                pass
        return count


# ══════════════════════════════════════════════════════════════════════════
#  Singletons
# ══════════════════════════════════════════════════════════════════════════

_checker: Optional[OwnershipChecker] = None
_checker_lock = threading.Lock()

_guard: Optional[TaskGuard] = None
_guard_lock = threading.Lock()


def get_ownership_checker() -> OwnershipChecker:
    global _checker
    with _checker_lock:
        if _checker is None:
            _checker = OwnershipChecker()
        return _checker


def get_task_guard() -> TaskGuard:
    global _guard
    with _guard_lock:
        if _guard is None:
            _guard = TaskGuard()
        return _guard
