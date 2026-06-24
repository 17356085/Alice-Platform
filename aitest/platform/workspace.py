"""
Workspace Model — v2.1 Resource Isolation.

Every Runtime resource (runs, artifacts, reports, cache) belongs to a workspace.
Workspaces belong to organizations. The Runtime receives only an ExecutionContext,
never Organization details.

Data model:
  Organization → Workspace → Project (.tlo/) → Run → Artifact → Report

ExecutionContext (passed to Runtime):
  { workspace_id, user_id, scopes, org_id }

Usage:
    from aitest.platform.workspace import WorkspaceManager, ExecutionContext

    # Platform layer resolves identity → ExecutionContext
    ctx = ExecutionContext(workspace_id="ws-1", user_id="alice", scopes=["read","execute"], org_id="my-org")

    # Runtime receives only ctx
    run_agent(module="equipment", context=ctx)
"""

import json
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field


# ── ExecutionContext ───────────────────────────────────────────────────

@dataclass
class ExecutionContext:
    """Minimal context passed from Platform to Runtime.

    Runtime never sees Organization directly. It only receives this context.
    """
    workspace_id: str
    user_id: str = "anonymous"
    scopes: list[str] = field(default_factory=lambda: ["read", "execute"])
    org_id: str = ""

    def has_scope(self, scope: str) -> bool:
        return scope in self.scopes or "admin" in self.scopes

    def require(self, scope: str):
        if not self.has_scope(scope):
            raise PermissionError(
                f"User '{self.user_id}' lacks scope '{scope}' in workspace '{self.workspace_id}'"
            )

    def to_dict(self) -> dict:
        return {
            "workspace_id": self.workspace_id,
            "user_id": self.user_id,
            "scopes": self.scopes,
            "org_id": self.org_id,
        }


# ── Workspace ──────────────────────────────────────────────────────────

@dataclass
class Workspace:
    id: str
    name: str
    org_id: str
    description: str = ""
    members: dict[str, str] = field(default_factory=dict)  # user_id → role
    quotas: dict = field(default_factory=lambda: {
        "max_runs_per_day": 50,
        "max_tokens_per_run": 100_000,
        "max_storage_mb": 500,
    })
    created_at: str = ""
    updated_at: str = ""


class WorkspaceManager:
    """Manages workspaces within organizations. Enforces isolation."""

    def __init__(self, data_dir: Path = None):
        self._root = data_dir or (Path(__file__).resolve().parent.parent.parent / "governance" / ".data" / "workspaces")
        self._root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    # ── CRUD ─────────────────────────────────────────────────────────

    def create(self, org_id: str, ws_id: str, name: str, description: str = "") -> Workspace:
        key = ws_id.lower().replace(" ", "-")
        path = self._path(org_id, key)
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists():
            raise ValueError(f"Workspace '{key}' already exists in org '{org_id}'")

        ws = Workspace(
            id=key, name=name, org_id=org_id, description=description,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._save(ws)
        return ws

    def get(self, org_id: str, ws_id: str) -> Optional[Workspace]:
        path = self._path(org_id, ws_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return Workspace(**data)

    def list(self, org_id: str) -> list[Workspace]:
        org_dir = self._root / org_id
        if not org_dir.exists():
            return []
        workspaces = []
        for path in sorted(org_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                workspaces.append(Workspace(**data))
            except Exception:
                pass
        return workspaces

    def delete(self, org_id: str, ws_id: str):
        path = self._path(org_id, ws_id)
        if path.exists():
            path.unlink()

    # ── Members (workspace-level) ───────────────────────────────────

    def add_member(self, org_id: str, ws_id: str, user_id: str, role: str = "member"):
        ws = self._get_or_raise(org_id, ws_id)
        ws.members[user_id] = role
        ws.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(ws)

    def remove_member(self, org_id: str, ws_id: str, user_id: str):
        ws = self._get_or_raise(org_id, ws_id)
        ws.members.pop(user_id, None)
        ws.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(ws)

    def list_members(self, org_id: str, ws_id: str) -> dict[str, str]:
        ws = self._get_or_raise(org_id, ws_id)
        return dict(ws.members)

    # ── Quotas ──────────────────────────────────────────────────────

    def get_quotas(self, org_id: str, ws_id: str) -> dict:
        ws = self._get_or_raise(org_id, ws_id)
        return dict(ws.quotas)

    def set_quota(self, org_id: str, ws_id: str, key: str, value: int):
        ws = self._get_or_raise(org_id, ws_id)
        ws.quotas[key] = value
        ws.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(ws)

    # ── ExecutionContext factory ────────────────────────────────────

    def make_context(self, org_id: str, ws_id: str, user_id: str) -> ExecutionContext:
        """Platform layer: resolve identity → ExecutionContext for Runtime."""
        ws = self._get_or_raise(org_id, ws_id)

        # Get user's role → scopes from Organization
        try:
            from aitest.platform.organization import get_org_manager, ROLE_DEFAULT_SCOPES
            om = get_org_manager()
            role = om.get_role(org_id, user_id)
            scopes = ROLE_DEFAULT_SCOPES.get(role, ["read"])
        except Exception:
            scopes = ["read", "execute"]  # fallback

        # Override with workspace-level role if exists
        ws_role = ws.members.get(user_id, "")
        if ws_role:
            from aitest.platform.organization import ROLE_DEFAULT_SCOPES
            scopes = ROLE_DEFAULT_SCOPES.get(ws_role, scopes)

        return ExecutionContext(
            workspace_id=ws_id,
            user_id=user_id,
            scopes=scopes,
            org_id=org_id,
        )

    # ── Internal ─────────────────────────────────────────────────────

    def _path(self, org_id: str, ws_id: str) -> Path:
        return self._root / org_id / f"{ws_id}.json"

    def _get_or_raise(self, org_id: str, ws_id: str) -> Workspace:
        ws = self.get(org_id, ws_id)
        if ws is None:
            raise ValueError(f"Workspace '{ws_id}' not found in org '{org_id}'")
        return ws

    def _save(self, ws: Workspace):
        path = self._path(ws.org_id, ws.id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            path.write_text(json.dumps(ws.__dict__, ensure_ascii=False, indent=2, default=str), encoding="utf-8")


# ── Singleton ──────────────────────────────────────────────────────────

_ws_manager: Optional[WorkspaceManager] = None
_wsm_lock = threading.Lock()


def get_ws_manager() -> WorkspaceManager:
    global _ws_manager
    with _wsm_lock:
        if _ws_manager is None:
            _ws_manager = WorkspaceManager()
        return _ws_manager
