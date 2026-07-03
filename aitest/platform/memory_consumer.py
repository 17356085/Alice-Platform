"""
MemoryConsumer — bridges ObservationBus events to TestingMemoryStore.

Extracted from observation_bus.py to decouple the bus from memory domain objects.
The bus should not know about its consumers; consumers register themselves.

Usage:
    from aitest.platform.memory_consumer import register_memory_consumer
    register_memory_consumer()  # auto-registers on ObservationBus
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from aitest.infra.logging import get_logger

if TYPE_CHECKING:
    from aitest.platform.observation_bus import ObservationBus, ObservationEvent
    from aitest.platform.testing_memory_store import TestingMemoryStore

_log = get_logger(__name__)

_registered = False
_registered_lock = threading.Lock()


def register_memory_consumer(store: TestingMemoryStore | None = None, bus: ObservationBus | None = None) -> None:
    """Register memory consumer on ObservationBus.

    Idempotent — subsequent calls are no-ops.

    Args:
        store: TestingMemoryStore instance. If None, creates a default one.
        bus: ObservationBus instance. If None, uses the global singleton.
    """
    global _registered
    with _registered_lock:
        if _registered:
            return
        _registered = True

    from aitest.platform.observation_bus import get_bus as get_obs_bus, EventType, ObservationEvent
    from aitest.platform.testing_memory import (
        LocatorHistoryMemory, KnownBugMemory, HistoricalFailureMemory,
    )
    from aitest.platform.testing_memory_store import TestingMemoryStore

    if store is None:
        try:
            store = TestingMemoryStore()
        except Exception:
            _log.warning("TestingMemoryStore unavailable, memory consumer disabled")
            with _registered_lock:
                _registered = False
            return

    if bus is None:
        bus = get_obs_bus()

    def on_test_failed(event: ObservationEvent):
        """Test failure → HistoricalFailure memory."""
        mem = HistoricalFailureMemory(
            content=f"Test failed: {event.data.get('test_name', 'unknown')} | "
                    f"error: {str(event.data.get('error', ''))[:300]}",
            failure_pattern=event.data.get("failure_pattern", ""),
            root_cause=event.data.get("root_cause", ""),
            fix_strategy=event.data.get("fix_strategy", ""),
            failure_count=1,
            module=event.module,
            page=event.page,
        )
        store.add(mem)

    def on_tool_call_failed(event: ObservationEvent):
        """Tool call failure → KnownBug memory."""
        mem = KnownBugMemory(
            content=f"Tool failed: {event.data.get('tool_name', 'unknown')} | "
                    f"error: {str(event.data.get('error', ''))[:300]}",
            bug_description=str(event.data.get('error', ''))[:500],
            workaround=event.data.get("workaround", ""),
            module=event.module,
            page=event.page,
        )
        store.add(mem)

    def on_locator_change(event: ObservationEvent):
        """Locator change → LocatorHistory memory."""
        mem = LocatorHistoryMemory(
            element=event.data.get("element", ""),
            stable_locator=event.data.get("new_locator", ""),
            failed_locators=[event.data.get("old_locator", "")] if event.data.get("old_locator") else [],
            module=event.module,
            page=event.page,
        )
        store.add(mem)

    # Use BoundSubscription for lifecycle tracking if available
    try:
        from aitest.platform.ownership import BoundSubscription
        subs = [
            BoundSubscription(bus, EventType.TEST_FAILED, on_test_failed,
                              owner_id="memory-consumer"),
            BoundSubscription(bus, EventType.TOOL_CALL_FAILED, on_tool_call_failed,
                              owner_id="memory-consumer"),
        ]
        for sub in subs:
            sub.activate()
    except Exception:
        # Fallback: bare subscribe when ownership module unavailable
        bus.subscribe(EventType.TEST_FAILED, on_test_failed)
        bus.subscribe(EventType.TOOL_CALL_FAILED, on_tool_call_failed)

    _log.info("Memory consumer registered on ObservationBus")
