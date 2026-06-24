"""
EventBus — lightweight in-process pub/sub for RunEvents. v2.2

Design: simple list[Callable]. No Kafka, no Redis Stream, no CloudEvent.
Extract to external message bus later if needed.

Usage:
    from aitest.platform.event_bus import get_bus
    from aitest.platform.run_event import EventType

    bus = get_bus()

    def on_run_completed(event):
        print(f"Run {event.run_id} completed")

    bus.subscribe(EventType.RUN_COMPLETED, on_run_completed)
    bus.publish(event)
"""

import threading
from typing import Callable

from .run_event import RunEvent

# Subscriber callback: (RunEvent) -> None
Subscriber = Callable[[RunEvent], None]


class EventBus:
    """Lightweight pub/sub. list[Callable] per event type."""

    def __init__(self):
        self._subscribers: dict[str, list[Subscriber]] = {}
        self._wildcards: list[Subscriber] = []  # "*" subscribers get all events
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, callback: Subscriber):
        """Subscribe to a specific event type. Use "*" for all events."""
        with self._lock:
            if event_type == "*":
                self._wildcards.append(callback)
            else:
                self._subscribers.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: str, callback: Subscriber):
        """Remove a subscriber."""
        with self._lock:
            if event_type == "*":
                if callback in self._wildcards:
                    self._wildcards.remove(callback)
            elif event_type in self._subscribers:
                subs = self._subscribers[event_type]
                if callback in subs:
                    subs.remove(callback)

    def publish(self, event: RunEvent):
        """Emit an event to all matching subscribers. Non-blocking, best-effort."""
        with self._lock:
            handlers = list(self._subscribers.get(event.event_type, []))
            handlers.extend(self._wildcards)

        for handler in handlers:
            try:
                handler(event)
            except Exception:
                # Best-effort: don't let one subscriber break others.
                # In production, log to error_logger.
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
