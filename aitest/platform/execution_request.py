"""
ExecutionRequest — user's intent to execute. v2.2

A live entity with a lifecycle. Created by API, managed by ExecutionService.
Transitions to Run on dispatch.

Lifecycle:
  created → queued → running → completed
                            → failed
                            → cancelled

Simple is deliberate. Alice is not Temporal. Expand states only when a real
consumer needs them.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ── Status constants ─────────────────────────────────────────────────────

class RequestStatus:
    CREATED = "created"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


ACTIVE_STATUSES = {RequestStatus.CREATED, RequestStatus.QUEUED, RequestStatus.RUNNING}
TERMINAL_STATUSES = {RequestStatus.COMPLETED, RequestStatus.FAILED, RequestStatus.CANCELLED}


# ── ExecutionRequest ─────────────────────────────────────────────────────

@dataclass
class ExecutionRequest:
    """User's intent to execute. Has a lifecycle. Managed by ExecutionService."""

    # ── Identity ─────────────────────────────────────────────────────────
    request_id: str                    # Platform-wide unique ID (UUID)
    workspace_id: str
    org_id: str

    # ── Who / How ───────────────────────────────────────────────────────
    triggered_by: str = ""             # user_id or api_key_id
    trigger_type: str = "manual"       # manual|webhook|schedule|api

    # ── What ────────────────────────────────────────────────────────────
    module: str = ""
    pages: list[str] = field(default_factory=list)
    mode: str = "full"                 # full|status|from_automation
    provider: str = "claude"           # LLM provider

    # ── Lifecycle ───────────────────────────────────────────────────────
    priority: int = 0                  # 0=normal, 1=high, 2=critical
    status: str = RequestStatus.CREATED
    run_ids: list[str] = field(default_factory=list)  # One request → many runs (retry, resume)
    created_at: str = ""
    started_at: str | None = None
    completed_at: str | None = None
    retry_count: int = 0
    max_retries: int = 0

    # ── Methods ─────────────────────────────────────────────────────────

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE_STATUSES

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATUSES

    @property
    def latest_run_id(self) -> str | None:
        """Most recent Run ID. Convenience for single-run (current) case."""
        return self.run_ids[-1] if self.run_ids else None

    def queue(self):
        if self.status != RequestStatus.CREATED:
            raise ValueError(f"Cannot queue request in status '{self.status}'")
        self.status = RequestStatus.QUEUED

    def dispatch(self, run_id: str):
        """Create a new Run attempt. One request can have many runs (retry/resume)."""
        if self.status not in (RequestStatus.CREATED, RequestStatus.QUEUED, RequestStatus.RUNNING):
            raise ValueError(f"Cannot dispatch request in status '{self.status}'")
        self.status = RequestStatus.RUNNING
        self.run_ids.append(run_id)
        self.started_at = self.started_at or datetime.now(timezone.utc).isoformat()

    def complete(self):
        self.status = RequestStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def fail(self):
        self.status = RequestStatus.FAILED
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def cancel(self):
        if self.is_terminal:
            return
        self.status = RequestStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "workspace_id": self.workspace_id,
            "org_id": self.org_id,
            "triggered_by": self.triggered_by,
            "trigger_type": self.trigger_type,
            "module": self.module,
            "pages": self.pages,
            "mode": self.mode,
            "provider": self.provider,
            "priority": self.priority,
            "status": self.status,
            "run_ids": self.run_ids,
            "latest_run_id": self.latest_run_id,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
        }
