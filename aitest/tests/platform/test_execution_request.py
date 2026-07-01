"""Tests for platform/execution_request.py — Request lifecycle FSM.

Tests: RequestStatus, ACTIVE_STATUSES, TERMINAL_STATUSES,
ExecutionRequest state transitions (queue/dispatch/complete/fail/cancel),
is_active, is_terminal, latest_run_id, to_dict.
Pure dataclass — zero dependencies.
"""
import pytest

from aitest.platform.execution_request import (
    ExecutionRequest, RequestStatus,
    ACTIVE_STATUSES, TERMINAL_STATUSES,
)


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


def _make_request(**overrides) -> ExecutionRequest:
    defaults = {
        "request_id": "req-1",
        "workspace_id": "ws-1",
        "org_id": "org-1",
        "triggered_by": "user-1",
    }
    defaults.update(overrides)
    return ExecutionRequest(**defaults)


# ══════════════════════════════════════════════════════════════════════════
#  RequestStatus constants
# ══════════════════════════════════════════════════════════════════════════


class TestRequestStatus:
    def test_created(self):
        assert RequestStatus.CREATED == "created"

    def test_queued(self):
        assert RequestStatus.QUEUED == "queued"

    def test_running(self):
        assert RequestStatus.RUNNING == "running"

    def test_completed(self):
        assert RequestStatus.COMPLETED == "completed"

    def test_failed(self):
        assert RequestStatus.FAILED == "failed"

    def test_cancelled(self):
        assert RequestStatus.CANCELLED == "cancelled"


class TestStatusSets:
    def test_active_statuses(self):
        assert "created" in ACTIVE_STATUSES
        assert "queued" in ACTIVE_STATUSES
        assert "running" in ACTIVE_STATUSES

    def test_terminal_statuses(self):
        assert "completed" in TERMINAL_STATUSES
        assert "failed" in TERMINAL_STATUSES
        assert "cancelled" in TERMINAL_STATUSES

    def test_no_overlap(self):
        assert len(ACTIVE_STATUSES & TERMINAL_STATUSES) == 0


# ══════════════════════════════════════════════════════════════════════════
#  ExecutionRequest — construction
# ══════════════════════════════════════════════════════════════════════════


class TestConstruction:
    def test_defaults(self):
        req = _make_request()
        assert req.status == RequestStatus.CREATED
        assert req.trigger_type == "manual"
        assert req.mode == "full"
        assert req.priority == 0
        assert req.run_ids == []
        assert req.retry_count == 0

    def test_auto_created_at(self):
        req = _make_request()
        assert req.created_at != ""
        assert "T" in req.created_at

    def test_custom_values(self):
        req = _make_request(
            module="equipment",
            pages=["alarm", "camera"],
            priority=2,
            trigger_type="api",
        )
        assert req.module == "equipment"
        assert req.pages == ["alarm", "camera"]
        assert req.priority == 2
        assert req.trigger_type == "api"


# ══════════════════════════════════════════════════════════════════════════
#  is_active / is_terminal
# ══════════════════════════════════════════════════════════════════════════


class TestStatusProperties:
    def test_created_is_active(self):
        req = _make_request()
        assert req.is_active is True
        assert req.is_terminal is False

    def test_queued_is_active(self):
        req = _make_request(status=RequestStatus.QUEUED)
        assert req.is_active is True

    def test_running_is_active(self):
        req = _make_request(status=RequestStatus.RUNNING)
        assert req.is_active is True

    def test_completed_is_terminal(self):
        req = _make_request(status=RequestStatus.COMPLETED)
        assert req.is_terminal is True
        assert req.is_active is False

    def test_failed_is_terminal(self):
        req = _make_request(status=RequestStatus.FAILED)
        assert req.is_terminal is True

    def test_cancelled_is_terminal(self):
        req = _make_request(status=RequestStatus.CANCELLED)
        assert req.is_terminal is True


# ══════════════════════════════════════════════════════════════════════════
#  latest_run_id
# ══════════════════════════════════════════════════════════════════════════


class TestLatestRunId:
    def test_no_runs_returns_none(self):
        req = _make_request()
        assert req.latest_run_id is None

    def test_returns_last_run(self):
        req = _make_request(run_ids=["run-1", "run-2", "run-3"])
        assert req.latest_run_id == "run-3"

    def test_single_run(self):
        req = _make_request(run_ids=["run-abc"])
        assert req.latest_run_id == "run-abc"


# ══════════════════════════════════════════════════════════════════════════
#  State transitions
# ══════════════════════════════════════════════════════════════════════════


class TestQueue:
    def test_queue_from_created(self):
        req = _make_request()
        req.queue()
        assert req.status == RequestStatus.QUEUED

    def test_queue_from_non_created_raises(self):
        req = _make_request(status=RequestStatus.QUEUED)
        with pytest.raises(ValueError, match="Cannot queue"):
            req.queue()

    def test_queue_from_running_raises(self):
        req = _make_request(status=RequestStatus.RUNNING)
        with pytest.raises(ValueError, match="Cannot queue"):
            req.queue()


class TestDispatch:
    def test_dispatch_from_created(self):
        req = _make_request()
        req.dispatch("run-1")
        assert req.status == RequestStatus.RUNNING
        assert req.run_ids == ["run-1"]
        assert req.started_at is not None

    def test_dispatch_from_queued(self):
        req = _make_request(status=RequestStatus.QUEUED)
        req.dispatch("run-1")
        assert req.status == RequestStatus.RUNNING

    def test_dispatch_from_running_allows_retry(self):
        req = _make_request(status=RequestStatus.RUNNING, run_ids=["run-1"])
        req.dispatch("run-2")
        assert req.run_ids == ["run-1", "run-2"]

    def test_dispatch_from_terminal_raises(self):
        req = _make_request(status=RequestStatus.COMPLETED)
        with pytest.raises(ValueError, match="Cannot dispatch"):
            req.dispatch("run-x")

    def test_dispatch_preserves_started_at(self):
        req = _make_request()
        req.dispatch("run-1")
        first_started = req.started_at
        req.dispatch("run-2")
        assert req.started_at == first_started  # Not overwritten


class TestComplete:
    def test_complete(self):
        req = _make_request(status=RequestStatus.RUNNING)
        req.complete()
        assert req.status == RequestStatus.COMPLETED
        assert req.completed_at is not None

    def test_complete_sets_timestamp(self):
        req = _make_request(status=RequestStatus.RUNNING)
        assert req.completed_at is None
        req.complete()
        assert req.completed_at != ""


class TestFail:
    def test_fail(self):
        req = _make_request(status=RequestStatus.RUNNING)
        req.fail()
        assert req.status == RequestStatus.FAILED
        assert req.completed_at is not None


class TestCancel:
    def test_cancel_from_active(self):
        req = _make_request(status=RequestStatus.RUNNING)
        req.cancel()
        assert req.status == RequestStatus.CANCELLED

    def test_cancel_from_terminal_is_noop(self):
        req = _make_request(status=RequestStatus.COMPLETED)
        req.cancel()
        assert req.status == RequestStatus.COMPLETED  # Unchanged

    def test_cancel_from_failed_is_noop(self):
        req = _make_request(status=RequestStatus.FAILED)
        req.cancel()
        assert req.status == RequestStatus.FAILED


# ══════════════════════════════════════════════════════════════════════════
#  Full lifecycle
# ══════════════════════════════════════════════════════════════════════════


class TestFullLifecycle:
    def test_created_queued_dispatched_completed(self):
        req = _make_request()
        assert req.status == "created"

        req.queue()
        assert req.status == "queued"

        req.dispatch("run-1")
        assert req.status == "running"
        assert req.latest_run_id == "run-1"

        req.complete()
        assert req.status == "completed"
        assert req.is_terminal is True

    def test_created_queued_dispatched_failed(self):
        req = _make_request()
        req.queue()
        req.dispatch("run-1")
        req.fail()
        assert req.status == "failed"

    def test_retry_lifecycle(self):
        req = _make_request()
        req.queue()
        req.dispatch("run-1")
        req.fail()
        # Can't dispatch from terminal — need new request for retry
        assert req.is_terminal is True


# ══════════════════════════════════════════════════════════════════════════
#  to_dict
# ══════════════════════════════════════════════════════════════════════════


class TestToDict:
    def test_to_dict_includes_all_fields(self):
        req = _make_request(module="equipment", pages=["alarm"])
        d = req.to_dict()
        assert d["request_id"] == "req-1"
        assert d["module"] == "equipment"
        assert d["pages"] == ["alarm"]
        assert d["status"] == "created"
        assert d["latest_run_id"] is None

    def test_to_dict_after_dispatch(self):
        req = _make_request()
        req.dispatch("run-1")
        d = req.to_dict()
        assert d["status"] == "running"
        assert d["latest_run_id"] == "run-1"
        assert d["run_ids"] == ["run-1"]
