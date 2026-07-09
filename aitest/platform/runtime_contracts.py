"""Platform projections for the shared runtime contract pack."""

from __future__ import annotations

from typing import Any
import uuid

from alice_engine.contracts import ExecutionContext, ExecutionResult
from alice_engine.runtime_contracts import (
    RuntimeArtifactRecord,
    RuntimeCheckpointRecord,
    RuntimeEventEnvelope,
    RuntimeReplaySessionRecord,
    RuntimeReplayStepRecord,
)

from .checkpoint import CheckpointSnapshot
from .replay import ExecutionStep, ReplaySession
from .run_event import EventDataKey as K, RunEvent


def runtime_event_to_run_event(envelope: RuntimeEventEnvelope) -> RunEvent:
    data: dict[str, Any] = dict(envelope.metadata)
    if envelope.module:
        data[K.MODULE] = envelope.module
    if envelope.pages:
        data[K.PAGES] = list(envelope.pages)
    if envelope.agent:
        data[K.AGENT] = envelope.agent
    if envelope.context:
        if envelope.context.workspace_id:
            data[K.WORKSPACE_ID] = envelope.context.workspace_id
        if envelope.context.org_id:
            data[K.ORG_ID] = envelope.context.org_id
    if envelope.total_tokens:
        data[K.TOTAL_TOKENS] = envelope.total_tokens
    if envelope.total_cost:
        data[K.TOTAL_COST] = float(envelope.total_cost)
    if envelope.agent_runs:
        data[K.AGENT_RUNS] = envelope.agent_runs
    if envelope.phase:
        data[K.PHASE] = envelope.phase
    if envelope.error_message:
        data[K.ERROR] = envelope.error_message
    if envelope.replay_session_id:
        data[K.REPLAY_SESSION_ID] = envelope.replay_session_id
    if envelope.checkpoint_thread_id:
        data["checkpoint_thread_id"] = envelope.checkpoint_thread_id
    if envelope.completed_phases:
        data["completed_phases"] = list(envelope.completed_phases)
    if envelope.failed_phases:
        data["failed_phases"] = list(envelope.failed_phases)
    if envelope.duration_ms:
        data["duration_ms"] = envelope.duration_ms

    if envelope.artifacts:
        first = envelope.artifacts[0]
        if first.kind:
            data[K.ARTIFACT_TYPE] = first.kind
        if first.path:
            data[K.ARTIFACT_PATH] = first.path
        data["artifacts"] = [artifact.to_dict() for artifact in envelope.artifacts]

    return RunEvent(
        event_id=envelope.event_id or str(uuid.uuid4()),
        event_type=envelope.event_type,
        run_id=envelope.run_id,
        request_id=envelope.request_id,
        timestamp=envelope.timestamp,
        data=data,
    )


def runtime_event_from_result(
    result: ExecutionResult,
    *,
    event_type: str,
    context: ExecutionContext | None = None,
    phase: str = "",
    replay_session_id: str = "",
    checkpoint_thread_id: str = "",
    artifacts: list[RuntimeArtifactRecord] | None = None,
    metadata: dict[str, Any] | None = None,
) -> RuntimeEventEnvelope:
    return RuntimeEventEnvelope.from_execution_result(
        result,
        event_type=event_type,
        context=context,
        phase=phase,
        replay_session_id=replay_session_id,
        checkpoint_thread_id=checkpoint_thread_id,
        artifacts=artifacts,
        metadata=metadata,
    )


def runtime_event_from_payload(
    *,
    event_type: str,
    run_id: str = "",
    request_id: str = "",
    event_id: str = "",
    timestamp: str = "",
    context: ExecutionContext | None = None,
    module: str = "",
    pages: list[str] | None = None,
    agent: str = "",
    phase: str = "",
    status: str = "",
    total_tokens: int = 0,
    total_cost: float = 0.0,
    agent_runs: int = 0,
    duration_ms: float = 0.0,
    error_message: str = "",
    replay_session_id: str = "",
    checkpoint_thread_id: str = "",
    completed_phases: list[str] | None = None,
    failed_phases: list[str] | None = None,
    artifacts: list[RuntimeArtifactRecord] | None = None,
    metadata: dict[str, Any] | None = None,
) -> RuntimeEventEnvelope:
    return RuntimeEventEnvelope(
        event_type=event_type,
        run_id=run_id,
        request_id=request_id,
        event_id=event_id,
        timestamp=timestamp,
        context=context,
        module=module,
        pages=list(pages or []),
        agent=agent,
        phase=phase,
        status=status,
        total_tokens=total_tokens,
        total_cost=total_cost,
        agent_runs=agent_runs,
        duration_ms=duration_ms,
        error_message=error_message,
        replay_session_id=replay_session_id,
        checkpoint_thread_id=checkpoint_thread_id,
        completed_phases=list(completed_phases or []),
        failed_phases=list(failed_phases or []),
        artifacts=list(artifacts or []),
        metadata=dict(metadata or {}),
    )


def checkpoint_snapshot_to_record(snapshot: CheckpointSnapshot) -> RuntimeCheckpointRecord:
    raw = dict(snapshot.raw) if isinstance(snapshot.raw, dict) else {}
    checkpoint_id = str(raw.get("id", raw.get("checkpoint_id", "")))
    return RuntimeCheckpointRecord(
        thread_id=snapshot.thread_id,
        checkpoint_id=checkpoint_id,
        available=snapshot.available,
        values=dict(snapshot.values),
        raw=raw,
        loaded_at=snapshot.loaded_at,
    )


def replay_session_to_record(session: ReplaySession) -> RuntimeReplaySessionRecord:
    return RuntimeReplaySessionRecord(
        session_id=session.id,
        run_id=session.run_id,
        module=session.module,
        page=session.page,
        agent=session.agent,
        mode=session.mode,
        status=session.status,
        step_count=session.step_count,
        total_duration_ms=session.total_duration_ms,
        created_at=session.created_at,
    )


def replay_step_to_record(step: ExecutionStep) -> RuntimeReplayStepRecord:
    return RuntimeReplayStepRecord(
        step_id=step.id,
        session_id=step.session_id,
        index=step.step_index,
        kind=step.step_type,
        name=step.name,
        status=step.status,
        input_data=dict(step.input_data),
        output_data=dict(step.output_data),
        error_message=step.error_message,
        duration_ms=step.duration_ms,
        started_at=step.started_at,
        completed_at=step.completed_at,
        metadata=dict(step.metadata),
    )
