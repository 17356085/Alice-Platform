"""Tests for platform/observation_bus.py — lightweight event bus.

Tests: EventType enum, ObservationEvent, ObservationBus (subscribe/emit/unsubscribe),
history management, error handling in callbacks.
Pure in-memory — no external dependencies.
"""
import pytest

from aitest.platform.observation_bus import (
    ObservationBus, ObservationEvent, EventType,
)


# ══════════════════════════════════════════════════════════════════════════
#  EventType
# ══════════════════════════════════════════════════════════════════════════


class TestEventType:
    def test_agent_events(self):
        assert EventType.SKILL_START == "skill_start"
        assert EventType.SKILL_COMPLETE == "skill_complete"
        assert EventType.SKILL_FAILED == "skill_failed"
        assert EventType.AGENT_START == "agent_start"
        assert EventType.AGENT_COMPLETE == "agent_complete"

    def test_tool_events(self):
        assert EventType.TOOL_CALL_START == "tool_call_start"
        assert EventType.TOOL_CALL_COMPLETE == "tool_call_complete"

    def test_memory_events(self):
        assert EventType.MEMORY_ADDED == "memory_added"
        assert EventType.MEMORY_VERIFIED == "memory_verified"

    def test_security_events(self):
        assert EventType.SECURITY_BLOCKED == "security_blocked"
        assert EventType.PROMPT_INJECTION_DETECTED == "prompt_injection_detected"

    def test_system_events(self):
        assert EventType.CONTEXT_WINDOW_WARN == "context_window_warn"
        assert EventType.PROVIDER_FALLBACK == "provider_fallback"

    def test_no_duplicate_values(self):
        values = [e.value for e in EventType]
        assert len(values) == len(set(values))


# ══════════════════════════════════════════════════════════════════════════
#  ObservationEvent
# ══════════════════════════════════════════════════════════════════════════


class TestObservationEvent:
    def test_defaults(self):
        ev = ObservationEvent(type=EventType.SKILL_START)
        assert ev.data == {}
        assert ev.agent_name == ""
        assert ev.module == ""
        assert ev.page == ""
        assert ev.timestamp > 0

    def test_custom_values(self):
        ev = ObservationEvent(
            type=EventType.SKILL_COMPLETE,
            data={"skill_id": "test", "output": "OK"},
            agent_name="automation-agent",
            module="equipment",
            page="alarm",
        )
        assert ev.data["skill_id"] == "test"
        assert ev.agent_name == "automation-agent"


# ══════════════════════════════════════════════════════════════════════════
#  ObservationBus — subscribe + emit
# ══════════════════════════════════════════════════════════════════════════


class TestSubscribeAndEmit:
    def test_subscribe_and_emit(self):
        bus = ObservationBus()
        received = []
        bus.subscribe(EventType.SKILL_START, lambda e: received.append(e))
        bus.emit(EventType.SKILL_START, {"skill_id": "s1"})
        assert len(received) == 1
        assert received[0].data["skill_id"] == "s1"

    def test_multiple_subscribers(self):
        bus = ObservationBus()
        a = []
        b = []
        bus.subscribe(EventType.SKILL_COMPLETE, lambda e: a.append(e))
        bus.subscribe(EventType.SKILL_COMPLETE, lambda e: b.append(e))
        bus.emit(EventType.SKILL_COMPLETE)
        assert len(a) == 1
        assert len(b) == 1

    def test_different_event_types(self):
        bus = ObservationBus()
        start = []
        complete = []
        bus.subscribe(EventType.SKILL_START, lambda e: start.append(e))
        bus.subscribe(EventType.SKILL_COMPLETE, lambda e: complete.append(e))
        bus.emit(EventType.SKILL_START)
        assert len(start) == 1
        assert len(complete) == 0

    def test_emit_with_no_subscribers(self):
        bus = ObservationBus()
        bus.emit(EventType.SKILL_START)  # Should not raise

    def test_emit_passes_agent_info(self):
        bus = ObservationBus()
        received = []
        bus.subscribe(EventType.AGENT_START, lambda e: received.append(e))
        bus.emit(EventType.AGENT_START, agent_name="test-agent", module="equipment", page="alarm")
        assert received[0].agent_name == "test-agent"
        assert received[0].module == "equipment"
        assert received[0].page == "alarm"


# ══════════════════════════════════════════════════════════════════════════
#  unsubscribe
# ══════════════════════════════════════════════════════════════════════════


class TestUnsubscribe:
    def test_unsubscribe_removes_callback(self):
        bus = ObservationBus()
        received = []
        cb = lambda e: received.append(e)
        bus.subscribe(EventType.SKILL_START, cb)
        bus.unsubscribe(EventType.SKILL_START, cb)
        bus.emit(EventType.SKILL_START)
        assert len(received) == 0

    def test_unsubscribe_nonexistent_is_noop(self):
        bus = ObservationBus()
        bus.unsubscribe(EventType.SKILL_START, lambda e: None)  # Should not raise


# ══════════════════════════════════════════════════════════════════════════
#  History
# ══════════════════════════════════════════════════════════════════════════


class TestHistory:
    def test_history_records_events(self):
        bus = ObservationBus()
        bus.emit(EventType.SKILL_START)
        bus.emit(EventType.SKILL_COMPLETE)
        assert len(bus._history) == 2

    def test_history_capped_at_max(self):
        bus = ObservationBus()
        bus._max_history = 5
        for _ in range(10):
            bus.emit(EventType.SKILL_START)
        assert len(bus._history) == 5

    def test_history_preserves_order(self):
        bus = ObservationBus()
        bus.emit(EventType.SKILL_START, {"n": 1})
        bus.emit(EventType.SKILL_COMPLETE, {"n": 2})
        assert bus._history[0].data["n"] == 1
        assert bus._history[1].data["n"] == 2


# ══════════════════════════════════════════════════════════════════════════
#  Error handling
# ══════════════════════════════════════════════════════════════════════════


class TestErrorHandling:
    def test_callback_exception_does_not_crash(self):
        bus = ObservationBus()
        bus.subscribe(EventType.SKILL_START, lambda e: (_ for _ in ()).throw(RuntimeError("boom")))
        bus.emit(EventType.SKILL_START)  # Should not raise

    def test_callback_exception_does_not_block_others(self):
        bus = ObservationBus()
        good = []
        bus.subscribe(EventType.SKILL_START, lambda e: (_ for _ in ()).throw(RuntimeError("boom")))
        bus.subscribe(EventType.SKILL_START, lambda e: good.append(e))
        bus.emit(EventType.SKILL_START)
        assert len(good) == 1
