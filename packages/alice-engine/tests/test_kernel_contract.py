"""Public execution kernel contract tests."""

from __future__ import annotations

from alice_engine import (
    ExecutionContext,
    ExecutionKernel,
    ExecutionResult,
    InlineExecutionKernel,
    KernelExecutionRequest,
    RuntimeExecutionKernel,
    SOPGraphExecutionKernel,
)


def _make_context() -> ExecutionContext:
    return ExecutionContext(
        workspace_id="ws-1",
        user_id="alice",
        scopes=["read", "execute"],
        org_id="org-1",
        module="equipment",
        pages=["alarm-config"],
        agent="automation-agent",
        mode="full",
        provider="mock",
        entrypoint="sdk",
        metadata={"source": "test"},
    )


def test_kernel_request_resolves_context_overrides():
    request = KernelExecutionRequest(
        context=_make_context(),
        kind="sop",
        run_id="run-123",
        checkpoint_thread_id="thread-123",
        metadata={"checkpoint": "enabled"},
    )

    resolved = request.resolved_context()

    assert request.effective_run_id == "run-123"
    assert request.module == "equipment"
    assert request.pages == ["alarm-config"]
    assert request.agent == "automation-agent"
    assert resolved.run_id == "run-123"
    assert resolved.metadata["source"] == "test"
    assert resolved.metadata["checkpoint"] == "enabled"


def test_inline_kernel_matches_public_protocol():
    def runner(request: KernelExecutionRequest) -> ExecutionResult:
        ctx = request.resolved_context()
        return ExecutionResult(
            request_id="req-1",
            run_id=ctx.run_id or "run-1",
            status="completed",
            module=ctx.module,
            pages=list(ctx.pages),
            agent=ctx.agent,
            mode=ctx.mode,
            summary=f"{request.kind}:{ctx.module}",
            metadata={"project_path": request.project_path},
        )

    kernel = InlineExecutionKernel(runner)

    assert isinstance(kernel, ExecutionKernel)
    result = kernel.execute(
        KernelExecutionRequest(
            context=_make_context(),
            kind="agent",
            project_path="D:/workspace/project",
        )
    )

    assert result.status == "completed"
    assert result.module == "equipment"
    assert result.summary == "agent:equipment"
    assert result.metadata["project_path"] == "D:/workspace/project"


def test_sop_graph_kernel_uses_existing_graph_adapter(monkeypatch):
    class FakeGraph:
        def run(self, state, event_bus=None):
            assert state["module"] == "equipment"
            assert state["knowledge_context"] == {"alarm-config": ["hint"]}
            assert state["memory_context"] == {"last_run": "demo"}
            return {
                **state,
                "status": "completed",
                "completed_phases": ["observe", "plan"],
                "agent_outputs": {"report-agent": {"success": True}},
            }

    monkeypatch.setattr(
        "alice_engine._internal.graph.build_sop_graph",
        lambda: FakeGraph(),
    )

    kernel = SOPGraphExecutionKernel()
    result = kernel.execute(
        KernelExecutionRequest(
            context=_make_context().with_execution(run_id="run-123", request_id="sdk-run-123"),
            kind="sop",
            project_path="D:/workspace/project",
            metadata={
                "knowledge_context": {"alarm-config": ["hint"]},
                "memory_context": {"last_run": "demo"},
            },
        )
    )

    assert isinstance(kernel, ExecutionKernel)
    assert result.run_id == "run-123"
    assert result.completed_phases == ["observe", "plan"]
    assert result.metadata["agent_outputs"]["report-agent"]["success"] is True


def test_runtime_kernel_runs_sop_runner(monkeypatch):
    class FakeRunner:
        def run(self):
            return {
                "status": "completed",
                "pages": ["alarm-config"],
                "completed_phases": ["Requirement"],
                "failed_phases": [],
                "agent_outputs": {"report-agent": {"success": True}},
                "memory": {"runtime_context": {"context_sources": ["memory"]}},
            }

    monkeypatch.setattr(
        "alice_engine.workflow.sop_runner.SOPRunner",
        lambda **kwargs: FakeRunner(),
    )

    kernel = RuntimeExecutionKernel()
    result = kernel.execute(
        KernelExecutionRequest(
            context=_make_context().with_execution(agent="sop", run_id="run-314", request_id="req-314"),
            kind="sop",
            project_path="D:/workspace/project",
        )
    )

    assert result.status == "completed"
    assert result.run_id == "run-314"
    assert result.completed_phases == ["Requirement"]
    assert result.metadata["runtime_context"]["context_sources"] == ["memory"]
