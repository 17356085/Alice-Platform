"""
Agent Platform v1 — unified Agent abstraction. v3.0

Agent = State + Tools + Policy + ExecutionLoop

Built on top of the Memory Control Plane infra (lifecycle.py, TTL, MemoryGuard).
Every agent on the platform satisfies AgentCore and runs via AgentRuntime.

Architecture:
    Agent Applications (chat / testing / onboarding / automation)
           ↓
    AgentRuntime (run / pause / resume / fork / observe / dispose)
           ↓
    AgentCore (Protocol: agent_id, state, run, run_interactive, dispose)
           ↓
    Runtime Layer (LifecycleRegistry + MemoryGuard + TTLSet + WorkerPool)
           ↓
    Infrastructure (OS / process / browser / Python runtime)

Usage:
    from aitest.agents.core import AgentCore, AgentRuntime, AgentResult, AgentContext

    # Any agent implements AgentCore:
    class MyAgent(AgentCore):
        agent_id = "my-agent"
        agent_type = "custom"

        async def run(self, ctx: AgentContext) -> AgentResult: ...
        async def run_interactive(self, ctx): ...
        def send_interaction(self, response): ...
        def dispose(self): ...

    # AgentRuntime manages execution:
    runtime = AgentRuntime()
    result = await runtime.execute(agent, context)
    # Or interactively:
    async for event in runtime.execute_interactive(agent, context):
        yield event
"""

from __future__ import annotations

import asyncio
import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Protocol, Optional, AsyncGenerator, Any,
    runtime_checkable,
)


# ══════════════════════════════════════════════════════════════════════════
#  Unified AgentResult — single output contract for all agent types
# ══════════════════════════════════════════════════════════════════════════

class AgentRunStatus(str, Enum):
    """Terminal status of an agent run."""
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"
    COMPLETED_WITH_ISSUES = "completed_with_issues"
    PAUSED = "paused"  # HITL — waiting for interaction


@dataclass
class AgentResult:
    """Unified result from any agent execution.

    Replaces: AgentState.to_dict(), SOPState, OnboardingState.to_dict(),
    QAResult — all now produce this single type.
    """

    agent_id: str
    agent_type: str           # "sop" | "onboarding" | "chat" | "qa" | "custom"
    status: AgentRunStatus = AgentRunStatus.SUCCESS
    run_id: str = ""

    # Execution stats
    steps_completed: int = 0
    skills_completed: list[str] = field(default_factory=list)
    skills_failed: list[str] = field(default_factory=list)
    total_tokens: int = 0
    total_cost: float = 0.0
    duration_ms: float = 0.0

    # Output
    summary: str = ""
    error: str = ""
    artifacts: dict = field(default_factory=dict)
    observations: list[dict] = field(default_factory=list)

    # Extensibility
    metadata: dict = field(default_factory=dict)

    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> dict:
        return {
            "agent_id": self.agent_id,
            "agent_type": self.agent_type,
            "status": self.status.value,
            "run_id": self.run_id,
            "steps_completed": self.steps_completed,
            "skills_completed": self.skills_completed,
            "skills_failed": self.skills_failed,
            "total_tokens": self.total_tokens,
            "total_cost": round(self.total_cost, 4),
            "duration_ms": round(self.duration_ms, 1),
            "summary": self.summary,
            "error": self.error,
            "artifacts": self.artifacts,
            "observations": self.observations,
            "metadata": self.metadata,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }

    @property
    def success(self) -> bool:
        return self.status in (AgentRunStatus.SUCCESS, AgentRunStatus.COMPLETED_WITH_ISSUES)


# ══════════════════════════════════════════════════════════════════════════
#  AgentContext — what the agent needs to know to execute
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class AgentContext:
    """Immutable execution context passed to every agent run.

    Contains only what the agent needs — no framework internals.
    """
    module: str = ""
    page: str = ""
    pages: list[str] = field(default_factory=list)
    provider: str = "claude"
    goal: str = ""
    mode: str = "full"            # "full" | "resume" | "from-requirement" | ...
    project_id: str = ""
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: dict) -> "AgentContext":
        return cls(
            module=d.get("module", ""),
            page=d.get("page", ""),
            pages=d.get("pages", []),
            provider=d.get("provider", "claude"),
            goal=d.get("goal", ""),
            mode=d.get("mode", "full"),
            project_id=d.get("project_id", ""),
            metadata=d.get("metadata", {}),
        )


# ══════════════════════════════════════════════════════════════════════════
#  AgentCore — the single contract every agent must satisfy
# ══════════════════════════════════════════════════════════════════════════

@runtime_checkable
class AgentCore(Protocol):
    """Every agent on the AITest platform satisfies this protocol.

    Agent = State + Tools + Policy + ExecutionLoop

    An agent:
      - Has a unique identity (agent_id, agent_type)
      - Accepts AgentContext and produces AgentResult
      - Supports both batch (run) and interactive (run_interactive) modes
      - Can receive external input mid-execution (send_interaction)
      - Can be paused, resumed, and disposed
      - Registers itself in the LifecycleRegistry for auto-GC
    """

    @property
    def agent_id(self) -> str:
        """Unique identifier within a run. e.g. 'automation-agent:equipment:alarm-config'."""
        ...

    @property
    def agent_type(self) -> str:
        """Category: 'sop' | 'onboarding' | 'chat' | 'qa' | 'custom'."""
        ...

    async def run(self, context: AgentContext) -> AgentResult:
        """Execute the agent to completion. Non-interactive."""
        ...

    async def run_interactive(
        self, context: AgentContext
    ) -> AsyncGenerator[Any, None]:
        """Execute interactively, yielding events for SSE streaming."""
        ...

    def send_interaction(self, response: str) -> None:
        """Send external input to a paused (HITL) agent run."""
        ...

    def pause(self) -> None:
        """Request pause at next yield point."""
        ...

    def resume(self) -> None:
        """Resume after pause."""
        ...

    def dispose(self) -> None:
        """Release all resources. Idempotent. Called by AgentRuntime."""
        ...


# ══════════════════════════════════════════════════════════════════════════
#  AgentRuntime — manages agent lifecycle on top of infra
# ══════════════════════════════════════════════════════════════════════════

class AgentRuntime:
    """Execution environment for AgentCore instances.

    Built on top of LifecycleRegistry + MemoryGuard + WorkerPool.
    Provides: run, pause, resume, fork, observe, dispose.

    Usage:
        runtime = AgentRuntime()
        result = await runtime.execute(agent, context)
    """

    def __init__(self, max_concurrent: int = 4):
        self._active: dict[str, AgentCore] = {}
        self._results: dict[str, AgentResult] = {}
        self._run_ids: dict[str, str] = {}  # agent_id → run_id
        self._max_concurrent = max_concurrent

    # ── Execute ────────────────────────────────────────────────────────

    async def execute(
        self, agent: AgentCore, context: AgentContext,
        timeout_s: float = 3600,
    ) -> AgentResult:
        """Run an agent to completion. Registers in LifecycleRegistry.

        Args:
            agent: AgentCore instance
            context: Execution context
            timeout_s: Max execution time before forced disposal

        Returns:
            AgentResult with full execution summary
        """
        run_id = f"run-{agent.agent_id}-{uuid.uuid4().hex[:8]}"
        self._run_ids[agent.agent_id] = run_id
        self._active[agent.agent_id] = agent

        # Register in LifecycleRegistry
        self._register_agent(agent, run_id, timeout_s)

        started = time.monotonic()
        try:
            result = await asyncio.wait_for(
                agent.run(context),
                timeout=timeout_s,
            )
        except asyncio.TimeoutError:
            result = AgentResult(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type,
                status=AgentRunStatus.TIMED_OUT,
                run_id=run_id,
                error=f"Timeout after {timeout_s}s",
                duration_ms=(time.monotonic() - started) * 1000,
            )
        except asyncio.CancelledError:
            result = AgentResult(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type,
                status=AgentRunStatus.CANCELLED,
                run_id=run_id,
                duration_ms=(time.monotonic() - started) * 1000,
            )
        except Exception as e:
            result = AgentResult(
                agent_id=agent.agent_id,
                agent_type=agent.agent_type,
                status=AgentRunStatus.FAILED,
                run_id=run_id,
                error=str(e)[:500],
                duration_ms=(time.monotonic() - started) * 1000,
            )

        if not result.run_id:
            result.run_id = run_id
        if not result.duration_ms:
            result.duration_ms = (time.monotonic() - started) * 1000

        self._results[agent.agent_id] = result
        self._unregister_agent(agent.agent_id)
        self._active.pop(agent.agent_id, None)
        return result

    async def execute_interactive(
        self, agent: AgentCore, context: AgentContext,
        timeout_s: float = 3600,
    ) -> AsyncGenerator[Any, None]:
        """Run an agent interactively, yielding events for SSE streaming.

        Registers in LifecycleRegistry. Unregisters on completion/error.
        """
        run_id = f"run-{agent.agent_id}-{uuid.uuid4().hex[:8]}"
        self._run_ids[agent.agent_id] = run_id
        self._active[agent.agent_id] = agent
        self._register_agent(agent, run_id, timeout_s)

        try:
            async for event in agent.run_interactive(context):
                yield event
        except asyncio.CancelledError:
            yield {"type": "agent_end", "status": "cancelled"}
        except Exception as e:
            yield {"type": "agent_end", "status": "fail", "error": str(e)[:500]}
        finally:
            self._unregister_agent(agent.agent_id)
            self._active.pop(agent.agent_id, None)

    # ── Lifecycle control ──────────────────────────────────────────────

    def pause(self, agent_id: str) -> bool:
        """Pause an agent at its next yield point."""
        agent = self._active.get(agent_id)
        if agent:
            agent.pause()
            return True
        return False

    def resume(self, agent_id: str) -> bool:
        """Resume a paused agent."""
        agent = self._active.get(agent_id)
        if agent:
            agent.resume()
            return True
        return False

    def send_interaction(self, agent_id: str, response: str) -> bool:
        """Send user response to a paused (HITL) agent."""
        agent = self._active.get(agent_id)
        if agent:
            agent.send_interaction(response)
            return True
        return False

    def dispose(self, agent_id: str) -> bool:
        """Force-dispose an agent and release all its resources."""
        agent = self._active.pop(agent_id, None)
        if agent:
            agent.dispose()
            self._unregister_agent(agent_id)
            return True
        return False

    def dispose_all(self) -> int:
        """Dispose all active agents. For shutdown."""
        count = 0
        for agent_id in list(self._active.keys()):
            if self.dispose(agent_id):
                count += 1
        return count

    # ── Observe ────────────────────────────────────────────────────────

    def observe(self, agent_id: str) -> dict:
        """Get current state of an agent for debugging/monitoring."""
        agent = self._active.get(agent_id)
        result = self._results.get(agent_id)
        run_id = self._run_ids.get(agent_id, "")
        return {
            "agent_id": agent_id,
            "active": agent is not None,
            "agent_type": agent.agent_type if agent else "unknown",
            "run_id": run_id,
            "result": result.to_dict() if result else None,
        }

    def list_active(self) -> list[dict]:
        """List all currently running agents."""
        return [
            {"agent_id": aid, "agent_type": a.agent_type}
            for aid, a in self._active.items()
        ]

    @property
    def active_count(self) -> int:
        return len(self._active)

    # ── Internal ───────────────────────────────────────────────────────

    def _register_agent(self, agent: AgentCore, run_id: str, ttl_s: float):
        try:
            from aitest.platform.lifecycle import get_registry, _ObjectRef
            get_registry().register(_ObjectRef(
                f"agent:{agent.agent_id}:{run_id}",
                f"agent-runtime:{agent.agent_type}",
                dispose_fn=agent.dispose,
                ttl_s=ttl_s,
            ))
        except Exception:
            pass

    def _unregister_agent(self, agent_id: str):
        try:
            from aitest.platform.lifecycle import get_registry
            run_id = self._run_ids.get(agent_id, "")
            if run_id:
                get_registry().unregister(f"agent:{agent_id}:{run_id}")
        except Exception:
            pass


# ══════════════════════════════════════════════════════════════════════════
#  Singleton
# ══════════════════════════════════════════════════════════════════════════

_runtime: Optional[AgentRuntime] = None
_runtime_lock = __import__('threading').Lock()


def get_agent_runtime() -> AgentRuntime:
    """Get or create the global AgentRuntime singleton."""
    global _runtime
    with _runtime_lock:
        if _runtime is None:
            _runtime = AgentRuntime()
        return _runtime


# ══════════════════════════════════════════════════════════════════════════
#  Adapters — wire existing agent types into AgentCore protocol
# ══════════════════════════════════════════════════════════════════════════

class AgentLoopAdapter:
    """Adapts AgentLoop (sync generator) → AgentCore (async protocol).

    AgentLoop.run() is a synchronous Generator[AgentEvent].
    AgentLoop.run_interactive() is a sync Generator.
    This adapter wraps them into async equivalents for AgentRuntime.

    Usage:
        loop = AgentLoop("automation-agent", module="equipment", page="alarm-config")
        adapter = AgentLoopAdapter(loop)
        runtime = get_agent_runtime()
        result = await runtime.execute(adapter, AgentContext(module="equipment"))
    """

    def __init__(self, agent_loop):
        from aitest.agents.agent_runner import AgentLoop
        self._loop: AgentLoop = agent_loop
        self._agent_id = f"{agent_loop.agent_name}:{agent_loop.module or '?'}:{agent_loop.page or '?'}"
        self._agent_type = "sop" if hasattr(agent_loop, '_sop_mode') else "testing"
        self._paused = False

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def agent_type(self) -> str:
        return self._agent_type

    async def run(self, context: AgentContext) -> AgentResult:
        """Run AgentLoop synchronously in a thread, produce AgentResult."""
        import threading
        from datetime import datetime, timezone

        started = datetime.now(timezone.utc)
        result_container = {}
        error_container = {}

        def _run_in_thread():
            try:
                state = self._loop.run()
                result_container["state"] = state
            except Exception as e:
                error_container["error"] = e

        thread = threading.Thread(target=_run_in_thread, daemon=True)
        thread.start()

        # Pump the event loop while waiting for the sync thread
        import asyncio as _asyncio
        while thread.is_alive():
            await _asyncio.sleep(0.1)

        if error_container:
            return AgentResult(
                agent_id=self._agent_id,
                agent_type=self._agent_type,
                status=AgentRunStatus.FAILED,
                error=str(error_container["error"])[:500],
                started_at=started.isoformat(),
            )

        state = result_container.get("state")
        if state is None:
            return AgentResult(
                agent_id=self._agent_id,
                agent_type=self._agent_type,
                status=AgentRunStatus.FAILED,
                error="AgentLoop.run() returned no state",
                started_at=started.isoformat(),
            )

        completed_at = datetime.now(timezone.utc)
        duration_ms = (completed_at - started).total_seconds() * 1000

        return AgentResult(
            agent_id=self._agent_id,
            agent_type=self._agent_type,
            status=(
                AgentRunStatus.SUCCESS if state.success
                else AgentRunStatus.COMPLETED_WITH_ISSUES if state.done
                else AgentRunStatus.FAILED
            ),
            steps_completed=state.step,
            skills_completed=list(state.completed_skills),
            skills_failed=list(state.failed_skills.keys()),
            summary=state.termination_reason or "",
            error="; ".join(state.failed_skills.values()) if state.failed_skills else "",
            observations=[
                {
                    "skill_id": o.skill_id, "status": o.status,
                    "summary": o.summary, "token_usage": o.token_usage,
                    "failure_category": o.failure_category,
                }
                for o in getattr(state, 'observations', [])
            ],
            duration_ms=duration_ms,
            started_at=started.isoformat(),
            completed_at=completed_at.isoformat(),
        )

    async def run_interactive(self, context: AgentContext) -> AsyncGenerator[Any, None]:
        """Bridge AgentLoop's sync generator to async generator for SSE."""
        import asyncio as _asyncio
        from queue import Queue

        event_queue: Queue = Queue()

        def _run():
            try:
                for event in self._loop.run_interactive():
                    event_queue.put(event)
                    if self._paused:
                        # Wait for resume signal
                        while self._paused:
                            time.sleep(0.1)
                event_queue.put(None)  # sentinel
            except Exception as e:
                event_queue.put({"type": "agent_end", "status": "fail", "error": str(e)[:500]})

        import threading
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        while True:
            # Non-blocking poll
            try:
                item = event_queue.get(timeout=0.1)
            except Exception:
                await _asyncio.sleep(0.05)
                continue

            if item is None:  # sentinel
                break

            if isinstance(item, dict):
                yield item
            else:
                # AgentEvent — convert to dict for SSE compatibility
                yield {
                    "type": getattr(item, 'type', 'unknown'),
                    "skill_id": getattr(item, 'skill_id', ''),
                    "content": getattr(item, 'content', ''),
                    "status": getattr(item, 'status', ''),
                    "summary": getattr(item, 'summary', ''),
                    "error": getattr(item, 'error', ''),
                    "progress": getattr(item, 'progress', {}),
                    "token_usage": getattr(item, 'token_usage', {}),
                }

    def send_interaction(self, response: str) -> None:
        if hasattr(self._loop, 'send_interaction'):
            self._loop.send_interaction(response)

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def dispose(self) -> None:
        """Release AgentLoop resources."""
        self._loop = None


class SOPRunnerAdapter:
    """Adapts SOPRunner (sync Generator) → AgentCore (async protocol)."""

    def __init__(self, sop_runner):
        from aitest.graphs.sop_runner import SOPRunner
        self._runner = sop_runner
        pages_str = ",".join(sop_runner.pages) if sop_runner.pages else sop_runner.module
        self._agent_id = f"sop-runner:{sop_runner.module}:{pages_str}"
        self._agent_type = "sop"
        self._paused = False

    @property
    def agent_id(self) -> str:
        return self._agent_id

    @property
    def agent_type(self) -> str:
        return self._agent_type

    async def run(self, context: AgentContext) -> AgentResult:
        """Run SOPRunner synchronously in a thread."""
        import threading
        from datetime import datetime, timezone

        started = datetime.now(timezone.utc)
        events = []
        error_str = ""

        def _run():
            nonlocal error_str
            try:
                for event in self._runner.run_interactive():
                    events.append(event)
            except Exception as e:
                error_str = str(e)

        thread = threading.Thread(target=_run, daemon=True)
        thread.start()
        import asyncio as _asyncio
        while thread.is_alive():
            await _asyncio.sleep(0.1)

        completed_at = datetime.now(timezone.utc)
        duration_ms = (completed_at - started).total_seconds() * 1000

        # Find terminal event
        last_event = events[-1] if events else None
        is_success = (
            hasattr(last_event, 'status') and last_event.status not in ("failed", "fail")
        ) if last_event else False

        return AgentResult(
            agent_id=self._agent_id,
            agent_type=self._agent_type,
            status=(
                AgentRunStatus.SUCCESS if is_success and not error_str
                else AgentRunStatus.FAILED
            ),
            steps_completed=len(events),
            summary=(
                getattr(last_event, 'summary', '') or getattr(last_event, 'content', '')
            ) if last_event else "",
            error=error_str[:500],
            duration_ms=duration_ms,
            started_at=started.isoformat(),
            completed_at=completed_at.isoformat(),
        )

    async def run_interactive(self, context: AgentContext) -> AsyncGenerator[Any, None]:
        """Bridge SOPRunner sync generator to async generator."""
        import asyncio as _asyncio
        from queue import Queue

        event_queue: Queue = Queue()

        def _run():
            try:
                for event in self._runner.run_interactive():
                    event_queue.put(event)
                    if self._paused:
                        while self._paused:
                            time.sleep(0.1)
                event_queue.put(None)
            except Exception as e:
                event_queue.put({"type": "sop_complete", "status": "fail", "error": str(e)[:500]})

        import threading
        thread = threading.Thread(target=_run, daemon=True)
        thread.start()

        while True:
            try:
                item = event_queue.get(timeout=0.1)
            except Exception:
                await _asyncio.sleep(0.05)
                continue

            if item is None:
                break

            if isinstance(item, dict):
                yield item
            else:
                yield {
                    "type": getattr(item, 'type', 'unknown'),
                    "content": getattr(item, 'content', ''),
                    "skill_id": getattr(item, 'skill_id', ''),
                    "progress": getattr(item, 'progress', {}),
                    "status": getattr(item, 'status', ''),
                    "summary": getattr(item, 'summary', ''),
                    "error": getattr(item, 'error', ''),
                }

    def send_interaction(self, response: str) -> None:
        if hasattr(self._runner, 'send_interaction'):
            self._runner.send_interaction(response)

    def pause(self) -> None:
        self._paused = True

    def resume(self) -> None:
        self._paused = False

    def dispose(self) -> None:
        self._runner = None
