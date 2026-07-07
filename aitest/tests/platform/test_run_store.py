"""Tests for platform/run_store.py — SQLite persistence for Run + RunEvent.

Tests: RunStore CRUD (save_run, load_run, list_runs, count_runs),
Event CRUD (save_event, list_events), Request CRUD.
Uses temp SQLite DB — no real DB dependency.
"""
import pytest
from pathlib import Path

from aitest.platform.run_store import RunStore
from aitest.platform.run import Run
from aitest.platform.run_event import RunEvent, make_event
from aitest.platform.execution_request import ExecutionRequest


# ══════════════════════════════════════════════════════════════════════════
#  Fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def store(temp_dir):
    db_path = temp_dir / "test_runs.db"
    return RunStore(db_path=db_path)


def _make_run(**overrides) -> Run:
    defaults = {
        "run_id": "run-1",
        "request_id": "req-1",
        "workspace_id": "ws-1",
        "org_id": "org-1",
        "triggered_by": "user-1",
    }
    defaults.update(overrides)
    return Run(**defaults)


def _make_request(**overrides) -> ExecutionRequest:
    defaults = {
        "request_id": "req-1",
        "workspace_id": "ws-1",
        "org_id": "org-1",
    }
    defaults.update(overrides)
    return ExecutionRequest(**defaults)


# ══════════════════════════════════════════════════════════════════════════
#  Run CRUD
# ══════════════════════════════════════════════════════════════════════════


class TestRunCRUD:
    def test_save_and_load_run(self, store):
        run = _make_run()
        store.save_run(run)
        loaded = store.load_run("run-1")
        assert loaded is not None
        assert loaded.run_id == "run-1"
        assert loaded.workspace_id == "ws-1"

    def test_load_nonexistent_returns_none(self, store):
        assert store.load_run("nonexistent") is None

    def test_save_run_with_pages(self, store):
        run = _make_run(pages=["alarm", "camera"])
        store.save_run(run)
        loaded = store.load_run("run-1")
        assert loaded.pages == ["alarm", "camera"]

    def test_save_run_with_artifacts(self, store):
        run = _make_run(artifacts=["report.xlsx", "test.py"])
        store.save_run(run)
        loaded = store.load_run("run-1")
        assert loaded.artifacts == ["report.xlsx", "test.py"]

    def test_save_run_upsert(self, store):
        run = _make_run(status="running")
        store.save_run(run)
        run.status = "completed"
        store.save_run(run)
        loaded = store.load_run("run-1")
        assert loaded.status == "completed"

    def test_list_runs_empty(self, store):
        assert store.list_runs() == []

    def test_list_runs_returns_all(self, store):
        store.save_run(_make_run(run_id="r1"))
        store.save_run(_make_run(run_id="r2"))
        runs = store.list_runs()
        assert len(runs) == 2

    def test_list_runs_filter_by_workspace(self, store):
        store.save_run(_make_run(run_id="r1", workspace_id="ws-1"))
        store.save_run(_make_run(run_id="r2", workspace_id="ws-2"))
        runs = store.list_runs(workspace_id="ws-1")
        assert len(runs) == 1
        assert runs[0].run_id == "r1"

    def test_list_runs_filter_by_status(self, store):
        store.save_run(_make_run(run_id="r1", status="running"))
        store.save_run(_make_run(run_id="r2", status="completed"))
        runs = store.list_runs(status="running")
        assert len(runs) == 1

    def test_list_runs_respects_limit(self, store):
        for i in range(10):
            store.save_run(_make_run(run_id=f"r{i}"))
        runs = store.list_runs(limit=5)
        assert len(runs) == 5

    def test_count_runs(self, store):
        store.save_run(_make_run(run_id="r1"))
        store.save_run(_make_run(run_id="r2"))
        assert store.count_runs() == 2

    def test_count_runs_by_workspace(self, store):
        store.save_run(_make_run(run_id="r1", workspace_id="ws-1"))
        store.save_run(_make_run(run_id="r2", workspace_id="ws-2"))
        assert store.count_runs(workspace_id="ws-1") == 1


# ══════════════════════════════════════════════════════════════════════════
#  Event CRUD
# ══════════════════════════════════════════════════════════════════════════


class TestEventCRUD:
    def test_save_and_list_event(self, store):
        ev = make_event("run.completed", run_id="run-1")
        store.save_event(ev)
        events = store.list_events(run_id="run-1")
        assert len(events) == 1
        assert events[0].event_type == "run.completed"

    def test_list_events_empty(self, store):
        assert store.list_events() == []

    def test_list_events_filter_by_type(self, store):
        store.save_event(make_event("run.completed", run_id="r1"))
        store.save_event(make_event("run.failed", run_id="r1"))
        events = store.list_events(event_type="run.completed")
        assert len(events) == 1

    def test_list_events_respects_limit(self, store):
        for i in range(10):
            store.save_event(make_event("run.completed", run_id=f"r{i}"))
        events = store.list_events(limit=3)
        assert len(events) == 3

    def test_event_with_data(self, store):
        ev = make_event("run.completed", run_id="r1", tokens=1000)
        store.save_event(ev)
        events = store.list_events(run_id="r1")
        assert events[0].data["tokens"] == 1000


# ══════════════════════════════════════════════════════════════════════════
#  Request CRUD
# ══════════════════════════════════════════════════════════════════════════


class TestRequestCRUD:
    def test_save_and_load_request(self, store):
        req = _make_request()
        store.save_request(req)
        loaded = store.load_request("req-1")
        assert loaded is not None
        assert loaded.request_id == "req-1"

    def test_load_nonexistent_request(self, store):
        assert store.load_request("nonexistent") is None

    def test_save_request_with_pages(self, store):
        req = _make_request(pages=["alarm", "camera"])
        store.save_request(req)
        loaded = store.load_request("req-1")
        assert loaded.pages == ["alarm", "camera"]

    def test_save_request_upsert(self, store):
        req = _make_request(status="created")
        store.save_request(req)
        req.status = "queued"
        store.save_request(req)
        loaded = store.load_request("req-1")
        assert loaded.status == "queued"

    def test_recover_stale_requests_requeues_running_request(self, store):
        from datetime import datetime, timezone, timedelta

        old_started_at = (datetime.now(timezone.utc) - timedelta(seconds=7200)).isoformat()
        req = _make_request(
            request_id="req-stale",
            status="running",
            started_at=old_started_at,
            run_ids=["run-stale"],
        )
        store.save_request(req)
        run = _make_run(run_id="run-stale", request_id="req-stale", status="running")
        store.save_run(run)

        recovered = store.recover_stale_requests()

        assert recovered == 1
        loaded = store.load_request("req-stale")
        assert loaded.status == "queued"
        assert loaded.started_at is None
        assert loaded.completed_at is None
        assert loaded.next_retry_at is None

        loaded_run = store.load_run("run-stale")
        assert loaded_run.status == "failed"
        assert loaded_run.error_message == "Server crash — run interrupted"

    def test_recover_stale_requests_ignores_recent_running_request(self, store):
        from datetime import datetime, timezone

        req = _make_request(
            request_id="req-recent",
            status="running",
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        store.save_request(req)

        recovered = store.recover_stale_requests()

        assert recovered == 0
        loaded = store.load_request("req-recent")
        assert loaded.status == "running"
