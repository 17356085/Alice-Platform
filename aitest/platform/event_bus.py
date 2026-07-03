"""
EventBus — lightweight in-process pub/sub for RunEvents. v3.1

P0-3 (RC3 fix): Subscribers stored as weakrefs where possible (bound methods).
Plain functions/module-level callbacks keep strong refs — they don't leak.
Dead weakrefs auto-cleaned on publish.

v2.5: Priority ordering — subscribers execute in priority order (lower first).
Default priority=20. Convention: 0=Critical(Audit), 10=High(Billing),
20=Normal(Metrics/Report), 30=Low(Webhook).

v3.0: Async dispatch — publish_async() dispatches I/O-bound handlers via
ThreadPoolExecutor to avoid blocking the caller (e.g. Webhook HTTP calls).

v3.1: Future tracking + backpressure + priority constraints.
  - publish_async() returns Future list for tracking async handler completion
  - await_async() waits for all pending async handlers
  - Queue depth limit prevents unbounded memory growth
  - PRIORITY_CONSTRAINTS enforced at subscribe time

Usage:
    from aitest.platform.event_bus import get_bus
    from aitest.platform.run_event import EventType

    bus = get_bus()

    def on_run_completed(event):
        _log.info(f"Run {event.run_id} completed")

    bus.subscribe(EventType.RUN_COMPLETED, on_run_completed, priority=10)
    bus.publish(event)
"""

import threading
import weakref
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Callable

from .run_event import RunEvent
from aitest.infra.logging import get_logger
_log = get_logger(__name__)

# Subscriber callback: (RunEvent) -> None
Subscriber = Callable[[RunEvent], None]

# ── Priority levels ─────────────────────────────────────────────────────
#
# Execution order constraint (enforced by design, not runtime):
#   Audit (0) → Billing (10) → Quota (15) → Metrics/Report (20) → Webhook (30)
#
# Why this order matters:
#   - Audit MUST fire before any side-effect consumer, so the audit trail
#     is guaranteed even if downstream handlers crash.
#   - Billing MUST fire before Quota, because quota enforcement may depend
#     on cost data computed by the billing hook.
#   - Metrics/Report are aggregation-only, safe to run after financial handlers.
#   - Webhook is last because it does slow external HTTP calls and should not
#     block financial recording.

PRIORITY_CRITICAL = 0    # Audit: must record before any side-effect
PRIORITY_HIGH = 10       # Billing: financial data — MUST be before Quota
PRIORITY_MEDIUM_HIGH = 15  # Quota: limit/usage data — depends on Billing
PRIORITY_NORMAL = 20     # Metrics, Report: aggregation (default)
PRIORITY_LOW = 30        # Webhook: external delivery, slow HTTP — MUST be last

# Documented priority constraints — violations log a warning at subscribe time
# Format: handler_name → (actual_priority, must_be_less_than_priority)
PRIORITY_CONSTRAINTS: dict[str, tuple[int, int]] = {
    "AuditLogger": (PRIORITY_CRITICAL, PRIORITY_HIGH),        # Must be before Billing
    "BillingHook": (PRIORITY_HIGH, PRIORITY_MEDIUM_HIGH),     # Must be before Quota
    "QuotaUsage": (PRIORITY_MEDIUM_HIGH, PRIORITY_NORMAL),    # Must be before Metrics
    "MetricsConsumer": (PRIORITY_NORMAL, PRIORITY_LOW),        # Must be before Webhook
    "ReportConsumer": (PRIORITY_NORMAL, PRIORITY_LOW),         # Must be before Webhook
    "WebhookDispatcher": (PRIORITY_LOW, PRIORITY_LOW + 10),    # Must be last
}


class EventBus:
    """Lightweight pub/sub. Weakref for bound methods, strong for functions.
    Subscribers execute in priority order (lower priority number first).

    v3.0: publish_async() dispatches I/O-bound handlers via ThreadPoolExecutor
    to avoid blocking the caller. Handlers with priority >= PRIORITY_LOW are
    automatically dispatched asynchronously.

    v3.1: Future tracking + backpressure + priority constraints.
    """

    # Handlers at or above this priority run in the thread pool (async)
    ASYNC_THRESHOLD = PRIORITY_LOW  # Webhook and slower handlers

    # Backpressure: max pending async futures before publish_async blocks
    MAX_PENDING_FUTURES = 100

    def __init__(self, max_workers: int = 4):
        # Each entry: list of (priority, ref) tuples
        self._subscribers: dict[str, list[tuple[int, Subscriber | weakref.ReferenceType]]] = {}
        self._wildcards: list[tuple[int, Subscriber | weakref.ReferenceType]] = []
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="eventbus")
        self._pending_futures: list[Future] = []
        self._futures_lock = threading.Lock()

    @staticmethod
    def _wrap(callback: Subscriber) -> Subscriber | weakref.ReferenceType:
        """Wrap bound methods in weakref to prevent RC3 leak. Plain functions keep strong ref."""
        if hasattr(callback, '__self__') and not isinstance(callback.__self__, type):
            # Bound method on instance — use weakref to allow GC
            try:
                return weakref.WeakMethod(callback)
            except TypeError:
                # Built-in methods (e.g. list.append) are not weakref-able.
                # Keep a strong reference — caller must unsubscribe explicitly.
                return callback
        return callback  # Plain function / static method — strong ref is fine

    @staticmethod
    def _resolve(ref: Subscriber | weakref.ReferenceType) -> Subscriber | None:
        """Resolve a stored ref to a callable or None if dead."""
        if isinstance(ref, weakref.ref):
            return ref()
        return ref

    def _cleanup_dead(self, lst: list):
        """Remove dead weakrefs from a subscriber list of (priority, ref) tuples."""
        dead = [entry for entry in lst if isinstance(entry[1], weakref.ref) and entry[1]() is None]
        for entry in dead:
            lst.remove(entry)

    def subscribe(self, event_type: str, callback: Subscriber, priority: int = PRIORITY_NORMAL,
                  handler_name: str = ""):
        """Subscribe to a specific event type. Use "*" for all events.
        Lower priority number = earlier execution.

        Args:
            event_type: Event type string or "*" for all events.
            callback: Handler function.
            priority: Execution priority (lower = earlier).
            handler_name: Optional name for constraint validation.
        """
        # Validate priority constraints if handler_name matches
        if handler_name and handler_name in PRIORITY_CONSTRAINTS:
            expected, must_be_less_than = PRIORITY_CONSTRAINTS[handler_name]
            if priority != expected:
                _log.warning(
                    f"EventBus priority constraint: {handler_name} "
                    f"expected priority={expected}, got priority={priority}"
                )
        wrapped = self._wrap(callback)
        with self._lock:
            if event_type == "*":
                self._wildcards.append((priority, wrapped))
                self._wildcards.sort(key=lambda x: x[0])
            else:
                self._subscribers.setdefault(event_type, []).append((priority, wrapped))
                self._subscribers[event_type].sort(key=lambda x: x[0])

    def unsubscribe(self, event_type: str, callback: Subscriber):
        """Remove a subscriber by matching resolved callback identity."""
        with self._lock:
            lst = self._wildcards if event_type == "*" else self._subscribers.get(event_type, [])
            for entry in list(lst):
                _, ref = entry
                resolved = self._resolve(ref)
                if resolved is callback or resolved is None:
                    lst.remove(entry)

    def _resolve_handlers(self, event_type: str) -> list[tuple[int, Subscriber]]:
        """Resolve and sort all handlers for an event type. Thread-safe."""
        with self._lock:
            specific = self._subscribers.get(event_type, [])
            all_entries = list(specific) + list(self._wildcards)
            handlers = []
            for prio, ref in all_entries:
                resolved = self._resolve(ref)
                if resolved is not None:
                    handlers.append((prio, resolved))
            handlers.sort(key=lambda x: x[0])
            self._cleanup_dead(self._subscribers.get(event_type, []))
            self._cleanup_dead(self._wildcards)
        return handlers

    @staticmethod
    def _run_handler(handler: Subscriber, event: RunEvent) -> bool:
        """Run a single handler. Returns True on success."""
        try:
            handler(event)
            return True
        except Exception:
            _log.error(
                f"EventBus handler error: "
                f"event={event.event_type} id={event.event_id} "
                f"handler={getattr(handler, '__name__', repr(handler))}"
            )
            return False

    def publish(self, event: RunEvent) -> tuple[int, int]:
        """Emit event synchronously. Auto-cleans dead weakrefs.
        Handlers execute in priority order (lower number first).

        Returns:
            (success_count, failure_count) — failures are logged, not raised.
        """
        handlers = self._resolve_handlers(event.event_type)
        ok = 0
        fail = 0
        for _, handler in handlers:
            if self._run_handler(handler, event):
                ok += 1
            else:
                fail += 1
        return ok, fail

    def publish_async(self, event: RunEvent) -> tuple[int, list[Future]]:
        """Emit event with async dispatch for I/O-bound handlers.

        Handlers with priority < ASYNC_THRESHOLD run synchronously (in caller thread).
        Handlers with priority >= ASYNC_THRESHOLD are dispatched via ThreadPoolExecutor.

        v3.1: Returns Future list for tracking. Backpressure via MAX_PENDING_FUTURES.

        Returns:
            (sync_success, async_futures) — sync count + list of Futures for async handlers.
        """
        # Backpressure: wait if too many pending futures
        with self._futures_lock:
            # Clean completed futures
            self._pending_futures = [f for f in self._pending_futures if not f.done()]
            if len(self._pending_futures) >= self.MAX_PENDING_FUTURES:
                _log.warning(
                    f"EventBus backpressure: {len(self._pending_futures)} pending futures, "
                    f"waiting for oldest to complete"
                )
                # Wait for oldest future to complete
                if self._pending_futures:
                    self._pending_futures[0].result(timeout=5)

        handlers = self._resolve_handlers(event.event_type)
        sync_ok = 0
        async_futures: list[Future] = []
        for prio, handler in handlers:
            if prio >= self.ASYNC_THRESHOLD:
                # I/O-bound — dispatch to thread pool
                future = self._executor.submit(self._run_handler, handler, event)
                async_futures.append(future)
                with self._futures_lock:
                    self._pending_futures.append(future)
            else:
                # Critical/high — run synchronously in caller thread
                if self._run_handler(handler, event):
                    sync_ok += 1
        return sync_ok, async_futures

    def await_async(self, timeout: float = 30.0) -> tuple[int, int]:
        """Wait for all pending async handlers to complete.

        Args:
            timeout: Maximum seconds to wait.

        Returns:
            (completed, failed) counts.
        """
        with self._futures_lock:
            futures = list(self._pending_futures)
        completed = 0
        failed = 0
        for f in futures:
            try:
                f.result(timeout=timeout)
                if f.done() and not f.cancelled():
                    completed += 1
            except Exception:
                failed += 1
        return completed, failed

    @property
    def pending_async_count(self) -> int:
        """Number of pending async handler futures."""
        with self._futures_lock:
            self._pending_futures = [f for f in self._pending_futures if not f.done()]
            return len(self._pending_futures)

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
    """Get the global EventBus singleton. Creates one on first call."""
    global _bus
    with _bus_lock:
        if _bus is None:
            _bus = EventBus()
        return _bus


def set_bus(bus: EventBus) -> None:
    """Inject a custom EventBus instance (for testing or plugin replacement).

    Replaces the global singleton. Call reset_bus() to restore default.
    """
    global _bus
    with _bus_lock:
        _bus = bus


def reset_bus() -> None:
    """Reset to default singleton (next get_bus() creates a fresh instance).
    Waits for pending async handlers, then shuts down executor."""
    global _bus
    with _bus_lock:
        if _bus is not None:
            # Wait for pending handlers (best-effort, max 5s)
            try:
                _bus.await_async(timeout=5.0)
            except Exception:
                pass
            _bus._executor.shutdown(wait=False)
        _bus = None
