"""
ExecutionService — Platform orchestration layer. v2.2

Sits between API and Runtime. Responsibilities:
  1. Validate (scope check via ExecutionContext)
  2. Create ExecutionRequest
  3. Emit execution.requested event
  4. Dispatch — create Run, emit execution.started
  5. Execute via AgentLoop
  6. Complete/fail Run, emit run.completed/run.failed
  7. Persist Run (immutable) + RunEvents

Runtime stays pure — it never sees Organization, Quota, or Billing.

Usage:
    from aitest.platform.execution_service import ExecutionService
    from aitest.platform.workspace import ExecutionContext

    svc = ExecutionService()
    result = svc.execute(
        ctx=ExecutionContext(workspace_id="ws-1", user_id="alice", org_id="my-org"),
        module="equipment",
        pages=["device-list"],
        agent="automation-agent",
    )
"""

import uuid
import time
import threading
from dataclasses import dataclass, field

from .workspace import ExecutionContext
from .execution_request import ExecutionRequest, RequestStatus
from .run import Run
from .run_event import RunEvent, EventType, make_event
from .event_bus import get_bus
from .run_store import get_run_store


# ── Result ───────────────────────────────────────────────────────────────

@dataclass
class ExecutionResult:
    """Returned by ExecutionService after execution completes."""
    request_id: str
    run_id: str
    status: str                    # completed|failed|cancelled
    total_tokens: int = 0
    total_cost: float = 0.0
    agent_runs: int = 0
    artifacts: list[str] = field(default_factory=list)
    error_message: str = ""
    duration_ms: float = 0.0


# ── Service ──────────────────────────────────────────────────────────────

class ExecutionService:
    """Platform orchestration: API → ExecutionService → Runtime."""

    def __init__(self):
        self._store = get_run_store()
        self._bus = get_bus()

    # ── Public API ────────────────────────────────────────────────────

    def execute(
        self,
        ctx: ExecutionContext,
        *,
        module: str,
        pages: list[str] | None = None,
        agent: str = "automation-agent",
        mode: str = "full",
        provider: str = "claude",
        priority: int = 0,
    ) -> ExecutionResult:
        """
        Execute an agent run with full Platform lifecycle.

        Flow:
          1. Validate — scope check
          2. Create ExecutionRequest
          3. Emit execution.requested
          4. Dispatch → Create Run → emit execution.started
          5. Execute via AgentLoop
          6. Complete/fail Run → emit run.completed/failed
          7. Persist Run + Events

        Args:
            ctx: ExecutionContext from Platform layer (never seen by Runtime)
            module: Target module name
            pages: Page slugs to execute
            agent: Agent name (automation-agent, execution-agent, ...)
            mode: SOP mode (full|status|from_automation)
            provider: LLM provider (claude|deepseek|openai)
            priority: Queue priority (0=normal, 1=high, 2=critical)

        Returns:
            ExecutionResult with request_id, run_id, status, summary.
        """
        pages = pages or []
        t0 = time.perf_counter()

        # 1. Validate
        ctx.require("execute")

        # 2. Create ExecutionRequest
        request = ExecutionRequest(
            request_id=str(uuid.uuid4()),
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            triggered_by=ctx.user_id,
            trigger_type="manual",
            module=module,
            pages=pages,
            mode=mode,
            provider=provider,
            priority=priority,
        )

        # 3. Emit execution.requested
        self._bus.publish(make_event(
            EventType.EXECUTION_REQUESTED,
            request_id=request.request_id,
            module=module, pages=pages, agent=agent,
        ))
        request.queue()
        self._store.save_request(request)  # Persist at queued

        # 4. Dispatch — create Run
        run = Run(
            run_id=str(uuid.uuid4()),
            request_id=request.request_id,
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            triggered_by=ctx.user_id,
            capability="browser",
            agent=agent,
            module=module,
            pages=pages,
            mode=mode,
        )
        request.dispatch(run.run_id)  # appends to run_ids (one-to-many)
        self._store.save_request(request)  # Persist after dispatch

        # Emit execution.started
        self._bus.publish(make_event(
            EventType.EXECUTION_STARTED,
            run_id=run.run_id,
            request_id=request.request_id,
            workspace_id=ctx.workspace_id,
            org_id=ctx.org_id,
            module=module, agent=agent,
        ))

        # 5. Execute via AgentLoop
        try:
            from aitest.agents.agent_runner import AgentLoop

            loop = AgentLoop(
                agent_name=agent,
                provider=provider,
                module=module,
                page=pages[0] if pages else "",
                pages=pages,
                verbose=True,
            )
            state = loop.run()

            # 6. Complete Run
            run.complete(
                total_tokens=getattr(state, 'total_tokens', 0),
                total_cost=getattr(state, 'estimated_cost', 0.0),
                agent_runs=getattr(state, 'step', 0),
            )
            request.complete()
            self._store.save_request(request)  # Persist completed

            self._bus.publish(make_event(
                EventType.RUN_COMPLETED,
                run_id=run.run_id,
                request_id=request.request_id,
                workspace_id=ctx.workspace_id,
                org_id=ctx.org_id,
                module=module,
                agent=agent,
                total_tokens=run.total_tokens,
                total_cost=run.total_cost,
                agent_runs=run.agent_runs,
            ))

            # Emit cost.recorded
            if run.total_cost > 0:
                self._bus.publish(make_event(
                    EventType.COST_RECORDED,
                    run_id=run.run_id,
                    request_id=request.request_id,
                    cost=run.total_cost,
                    tokens=run.total_tokens,
                    org_id=ctx.org_id,
                    workspace_id=ctx.workspace_id,
                ))

        except Exception as e:
            run.fail(str(e))
            request.fail()
            self._store.save_request(request)  # Persist failed

            self._bus.publish(make_event(
                EventType.RUN_FAILED,
                run_id=run.run_id,
                request_id=request.request_id,
                workspace_id=ctx.workspace_id,
                org_id=ctx.org_id,
                module=module,
                agent=agent,
                total_tokens=run.total_tokens,
                total_cost=run.total_cost,
                agent_runs=run.agent_runs,
                error=str(e),
            ))

        # 7. Persist
        self._store.save_run(run)
        duration_ms = (time.perf_counter() - t0) * 1000

        return ExecutionResult(
            request_id=request.request_id,
            run_id=run.run_id,
            status=run.status,
            total_tokens=run.total_tokens,
            total_cost=run.total_cost,
            agent_runs=run.agent_runs,
            artifacts=run.artifacts,
            error_message=run.error_message,
            duration_ms=round(duration_ms, 1),
        )

    def cancel(self, request_id: str) -> bool:
        """Cancel a pending/queued ExecutionRequest. Best-effort.

        v2.2: ExecutionRequest is in-memory only. Look up Run by request_id,
        cancel if not yet terminal.
        """
        # Find Run by request_id
        runs = self._store.list_runs(limit=500)
        run = next((r for r in runs if r.request_id == request_id), None)

        if run is None:
            return False
        if run.is_frozen:
            return False

        run.cancel()
        self._store.save_run(run)

        # Find and cancel the ExecutionRequest
        request = self._store.load_request(request_id)
        if request:
            request.cancel()
            self._store.save_request(request)

        self._bus.publish(make_event(
            EventType.RUN_CANCELLED,
            run_id=run.run_id,
            request_id=request_id,
            workspace_id=run.workspace_id,
            org_id=run.org_id,
            module=run.module,
            agent=run.agent,
        ))
        return True
