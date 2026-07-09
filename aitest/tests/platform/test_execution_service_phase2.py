from alice_engine.contracts import ExecutionContext, ExecutionResult
from alice_engine.core.runtime_environment import (
    current_llm_provider,
    current_mock_llm,
    current_workstudy,
)

from aitest.platform.execution_service import ExecutionService


class _FakeRecorder:
    def __init__(self, run_id: str, module: str, page: str = "", agent: str = ""):
        self.session_id = f"replay-{run_id}"

    def finish(self):
        return None


class _FakeEngine:
    def __init__(self, recorder):
        self._recorder = recorder

    def run(self):
        return {
            "success": True,
            "step": 2,
            "artifacts": ["a.md"],
            "memory": {
                "runtime_context": {
                    "context_sources": ["memory", "knowledge"],
                },
                "replay_session_id": self._recorder.session_id,
            },
        }

    def cancel(self):
        return None


class _FakeKernel:
    def __init__(self, recorder_session_id: str = ""):
        self._recorder_session_id = recorder_session_id

    def execute(self, request):
        return ExecutionResult(
            request_id=request.context.request_id or "req-1",
            run_id=request.run_id or "run-1",
            status="completed",
            module=request.module,
            pages=request.pages,
            agent=request.agent,
            mode=request.mode,
            agent_runs=2,
            artifacts=["a.md"],
            completed_phases=["Requirement"],
            metadata={
                "runtime_context": {"context_sources": ["memory", "knowledge"]},
                "replay_session_id": self._recorder_session_id,
            },
        )

    def cancel(self, run_id: str):
        return None


def test_execution_service_result_exposes_replay_and_runtime_context(monkeypatch, tmp_path):
    monkeypatch.setenv("AITEST_GOVERNANCE_POLICY_VERSION", "2026.07")
    monkeypatch.setattr("aitest.platform.replay.ReplayRecorder", _FakeRecorder)
    monkeypatch.setenv("AITEST_DB_BACKEND", "sqlite")
    import aitest.infra.database as database
    import aitest.infra.database_sqlite as database_sqlite
    database._backend = None
    database_sqlite._DB_PATH = tmp_path / "aitest.db"

    service = ExecutionService()

    monkeypatch.setattr(
        "aitest.platform.engine_factory.get_execution_kernel",
        lambda: _FakeKernel("replay-run-1"),
    )

    result = service.execute(
        ExecutionContext(workspace_id="ws", scopes=["read", "execute"], entrypoint="test"),
        module="equipment",
        pages=["alarm"],
        agent="automation-agent",
    )

    assert result.status == "completed"
    assert result.metadata["replay_session_id"].startswith("replay-")
    assert result.metadata["runtime_context"]["context_sources"] == ["memory", "knowledge"]
    assert result.metadata["policy_version"] == "2026.07"
    assert result.metadata["governance_version"] == "2026.07"


def test_execution_service_idempotency_returns_existing_request(monkeypatch, tmp_path):
    monkeypatch.setenv("AITEST_GOVERNANCE_POLICY_VERSION", "2026.07")
    monkeypatch.setenv("AITEST_DB_BACKEND", "sqlite")
    import aitest.infra.database as database
    import aitest.infra.database_sqlite as database_sqlite
    from aitest.platform.run_store import reset_run_store

    database._backend = None
    database_sqlite._DB_PATH = tmp_path / "aitest.db"
    reset_run_store()

    service = ExecutionService()
    ctx = ExecutionContext(workspace_id="ws", scopes=["read", "execute"], entrypoint="test")

    first = service.submit_async(
        ctx,
        module="equipment",
        pages=["alarm"],
        agent="automation-agent",
        idempotency_key="idem-123",
    )
    second = service.submit_async(
        ctx,
        module="equipment",
        pages=["alarm"],
        agent="automation-agent",
        idempotency_key="idem-123",
    )

    assert first.request_id == second.request_id
    rows = service._store.list_requests(workspace_id="ws", limit=10)
    assert len(rows) == 1
    assert rows[0].idempotency_key == "idem-123"


def test_execution_service_scopes_runtime_environment_for_kernel(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_PROVIDER", "outer-provider")
    monkeypatch.setenv("ENGINE_WORKSTUDY", "outer-workstudy")
    monkeypatch.delenv("MOCK_LLM", raising=False)

    seen = {}

    class _ScopedKernel:
        def execute(self, request):
            seen["provider"] = current_llm_provider()
            seen["workstudy"] = current_workstudy()
            seen["mock_llm"] = current_mock_llm()
            return ExecutionResult(
                request_id=request.context.request_id or "req-scope",
                run_id=request.run_id or "run-scope",
                status="completed",
                module=request.module,
                pages=request.pages,
                agent=request.agent,
                mode=request.mode,
                metadata={},
            )

    monkeypatch.setattr(
        "aitest.platform.engine_factory.get_execution_kernel",
        lambda: _ScopedKernel(),
    )

    service = ExecutionService()
    ctx = ExecutionContext(
        workspace_id="ws",
        scopes=["read", "execute"],
        entrypoint="test",
        metadata={"project_path": str(tmp_path)},
    )

    result = service.execute(
        ctx,
        module="equipment",
        pages=["alarm"],
        agent="automation-agent",
        provider="mock",
    )

    assert result.status == "completed"
    assert seen["provider"] == "mock"
    assert seen["workstudy"] == tmp_path
    assert seen["mock_llm"] is True
    assert current_llm_provider() == "outer-provider"
    assert current_workstudy().name == "outer-workstudy"
