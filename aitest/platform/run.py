"""
Run — immutable Platform execution record. v2.2

Run is a Platform first-class resource. Created by ExecutionService on dispatch.
Immutable after completion. References capability+agent, never runtime.

Usage:
    from aitest.platform.run import Run

    run = Run(
        run_id="run-abc123",
        request_id="req-xyz789",
        workspace_id="ws-1",
        org_id="my-org",
        triggered_by="user-alice",
        capability="browser",
        agent="automation-agent",
        module="equipment",
        pages=["device-list", "device-form"],
    )
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional


# ── Terminal states (Run is frozen after these) ──────────────────────────
TERMINAL_STATES = {"completed", "failed", "cancelled", "timed_out"}


# ── Run ──────────────────────────────────────────────────────────────────

@dataclass
class Run:
    """Immutable execution record — what actually happened.

    Design principles:
      - Created on dispatch by ExecutionService.
      - Frozen after status reaches terminal state. Corrections append RunEvents.
      - References capability ("browser"), NOT runtime ("BrowserRuntime").
      - Denormalized summary populated once on completion, never updated.

    Future runtimes (CLI, MCP, Python, Remote CDP) add capabilities without
    changing this model. Billing charges by capability type.
    """

    # ── Identity ─────────────────────────────────────────────────────────
    run_id: str                         # Platform-wide unique ID (UUID7)
    request_id: str                     # Back-link to ExecutionRequest
    workspace_id: str                   # Scoped to workspace
    org_id: str                         # Denormalized for billing queries

    # ── Who / What ──────────────────────────────────────────────────────
    triggered_by: str                   # user_id or api_key_id
    capability: str = "browser"         # Platform capability: browser|cli|mcp|api
    agent: str = ""                     # Agent name: automation-agent|execution-agent|...
    module: str = ""                    # Target module
    pages: list[str] = field(default_factory=list)
    mode: str = "full"                  # full|status|from_automation

    # ── Lifecycle ───────────────────────────────────────────────────────
    status: str = "running"             # running|completed|failed|cancelled|timed_out
    created_at: str = ""
    completed_at: str = ""

    # ── Denormalized summary (populated once on completion) ─────────────
    total_tokens: int = 0
    total_cost: float = 0.0
    agent_runs: int = 0
    artifacts: list[str] = field(default_factory=list)
    error_message: str = ""

    # ── Methods ──────────────────────────────────────────────────────────

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    @property
    def is_terminal(self) -> bool:
        return self.status in TERMINAL_STATES

    @property
    def is_frozen(self) -> bool:
        """Once terminal, Run is immutable. Corrections → RunEvents."""
        return self.is_terminal

    def complete(
        self,
        *,
        total_tokens: int = 0,
        total_cost: float = 0.0,
        agent_runs: int = 0,
        artifacts: list[str] | None = None,
    ):
        """Mark Run as completed and populate summary. Idempotent if frozen."""
        if self.is_frozen:
            return
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.total_tokens = total_tokens
        self.total_cost = total_cost
        self.agent_runs = agent_runs
        if artifacts:
            self.artifacts = artifacts

    def fail(self, error_message: str = ""):
        """Mark Run as failed. Idempotent if frozen."""
        if self.is_frozen:
            return
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc).isoformat()
        self.error_message = error_message

    def cancel(self):
        """Mark Run as cancelled. Idempotent if frozen."""
        if self.is_frozen:
            return
        self.status = "cancelled"
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def timed_out(self):
        """Mark Run as timed out. Idempotent if frozen."""
        if self.is_frozen:
            return
        self.status = "timed_out"
        self.completed_at = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "request_id": self.request_id,
            "workspace_id": self.workspace_id,
            "org_id": self.org_id,
            "triggered_by": self.triggered_by,
            "capability": self.capability,
            "agent": self.agent,
            "module": self.module,
            "pages": self.pages,
            "mode": self.mode,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "agent_runs": self.agent_runs,
            "artifacts": self.artifacts,
            "error_message": self.error_message,
        }
