from alice_engine.contracts import ExecutionContext

from aitest.platform.execution_service import ExecutionService
from aitest.platform.execution_worker import ExecutionWorker


def test_async_submit_queues_and_worker_claims_request(monkeypatch, tmp_path):
    monkeypatch.setenv("AITEST_DB_BACKEND", "sqlite")
    import aitest.infra.database as database
    import aitest.infra.database_sqlite as database_sqlite
    from aitest.platform.run_store import reset_run_store

    database._backend = None
    database_sqlite._DB_PATH = tmp_path / "aitest.db"
    reset_run_store()

    service = ExecutionService()
    ctx = ExecutionContext(workspace_id="ws", scopes=["read", "execute"], entrypoint="test")

    pending = service.submit_async(
        ctx,
        module="equipment",
        pages=["alarm"],
        agent="automation-agent",
    )

    request = service._store.load_request(pending.request_id)
    assert request is not None
    assert request.status == "queued"
    assert request.agent == "automation-agent"

    seen = {}

    def _fake_run_request_flow(ctx, request, *, agent, t0, verbose, checkpoint_thread_id="", allow_retry=False):
        seen["agent"] = agent
        seen["request_status"] = request.status
        seen["checkpoint_thread_id"] = checkpoint_thread_id
        request.complete()
        service._store.save_request(request)
        return None

    monkeypatch.setattr(service, "_run_request_flow", _fake_run_request_flow)

    worker = ExecutionWorker(service=service, store=service._store, poll_interval=0.1)
    assert worker.run_once() is True

    loaded = service._store.load_request(pending.request_id)
    assert loaded is not None
    assert loaded.status == "completed"
    assert seen["agent"] == "automation-agent"
    assert seen["request_status"] == "running"
    assert seen["checkpoint_thread_id"] == pending.request_id


def test_worker_requeues_retryable_failure(monkeypatch, tmp_path):
    monkeypatch.setenv("AITEST_DB_BACKEND", "sqlite")
    import aitest.infra.database as database
    import aitest.infra.database_sqlite as database_sqlite
    from aitest.platform.run_store import reset_run_store

    database._backend = None
    database_sqlite._DB_PATH = tmp_path / "aitest.db"
    reset_run_store()

    service = ExecutionService()
    ctx = ExecutionContext(workspace_id="ws", scopes=["read", "execute"], entrypoint="test")

    pending = service.submit_async(
        ctx,
        module="equipment",
        pages=["alarm"],
        agent="automation-agent",
        max_retries=2,
    )

    class _FailingKernel:
        def execute(self, request):
            raise RuntimeError("temporary network glitch")

        def cancel(self, run_id: str):
            return None

    monkeypatch.setattr(
        "aitest.platform.engine_factory.get_execution_kernel",
        lambda: _FailingKernel(),
    )

    worker = ExecutionWorker(service=service, store=service._store, poll_interval=0.1)
    assert worker.run_once() is True

    loaded = service._store.load_request(pending.request_id)
    assert loaded is not None
    assert loaded.status == "queued"
    assert loaded.retry_count == 1
    assert loaded.next_retry_at is not None
