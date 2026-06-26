"""
EventBus — lightweight in-process pub/sub for RunEvents. v2.2

P0-3 (RC3 fix): Subscribers stored as weakrefs where possible (bound methods).
Plain functions/module-level callbacks keep strong refs — they don't leak.
Dead weakrefs auto-cleaned on publish.

Usage:
    from aitest.platform.event_bus import get_bus
    from aitest.platform.run_event import EventType

    bus = get_bus()

    def on_run_completed(event):
        _log.info(f"Run {event.run_id} completed")

    bus.subscribe(EventType.RUN_COMPLETED, on_run_completed)
    bus.publish(event)
"""

import threading
import weakref
from typing import Callable

from .run_event import RunEvent
from aitest.infra.logging import get_logger
_log = get_logger(__name__)

# Subscriber callback: (RunEvent) -> None
Subscriber = Callable[[RunEvent], None]


class EventBus:
    """Lightweight pub/sub. Weakref for bound methods, strong for functions."""

    def __init__(self):
        self._subscribers: dict[str, list[Subscriber | weakref.ReferenceType]] = {}
        self._wildcards: list[Subscriber | weakref.ReferenceType] = []
        self._lock = threading.Lock()

    @staticmethod
    def _wrap(callback: Subscriber) -> Subscriber | weakref.ReferenceType:
        """Wrap bound methods in weakref to prevent RC3 leak. Plain functions keep strong ref."""
        if hasattr(callback, '__self__') and not isinstance(callback.__self__, type):
            # Bound method on instance — use weakref to allow GC
            return weakref.WeakMethod(callback)
        return callback  # Plain function / static method — strong ref is fine

    @staticmethod
    def _resolve(ref: Subscriber | weakref.ReferenceType) -> Subscriber | None:
        """Resolve a stored ref to a callable or None if dead."""
        if isinstance(ref, weakref.ref):
            return ref()
        return ref

    def _cleanup_dead(self, lst: list):
        """Remove dead weakrefs from a subscriber list."""
        dead = [r for r in lst if isinstance(r, weakref.ref) and r() is None]
        for r in dead:
            lst.remove(r)

    def subscribe(self, event_type: str, callback: Subscriber):
        """Subscribe to a specific event type. Use "*" for all events."""
        wrapped = self._wrap(callback)
        with self._lock:
            if event_type == "*":
                self._wildcards.append(wrapped)
            else:
                self._subscribers.setdefault(event_type, []).append(wrapped)

    def unsubscribe(self, event_type: str, callback: Subscriber):
        """Remove a subscriber by matching resolved callback identity."""
        with self._lock:
            lst = self._wildcards if event_type == "*" else self._subscribers.get(event_type, [])
            for ref in list(lst):
                resolved = self._resolve(ref)
                if resolved is callback or resolved is None:
                    lst.remove(ref)

    def publish(self, event: RunEvent):
        """Emit event. Auto-cleans dead weakrefs. Best-effort, non-blocking."""
        with self._lock:
            handlers = [self._resolve(r) for r in self._subscribers.get(event.event_type, [])]
            handlers.extend(self._resolve(r) for r in self._wildcards)
            # Clean dead weakrefs
            self._cleanup_dead(self._subscribers.get(event.event_type, []))
            self._cleanup_dead(self._wildcards)

        for handler in handlers:
            if handler is None:
                continue
            try:
                handler(event)
            except Exception:
                pass

    @property
    def subscriber_count(self) -> int:
        with self._lock:
            total = len(self._wildcards)
            for subs in self._subscribers.values():
                total += len(subs)
            return total


# ── Singleton ────────────────────────────────────────────────────────────

_bus: EventBus | None = None
_bus_lock = threading.Lock()


def get_bus() -> EventBus:
    global _bus
    with _bus_lock:
        if _bus is None:
            _bus = EventBus()
        return _bus
