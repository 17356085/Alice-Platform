"""Tests for platform/run.py + run_event.py — Run lifecycle + RunEvent.

Tests: Run state transitions (complete/fail/cancel/timed_out),
idempotency (frozen state), Run.to_dict(), RunEvent creation,
EventType constants, make_event factory.
"""
import pytest

from aitest.platform.run import Run, TERMINAL_STATES
from aitest.platform.run_event import (
    RunEvent, EventType, make_event,
)


# ══════════════════════════════════════════════════════════════════════════
#  Run — construction
# ══════════════════════════════════════════════════════════════════════════


class TestRunConstruction:
    def test_minimal_run(self):
        run = Run(
            run_id="r1", request_id="req-1",
            workspace_id="ws-1", org_id="org-1",
            triggered_by="user-1",
        )
        assert run.run_id == "r1"
        assert run.status == "running"
        assert run.is_terminal is False

    def test_created_at_auto_set(self):
        run = Run(run_id="r1", request_id="req-1",
                  workspace_id="ws-1", org_id="org-1", triggered_by="u1")
        assert run.created_at != ""
        assert "T" in run.created_at  # ISO format

    def test_created_at_respected_when_provided(self):
        run = Run(run_id="r1", request_id="req-1",
                  workspace_id="ws-1", org_id="org-1",
                  triggered_by="u1", created_at="2026-01-01T00:00:00")
        assert run.created_at == "2026-01-01T00:00:00"

    def test_defaults(self):
        run = Run(run_id="r1", request_id="req-1",
                  workspace_id="ws-1", org_id="org-1", triggered_by="u1")
        assert run.capability == "browser"
        assert run.agent == ""
        assert run.pages == []
        assert run.mode == "full"


# ══════════════════════════════════════════════════════════════════════════
#  Run — state transitions
# ══════════════════════════════════════════════════════════════════════════


class TestRunTransitions:
    def test_complete_sets_status(self):
        run = Run(run_id="r1", request_id="req-1",
                  workspace_id="ws-1", org_id="org-1", triggered_by="u1")
        run.complete(total_tokens=1000, total_cost=0.05, agent_runs=3,
                     artifacts=["report.xlsx"])
        assert run.status == "completed"
        assert run.is_terminal is True
        assert run.is_frozen is True
        assert run.total_tokens == 1000
        assert run.artifacts == ["report.xlsx"]

    def test_fail_sets_status(self):
        run = Run(run_id="r1", request_id="req-1",
                  workspace_id="ws-1", org_id="org-1", triggered_by="u1")
        run.fail("Something broke")
        assert run.status == "failed"
        assert run.is_terminal is True
        assert run.error_message == "Something broke"

    def test_cancel_sets_status(self):
        run = Run(run_id="r1", request_id="req-1",
                  workspace_id="ws-1", org_id="org-1", triggered_by="u1")
        run.cancel()
        assert run.status == "cancelled"
        assert run.is_terminal is True

    def test_timed_out_sets_status(self):
        run = Run(run_id="r1", request_id="req-1",
                  workspace_id="ws-1", org_id="org-1", triggered_by="u1")
        run.timed_out()
        assert run.status == "timed_out"
        assert run.is_terminal is True

    def test_completed_at_set_on_complete(self):
        run = Run(run_id="r1", request_id="req-1",
                  workspace_id="ws-1", org_id="org-1", triggered_by="u1")
        assert run.completed_at == ""
        run.complete()
        assert run.completed_at != ""

    def test_complete_is_idempotent(self):
        run = Run(run_id="r1", request_id="req-1",
                  workspace_id="ws-1", org_id="org-1", triggered_by="u1")
        run.complete(total_tokens=1000)
        run.complete(total_tokens=9999)  # Should be ignored
        assert run.total_tokens == 1000  # Unchanged

    def test_fail_is_idempotent(self):
        run = Run(run_id="r1", request_id="req-1",
                  workspace_id="ws-1", org_id="org-1", triggered_by="u1")
        run.fail("first error")
        run.fail("second error")
        assert run.error_message == "first error"

    def test_cancel_is_idempotent(self):
        run = Run(run_id="r1", request_id="req-1",
                  workspace_id="ws-1", org_id="org-1", triggered_by="u1")
        run.complete()
        run.cancel()  # Ignored — already frozen
        assert run.status == "completed"

    def test_to_dict(self):
        run = Run(run_id="r1", request_id="req-1",
                  workspace_id="ws-1", org_id="org-1",
                  triggered_by="u1", module="equipment",
                  pages=["alarm", "config"])
        run.complete(total_tokens=500, total_cost=0.03)
        d = run.to_dict()
        assert d["run_id"] == "r1"
        assert d["status"] == "completed"
        assert d["module"] == "equipment"
        assert d["pages"] == ["alarm", "config"]
        assert d["total_tokens"] == 500


# ══════════════════════════════════════════════════════════════════════════
#  TERMINAL_STATES
# ══════════════════════════════════════════════════════════════════════════


class TestTerminalStates:
    def test_all_are_terminal(self):
        for state in TERMINAL_STATES:
            run = Run(run_id="r1", request_id="req-1",
                      workspace_id="ws-1", org_id="org-1",
                      triggered_by="u1", status=state)
            assert run.is_terminal is True, f"{state} should be terminal"


# ══════════════════════════════════════════════════════════════════════════
#  RunEvent
# ══════════════════════════════════════════════════════════════════════════


class TestRunEvent:
    def test_auto_timestamp(self):
        ev = RunEvent(event_id="e1", event_type="run.completed", run_id="r1")
        assert ev.timestamp != ""
        assert "T" in ev.timestamp

    def test_to_dict(self):
        ev = RunEvent(
            event_id="e1", event_type="run.completed", run_id="r1",
            request_id="req-1", data={"tokens": 1000},
        )
        d = ev.to_dict()
        assert d["event_id"] == "e1"
        assert d["data"]["tokens"] == 1000

    def test_data_default_empty(self):
        ev = RunEvent(event_id="e1", event_type="run.started", run_id="r1")
        assert ev.data == {}


# ══════════════════════════════════════════════════════════════════════════
#  EventType constants
# ══════════════════════════════════════════════════════════════════════════


class TestEventType:
    def test_execution_events(self):
        assert EventType.EXECUTION_REQUESTED == "execution.requested"
        assert EventType.RUN_COMPLETED == "run.completed"
        assert EventType.RUN_FAILED == "run.failed"

    def test_phase_events(self):
        assert EventType.PHASE_STARTED == "phase.started"
        assert EventType.PHASE_COMPLETED == "phase.completed"

    def test_platform_events(self):
        assert EventType.ORG_CREATED == "org.created"
        assert EventType.WORKSPACE_CREATED == "workspace.created"

    def test_no_duplicate_values(self):
        """All EventType values must be unique."""
        attrs = [v for k, v in vars(EventType).items() if not k.startswith("_") and isinstance(v, str)]
        assert len(attrs) == len(set(attrs))


# ══════════════════════════════════════════════════════════════════════════
#  make_event
# ══════════════════════════════════════════════════════════════════════════


class TestMakeEvent:
    def test_creates_event_with_generated_id(self):
        ev = make_event("run.completed", run_id="r1")
        assert isinstance(ev, RunEvent)
        assert ev.event_id != ""
        assert ev.run_id == "r1"

    def test_unique_event_ids(self):
        e1 = make_event("run.started")
        e2 = make_event("run.started")
        assert e1.event_id != e2.event_id

    def test_passes_extra_kwargs_as_data(self):
        ev = make_event("phase.completed", run_id="r1",
                        phase="automation", duration_ms=4200)
        assert ev.data["phase"] == "automation"
        assert ev.data["duration_ms"] == 4200
