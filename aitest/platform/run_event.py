"""
RunEvent — typed, immutable events emitted during execution lifecycle. v3.1

Downstream consumers (Webhooks, Audit, Timeline, Billing, Metrics) subscribe
to RunEvent types rather than polling Run state.

v3.0: Runtime schema validation — make_event() validates data against
EVENT_SCHEMAS in development mode (AITEST_ENV=dev). Production mode skips
validation for zero overhead.

v3.1: EventDataKey constants — all event.data key access goes through
named constants, eliminating hardcoded string key coupling.

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

__all__ = [
    "RunEvent", "EventType", "EventDataKey", "make_event",
    "ExecutionRequestedData", "ExecutionStartedData", "RunCompletedData",
    "RunFailedData", "RunCancelledData", "CostRecordedData",
    "PhaseStartedData", "PhaseCompletedData", "ArtifactCreatedData",
    "RunEventData", "EVENT_SCHEMAS",
]

import os
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TypedDict, Union

_log = logging.getLogger(__name__)


# ── Event Data Key Constants (v3.1) ────────────────────────────────────
#
# ALL event.data key access MUST go through these constants.
# This eliminates the hidden coupling where consumers hardcode string keys
# that silently break if the producer changes the key name.

class EventDataKey:
    """Named constants for RunEvent.data dict keys.

    Usage:
        from aitest.platform.run_event import EventDataKey as K

        # Producer (ExecutionService):
        make_event(EventType.RUN_COMPLETED, **{K.TOTAL_TOKENS: 100})

        # Consumer (MetricsConsumer):
        tokens = event.data.get(K.TOTAL_TOKENS, 0)
    """
    # Identity
    MODULE = "module"
    AGENT = "agent"
    PAGES = "pages"
    WORKSPACE_ID = "workspace_id"
    ORG_ID = "org_id"

    # Execution
    TOTAL_TOKENS = "total_tokens"
    TOTAL_COST = "total_cost"
    AGENT_RUNS = "agent_runs"
    ERROR = "error"

    # Phase
    PHASE = "phase"

    # Artifact
    ARTIFACT_TYPE = "artifact_type"
    ARTIFACT_PATH = "artifact_path"

    # Resume
    RESUME = "resume"
    ORIGINAL_RUN_ID = "original_run_id"

    # Audit / Identity
    TRIGGERED_BY = "triggered_by"

    # Replay / Traceability
    REPLAY_SESSION_ID = "replay_session_id"
    REPLAY_STEP_ID = "replay_step_id"

    # Versioning / Governance
    POLICY_VERSION = "policy_version"
    GOVERNANCE_VERSION = "governance_version"
    CONFIG_VERSION = "config_version"
    GOVERNANCE_PACK_ROOT = "governance_pack_root"


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


# ── Typed data schemas per event type ────────────────────────────────────
# These TypedDicts document the expected structure of RunEvent.data for each
# event type. They are not enforced at runtime (data remains dict[str, Any])
# but provide static type checking and IDE autocompletion.

class ExecutionRequestedData(TypedDict, total=False):
    module: str
    pages: list[str]
    agent: str

class ExecutionStartedData(TypedDict, total=False):
    workspace_id: str
    org_id: str
    module: str
    agent: str
    replay_session_id: str
    policy_version: str
    governance_version: str
    config_version: str
    governance_pack_root: str

class RunCompletedData(TypedDict, total=False):
    workspace_id: str
    org_id: str
    module: str
    agent: str
    total_tokens: int
    total_cost: float
    agent_runs: int
    duration_ms: float
    retry_count: int
    max_retries: int
    replay_session_id: str
    policy_version: str
    governance_version: str
    config_version: str
    governance_pack_root: str

class RunFailedData(TypedDict, total=False):
    workspace_id: str
    org_id: str
    module: str
    agent: str
    total_tokens: int
    total_cost: float
    agent_runs: int
    duration_ms: float
    retry_count: int
    max_retries: int
    error: str
    replay_session_id: str
    policy_version: str
    governance_version: str
    config_version: str
    governance_pack_root: str

class RunCancelledData(TypedDict, total=False):
    workspace_id: str
    org_id: str

class CostRecordedData(TypedDict, total=False):
    total_cost: float
    total_tokens: int
    org_id: str
    workspace_id: str
    replay_session_id: str
    policy_version: str
    governance_version: str
    config_version: str
    governance_pack_root: str

class PhaseStartedData(TypedDict, total=False):
    phase: str
    module: str
    replay_session_id: str
    policy_version: str
    governance_version: str
    config_version: str
    governance_pack_root: str

class PhaseCompletedData(TypedDict, total=False):
    phase: str
    module: str
    replay_session_id: str
    policy_version: str
    governance_version: str
    config_version: str
    governance_pack_root: str

class ArtifactCreatedData(TypedDict, total=False):
    artifact_type: str
    artifact_path: str
    phase: str

# Union of all known event data shapes (for documentation; not runtime-enforced)
RunEventData = Union[
    ExecutionRequestedData,
    ExecutionStartedData,
    RunCompletedData,
    RunFailedData,
    RunCancelledData,
    CostRecordedData,
    PhaseStartedData,
    PhaseCompletedData,
    ArtifactCreatedData,
    dict[str, Any],  # fallback for unknown/generic events
]


# ── Runtime schema validation (v3.0) ─────────────────────────────────────
#
# Each event type maps to a set of expected keys with (type, required) tuples.
# In dev mode (AITEST_ENV=dev), make_event() validates data against these
# schemas and logs warnings for missing/extra keys. Production mode skips
# validation entirely.

EVENT_SCHEMAS: dict[str, dict[str, tuple[type, bool]]] = {
    EventType.EXECUTION_REQUESTED: {
        "module": (str, True),
        "pages": (list, False),
        "agent": (str, False),
    },
    EventType.EXECUTION_STARTED: {
        "workspace_id": (str, False),
        "org_id": (str, False),
        "module": (str, False),
        "agent": (str, False),
        "replay_session_id": (str, False),
    },
    EventType.RUN_COMPLETED: {
        "workspace_id": (str, False),
        "org_id": (str, False),
        "module": (str, False),
        "agent": (str, False),
        "total_tokens": (int, False),
        "total_cost": (float, False),
        "agent_runs": (int, False),
        "duration_ms": (float, False),
        "retry_count": (int, False),
        "max_retries": (int, False),
        "replay_session_id": (str, False),
    },
    EventType.RUN_FAILED: {
        "workspace_id": (str, False),
        "org_id": (str, False),
        "module": (str, False),
        "agent": (str, False),
        "error": (str, False),
        "duration_ms": (float, False),
        "retry_count": (int, False),
        "max_retries": (int, False),
        "replay_session_id": (str, False),
    },
    EventType.RUN_CANCELLED: {
        "workspace_id": (str, False),
        "org_id": (str, False),
    },
    EventType.COST_RECORDED: {
        "total_cost": (float, False),
        "total_tokens": (int, False),
        "org_id": (str, False),
        "workspace_id": (str, False),
        "replay_session_id": (str, False),
    },
    EventType.PHASE_STARTED: {
        "phase": (str, True),
        "module": (str, False),
        "replay_session_id": (str, False),
    },
    EventType.PHASE_COMPLETED: {
        "phase": (str, True),
        "module": (str, False),
        "replay_session_id": (str, False),
    },
    EventType.ARTIFACT_CREATED: {
        "artifact_type": (str, False),
        "artifact_path": (str, False),
        "phase": (str, False),
    },
}

# Cache: is dev mode?
_DEV_MODE: bool | None = None


def _is_dev_mode() -> bool:
    global _DEV_MODE
    if _DEV_MODE is None:
        _DEV_MODE = os.environ.get("AITEST_ENV", "").lower() in ("dev", "development", "test")
    return _DEV_MODE


def _validate_data(event_type: str, data: dict[str, Any]) -> None:
    """Validate event data against EVENT_SCHEMAS. Logs warnings, never raises.

    Only runs in dev mode (AITEST_ENV=dev/development/test).
    """
    if not _is_dev_mode():
        return
    schema = EVENT_SCHEMAS.get(event_type)
    if schema is None:
        return  # Unknown event type — no schema to validate against
    # Check required keys
    for key, (expected_type, required) in schema.items():
        if required and key not in data:
            _log.warning(f"Event schema: missing required key '{key}' for {event_type}")
        elif key in data and not isinstance(data[key], expected_type):
            _log.warning(
                f"Event schema: key '{key}' for {event_type} "
                f"expected {expected_type.__name__}, got {type(data[key]).__name__}"
            )


# ── RunEvent ─────────────────────────────────────────────────────────────

@dataclass
class RunEvent:
    """Immutable event emitted during execution lifecycle.

    Consumers subscribe via EventBus: bus.subscribe(EventType.RUN_COMPLETED, handler)

    The ``data`` field carries event-type-specific payload. Use the TypedDict
    aliases (RunCompletedData, etc.) for static type hints; at runtime it is
    always ``dict[str, Any]``.
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
    """Create a RunEvent with a generated event_id.

    In dev mode (AITEST_ENV=dev), validates data against EVENT_SCHEMAS
    and logs warnings for schema violations. Production mode skips validation.
    """
    import uuid
    _validate_data(event_type, data)
    return RunEvent(
        event_id=str(uuid.uuid4()),
        event_type=event_type,
        run_id=run_id,
        request_id=request_id,
        data=data,
    )
