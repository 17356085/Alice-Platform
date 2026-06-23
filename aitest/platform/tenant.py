"""
Tenant Manager — multi-project isolation and resource governance.

Each project is a tenant with isolated:
  - ChromaDB namespace (chroma_namespace in project.yaml)
  - Session storage (scoped by project_id)
  - Artifacts and knowledge (.tlo/ per project)
  - KPI/timeseries data
  - Resource limits (max concurrent agents, token budget)

Usage:
    from aitest.platform.tenant import TenantManager, get_tenant

    tm = TenantManager()
    tenant = tm.get("web-automation")
    tenant.check_capacity("agent_execution")  # raises if over limit
    with tenant.scope():
        # All operations in this block are scoped to tenant
        run_sop(module="equipment")

    # Check resource usage
    usage = tenant.usage_summary()
"""

import threading
import time
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class TenantLimits:
    """Per-tenant resource limits."""
    max_concurrent_agents: int = 3
    max_token_budget_per_run: int = 100_000
    max_sessions: int = 100
    max_chromadb_docs: int = 10_000


@dataclass
class TenantUsage:
    """Current resource usage snapshot."""
    active_agents: int = 0
    active_runs: int = 0
    sessions_count: int = 0
    chromadb_docs: int = 0
    token_usage_today: int = 0


class TenantCapacityError(Exception):
    """Raised when a tenant exceeds resource limits."""
    def __init__(self, tenant_id: str, resource: str, limit: int, current: int):
        super().__init__(
            f"Tenant '{tenant_id}' exceeded {resource} limit: "
            f"{current}/{limit}"
        )
        self.tenant_id = tenant_id
        self.resource = resource
        self.limit = limit
        self.current = current


class Tenant:
    """A single tenant (project) with isolation and resource governance."""

    def __init__(self, tenant_id: str, limits: TenantLimits = None):
        self.tenant_id = tenant_id
        self.limits = limits or TenantLimits()
        self._usage = TenantUsage()
        self._lock = threading.Lock()
        self._scope_count = 0

    # ── Capacity checks ────────────────────────────────────────────

    def check_capacity(self, resource: str):
        """Check if tenant has capacity. Raises TenantCapacityError if not."""
        with self._lock:
            if resource == "agent_execution":
                if self._usage.active_agents >= self.limits.max_concurrent_agents:
                    raise TenantCapacityError(
                        self.tenant_id, "concurrent_agents",
                        self.limits.max_concurrent_agents, self._usage.active_agents,
                    )
                self._usage.active_agents += 1

            elif resource == "token_budget":
                if self._usage.token_usage_today >= self.limits.max_token_budget_per_run:
                    raise TenantCapacityError(
                        self.tenant_id, "token_budget",
                        self.limits.max_token_budget_per_run, self._usage.token_usage_today,
                    )

    def release(self, resource: str):
        """Release a resource (called after operation completes)."""
        with self._lock:
            if resource == "agent_execution" and self._usage.active_agents > 0:
                self._usage.active_agents -= 1

    def record_tokens(self, count: int):
        """Record token usage for this tenant."""
        with self._lock:
            self._usage.token_usage_today += count

    # ── Scope context manager ───────────────────────────────────────

    def scope(self):
        """Context manager: sets this tenant as active for the duration.

        Usage:
            with tenant.scope():
                # Active project is now set to this tenant
                run_sop(...)
        """
        return _TenantScope(self)

    # ── Query ───────────────────────────────────────────────────────

    def usage_summary(self) -> dict:
        with self._lock:
            return {
                "tenant_id": self.tenant_id,
                "active_agents": self._usage.active_agents,
                "active_runs": self._usage.active_runs,
                "sessions_count": self._usage.sessions_count,
                "chromadb_docs": self._usage.chromadb_docs,
                "token_usage_today": self._usage.token_usage_today,
                "limits": {
                    "max_concurrent_agents": self.limits.max_concurrent_agents,
                    "max_token_budget_per_run": self.limits.max_token_budget_per_run,
                    "max_sessions": self.limits.max_sessions,
                },
            }


class _TenantScope:
    """Context manager: temporarily set active project to this tenant."""

    def __init__(self, tenant: Tenant):
        self._tenant = tenant
        self._previous = None

    def __enter__(self):
        from aitest.platform.context import get_active_project_id, set_active_project
        self._previous = get_active_project_id()
        set_active_project(self._tenant.tenant_id)
        return self._tenant

    def __exit__(self, *args):
        from aitest.platform.context import set_active_project
        if self._previous:
            set_active_project(self._previous)


# ── Tenant Manager ────────────────────────────────────────────────────

class TenantManager:
    """Manages all tenants (projects) in the platform."""

    def __init__(self):
        self._tenants: dict[str, Tenant] = {}
        self._lock = threading.Lock()

    def get(self, tenant_id: str) -> Tenant:
        """Get or create a tenant. Tenant ID = project ID."""
        with self._lock:
            if tenant_id not in self._tenants:
                self._tenants[tenant_id] = Tenant(tenant_id)
            return self._tenants[tenant_id]

    def list_tenants(self) -> list[str]:
        """List all known tenant IDs."""
        try:
            from aitest.platform.context import list_projects
            return list_projects()
        except Exception:
            return list(self._tenants.keys())

    def all_usage(self) -> dict[str, dict]:
        """Get usage summary for all tenants."""
        return {
            tid: t.usage_summary()
            for tid, t in self._tenants.items()
        }

    def get_or_default(self, tenant_id: str) -> Tenant:
        """Get tenant, creating with default limits if not found."""
        return self.get(tenant_id)


# ── Singleton ─────────────────────────────────────────────────────────

_tenant_manager: Optional[TenantManager] = None
_tm_lock = threading.Lock()


def get_tenant_manager() -> TenantManager:
    global _tenant_manager
    with _tm_lock:
        if _tenant_manager is None:
            _tenant_manager = TenantManager()
        return _tenant_manager


def get_tenant(tenant_id: str = None) -> Tenant:
    """Get current tenant. If no tenant_id given, uses active project."""
    if tenant_id is None:
        from aitest.platform.context import get_active_project_id
        tenant_id = get_active_project_id()
    return get_tenant_manager().get(tenant_id)
