"""Event projection layer for execution lifecycle.

This module handles the transformation of execution lifecycle events
into runtime event envelopes and publishes them to the event bus.

Extracted from execution_service.py to improve modularity.
"""

from __future__ import annotations

from typing import Any

from alice_engine.contracts import ExecutionContext
from alice_engine.runtime_contracts import RuntimeArtifactRecord, RuntimeEventEnvelope

from .execution_request import ExecutionRequest
from .run import Run
from .run_event import EventType
from .runtime_contracts import runtime_event_to_run_event


class ExecutionEventEmitter:
    """Handles event emission for execution lifecycle."""

    def __init__(self, store, bus):
        """Initialize event emitter.

        Args:
            store: Run store for persisting events
            bus: Event bus for publishing events
        """
        self._store = store
        self._bus = bus

    def emit_execution_requested(
        self,
        ctx: ExecutionContext,
        request: ExecutionRequest,
        agent: str,
        version_payload: dict[str, Any],
    ) -> None:
        """Emit execution requested event."""
        envelope = RuntimeEventEnvelope(
            event_type=EventType.EXECUTION_REQUESTED,
            run_id="",
            request_id=request.request_id,
            context=ctx,
            module=request.module,
            pages=list(request.pages),
            agent=agent,
            metadata=version_payload,
        )
        ev = runtime_event_to_run_event(envelope)
        self._store.save_event(ev)
        self._bus.publish_async(ev)

    def emit_started(
        self,
        ctx: ExecutionContext,
        request: ExecutionRequest,
        run: Run,
        version_payload: dict[str, Any],
    ) -> None:
        """Emit execution started event."""
        replay_session_id = getattr(run, "replay_session_id", "")
        envelope = RuntimeEventEnvelope(
            event_type=EventType.EXECUTION_STARTED,
            run_id=run.run_id,
            request_id=request.request_id,
            context=ctx,
            module=run.module,
            agent=run.agent,
            replay_session_id=replay_session_id,
            metadata=version_payload,
        )
        ev = runtime_event_to_run_event(envelope)
        self._store.save_event(ev)
        self._bus.publish_async(ev)

    def emit_phase_started(
        self,
        request: ExecutionRequest,
        run: Run,
        version_payload: dict[str, Any],
    ) -> None:
        """Emit phase started event."""
        replay_session_id = getattr(run, "replay_session_id", "")
        envelope = RuntimeEventEnvelope(
            event_type=EventType.PHASE_STARTED,
            run_id=run.run_id,
            request_id=request.request_id,
            module=run.module,
            phase="execution",
            replay_session_id=replay_session_id,
            metadata=version_payload,
        )
        ev = runtime_event_to_run_event(envelope)
        self._store.save_event(ev)
        self._bus.publish_async(ev)

    def emit_phase_completed(
        self,
        request: ExecutionRequest,
        run: Run,
        version_payload: dict[str, Any],
    ) -> None:
        """Emit phase completed event."""
        replay_session_id = getattr(run, "replay_session_id", "")
        envelope = RuntimeEventEnvelope(
            event_type=EventType.PHASE_COMPLETED,
            run_id=run.run_id,
            request_id=request.request_id,
            module=run.module,
            phase="execution",
            replay_session_id=replay_session_id,
            metadata=version_payload,
        )
        ev = runtime_event_to_run_event(envelope)
        self._store.save_event(ev)
        self._bus.publish_async(ev)

    def emit_terminal_event(
        self,
        ctx: ExecutionContext,
        request: ExecutionRequest,
        run: Run,
        completed_phases: list[str],
        failed_phases: list[str],
        artifacts: list[RuntimeArtifactRecord],
        version_payload: dict[str, Any],
        *,
        duration_ms: float = 0.0,
    ) -> None:
        """Emit terminal event (completed/cancelled/failed)."""
        replay_session_id = getattr(run, "replay_session_id", "")
        if run.status == "completed":
            event_type = EventType.RUN_COMPLETED
        elif run.status == "cancelled":
            event_type = EventType.RUN_CANCELLED
        else:
            event_type = EventType.RUN_FAILED

        envelope = RuntimeEventEnvelope(
            event_type=event_type,
            run_id=run.run_id,
            request_id=request.request_id,
            context=ctx,
            module=run.module,
            pages=list(run.pages),
            agent=run.agent,
            status=run.status,
            total_tokens=run.total_tokens,
            total_cost=run.total_cost,
            agent_runs=run.agent_runs,
            duration_ms=duration_ms,
            error_message=run.error_message,
            completed_phases=completed_phases,
            failed_phases=failed_phases,
            replay_session_id=replay_session_id,
            artifacts=artifacts,
            metadata={
                **version_payload,
                "retry_count": request.retry_count,
                "max_retries": request.max_retries,
            },
        )
        ev = runtime_event_to_run_event(envelope)
        self._store.save_event(ev)
        self._bus.publish_async(ev)

    def emit_failed(
        self,
        ctx: ExecutionContext,
        request: ExecutionRequest,
        run: Run,
        error: str,
        version_payload: dict[str, Any],
        *,
        duration_ms: float = 0.0,
    ) -> None:
        """Emit execution failed event."""
        replay_session_id = getattr(run, "replay_session_id", "")
        envelope = RuntimeEventEnvelope(
            event_type=EventType.RUN_FAILED,
            run_id=run.run_id,
            request_id=request.request_id,
            context=ctx,
            module=run.module,
            pages=list(run.pages),
            agent=run.agent,
            status="failed",
            error_message=error,
            duration_ms=duration_ms,
            replay_session_id=replay_session_id,
            metadata={
                **version_payload,
                "retry_count": request.retry_count,
                "max_retries": request.max_retries,
            },
        )
        ev = runtime_event_to_run_event(envelope)
        self._store.save_event(ev)
        self._bus.publish_async(ev)
