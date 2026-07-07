"""Shared execution contracts for platform, SDK, CLI, and chat adapters."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

ExecutionStatus = Literal[
    "pending",
    "running",
    "completed",
    "completed_with_issues",
    "failed",
    "cancelled",
    "timed_out",
]


@dataclass
class ExecutionContext:
    """Unified execution input contract.

    Platform-specific identity data and execution-specific routing data live in one
    transport object so every entrypoint can normalize into the same shape.
    """

    workspace_id: str
    user_id: str = "anonymous"
    scopes: list[str] = field(default_factory=lambda: ["read", "execute"])
    org_id: str = ""
    module: str = ""
    pages: list[str] = field(default_factory=list)
    agent: str = ""
    mode: str = "full"
    provider: str = ""
    priority: int = 0
    entrypoint: str = ""
    request_id: str = ""
    run_id: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes or "admin" in self.scopes

    def require(self, scope: str) -> None:
        if not self.has_scope(scope):
            raise PermissionError(
                f"User '{self.user_id}' lacks scope '{scope}' in workspace '{self.workspace_id}'"
            )

    @property
    def page(self) -> str:
        return self.pages[0] if self.pages else ""

    def with_execution(
        self,
        *,
        module: str | None = None,
        pages: list[str] | None = None,
        agent: str | None = None,
        mode: str | None = None,
        provider: str | None = None,
        priority: int | None = None,
        request_id: str | None = None,
        run_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "ExecutionContext":
        merged_metadata = dict(self.metadata)
        if metadata:
            merged_metadata.update(metadata)
        return ExecutionContext(
            workspace_id=self.workspace_id,
            user_id=self.user_id,
            scopes=list(self.scopes),
            org_id=self.org_id,
            module=self.module if module is None else module,
            pages=list(self.pages if pages is None else pages),
            agent=self.agent if agent is None else agent,
            mode=self.mode if mode is None else mode,
            provider=self.provider if provider is None else provider,
            priority=self.priority if priority is None else priority,
            entrypoint=self.entrypoint,
            request_id=self.request_id if request_id is None else request_id,
            run_id=self.run_id if run_id is None else run_id,
            metadata=merged_metadata,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "scopes": list(self.scopes),
            "org_id": self.org_id,
            "module": self.module,
            "pages": list(self.pages),
            "agent": self.agent,
            "mode": self.mode,
            "provider": self.provider,
            "priority": self.priority,
            "entrypoint": self.entrypoint,
            "request_id": self.request_id,
            "run_id": self.run_id,
            "metadata": dict(self.metadata),
        }


@dataclass
class ExecutionResult:
    """Unified execution output contract."""

    request_id: str
    run_id: str
    status: ExecutionStatus
    module: str = ""
    pages: list[str] = field(default_factory=list)
    agent: str = ""
    mode: str = "full"
    total_tokens: int = 0
    total_cost: float = 0.0
    agent_runs: int = 0
    artifacts: list[str] = field(default_factory=list)
    error_message: str = ""
    duration_ms: float = 0.0
    completed_phases: list[str] = field(default_factory=list)
    failed_phases: list[str] = field(default_factory=list)
    summary: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def success(self) -> bool:
        return self.status == "completed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "run_id": self.run_id,
            "status": self.status,
            "module": self.module,
            "pages": list(self.pages),
            "agent": self.agent,
            "mode": self.mode,
            "total_tokens": self.total_tokens,
            "total_cost": self.total_cost,
            "agent_runs": self.agent_runs,
            "artifacts": list(self.artifacts),
            "error_message": self.error_message,
            "duration_ms": self.duration_ms,
            "completed_phases": list(self.completed_phases),
            "failed_phases": list(self.failed_phases),
            "summary": self.summary,
            "metadata": dict(self.metadata),
            "success": self.success,
        }


class ExecutionControl(Protocol):
    """Formal control interface for live execution instances."""

    def cancel(self) -> None:
        ...
