"""Public execution kernel contract shared by SDK and platform facades.

Phase 7 freezes this boundary before either caller changes its execution path.
The kernel owns execution semantics only. Platform request/run lifecycle,
tenant checks, audit, billing, and transport adapters stay outside this layer.
"""

from __future__ import annotations

import asyncio
import threading
import time
from dataclasses import dataclass, field, replace
from typing import Any, Callable, Literal, Protocol, runtime_checkable

from .contracts import ExecutionContext, ExecutionResult

KernelKind = Literal["agent", "sop"]
KernelExecutionResult = ExecutionResult


@dataclass(frozen=True)
class KernelExecutionRequest:
    """Minimal stable input contract for the public execution kernel."""

    context: ExecutionContext
    kind: KernelKind = "agent"
    project_path: str = ""
    run_id: str = ""
    checkpoint_thread_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def module(self) -> str:
        return self.context.module

    @property
    def pages(self) -> list[str]:
        return list(self.context.pages)

    @property
    def agent(self) -> str:
        return self.context.agent

    @property
    def mode(self) -> str:
        return self.context.mode

    @property
    def provider(self) -> str:
        return self.context.provider

    @property
    def effective_run_id(self) -> str:
        return self.run_id or self.context.run_id

    def resolved_context(self) -> ExecutionContext:
        """Merge kernel-level overrides onto the shared execution context."""
        if not self.run_id and not self.metadata:
            return self.context
        return self.context.with_execution(
            run_id=self.run_id or None,
            metadata=self.metadata or None,
        )

    def with_updates(self, **changes: Any) -> "KernelExecutionRequest":
        """Return an updated copy while preserving immutability at the boundary."""
        return replace(self, **changes)


@runtime_checkable
class ExecutionKernel(Protocol):
    """Stable sync/async contract shared by standalone and platform callers."""

    def execute(self, request: KernelExecutionRequest) -> KernelExecutionResult:
        """Run one execution request and return the unified result model."""
        ...

    async def execute_async(self, request: KernelExecutionRequest) -> KernelExecutionResult:
        """Async twin of ``execute`` for callers that already live in an event loop."""
        ...


class InlineExecutionKernel:
    """Tiny adapter for tests and simple local composition roots."""

    def __init__(
        self,
        runner: Callable[[KernelExecutionRequest], KernelExecutionResult],
    ) -> None:
        self._runner = runner

    def execute(self, request: KernelExecutionRequest) -> KernelExecutionResult:
        return self._runner(request)

    async def execute_async(self, request: KernelExecutionRequest) -> KernelExecutionResult:
        return await asyncio.to_thread(self.execute, request)


class SOPGraphExecutionKernel:
    """Transitional public kernel backed by the existing SDK SOP graph."""

    def execute(self, request: KernelExecutionRequest) -> KernelExecutionResult:
        if request.kind != "sop":
            raise ValueError(f"SOPGraphExecutionKernel only supports kind='sop', got {request.kind!r}")

        from alice_engine._internal.graph import build_sop_graph

        ctx = request.resolved_context()
        metadata = dict(request.metadata)
        initial_state = {
            "module": ctx.module,
            "pages": list(ctx.pages),
            "mode": ctx.mode,
            "run_id": request.effective_run_id,
            "current_phase": "",
            "completed_phases": [],
            "failed_phases": [],
            "status": "running",
            "agent_outputs": {},
            "governance": {},
            "project_path": request.project_path,
            "knowledge_context": metadata.get("knowledge_context", {}),
            "memory_context": metadata.get("memory_context"),
        }

        graph = build_sop_graph()
        final_state = graph.run(initial_state, event_bus=metadata.get("event_bus"))
        return ExecutionResult(
            request_id=ctx.request_id or f"sdk-{request.effective_run_id}",
            run_id=request.effective_run_id,
            status=final_state.get("status", "completed"),
            module=ctx.module,
            pages=final_state.get("pages", list(ctx.pages)),
            agent=ctx.agent,
            mode=ctx.mode,
            completed_phases=final_state.get("completed_phases", []),
            failed_phases=final_state.get("failed_phases", []),
            summary=f"{ctx.module} {final_state.get('status', 'completed')}",
            metadata={
                "entrypoint": ctx.entrypoint or "sdk.engine",
                "kernel": type(self).__name__,
                "project_path": request.project_path,
                "checkpoint_thread_id": request.checkpoint_thread_id,
                "agent_outputs": final_state.get("agent_outputs", {}),
            },
        )

    async def execute_async(self, request: KernelExecutionRequest) -> KernelExecutionResult:
        return await asyncio.to_thread(self.execute, request)


class RuntimeExecutionKernel:
    """Shared runtime kernel used by standalone SDK and platform mainline."""

    def __init__(self) -> None:
        self._controls: dict[str, Any] = {}
        self._lock = threading.Lock()

    def execute(self, request: KernelExecutionRequest) -> KernelExecutionResult:
        started = time.perf_counter()
        control = self._build_control(request)
        run_id = request.effective_run_id
        if run_id:
            with self._lock:
                self._controls[run_id] = control
        try:
            state = control.run()
        finally:
            if run_id:
                with self._lock:
                    self._controls.pop(run_id, None)
        duration_ms = round((time.perf_counter() - started) * 1000, 1)
        return self._normalize_result(request, state, duration_ms=duration_ms)

    async def execute_async(self, request: KernelExecutionRequest) -> KernelExecutionResult:
        return await asyncio.to_thread(self.execute, request)

    def cancel(self, run_id: str) -> None:
        with self._lock:
            control = self._controls.get(run_id)
        if control is not None and hasattr(control, "cancel"):
            control.cancel()

    def _build_control(self, request: KernelExecutionRequest):
        ctx = request.resolved_context()
        metadata = dict(request.metadata)
        if request.kind == "sop":
            from alice_engine.workflow.sop_runner import SOPRunner

            return SOPRunner(
                module=ctx.module,
                pages=list(ctx.pages),
                provider=ctx.provider or None,
                mode=ctx.mode,
                run_id=request.effective_run_id,
                checkpoint_thread_id=request.checkpoint_thread_id,
            )
        if request.kind == "agent":
            from alice_engine.core.executor import AgentLoop

            return AgentLoop(
                agent_name=ctx.agent or "automation-agent",
                provider=ctx.provider or None,
                module=ctx.module,
                page=ctx.page,
                pages=list(ctx.pages),
                verbose=bool(metadata.get("verbose", False)),
                replay_recorder=metadata.get("replay_recorder"),
                page_configs=metadata.get("page_configs", []),
            )
        raise ValueError(f"Unsupported kernel kind: {request.kind!r}")

    def _normalize_result(
        self,
        request: KernelExecutionRequest,
        state: Any,
        *,
        duration_ms: float,
    ) -> KernelExecutionResult:
        ctx = request.resolved_context()
        request_id = ctx.request_id or f"sdk-{request.effective_run_id}"
        if request.kind == "sop":
            final_state = state if isinstance(state, dict) else {}
            memory = final_state.get("memory", {}) if isinstance(final_state.get("memory", {}), dict) else {}
            return ExecutionResult(
                request_id=request_id,
                run_id=request.effective_run_id,
                status=final_state.get("status", "completed"),
                module=ctx.module,
                pages=final_state.get("pages", list(ctx.pages)),
                agent=ctx.agent,
                mode=ctx.mode,
                total_tokens=int(final_state.get("total_tokens", 0) or 0),
                total_cost=float(final_state.get("estimated_cost", final_state.get("total_cost", 0.0)) or 0.0),
                agent_runs=int(final_state.get("step", len(final_state.get("agent_outputs", {}) or {})) or 0),
                artifacts=_coerce_artifacts(final_state.get("artifacts", [])),
                error_message=str(final_state.get("termination_reason", "") or ""),
                duration_ms=duration_ms,
                completed_phases=list(final_state.get("completed_phases", []) or []),
                failed_phases=list(final_state.get("failed_phases", []) or []),
                summary=f"{ctx.module} {final_state.get('status', 'completed')}",
                metadata={
                    "entrypoint": ctx.entrypoint or "sdk.engine",
                    "kernel": type(self).__name__,
                    "project_path": request.project_path,
                    "checkpoint_thread_id": request.checkpoint_thread_id,
                    "agent_outputs": final_state.get("agent_outputs", {}),
                    "runtime_context": memory.get("runtime_context", {}),
                    "replay_session_id": memory.get("replay_session_id", ""),
                },
            )

        state_dict = state.to_dict() if hasattr(state, "to_dict") else {}
        failed_skills = state_dict.get("failed_skills", {}) if isinstance(state_dict.get("failed_skills", {}), dict) else {}
        termination_reason = str(state_dict.get("termination_reason", "") or "")
        status = "completed" if getattr(state, "success", False) else "failed"
        if termination_reason == "cancelled":
            status = "cancelled"
        memory = state_dict.get("memory", {}) if isinstance(state_dict.get("memory", {}), dict) else {}
        return ExecutionResult(
            request_id=request_id,
            run_id=request.effective_run_id,
            status=status,
            module=ctx.module,
            pages=list(ctx.pages),
            agent=ctx.agent,
            mode=ctx.mode,
            total_tokens=int(state_dict.get("total_tokens", 0) or 0),
            total_cost=float(state_dict.get("estimated_cost", state_dict.get("total_cost", 0.0)) or 0.0),
            agent_runs=int(state_dict.get("step", 0) or 0),
            artifacts=_coerce_artifacts(state_dict.get("artifacts", {})),
            error_message=termination_reason if status != "completed" else "",
            duration_ms=duration_ms,
            completed_phases=list(state_dict.get("completed_skills", []) or []),
            failed_phases=list(failed_skills.keys()),
            summary=f"{ctx.agent or request.kind} {status}",
            metadata={
                "entrypoint": ctx.entrypoint or "sdk.engine",
                "kernel": type(self).__name__,
                "project_path": request.project_path,
                "checkpoint_thread_id": request.checkpoint_thread_id,
                "agent_outputs": {ctx.agent or "agent": state_dict},
                "runtime_context": memory.get("runtime_context", {}),
                "replay_session_id": memory.get("replay_session_id", ""),
            },
        )


def _coerce_artifacts(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, dict):
        return [str(v) for v in value.values()]
    if value:
        return [str(value)]
    return []
