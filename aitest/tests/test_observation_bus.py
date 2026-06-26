"""Tests for platform/observation_bus.py — event emit, subscribe, unsubscribe, history.

P1-7: Zero existing tests for this core platform event bus.
Tests ObservationBus pub/sub, event history, singleton get_bus().
"""
import pytest
from aitest.platform.observation_bus import (
    ObservationBus, ObservationEvent, EventType, get_bus,
)


# ── EventType Enum ────────────────────────────────────────────────────

class TestEventType:
    def test_skill_events_exist(self):
        assert EventType.SKILL_START == "skill_start"
        assert EventType.SKILL_COMPLETE == "skill_complete"
        assert EventType.SKILL_FAILED == "skill_failed"

    def test_agent_events_exist(self):
        assert EventType.AGENT_START == "agent_start"
        assert EventType.AGENT_COMPLETE == "agent_complete"

    def test_tool_call_events_exist(self):
        assert EventType.TOOL_CALL_START == "tool_call_start"

    def test_execution_events_exist(self):
        assert EventType.TEST_PASSED == "test_passed"
        assert EventType.TEST_FAILED == "test_failed"

    def test_memory_events_exist(self):
        assert EventType.MEMORY_ADDED == "memory_added"

    def test_security_events_exist(self):
        assert EventType.SECURITY_BLOCKED == "security_blocked"

    def test_system_events_exist(self):
        assert EventType.CONTEXT_WINDOW_WARN == "context_window_warn"
        assert EventType.PROVIDER_FALLBACK == "provider_fallback"


# ── ObservationEvent ──────────────────────────────────────────────────

class TestObservationEvent:
    def test_create_event_with_defaults(self):
        evt = ObservationEvent(type=EventType.AGENT_START, agent_name="test-agent")
        assert evt.type == EventType.AGENT_START
        assert evt.agent_name == "test-agent"
        assert evt.data == {}
        assert evt.timestamp > 0

    def test_create_event_with_data(self):
        evt = ObservationEvent(
            type=EventType.SKILL_COMPLETE,
            data={"skill_id": "page-observe", "output": "done"},
            agent_name="automation-agent",
            module="equipment",
            page="device-list",
        )
        assert evt.module == "equipment"
        assert evt.page == "device-list"
        assert evt.data["skill_id"] == "page-observe"


# ── ObservationBus ────────────────────────────────────────────────────

class TestObservationBus:
    def test_subscribe_and_emit(self):
        bus = ObservationBus()
        received = []

        bus.subscribe(EventType.SKILL_COMPLETE, lambda e: received.append(e))
        bus.emit(EventType.SKILL_COMPLETE, {"skill_id": "x"})

        assert len(received) == 1
        assert received[0].data["skill_id"] == "x"

    def test_multiple_subscribers_same_event(self):
        bus = ObservationBus()
        results = []

        bus.subscribe(EventType.TEST_PASSED, lambda e: results.append("a"))
        bus.subscribe(EventType.TEST_PASSED, lambda e: results.append("b"))
        bus.emit(EventType.TEST_PASSED, {"test": "test_login"})

        assert results == ["a", "b"]

    def test_different_event_types_isolated(self):
        bus = ObservationBus()
        received = []

        bus.subscribe(EventType.SKILL_START, lambda e: received.append(e))
        bus.emit(EventType.SKILL_COMPLETE, {})  # Different type

        assert len(received) == 0

    def test_unsubscribe_removes_listener(self):
        bus = ObservationBus()
        received = []

        cb = lambda e: received.append(e)
        bus.subscribe(EventType.AGENT_COMPLETE, cb)
        bus.emit(EventType.AGENT_COMPLETE, {})
        assert len(received) == 1

        bus.unsubscribe(EventType.AGENT_COMPLETE, cb)
        bus.emit(EventType.AGENT_COMPLETE, {})
        assert len(received) == 1  # No new events

    def test_unsubscribe_nonexistent_no_error(self):
        bus = ObservationBus()
        bus.unsubscribe(EventType.SKILL_RETRY, lambda e: None)
        # Should not raise

    def test_emit_stores_in_history(self):
        bus = ObservationBus()
        bus.emit(EventType.AGENT_START, {"phase": "init"})
        bus.emit(EventType.AGENT_COMPLETE, {"phase": "done"})

        assert len(bus._history) == 2
        assert bus._history[0].data["phase"] == "init"
        assert bus._history[1].data["phase"] == "done"

    def test_history_truncated_at_max(self):
        bus = ObservationBus()
        bus._max_history = 5

        for i in range(10):
            bus.emit(EventType.SKILL_START, {"i": i})

        assert len(bus._history) == 5
        # Should keep most recent
        assert bus._history[0].data["i"] == 5

    def test_emit_creates_event_with_correct_type(self):
        bus = ObservationBus()
        bus.emit(EventType.PROVIDER_FALLBACK, {"from": "claude", "to": "deepseek"})

        evt = bus._history[0]
        assert evt.type == EventType.PROVIDER_FALLBACK
        assert evt.data["from"] == "claude"

    def test_emit_with_agent_context(self):
        bus = ObservationBus()
        bus.emit(EventType.SKILL_FAILED, {"error": "timeout"},
                 agent_name="execution-agent", module="equipment")

        evt = bus._history[0]
        assert evt.agent_name == "execution-agent"
        assert evt.module == "equipment"

    def test_subscriber_exception_does_not_break_others(self):
        bus = ObservationBus()
        received = []

        def bad_callback(e):
            raise RuntimeError("boom")

        bus.subscribe(EventType.TEST_FAILED, bad_callback)
        bus.subscribe(EventType.TEST_FAILED, lambda e: received.append("ok"))
        bus.emit(EventType.TEST_FAILED, {})

        assert received == ["ok"]

    def test_singleton_get_bus(self):
        b1 = get_bus()
        b2 = get_bus()
        assert b1 is b2
