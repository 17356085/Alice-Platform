"""Engine EventBus adapter regression tests."""

from __future__ import annotations

from aitest.engine.event_bus import EngineEventBusAdapter


class _FakePlatformBus:
    def __init__(self) -> None:
        self.events = []

    def publish(self, event) -> None:
        self.events.append(event)


def test_engine_event_bus_adapter_projects_to_platform_run_event():
    bus = EngineEventBusAdapter()
    fake_platform_bus = _FakePlatformBus()
    bus._platform_bus = fake_platform_bus

    bus.emit(
        "skill_start",
        {
            "run_id": "run-1",
            "request_id": "req-1",
            "module": "equipment",
            "agent": "automation-agent",
            "status": "running",
            "custom": "value",
        },
    )

    assert len(fake_platform_bus.events) == 1
    event = fake_platform_bus.events[0]
    assert event.event_type == "engine.skill_start"
    assert event.run_id == "run-1"
    assert event.request_id == "req-1"
    assert event.data["module"] == "equipment"
    assert event.data["agent"] == "automation-agent"
    assert event.data["custom"] == "value"
