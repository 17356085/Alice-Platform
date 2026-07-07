"""Scheduler core data model.

Phase 5.1 freezes the platform scheduling vocabulary so later PRs can build
async dispatch, checkpoint resume, worker separation, and retry on top of one
shared contract.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


class JobStatus:
    """Scheduler job lifecycle states."""

    CREATED = "created"
    QUEUED = "queued"
    DISPATCHED = "dispatched"
    RUNNING = "running"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


ACTIVE_JOB_STATUSES = {
    JobStatus.CREATED,
    JobStatus.QUEUED,
    JobStatus.DISPATCHED,
    JobStatus.RUNNING,
    JobStatus.RETRYING,
}

TERMINAL_JOB_STATUSES = {
    JobStatus.COMPLETED,
    JobStatus.FAILED,
    JobStatus.CANCELLED,
    JobStatus.EXPIRED,
}


@dataclass
class RetryPolicy:
    """Retry semantics for a schedulable job."""

    max_attempts: int = 3
    base_delay_s: float = 1.0
    max_delay_s: float = 60.0
    backoff_factor: float = 2.0
    jitter_ratio: float = 0.3
    retryable_statuses: tuple[str, ...] = ("failed", "expired")

    def delay_for_attempt(self, attempt: int) -> float:
        """Return the backoff delay for a zero-based retry attempt."""
        raw_delay = self.base_delay_s * (self.backoff_factor ** max(attempt, 0))
        capped = min(raw_delay, self.max_delay_s)
        return round(capped, 3)

    def can_retry(self, attempt_count: int, status: str) -> bool:
        """Check whether another retry is allowed."""
        if attempt_count >= self.max_attempts:
            return False
        return status in self.retryable_statuses


@dataclass
class QueueLease:
    """Worker lease for a running job."""

    lease_id: str
    worker_id: str
    acquired_at: str
    expires_at: float
    heartbeat_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def acquire(
        cls,
        lease_id: str,
        worker_id: str,
        *,
        ttl_seconds: int = 1800,
        metadata: dict[str, Any] | None = None,
    ) -> "QueueLease":
        now = datetime.now(timezone.utc)
        return cls(
            lease_id=lease_id,
            worker_id=worker_id,
            acquired_at=now.isoformat(),
            expires_at=(now.timestamp() + ttl_seconds),
            heartbeat_at=now.isoformat(),
            metadata=metadata or {},
        )

    def is_expired(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        return current.timestamp() >= float(self.expires_at)

    def heartbeat(self, now: datetime | None = None) -> None:
        current = now or datetime.now(timezone.utc)
        self.heartbeat_at = current.isoformat()


@dataclass
class SchedulerJob:
    """Canonical scheduler job entity."""

    job_id: str
    request_id: str
    workspace_id: str
    org_id: str
    module: str = ""
    pages: list[str] = field(default_factory=list)
    agent: str = "automation-agent"
    provider: str = ""
    mode: str = "full"
    priority: int = 0
    status: str = JobStatus.CREATED
    attempt_count: int = 0
    created_at: str = ""
    queued_at: str | None = None
    dispatched_at: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    next_retry_at: str | None = None
    lease: QueueLease | None = None
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    error_message: str = ""
    result: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_active(self) -> bool:
        return self.status in ACTIVE_JOB_STATUSES

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_JOB_STATUSES

    def queue(self) -> None:
        if self.is_terminal:
            raise ValueError(f"Cannot queue terminal job '{self.status}'")
        self.status = JobStatus.QUEUED
        self.queued_at = datetime.now(timezone.utc).isoformat()

    def dispatch(self, lease: QueueLease | None = None) -> None:
        if self.is_terminal:
            raise ValueError(f"Cannot dispatch terminal job '{self.status}'")
        self.status = JobStatus.DISPATCHED
        self.dispatched_at = datetime.now(timezone.utc).isoformat()
        self.attempt_count += 1
        self.lease = lease

    def start(self, lease: QueueLease | None = None) -> None:
        self.status = JobStatus.RUNNING
        self.started_at = datetime.now(timezone.utc).isoformat()
        if lease is not None:
            self.lease = lease

    def complete(self, result: dict[str, Any] | None = None) -> None:
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.result = result or {}
        self.error_message = ""
        self.lease = None

    def fail(self, error_message: str, *, retryable: bool = True) -> None:
        self.error_message = error_message
        if retryable and self.retry_policy.can_retry(self.attempt_count, "failed"):
            self.status = JobStatus.RETRYING
            self.next_retry_at = datetime.now(timezone.utc).isoformat()
            return
        self.status = JobStatus.FAILED
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.lease = None

    def cancel(self) -> None:
        if self.is_terminal:
            return
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.lease = None

    def expire(self) -> None:
        if self.is_terminal:
            return
        self.status = JobStatus.EXPIRED
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.lease = None

    def schedule_retry(self) -> None:
        if not self.retry_policy.can_retry(self.attempt_count, "failed"):
            raise ValueError("Retry budget exhausted")
        self.status = JobStatus.QUEUED
        self.next_retry_at = datetime.now(timezone.utc).isoformat()
        self.error_message = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "request_id": self.request_id,
            "workspace_id": self.workspace_id,
            "org_id": self.org_id,
            "module": self.module,
            "pages": list(self.pages),
            "agent": self.agent,
            "provider": self.provider,
            "mode": self.mode,
            "priority": self.priority,
            "status": self.status,
            "attempt_count": self.attempt_count,
            "created_at": self.created_at,
            "queued_at": self.queued_at,
            "dispatched_at": self.dispatched_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "next_retry_at": self.next_retry_at,
            "lease": self.lease.__dict__ if self.lease else None,
            "retry_policy": self.retry_policy.__dict__,
            "error_message": self.error_message,
            "result": dict(self.result),
            "metadata": dict(self.metadata),
        }
