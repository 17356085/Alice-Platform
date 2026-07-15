"""
ExecutionService — Platform orchestration layer.

Official mainline:
  Entry Adapter -> ExecutionService -> EngineFactory -> Runtime Executor
"""

from __future__ import annotations

__all__ = ["ExecutionService", "ExecutionResult", "ExecutionContext", "get_execution_service_static"]

import asyncio
from datetime import datetime, timezone
import threading
import time
import uuid
from typing import Any

from alice_engine.contracts import ExecutionContext, ExecutionResult

from .config_registry import cfg
from .event_bus import get_bus
from .execution_request import ExecutionRequest
from aitest.infra.metrics import (
    record_execution_request,
    record_execution_result,
    record_execution_retry,
)
from .run import Run
from .run_event import EventDataKey as K, EventType, make_event
from .run_store import get_run_store
from .versioning import resolve_version_metadata
from alice_engine.kernel import KernelExecutionRequest


_STATIC_SERVICE: "ExecutionService | None" = None


def get_execution_service_static() -> "ExecutionService":
    """Return the process-local service used by non-request adapters.

    Keeping this factory in the platform layer prevents workflow/CLI adapters
    from importing the HTTP server layer and gives those adapters the same
    service boundary as the FastAPI dependency.
    """
    global _STATIC_SERVICE
    if _STATIC_SERVICE is None:
        _STATIC_SERVICE = ExecutionService()
    return _STATIC_SERVICE


class ExecutionService:
    """Platform orchestration: API / CLI / Chat adapters -> runtime execution."""

    def __init__(self, store=None, bus=None):
        self._store = store or get_run_store()
        self._bus = bus or get_bus()
        self._active_controls: dict[str, Any] = {}
        self._async_tasks: dict[str, asyncio.Task] = {}
        self._controls_lock = threading.Lock()

    def normalize_context(
        self,
        ctx: ExecutionContext,
        *,
        module: str = "",
        pages: list[str] | None = None,
        agent: str = "automation-agent",
        mode: str = "full",
        provider: str | None = None,
        priority: int = 0,
        idempotency_key: str = "",
        max_retries: int = 3,
        metadata: dict[str, Any] | None = None,
    ) -> ExecutionContext:
        """Normalize any entrypoint input into the shared execution contract."""
        merged_metadata = dict(metadata or {})
        if idempotency_key:
            merged_metadata["idempotency_key"] = idempotency_key
        merged_metadata["max_retries"] = max_retries
        if module and pages:
            from .page_config import load_page_configs

            project_id = str(merged_metadata.get("project_id") or ctx.workspace_id or "web-automation")
            merged_metadata["page_configs"] = load_page_configs(project_id, module, list(pages))
        return ctx.with_execution(
            module=module or ctx.module,
            pages=pages if pages is not None else ctx.pages,
            agent=agent or ctx.agent,
            mode=mode or ctx.mode,
            provider=provider if provider is not None else ctx.provider,
            priority=priority,
            metadata=merged_metadata,
        )

    def create_engine(
        self,
        ctx: ExecutionContext,
        *,
        module: str = "",
        pages: list[str] | None = None,
        agent: str = "automation-agent",
        mode: str = "full",
        provider: str | None = None,
        run_id: str = "",
        checkpoint_thread_id: str = "",
        verbose: bool = False,
        **kwargs,
    ):
        """Build an execution engine through the official service boundary."""
        from .engine_factory import get_engine

        resolved = self.normalize_context(
            ctx,
            module=module,
            pages=pages,
            agent=agent,
            mode=mode,
            provider=provider,
        )
        return get_engine(
            resolved.agent or "automation-agent",
            module=resolved.module,
            pages=resolved.pages,
            page=resolved.page,
            agent=resolved.agent or "automation-agent",
            provider=resolved.provider or "",
            mode=resolved.mode,
            run_id=run_id,
            checkpoint_thread_id=checkpoint_thread_id,
            verbose=verbose,
            **kwargs,
        )

    class _KernelRunControl:
        def __init__(self, kernel, run_id: str):
            self._kernel = kernel
            self._run_id = run_id

        def cancel(self) -> None:
            cancel = getattr(self._kernel, "cancel", None)
            if callable(cancel):
                cancel(self._run_id)

    def execute(
        self,
        ctx: ExecutionContext,
        *,
        module: str,
        pages: list[str] | None = None,
        agent: str = "automation-agent",
        mode: str = "full",
        provider: str | None = None,
        priority: int = 0,
        idempotency_key: str = "",
        max_retries: int = 3,
        checkpoint_thread_id: str = "",
    ) -> ExecutionResult:
        pages = pages or []
        version_metadata = resolve_version_metadata()
        ctx = self.normalize_context(
            ctx,
            module=module,
            pages=pages,
            agent=agent,
            mode=mode,
            provider=provider,
            priority=priority,
            idempotency_key=idempotency_key,
            max_retries=max_retries,
            metadata=version_metadata,
        )
        ctx.require("execute")
        idem_key = self._resolve_idempotency_key(ctx, idempotency_key)
        if idem_key:
            existing = self._find_existing_request(ctx, idem_key)
            if existing is not None:
                return self._build_result_from_request(ctx, existing)
        request = self._create_request(ctx, agent=agent)
        request.queue()
        record_execution_request(request.agent or agent, request.module, request.status)
        self._emit_execution_requested(ctx, request, agent)
        self._store.save_request(request)
        return self._run_request_flow(
            ctx,
            request,
            agent=agent,
            t0=time.perf_counter(),
            verbose=True,
            checkpoint_thread_id=checkpoint_thread_id or request.request_id,
        )

    def submit_async(
        self,
        ctx: ExecutionContext,
        *,
        module: str,
        pages: list[str] | None = None,
        agent: str = "automation-agent",
        mode: str = "full",
        provider: str | None = None,
        priority: int = 0,
        idempotency_key: str = "",
        max_retries: int = 3,
        checkpoint_thread_id: str = "",
    ) -> ExecutionResult:
        """Create an execution request and hand it to the worker plane."""
        pages = pages or []
        version_metadata = resolve_version_metadata()
        ctx = self.normalize_context(
            ctx,
            module=module,
            pages=pages,
            agent=agent,
            mode=mode,
            provider=provider,
            priority=priority,
            idempotency_key=idempotency_key,
            max_retries=max_retries,
            metadata=version_metadata,
        )
        ctx.require("execute")
        idem_key = self._resolve_idempotency_key(ctx, idempotency_key)
        if idem_key:
            existing = self._find_existing_request(ctx, idem_key)
            if existing is not None:
                return self._build_result_from_request(ctx, existing)
        request = self._create_request(ctx, agent=agent)
        request.queue()
        record_execution_request(request.agent or agent, request.module, request.status)
        self._emit_execution_requested(ctx, request, agent)
        self._store.save_request(request)
        return self._build_pending_result(
            ctx,
            request=request,
            agent=agent,
            checkpoint_thread_id=checkpoint_thread_id or request.request_id,
        )

    def _create_request(self, ctx: ExecutionContext, *, agent: str) -> ExecutionRequest:
        return ExecutionRequest(
            request_id=str(uuid.uuid4()),
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            triggered_by=ctx.user_id,
            trigger_type=ctx.metadata.get("trigger_type", "manual"),
            agent=agent,
            idempotency_key=self._resolve_idempotency_key(ctx, ctx.metadata.get("idempotency_key", "")),
            module=ctx.module,
            pages=ctx.pages,
            mode=ctx.mode,
            provider=ctx.provider or None,
            priority=ctx.priority,
            max_retries=self._safe_int(ctx.metadata.get("max_retries", 3), default=3),
        )

    def _safe_int(self, value: Any, *, default: int) -> int:
        try:
            return int(value)
        except Exception:
            return default

    def _resolve_idempotency_key(self, ctx: ExecutionContext, idempotency_key: str = "") -> str:
        key = str(idempotency_key or (ctx.metadata.get("idempotency_key", "") if isinstance(ctx.metadata, dict) else "")).strip()
        return key

    def _find_existing_request(self, ctx: ExecutionContext, idempotency_key: str) -> ExecutionRequest | None:
        if not idempotency_key:
            return None
        finder = getattr(self._store, "find_request_by_idempotency_key", None)
        if callable(finder):
            return finder(
                idempotency_key,
                workspace_id=ctx.workspace_id,
                org_id=ctx.org_id,
            )
        return None

    def _build_result_from_request(self, ctx: ExecutionContext, request: ExecutionRequest) -> ExecutionResult:
        latest_run_id = request.latest_run_id
        if request.is_terminal and latest_run_id:
            run = self._store.load_run(latest_run_id)
            if run is not None:
                duration_ms = 0.0
                try:
                    started = datetime.fromisoformat(run.created_at)
                    ended = datetime.fromisoformat(run.completed_at or run.created_at)
                    duration_ms = round((ended - started).total_seconds() * 1000, 1)
                except Exception:
                    pass
                return self._build_result(
                    ctx,
                    request_id=request.request_id,
                    run=run,
                    duration_ms=duration_ms,
                    completed_phases=[],
                    failed_phases=[],
                    checkpoint_thread_id=request.request_id,
                )
        return self._build_pending_result(
            ctx,
            request=request,
            agent=request.agent or ctx.agent,
            checkpoint_thread_id=request.request_id,
        )

    def _build_pending_result(
        self,
        ctx: ExecutionContext,
        *,
        request: ExecutionRequest,
        agent: str,
        checkpoint_thread_id: str,
    ) -> ExecutionResult:
        return ExecutionResult(
            request_id=request.request_id,
            run_id="",
            status="pending",
            module=ctx.module,
            pages=list(ctx.pages),
            agent=agent,
            mode=ctx.mode,
            summary="execution queued asynchronously",
            metadata={
                "workspace_id": ctx.workspace_id,
                "org_id": ctx.org_id,
                "entrypoint": ctx.entrypoint,
                "async": True,
                "checkpoint_thread_id": checkpoint_thread_id,
                "idempotency_key": request.idempotency_key,
                "retry_count": request.retry_count,
                "max_retries": request.max_retries,
                "policy_version": ctx.metadata.get(K.POLICY_VERSION, cfg.governance_policy_version),
                "governance_version": ctx.metadata.get(K.GOVERNANCE_VERSION, cfg.governance_policy_version),
                "config_version": ctx.metadata.get(K.CONFIG_VERSION, cfg.governance_policy_version),
                "governance_pack_root": ctx.metadata.get(K.GOVERNANCE_PACK_ROOT, ""),
            },
        )

    def _run_request_flow(
        self,
        ctx: ExecutionContext,
        request: ExecutionRequest,
        *,
        agent: str,
        t0: float,
        verbose: bool,
        checkpoint_thread_id: str = "",
        allow_retry: bool = False,
    ) -> ExecutionResult:
        run = Run(
            run_id=str(uuid.uuid4()),
            request_id=request.request_id,
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            triggered_by=ctx.user_id,
            capability="graph" if agent == "sop" else "agent",
            agent=agent,
            module=ctx.module,
            pages=ctx.pages,
            mode=ctx.mode,
        )
        request.dispatch(run.run_id)
        self._store.save_request(request)
        self._store.save_run(run)
        self._emit_started(ctx, request, run)

        completed_phases: list[str] = []
        failed_phases: list[str] = []
        try:
            self._emit_phase_started(request, run)
            replay_recorder = None
            try:
                from .replay import ReplayRecorder

                replay_recorder = ReplayRecorder(
                    run_id=run.run_id,
                    module=ctx.module,
                    page=ctx.page,
                    agent=agent,
                )
                setattr(run, "replay_session_id", replay_recorder.session_id)
            except Exception:
                replay_recorder = None

            kernel = self._resolve_execution_kernel()
            self._register_control(run.run_id, self._KernelRunControl(kernel, run.run_id))
            try:
                state = self._execute_request_via_kernel(
                    ctx,
                    request,
                    run,
                    agent=agent,
                    verbose=verbose,
                    checkpoint_thread_id=checkpoint_thread_id or run.run_id,
                    replay_recorder=replay_recorder,
                    kernel=kernel,
                )
            finally:
                self._unregister_control(run.run_id)
                if replay_recorder is not None:
                    try:
                        replay_recorder.finish()
                    except Exception:
                        pass

            completed_phases = self._extract_list(state, "completed_phases")
            failed_phases = self._extract_list(state, "failed_phases")
            self._finalize_run_from_state(run, state)
            request.complete()
            self._store.save_run(run)
            self._store.save_request(request)
            duration_ms = round((time.perf_counter() - t0) * 1000, 1)
            self._emit_phase_completed(request, run)
            self._emit_terminal_event(ctx, request, run, completed_phases, failed_phases, duration_ms=duration_ms)
            record_execution_result(
                run.agent or agent,
                run.status,
                duration_s=duration_ms / 1000.0,
                module=run.module,
            )
        except Exception as exc:
            retry_scheduled = False
            duration_ms = round((time.perf_counter() - t0) * 1000, 1)
            if allow_retry and self._can_retry_request(request, exc):
                retry_scheduled = True
                delay_s = self._retry_delay_for_request(request)
                run.fail(str(exc))
                request.schedule_retry(delay_s)
                record_execution_retry(request.agent or agent, request.module)
            else:
                run.fail(str(exc))
                request.fail()
            self._store.save_run(run)
            self._store.save_request(request)
            self._emit_phase_completed(request, run)
            self._emit_failed(ctx, request, run, str(exc), duration_ms=duration_ms)
            record_execution_result(
                request.agent or agent,
                run.status,
                duration_s=duration_ms / 1000.0,
                module=request.module,
            )
            if retry_scheduled:
                return self._build_pending_result(
                    ctx,
                    request=request,
                    agent=agent,
                    checkpoint_thread_id=checkpoint_thread_id or request.request_id,
                )

        duration_ms = round((time.perf_counter() - t0) * 1000, 1)
        self._store.save_run(run)
        return self._build_result(
            ctx,
            request_id=request.request_id,
            run=run,
            duration_ms=duration_ms,
            completed_phases=completed_phases,
            failed_phases=failed_phases,
            checkpoint_thread_id=checkpoint_thread_id or request.request_id,
        )

    def _can_retry_request(self, request: ExecutionRequest, exc: Exception) -> bool:
        if request.is_terminal:
            return False
        if request.max_retries <= 0:
            return False
        if request.retry_count >= request.max_retries:
            return False
        error = str(exc).lower()
        fatal_markers = ("fatal", "permission", "denied", "auth", "context_length", "invalid")
        return not any(marker in error for marker in fatal_markers)

    def _retry_delay_for_request(self, request: ExecutionRequest) -> float:
        from .scheduler import RetryPolicy

        policy = RetryPolicy(max_attempts=max(request.max_retries, 1))
        return policy.delay_for_attempt(request.retry_count)

    def _resolve_execution_kernel(self):
        from .engine_factory import get_execution_kernel

        return get_execution_kernel()

    def _execute_request_via_kernel(
        self,
        ctx: ExecutionContext,
        request: ExecutionRequest,
        run: Run,
        *,
        agent: str,
        verbose: bool,
        checkpoint_thread_id: str,
        replay_recorder=None,
        kernel=None,
    ) -> ExecutionResult:
        from .engine_factory import resolve_kernel_kind
        from alice_engine.core.runtime_environment import runtime_environment_scope

        kernel = kernel or self._resolve_execution_kernel()
        kernel_ctx = ctx.with_execution(
            agent=agent,
            request_id=request.request_id,
            run_id=run.run_id,
            provider=ctx.provider,
        )
        project_path = str(ctx.metadata.get("project_path", "")) if isinstance(ctx.metadata, dict) else ""
        kernel_request = KernelExecutionRequest(
            context=kernel_ctx,
            kind=resolve_kernel_kind(agent, agent=agent),
            project_path=project_path,
            run_id=run.run_id,
            checkpoint_thread_id=checkpoint_thread_id,
            metadata={
                "page": ctx.page,
                "verbose": verbose,
                "replay_recorder": replay_recorder,
                "page_configs": ctx.metadata.get("page_configs", []),
            },
        )
        provider = ctx.provider or ""
        scope_kwargs: dict[str, Any] = {}
        if provider:
            scope_kwargs["llm_provider"] = provider
            scope_kwargs["mock_llm"] = provider == "mock"
        if project_path:
            scope_kwargs["workstudy"] = project_path
        with runtime_environment_scope(**scope_kwargs):
            return kernel.execute(kernel_request)

    def resume(self, run_id: str) -> ExecutionResult | None:
        run = self._store.load_run(run_id)
        if run is None or run.status == "completed":
            return None

        checkpoint_thread_id = run.request_id or run.run_id
        ctx = ExecutionContext(
            workspace_id=run.workspace_id,
            user_id=run.triggered_by,
            scopes=["read", "execute"],
            org_id=run.org_id,
            module=run.module,
            pages=list(run.pages),
            agent=run.agent,
            mode=run.mode,
            metadata={"entrypoint": "resume", "trigger_type": "resume"},
        )
        result = self.execute(
            ctx,
            module=run.module,
            pages=run.pages,
            agent=run.agent,
            mode="resume",
            provider="",
            checkpoint_thread_id=checkpoint_thread_id,
        )
        return result

    def cancel(self, request_id: str) -> bool:
        runs = self._store.list_runs(limit=500)
        run = next((r for r in runs if r.request_id == request_id), None)
        if run is None or run.is_frozen:
            return False

        control = self._get_control(run.run_id)
        if control is not None and hasattr(control, "cancel"):
            control.cancel()

        run.cancel()
        self._store.save_run(run)
        request = self._store.load_request(request_id)
        if request:
            request.cancel()
            self._store.save_request(request)

        ev = make_event(
            EventType.RUN_CANCELLED,
            run_id=run.run_id,
            request_id=request_id,
            workspace_id=run.workspace_id,
            org_id=run.org_id,
            module=run.module,
            agent=run.agent,
        )
        self._store.save_event(ev)
        self._bus.publish_async(ev)
        return True

    def timeout_run(self, run_id: str) -> bool:
        run = self._store.load_run(run_id)
        if run is None or run.is_frozen:
            return False

        control = self._get_control(run_id)
        if control is not None and hasattr(control, "cancel"):
            control.cancel()

        run.timed_out()
        self._store.save_run(run)
        ev = make_event(
            EventType.RUN_FAILED,
            run_id=run.run_id,
            request_id=run.request_id,
            workspace_id=run.workspace_id,
            org_id=run.org_id,
            module=run.module,
            agent=run.agent,
            error="timeout",
        )
        self._store.save_event(ev)
        self._bus.publish_async(ev)
        return True

    def get_active_run_ids(self) -> list[str]:
        with self._controls_lock:
            return list(self._active_controls.keys())

    def _register_control(self, run_id: str, control: Any) -> None:
        with self._controls_lock:
            self._active_controls[run_id] = control

    def _unregister_control(self, run_id: str) -> None:
        with self._controls_lock:
            self._active_controls.pop(run_id, None)

    def _get_control(self, run_id: str) -> Any | None:
        with self._controls_lock:
            return self._active_controls.get(run_id)

    def _emit_execution_requested(self, ctx: ExecutionContext, request: ExecutionRequest, agent: str) -> None:
        ev = make_event(
            EventType.EXECUTION_REQUESTED,
            request_id=request.request_id,
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            module=request.module,
            pages=request.pages,
            agent=agent,
            **self._version_payload(ctx),
        )
        self._store.save_event(ev)
        self._bus.publish_async(ev)

    def _emit_started(self, ctx: ExecutionContext, request: ExecutionRequest, run: Run) -> None:
        replay_session_id = getattr(run, "replay_session_id", "")
        ev = make_event(
            EventType.EXECUTION_STARTED,
            run_id=run.run_id,
            request_id=request.request_id,
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            module=run.module,
            agent=run.agent,
            replay_session_id=replay_session_id,
            **self._version_payload(ctx),
        )
        self._store.save_event(ev)
        self._bus.publish_async(ev)

    def _emit_phase_started(self, request: ExecutionRequest, run: Run) -> None:
        replay_session_id = getattr(run, "replay_session_id", "")
        ev = make_event(
            EventType.PHASE_STARTED,
            run_id=run.run_id,
            request_id=request.request_id,
            phase="execution",
            module=run.module,
            replay_session_id=replay_session_id,
            **self._version_payload_from_run(run),
        )
        self._store.save_event(ev)
        self._bus.publish_async(ev)

    def _emit_phase_completed(self, request: ExecutionRequest, run: Run) -> None:
        replay_session_id = getattr(run, "replay_session_id", "")
        ev = make_event(
            EventType.PHASE_COMPLETED,
            run_id=run.run_id,
            request_id=request.request_id,
            phase="execution",
            module=run.module,
            replay_session_id=replay_session_id,
            **self._version_payload_from_run(run),
        )
        self._store.save_event(ev)
        self._bus.publish_async(ev)

    def _emit_terminal_event(
        self,
        ctx: ExecutionContext,
        request: ExecutionRequest,
        run: Run,
        completed_phases: list[str],
        failed_phases: list[str],
        *,
        duration_ms: float = 0.0,
    ) -> None:
        replay_session_id = getattr(run, "replay_session_id", "")
        if run.status == "completed":
            event_type = EventType.RUN_COMPLETED
        elif run.status == "cancelled":
            event_type = EventType.RUN_CANCELLED
        else:
            event_type = EventType.RUN_FAILED
        ev = make_event(
            event_type,
            run_id=run.run_id,
            request_id=request.request_id,
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            module=run.module,
            agent=run.agent,
            total_tokens=run.total_tokens,
            total_cost=run.total_cost,
            agent_runs=run.agent_runs,
            duration_ms=duration_ms,
            retry_count=request.retry_count,
            max_retries=request.max_retries,
            error=run.error_message,
            completed_phases=completed_phases,
            failed_phases=failed_phases,
            replay_session_id=replay_session_id,
            **self._version_payload(ctx),
        )
        self._store.save_event(ev)
        self._bus.publish_async(ev)

        if run.total_cost > 0:
            cost = make_event(
                EventType.COST_RECORDED,
                run_id=run.run_id,
                request_id=request.request_id,
                total_cost=run.total_cost,
                total_tokens=run.total_tokens,
                org_id=ctx.org_id,
                workspace_id=ctx.workspace_id,
                replay_session_id=replay_session_id,
                **self._version_payload(ctx),
            )
            self._store.save_event(cost)
            self._bus.publish_async(cost)

    def _emit_failed(self, ctx: ExecutionContext, request: ExecutionRequest, run: Run, error: str, *, duration_ms: float = 0.0) -> None:
        replay_session_id = getattr(run, "replay_session_id", "")
        ev = make_event(
            EventType.RUN_FAILED,
            run_id=run.run_id,
            request_id=request.request_id,
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            module=run.module,
            agent=run.agent,
            total_tokens=run.total_tokens,
            total_cost=run.total_cost,
            agent_runs=run.agent_runs,
            duration_ms=duration_ms,
            retry_count=request.retry_count,
            max_retries=request.max_retries,
            error=error,
            replay_session_id=replay_session_id,
            **self._version_payload(ctx),
        )
        self._store.save_event(ev)
        self._bus.publish_async(ev)

    def _extract_value(self, state: Any, key: str, default: Any = None) -> Any:
        if isinstance(state, ExecutionResult):
            return getattr(state, key, default)
        if isinstance(state, dict):
            return state.get(key, default)
        return getattr(state, key, default)

    def _extract_list(self, state: Any, key: str) -> list[str]:
        value = self._extract_value(state, key, [])
        return list(value) if isinstance(value, (list, tuple, set)) else []

    def _extract_artifacts(self, state: Any) -> list[str]:
        if isinstance(state, ExecutionResult):
            return [str(v) for v in state.artifacts]
        value = self._extract_value(state, "artifacts", [])
        if isinstance(value, list):
            return [str(v) for v in value]
        return []

    def _version_payload(self, ctx: ExecutionContext) -> dict[str, Any]:
        metadata = ctx.metadata if isinstance(ctx.metadata, dict) else {}
        return {
            K.POLICY_VERSION: metadata.get(K.POLICY_VERSION, cfg.governance_policy_version),
            K.GOVERNANCE_VERSION: metadata.get(K.GOVERNANCE_VERSION, cfg.governance_policy_version),
            K.CONFIG_VERSION: metadata.get(K.CONFIG_VERSION, cfg.governance_policy_version),
            K.GOVERNANCE_PACK_ROOT: metadata.get(K.GOVERNANCE_PACK_ROOT, ""),
        }

    def _version_payload_from_run(self, run: Run) -> dict[str, Any]:
        metadata = getattr(run, "runtime_context", {})
        if not isinstance(metadata, dict):
            metadata = {}
        return {
            K.POLICY_VERSION: metadata.get(K.POLICY_VERSION, cfg.governance_policy_version),
            K.GOVERNANCE_VERSION: metadata.get(K.GOVERNANCE_VERSION, cfg.governance_policy_version),
            K.CONFIG_VERSION: metadata.get(K.CONFIG_VERSION, cfg.governance_policy_version),
            K.GOVERNANCE_PACK_ROOT: metadata.get(K.GOVERNANCE_PACK_ROOT, ""),
        }

    def _finalize_run_from_state(self, run: Run, state: Any) -> None:
        if isinstance(state, ExecutionResult):
            setattr(run, "runtime_context", state.metadata.get("runtime_context", {}))
            setattr(run, "replay_session_id", state.metadata.get("replay_session_id", ""))
            if state.status == "cancelled":
                run.total_tokens = state.total_tokens
                run.total_cost = state.total_cost
                run.agent_runs = state.agent_runs
                run.artifacts = list(state.artifacts)
                run.cancel()
                return

            if state.status in {"failed", "timed_out"} or state.failed_phases:
                run.total_tokens = state.total_tokens
                run.total_cost = state.total_cost
                run.agent_runs = state.agent_runs
                run.artifacts = list(state.artifacts)
                if state.status == "timed_out":
                    run.timed_out()
                else:
                    run.fail(state.error_message or "execution_failed")
                return

            run.complete(
                total_tokens=state.total_tokens,
                total_cost=state.total_cost,
                agent_runs=state.agent_runs,
                artifacts=list(state.artifacts),
            )
            return

        total_tokens = int(self._extract_value(state, "total_tokens", 0) or 0)
        total_cost = float(
            self._extract_value(
                state,
                "estimated_cost",
                self._extract_value(state, "total_cost", 0.0),
            )
            or 0.0
        )
        agent_runs = int(
            self._extract_value(
                state,
                "step",
                len(self._extract_value(state, "agent_outputs", {}) or {}),
            )
            or 0
        )
        artifacts = self._extract_artifacts(state)
        failed_phases = self._extract_list(state, "failed_phases")
        termination_reason = str(self._extract_value(state, "termination_reason", "") or "")
        success = self._extract_value(state, "success", None)
        status_hint = str(self._extract_value(state, "status", "") or "").lower()
        setattr(run, "runtime_context", self._extract_value(state, "memory", {}).get("runtime_context", {}))
        setattr(run, "replay_session_id", self._extract_value(state, "memory", {}).get("replay_session_id", ""))

        if status_hint == "cancelled" or termination_reason == "cancelled":
            run.total_tokens = total_tokens
            run.total_cost = total_cost
            run.agent_runs = agent_runs
            run.artifacts = artifacts
            run.cancel()
            return

        if status_hint in {"failed", "timed_out"} or success is False or failed_phases:
            run.total_tokens = total_tokens
            run.total_cost = total_cost
            run.agent_runs = agent_runs
            run.artifacts = artifacts
            if status_hint == "timed_out":
                run.timed_out()
            else:
                run.fail(termination_reason or "execution_failed")
            return

        run.complete(
            total_tokens=total_tokens,
            total_cost=total_cost,
            agent_runs=agent_runs,
            artifacts=artifacts,
        )

    def _build_result(
        self,
        ctx: ExecutionContext,
        *,
        request_id: str,
        run: Run,
        duration_ms: float,
        completed_phases: list[str],
        failed_phases: list[str],
        checkpoint_thread_id: str = "",
    ) -> ExecutionResult:
        summary = (
            f"{run.agent} {run.status}"
            f" | phases={len(completed_phases)}"
            f" | failed={len(failed_phases)}"
        )
        return ExecutionResult(
            request_id=request_id,
            run_id=run.run_id,
            status=run.status,
            module=run.module,
            pages=list(run.pages),
            agent=run.agent,
            mode=run.mode,
            total_tokens=run.total_tokens,
            total_cost=run.total_cost,
            agent_runs=run.agent_runs,
            artifacts=list(run.artifacts),
            error_message=run.error_message,
            duration_ms=duration_ms,
            completed_phases=completed_phases,
            failed_phases=failed_phases,
            summary=summary,
            metadata={
                "workspace_id": ctx.workspace_id,
                "org_id": ctx.org_id,
                "entrypoint": ctx.entrypoint,
                "runtime_context": getattr(run, "runtime_context", {}),
                "replay_session_id": getattr(run, "replay_session_id", ""),
                "checkpoint_thread_id": checkpoint_thread_id,
                "policy_version": ctx.metadata.get(K.POLICY_VERSION, cfg.governance_policy_version),
                "governance_version": ctx.metadata.get(K.GOVERNANCE_VERSION, cfg.governance_policy_version),
                "config_version": ctx.metadata.get(K.CONFIG_VERSION, cfg.governance_policy_version),
                "governance_pack_root": ctx.metadata.get(K.GOVERNANCE_PACK_ROOT, ""),
            },
        )
