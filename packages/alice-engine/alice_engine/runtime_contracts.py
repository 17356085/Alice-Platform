"""Shared runtime contract pack for SDK-neutral execution surfaces.

Phase 8 freezes the minimal contracts that sit between the execution kernel and
platform-specific projections. These types are intentionally small and stable:
the SDK owns the neutral shape, while the platform maps them into RunEvent,
audit, billing, replay persistence, and checkpoint/adaptor concerns.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from .contracts import ExecutionContext, ExecutionResult


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class RuntimeArtifactRecord:
    """SDK-neutral artifact contract."""

    path: str
    kind: str = ""
    phase: str = ""
    module: str = ""
    page: str = ""
    run_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "kind": self.kind,
            "phase": self.phase,
            "module": self.module,
            "page": self.page,
            "run_id": self.run_id,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeCheckpointRecord:
    """Resume/checkpoint contract shared across SDK and platform adapters."""

    thread_id: str
    checkpoint_id: str = ""
    available: bool = False
    values: dict[str, Any] = field(default_factory=dict)
    raw: dict[str, Any] = field(default_factory=dict)
    loaded_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "thread_id": self.thread_id,
            "checkpoint_id": self.checkpoint_id,
            "available": self.available,
            "values": dict(self.values),
            "raw": dict(self.raw),
            "loaded_at": self.loaded_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeReplaySessionRecord:
    """Replay session metadata contract."""

    session_id: str
    run_id: str
    module: str
    page: str = ""
    agent: str = ""
    mode: str = ""
    status: str = ""
    step_count: int = 0
    total_duration_ms: float = 0.0
    created_at: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "run_id": self.run_id,
            "module": self.module,
            "page": self.page,
            "agent": self.agent,
            "mode": self.mode,
            "status": self.status,
            "step_count": self.step_count,
            "total_duration_ms": self.total_duration_ms,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeReplayStepRecord:
    """Replay step contract."""

    step_id: str
    session_id: str
    index: int
    kind: str
    name: str
    status: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    output_data: dict[str, Any] = field(default_factory=dict)
    error_message: str = ""
    duration_ms: float = 0.0
    started_at: float = 0.0
    completed_at: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "session_id": self.session_id,
            "index": self.index,
            "kind": self.kind,
            "name": self.name,
            "status": self.status,
            "input_data": dict(self.input_data),
            "output_data": dict(self.output_data),
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class RuntimeEventEnvelope:
    """Neutral runtime event contract before platform-specific projection."""

    event_type: str
    run_id: str
    request_id: str = ""
    event_id: str = ""
    timestamp: str = ""
    context: ExecutionContext | None = None
    module: str = ""
    pages: list[str] = field(default_factory=list)
    agent: str = ""
    phase: str = ""
    status: str = ""
    total_tokens: int = 0
    total_cost: float = 0.0
    agent_runs: int = 0
    duration_ms: float = 0.0
    error_message: str = ""
    replay_session_id: str = ""
    checkpoint_thread_id: str = ""
    completed_phases: list[str] = field(default_factory=list)
    failed_phases: list[str] = field(default_factory=list)
    artifacts: list[RuntimeArtifactRecord] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            object.__setattr__(self, "timestamp", _utcnow())

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "run_id": self.run_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "context": self.context.to_dict() if self.context else None,
            "module": self.module,
            "pages": list(self.pages),
            "agent": self.agent,
            "phase": self.phase,
            "status": self.status,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "agent_runs": self.agent_runs,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "replay_session_id": self.replay_session_id,
            "checkpoint_thread_id": self.checkpoint_thread_id,
            "completed_phases": list(self.completed_phases),
            "failed_phases": list(self.failed_phases),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "metadata": dict(self.metadata),
        }

    @classmethod
    def from_execution_result(
        cls,
        result: ExecutionResult,
        *,
        event_type: str,
        context: ExecutionContext | None = None,
        phase: str = "",
        status: str = "",
        replay_session_id: str = "",
        checkpoint_thread_id: str = "",
        artifacts: list[RuntimeArtifactRecord] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "RuntimeEventEnvelope":
        return cls(
            event_type=event_type,
            run_id=result.run_id,
            request_id=result.request_id,
            context=context,
            module=result.module,
            pages=list(result.pages),
            agent=result.agent,
            phase=phase,
            status=status or result.status,
            total_tokens=result.total_tokens,
            total_cost=result.total_cost,
            agent_runs=result.agent_runs,
            duration_ms=result.duration_ms,
            error_message=result.error_message,
            replay_session_id=replay_session_id or str(result.metadata.get("replay_session_id", "")),
            checkpoint_thread_id=checkpoint_thread_id or str(result.metadata.get("checkpoint_thread_id", "")),
            completed_phases=list(result.completed_phases),
            failed_phases=list(result.failed_phases),
            artifacts=list(artifacts or [RuntimeArtifactRecord(path=path, run_id=result.run_id) for path in result.artifacts]),
            metadata=dict(metadata or result.metadata),
        )
