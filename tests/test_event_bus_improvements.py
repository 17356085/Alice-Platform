"""Test: EventBus improvements — Future tracking, backpressure, priority constraints.

Batch 3 of coupling fix plan. Verifies:
  1. publish_async returns Future list
  2. await_async waits for completion
  3. pending_async_count tracks in-flight handlers
  4. PRIORITY_CONSTRAINTS are populated
  5. subscribe validates priority constraints
"""

import pytest
import time
import threading
from aitest.platform.event_bus import EventBus, PRIORITY_CONSTRAINTS
from aitest.platform.run_event import RunEvent, EventType, make_event


# ── 1. Future tracking ────────────────────────────────────────────────

def test_publish_async_returns_futures():
    """publish_async should return (sync_ok, async_futures)."""
    bus = EventBus()
    results = []

    def slow_handler(event):
        time.sleep(0.1)
        results.append("done")

    bus.subscribe(EventType.RUN_COMPLETED, slow_handler, priority=30)
    ev = make_event(EventType.RUN_COMPLETED, run_id="test")
    sync_ok, futures = bus.publish_async(ev)

    assert isinstance(futures, list)
    assert len(futures) == 1
    # Wait for completion
    futures[0].result(timeout=2)
    assert results == ["done"]
    bus._executor.shutdown(wait=False)


def test_publish_async_sync_handlers_dont_create_futures():
    """Handlers with priority < ASYNC_THRESHOLD run synchronously, no futures."""
    bus = EventBus()
    results = []

    def fast_handler(event):
        results.append("sync")

    bus.subscribe(EventType.RUN_COMPLETED, fast_handler, priority=0)
    ev = make_event(EventType.RUN_COMPLETED, run_id="test")
    sync_ok, futures = bus.publish_async(ev)

    assert sync_ok == 1
    assert len(futures) == 0
    assert results == ["sync"]
    bus._executor.shutdown(wait=False)


# ── 2. await_async ────────────────────────────────────────────────────

def test_await_async_waits_for_completion():
    """await_async should block until all async handlers complete."""
    bus = EventBus()
    results = []

    def slow_handler(event):
        time.sleep(0.2)
        results.append("done")

    bus.subscribe(EventType.RUN_COMPLETED, slow_handler, priority=30)
    ev = make_event(EventType.RUN_COMPLETED, run_id="test")
    bus.publish_async(ev)

    completed, failed = bus.await_async(timeout=2)
    assert completed >= 1
    assert "done" in results
    bus._executor.shutdown(wait=False)


# ── 3. pending_async_count ────────────────────────────────────────────

def test_pending_async_count():
    """pending_async_count should track in-flight async handlers."""
    bus = EventBus()
    barrier = threading.Event()

    def blocking_handler(event):
        barrier.wait(timeout=2)

    bus.subscribe(EventType.RUN_COMPLETED, blocking_handler, priority=30)
    ev = make_event(EventType.RUN_COMPLETED, run_id="test")
    bus.publish_async(ev)

    # Handler is blocked, so pending count should be > 0
    assert bus.pending_async_count >= 1

    # Release the handler
    barrier.set()
    time.sleep(0.1)
    bus._executor.shutdown(wait=False)


# ── 4. PRIORITY_CONSTRAINTS populated ─────────────────────────────────

def test_priority_constraints_populated():
    """PRIORITY_CONSTRAINTS should have entries for all known consumers."""
    assert len(PRIORITY_CONSTRAINTS) >= 5
    assert "AuditLogger" in PRIORITY_CONSTRAINTS
    assert "BillingHook" in PRIORITY_CONSTRAINTS
    assert "QuotaUsage" in PRIORITY_CONSTRAINTS
    assert "MetricsConsumer" in PRIORITY_CONSTRAINTS
    assert "WebhookDispatcher" in PRIORITY_CONSTRAINTS


def test_priority_constraints_ordering():
    """Priority constraints should enforce the correct ordering."""
    audit_prio, audit_max = PRIORITY_CONSTRAINTS["AuditLogger"]
    billing_prio, billing_max = PRIORITY_CONSTRAINTS["BillingHook"]
    quota_prio, quota_max = PRIORITY_CONSTRAINTS["QuotaUsage"]
    webhook_prio, webhook_max = PRIORITY_CONSTRAINTS["WebhookDispatcher"]

    assert audit_prio < billing_prio
    assert billing_prio < quota_prio
    assert quota_prio < webhook_prio


# ── 5. subscribe validates priority ───────────────────────────────────

def test_subscribe_logs_warning_on_constraint_violation(caplog):
    """subscribe should log a warning if priority doesn't match constraint."""
    import logging
    bus = EventBus()

    with caplog.at_level(logging.WARNING):
        # BillingHook should be priority=10, but we give it priority=20
        bus.subscribe(EventType.RUN_COMPLETED, lambda e: None,
                      priority=20, handler_name="BillingHook")

    assert any("BillingHook" in r.message and "priority" in r.message
               for r in caplog.records)
    bus._executor.shutdown(wait=False)


def test_subscribe_no_warning_on_correct_priority(caplog, ):
    """subscribe should not log if priority matches constraint."""
    import logging
    bus = EventBus()

    with caplog.at_level(logging.WARNING):
        bus.subscribe(EventType.RUN_COMPLETED, lambda e: None,
                      priority=10, handler_name="BillingHook")

    assert not any("BillingHook" in r.message for r in caplog.records)
    bus._executor.shutdown(wait=False)
