"""
Platform Architecture Freeze Tests — v1.0 Stabilization

Protects the frozen execution model:
  Run → RunEvent → EventBus → ExecutionService → RunStore → Consumer

These tests verify existing behavior. They do NOT drive new design.

Run: python -m pytest aitest/tests/test_platform_freeze.py -v
"""

import pytest
import uuid
import threading
import time


# ══════════════════════════════════════════════════════════════════════════
#  Run Lifecycle
# ══════════════════════════════════════════════════════════════════════════

class TestRunLifecycle:
    """Run dataclass: state transitions + freeze idempotency."""

    def test_run_created_running(self):
        from aitest.platform.run import Run
        run = Run(
            run_id="test-r1", request_id="req-1",
            workspace_id="ws-1", org_id="org-1", triggered_by="test",
        )
        assert run.status == "running"
        assert not run.is_frozen
        assert run.created_at != ""

    def test_run_complete_freezes(self):
        from aitest.platform.run import Run
        run = Run(run_id="test-r2", request_id="req-1", workspace_id="ws-1",
                  org_id="org-1", triggered_by="test")
        run.complete(total_tokens=500, total_cost=0.25, agent_runs=5)
        assert run.status == "completed"
        assert run.is_frozen
        assert run.total_tokens == 500
        assert run.total_cost == 0.25
        assert run.agent_runs == 5

    def test_run_fail_freezes(self):
        from aitest.platform.run import Run
        run = Run(run_id="test-r3", request_id="req-1", workspace_id="ws-1",
                  org_id="org-1", triggered_by="test")
        run.fail("something broke")
        assert run.status == "failed"
        assert run.is_frozen
        assert "something broke" in run.error_message

    def test_run_freeze_idempotent(self):
        """Once frozen, complete/fail/cancel must not change state."""
        from aitest.platform.run import Run
        run = Run(run_id="test-r4", request_id="req-1", workspace_id="ws-1",
                  org_id="org-1", triggered_by="test")
        run.complete(total_tokens=100)
        assert run.status == "completed"

        # Attempt to overwrite — must be ignored
        run.fail("should be ignored")
        assert run.status == "completed"
        run.cancel()
        assert run.status == "completed"
        run.timed_out()
        assert run.status == "completed"

    def test_run_cancel_from_running(self):
        from aitest.platform.run import Run
        run = Run(run_id="test-r5", request_id="req-1", workspace_id="ws-1",
                  org_id="org-1", triggered_by="test")
        run.cancel()
        assert run.status == "cancelled"
        assert run.is_frozen

    def test_run_to_dict(self):
        from aitest.platform.run import Run
        run = Run(run_id="test-r6", request_id="req-1", workspace_id="ws-1",
                  org_id="org-1", triggered_by="test",
                  capability="browser", agent="auto", module="equipment",
                  pages=["p1", "p2"], mode="full")
        d = run.to_dict()
        assert d["run_id"] == "test-r6"
        assert d["capability"] == "browser"
        assert d["pages"] == ["p1", "p2"]


# ══════════════════════════════════════════════════════════════════════════
#  RunEvent + EventType
# ══════════════════════════════════════════════════════════════════════════

class TestRunEvent:
    """RunEvent dataclass + make_event factory."""

    def test_make_event(self):
        from aitest.platform.run_event import make_event, EventType
        ev = make_event(EventType.RUN_COMPLETED, run_id="r1",
                        request_id="req1", total_tokens=100)
        assert ev.event_type == "run.completed"
        assert ev.run_id == "r1"
        assert ev.data["total_tokens"] == 100
        assert ev.event_id != ""
        assert ev.timestamp != ""

    def test_event_to_dict(self):
        from aitest.platform.run_event import make_event, EventType
        ev = make_event(EventType.EXECUTION_STARTED, run_id="r1",
                        request_id="req1", workspace_id="ws-1")
        d = ev.to_dict()
        assert d["event_type"] == "execution.started"
        assert d["data"]["workspace_id"] == "ws-1"

    def test_event_type_constants(self):
        from aitest.platform.run_event import EventType
        # Core execution events — must exist
        assert EventType.EXECUTION_REQUESTED == "execution.requested"
        assert EventType.EXECUTION_STARTED == "execution.started"
        assert EventType.RUN_COMPLETED == "run.completed"
        assert EventType.RUN_FAILED == "run.failed"
        assert EventType.RUN_CANCELLED == "run.cancelled"
        assert EventType.COST_RECORDED == "cost.recorded"


# ══════════════════════════════════════════════════════════════════════════
#  EventBus
# ══════════════════════════════════════════════════════════════════════════

class TestEventBus:
    """EventBus: subscribe, unsubscribe, publish, wildcards."""

    def test_subscribe_and_publish(self):
        from aitest.platform.event_bus import EventBus
        from aitest.platform.run_event import RunEvent, EventType
        bus = EventBus()
        received = []
        bus.subscribe(EventType.RUN_COMPLETED, received.append)
        ev = RunEvent(event_id="e1", event_type=EventType.RUN_COMPLETED, run_id="r1")
        bus.publish(ev)
        assert len(received) == 1
        assert received[0].event_id == "e1"

    def test_unsubscribe(self):
        from aitest.platform.event_bus import EventBus
        from aitest.platform.run_event import RunEvent, EventType
        bus = EventBus()
        received = []
        bus.subscribe(EventType.RUN_COMPLETED, received.append)
        bus.unsubscribe(EventType.RUN_COMPLETED, received.append)
        ev = RunEvent(event_id="e2", event_type=EventType.RUN_COMPLETED, run_id="r1")
        bus.publish(ev)
        assert len(received) == 0

    def test_wildcard_subscriber(self):
        from aitest.platform.event_bus import EventBus
        from aitest.platform.run_event import RunEvent, EventType
        bus = EventBus()
        received = []
        bus.subscribe("*", received.append)
        bus.publish(RunEvent(event_id="e3", event_type=EventType.RUN_COMPLETED, run_id="r1"))
        bus.publish(RunEvent(event_id="e4", event_type=EventType.RUN_FAILED, run_id="r2"))
        assert len(received) == 2

    def test_best_effort_no_crash_on_exception(self):
        from aitest.platform.event_bus import EventBus
        from aitest.platform.run_event import RunEvent, EventType
        bus = EventBus()

        def bad_handler(event):
            raise RuntimeError("boom")

        good = []
        bus.subscribe(EventType.RUN_COMPLETED, bad_handler)
        bus.subscribe(EventType.RUN_COMPLETED, good.append)
        bus.publish(RunEvent(event_id="e5", event_type=EventType.RUN_COMPLETED, run_id="r1"))
        assert len(good) == 1  # second handler still called

    def test_singleton(self):
        from aitest.platform.event_bus import get_bus
        b1 = get_bus()
        b2 = get_bus()
        assert b1 is b2


# ══════════════════════════════════════════════════════════════════════════
#  RunStore
# ══════════════════════════════════════════════════════════════════════════

class TestRunStore:
    """RunStore: save/load Run, save/load ExecutionRequest, list events."""

    def test_save_and_load_run(self):
        from aitest.platform.run_store import RunStore
        from aitest.platform.run import Run
        from pathlib import Path
        import tempfile, os
        db = Path(tempfile.mktemp(suffix=".db"))
        try:
            store = RunStore(db_path=db)
            run = Run(run_id="rs-r1", request_id="req-1", workspace_id="ws-1",
                      org_id="org-1", triggered_by="test")
            run.complete(total_tokens=100)
            store.save_run(run)

            loaded = store.load_run("rs-r1")
            assert loaded is not None
            assert loaded.status == "completed"
            assert loaded.total_tokens == 100
        finally:
            if db.exists():
                db.unlink()

    def test_save_and_load_request(self):
        from aitest.platform.run_store import RunStore
        from aitest.platform.execution_request import ExecutionRequest
        from pathlib import Path
        import tempfile, os
        db = Path(tempfile.mktemp(suffix=".db"))
        try:
            store = RunStore(db_path=db)
            req = ExecutionRequest(
                request_id="rs-req1", workspace_id="ws-1", org_id="org-1",
                triggered_by="test", module="equipment", pages=["p1"],
            )
            req.queue()
            store.save_request(req)

            loaded = store.load_request("rs-req1")
            assert loaded is not None
            assert loaded.module == "equipment"
            assert loaded.pages == ["p1"]
        finally:
            if db.exists():
                db.unlink()

    def test_list_runs_filtered(self):
        from aitest.platform.run_store import RunStore
        from aitest.platform.run import Run
        from pathlib import Path
        import tempfile, os
        db = Path(tempfile.mktemp(suffix=".db"))
        try:
            store = RunStore(db_path=db)
            store.save_run(Run(run_id="rs-r-ws1", request_id="req-1",
                               workspace_id="ws-1", org_id="org-1", triggered_by="t"))
            store.save_run(Run(run_id="rs-r-ws2", request_id="req-2",
                               workspace_id="ws-2", org_id="org-1", triggered_by="t"))

            runs = store.list_runs(workspace_id="ws-1")
            assert len(runs) == 1
            assert runs[0].run_id == "rs-r-ws1"
        finally:
            if db.exists():
                db.unlink()

    def test_save_and_list_events(self):
        from aitest.platform.run_store import RunStore
        from aitest.platform.run_event import make_event, EventType
        from pathlib import Path
        import tempfile, os
        db = Path(tempfile.mktemp(suffix=".db"))
        try:
            store = RunStore(db_path=db)
            ev = make_event(EventType.RUN_COMPLETED, run_id="rs-r2",
                            request_id="req-3", module="m", agent="a")
            store.save_event(ev)

            events = store.list_events(run_id="rs-r2")
            assert len(events) == 1
            assert events[0].event_type == "run.completed"
        finally:
            if db.exists():
                db.unlink()


# ══════════════════════════════════════════════════════════════════════════
#  ExecutionRequest
# ══════════════════════════════════════════════════════════════════════════

class TestExecutionRequest:
    """ExecutionRequest: lifecycle + one-to-many run relationship."""

    def test_lifecycle_created_to_completed(self):
        from aitest.platform.execution_request import ExecutionRequest, RequestStatus
        req = ExecutionRequest(
            request_id="er1", workspace_id="ws-1", org_id="org-1",
            triggered_by="test",
        )
        assert req.status == RequestStatus.CREATED
        req.queue()
        assert req.status == RequestStatus.QUEUED
        req.dispatch("run-1")
        assert req.status == RequestStatus.RUNNING
        assert req.run_ids == ["run-1"]
        req.complete()
        assert req.status == RequestStatus.COMPLETED
        assert req.is_terminal

    def test_one_to_many_runs(self):
        from aitest.platform.execution_request import ExecutionRequest
        req = ExecutionRequest(
            request_id="er2", workspace_id="ws-1", org_id="org-1",
            triggered_by="test",
        )
        req.queue()
        req.dispatch("run-1")
        req.dispatch("run-2")  # retry
        req.dispatch("run-3")  # another retry
        assert req.run_ids == ["run-1", "run-2", "run-3"]
        assert req.latest_run_id == "run-3"

    def test_cannot_queue_twice(self):
        from aitest.platform.execution_request import ExecutionRequest
        req = ExecutionRequest(
            request_id="er3", workspace_id="ws-1", org_id="org-1",
            triggered_by="test",
        )
        req.queue()
        with pytest.raises(ValueError):
            req.queue()

    def test_cannot_dispatch_terminal(self):
        from aitest.platform.execution_request import ExecutionRequest
        req = ExecutionRequest(
            request_id="er4", workspace_id="ws-1", org_id="org-1",
            triggered_by="test",
        )
        req.queue()
        req.dispatch("run-1")
        req.complete()
        with pytest.raises(ValueError):
            req.dispatch("run-2")


# ══════════════════════════════════════════════════════════════════════════
#  Consumer Protocol + Implementations
# ══════════════════════════════════════════════════════════════════════════

class TestConsumers:
    """Consumers: start/stop lifecycle, idempotency, protocol compliance."""

    def test_metrics_consumer_lifecycle(self):
        from aitest.platform.metrics_consumer import MetricsConsumer
        mc = MetricsConsumer()
        assert not mc.is_active
        mc.start()
        assert mc.is_active
        mc.stop()
        assert not mc.is_active

    def test_metrics_consumer_idempotent_start(self):
        from aitest.platform.metrics_consumer import MetricsConsumer
        mc = MetricsConsumer()
        mc.start()
        mc.start()  # duplicate
        mc.start()  # duplicate
        assert mc.is_active
        mc.stop()

    def test_metrics_consumer_idempotent_counting(self):
        from aitest.platform.run_event import make_event, EventType
        from aitest.platform.metrics_consumer import MetricsConsumer
        mc = MetricsConsumer()
        mc.start()

        ev = make_event(EventType.RUN_COMPLETED, event_id="dup-m1",
                        run_id="r1", request_id="req1",
                        workspace_id="ws-1", org_id="org-1",
                        module="m", agent="a",
                        total_tokens=100, total_cost=0.05, agent_runs=3)
        mc._on_run_completed(ev)
        mc._on_run_completed(ev)  # duplicate — must be ignored
        snap = mc.snapshot()
        assert snap["runs"]["total"] == 1
        mc.stop()

    def test_quota_usage_idempotent(self):
        from aitest.platform.run_event import make_event, EventType
        from aitest.platform.quota_usage import QuotaUsageConsumer
        qu = QuotaUsageConsumer()
        qu.start()

        ev = make_event(EventType.RUN_COMPLETED, event_id="dup-q1",
                        run_id="r1", request_id="req1",
                        workspace_id="ws-1", org_id="org-1",
                        total_tokens=200, total_cost=0.10,
                        module="m", agent="a")
        qu._on_run_completed(ev)
        qu._on_run_completed(ev)  # duplicate
        usage = qu.get_usage("ws-1")
        assert usage["run_count"] == 1
        qu.stop()

    def test_billing_hook_idempotent(self):
        from aitest.platform.run_event import make_event, EventType
        from aitest.platform.billing_hook import BillingHookConsumer
        bh = BillingHookConsumer()
        bh.start()

        ev = make_event(EventType.RUN_COMPLETED, event_id="dup-b1",
                        run_id="r1", request_id="req1",
                        workspace_id="ws-1", org_id="org-1",
                        total_tokens=300, total_cost=0.15,
                        module="m", agent="a")
        bh._on_run_completed(ev)
        bh._on_run_completed(ev)  # duplicate
        assert len(bh._seen) == 1
        bh.stop()

    def test_consumer_protocol(self):
        """All consumers must structurally match RunEventConsumer Protocol."""
        from aitest.platform.consumer import RunEventConsumer
        from aitest.platform.metrics_consumer import MetricsConsumer
        from aitest.platform.quota_usage import QuotaUsageConsumer
        from aitest.platform.billing_hook import BillingHookConsumer
        from aitest.platform.audit_log import AuditLogger

        for cls in [MetricsConsumer, QuotaUsageConsumer, BillingHookConsumer, AuditLogger]:
            assert hasattr(cls, 'start'), f"{cls.__name__} missing start()"
            assert hasattr(cls, 'stop'), f"{cls.__name__} missing stop()"
            assert hasattr(cls, 'is_active'), f"{cls.__name__} missing is_active"


# ══════════════════════════════════════════════════════════════════════════
#  Integration: ExecutionService flow
# ══════════════════════════════════════════════════════════════════════════

class TestExecutionServiceIntegration:
    """End-to-end: ExecutionContext → ExecutionService → Run → Events."""

    def test_execution_context_scope_check(self):
        from aitest.platform.workspace import ExecutionContext
        ctx = ExecutionContext(
            workspace_id="ws-1", user_id="alice",
            scopes=["read", "execute"], org_id="org-1",
        )
        ctx.require("execute")  # must not raise
        with pytest.raises(PermissionError):
            ctx.require("admin")

    def test_execution_result_dataclass(self):
        from aitest.platform.execution_service import ExecutionResult
        result = ExecutionResult(
            request_id="req-1", run_id="run-1", status="completed",
            total_tokens=500, total_cost=0.25, agent_runs=5,
            duration_ms=1234.5,
        )
        assert result.status == "completed"
        assert result.request_id == "req-1"

    def test_cancel_non_existent(self):
        from aitest.platform.execution_service import ExecutionService
        svc = ExecutionService()
        cancelled = svc.cancel("nonexistent-id")
        assert not cancelled
