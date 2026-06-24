"""
RunEvent — typed, immutable events emitted during execution lifecycle. v2.2

Downstream consumers (Webhooks, Audit, Timeline, Billing, Metrics) subscribe
to RunEvent types rather than polling Run state.

Event types:
  execution.requested   — ExecutionRequest created
  execution.queued      — ExecutionRequest enqueued
  execution.started     — ExecutionRequest dispatched → Run created
  phase.started         — Agent phase began
  phase.completed       — Agent phase finished
  artifact.created      — Artifact produced
  run.completed         — Run finished successfully
  run.failed            — Run failed
  run.cancelled         — Run cancelled by user
  cost.recorded         — Cost snapshot recorded
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ── Event type constants ─────────────────────────────────────────────────

class EventType:
    EXECUTION_REQUESTED = "execution.requested"
    EXECUTION_QUEUED = "execution.queued"
    EXECUTION_STARTED = "execution.started"
    PHASE_STARTED = "phase.started"
    PHASE_COMPLETED = "phase.completed"
    ARTIFACT_CREATED = "artifact.created"
    RUN_COMPLETED = "run.completed"
    RUN_FAILED = "run.failed"
    RUN_CANCELLED = "run.cancelled"
    COST_RECORDED = "cost.recorded"

    # Platform operational events (v2.3+)
    ORG_CREATED = "org.created"
    WORKSPACE_CREATED = "workspace.created"
    API_KEY_CREATED = "api_key.created"
    API_KEY_REVOKED = "api_key.revoked"
    MEMBER_ADDED = "member.added"
    MEMBER_REMOVED = "member.removed"
    QUOTA_CHANGED = "quota.changed"


# ── RunEvent ─────────────────────────────────────────────────────────────

@dataclass
class RunEvent:
    """Immutable event emitted during execution lifecycle.

    Consumers subscribe via EventBus: bus.subscribe(EventType.RUN_COMPLETED, handler)
    """

    event_id: str              # Unique event ID (UUID7)
    event_type: str            # One of EventType constants
    run_id: str                # Parent Run ID
    request_id: str = ""       # Parent ExecutionRequest ID
    timestamp: str = ""
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "run_id": self.run_id,
            "request_id": self.request_id,
            "timestamp": self.timestamp,
            "data": self.data,
        }


# ── Factory helpers ──────────────────────────────────────────────────────

def make_event(
    event_type: str,
    run_id: str = "",
    request_id: str = "",
    **data,
) -> RunEvent:
    """Create a RunEvent with a generated event_id."""
    import uuid
    return RunEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        run_id=run_id,
        request_id=request_id,
        data=data,
    )
