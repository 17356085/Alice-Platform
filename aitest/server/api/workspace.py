"""Workspace API — v2.1 Resource Isolation.

Endpoints:
  POST   /api/platform/orgs/:orgId/workspaces          — Create workspace
  GET    /api/platform/orgs/:orgId/workspaces          — List workspaces
  GET    /api/platform/orgs/:orgId/workspaces/:wsId     — Get workspace
  DELETE /api/platform/orgs/:orgId/workspaces/:wsId     — Delete workspace
  POST   /api/platform/orgs/:orgId/workspaces/:wsId/members — Add member
  GET    /api/platform/orgs/:orgId/workspaces/:wsId/members — List members
  DELETE /api/platform/orgs/:orgId/workspaces/:wsId/members/:uid — Remove member
  GET    /api/platform/orgs/:orgId/workspaces/:wsId/quotas    — Get quotas
  PUT    /api/platform/orgs/:orgId/workspaces/:wsId/quotas    — Set quota
  POST   /api/platform/orgs/:orgId/workspaces/:wsId/context   — Get ExecutionContext
"""
import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

workspace_router = APIRouter(prefix="/api/v1/workspaces", tags=["Workspace v2.1"])


class CreateWorkspaceRequest(BaseModel):
    id: str
    name: str
    description: str = ""


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "member"


class SetQuotaRequest(BaseModel):
    key: str
    value: int


def _get_ws_manager():
    from aitest.platform.workspace import get_ws_manager
    return get_ws_manager()


def _require_workspace_access(request: Request, *, org_id: str, ws_id: str, required_scope: str = "read"):
    from aitest.platform.ownership import resolve_request_identity, require_workspace_access

    user_id, request_org_id, scopes = resolve_request_identity(request)
    if not _rbac_required(request) and not request_org_id and not scopes:
        return
    if request_org_id and request_org_id != org_id:
        raise HTTPException(403, f"Request org '{request_org_id}' cannot access org '{org_id}'")
    try:
        require_workspace_access(
            org_id=org_id,
            workspace_id=ws_id,
            user_id=user_id,
            required_scope=required_scope,
            request_scopes=scopes,
        )
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))


def _rbac_required(request: Request) -> bool:
    """Enable strict RBAC explicitly for production while preserving local mode."""
    if os.environ.get("AITEST_RBAC_REQUIRED", "0").lower() in {"1", "true", "yes"}:
        return True
    return bool(getattr(request.state, "org_id", None) or getattr(request.state, "scopes", None))


def _require_org_scope(request: Request, org_id: str, required_scope: str) -> None:
    if not _rbac_required(request) and not request.headers.get("X-Org-Id"):
        return
    from aitest.platform.ownership import resolve_request_identity
    from aitest.platform.organization import ROLE_DEFAULT_SCOPES, get_org_manager

    user_id, request_org_id, request_scopes = resolve_request_identity(request)
    if request_org_id and request_org_id not in {org_id, "*"}:
        raise HTTPException(403, f"Request org '{request_org_id}' cannot access org '{org_id}'")
    scopes = list(request_scopes)
    if request_org_id != "*":
        try:
            role = get_org_manager().get_role(org_id, user_id)
            scopes = ROLE_DEFAULT_SCOPES.get(role, scopes)
        except Exception:
            pass
    if required_scope not in scopes and "admin" not in scopes:
        raise HTTPException(403, f"User '{user_id}' lacks scope '{required_scope}' in org '{org_id}'")


# ── CRUD ───────────────────────────────────────────────────────────────

@workspace_router.post("")
async def create_workspace(org_id: str, req: CreateWorkspaceRequest, request: Request):
    _require_org_scope(request, org_id, "admin")
    try:
        ws = _get_ws_manager().create(org_id, req.id, req.name, req.description)
        return {"status": "created", "workspace": ws.__dict__}
    except ValueError as e:
        raise HTTPException(409, str(e))


@workspace_router.get("")
async def list_workspaces(org_id: str, request: Request):
    _require_org_scope(request, org_id, "read")
    workspaces = _get_ws_manager().list(org_id)
    return {"org_id": org_id, "workspaces": [
        {"id": w.id, "name": w.name, "description": w.description,
         "members": len(w.members), "created_at": w.created_at}
        for w in workspaces
    ]}


@workspace_router.get("/{ws_id}")
async def get_workspace(org_id: str, ws_id: str, request: Request):
    _require_workspace_access(request, org_id=org_id, ws_id=ws_id, required_scope="read")
    ws = _get_ws_manager().get(org_id, ws_id)
    if not ws:
        raise HTTPException(404, f"Workspace '{ws_id}' not found")
    return {"workspace": ws.__dict__}


@workspace_router.delete("/{ws_id}")
async def delete_workspace(org_id: str, ws_id: str, request: Request):
    _require_workspace_access(request, org_id=org_id, ws_id=ws_id, required_scope="admin")
    _get_ws_manager().delete(org_id, ws_id)
    return {"status": "deleted"}


# ── Members ────────────────────────────────────────────────────────────

@workspace_router.post("/{ws_id}/members")
async def add_member(org_id: str, ws_id: str, req: AddMemberRequest, request: Request):
    _require_workspace_access(request, org_id=org_id, ws_id=ws_id, required_scope="admin")
    try:
        _get_ws_manager().add_member(org_id, ws_id, req.user_id, req.role)
        return {"status": "added"}
    except ValueError as e:
        raise HTTPException(400, str(e))


@workspace_router.get("/{ws_id}/members")
async def list_members(org_id: str, ws_id: str, request: Request):
    _require_workspace_access(request, org_id=org_id, ws_id=ws_id, required_scope="read")
    try:
        members = _get_ws_manager().list_members(org_id, ws_id)
        return {"members": members}
    except ValueError as e:
        raise HTTPException(404, str(e))


@workspace_router.delete("/{ws_id}/members/{user_id}")
async def remove_member(org_id: str, ws_id: str, user_id: str, request: Request):
    _require_workspace_access(request, org_id=org_id, ws_id=ws_id, required_scope="admin")
    try:
        _get_ws_manager().remove_member(org_id, ws_id, user_id)
        return {"status": "removed"}
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── Quotas ─────────────────────────────────────────────────────────────

@workspace_router.get("/{ws_id}/quotas")
async def get_quotas(org_id: str, ws_id: str, request: Request):
    _require_workspace_access(request, org_id=org_id, ws_id=ws_id, required_scope="read")
    try:
        return {"quotas": _get_ws_manager().get_quotas(org_id, ws_id)}
    except ValueError as e:
        raise HTTPException(404, str(e))


@workspace_router.put("/{ws_id}/quotas")
async def set_quota(org_id: str, ws_id: str, req: SetQuotaRequest, request: Request):
    _require_workspace_access(request, org_id=org_id, ws_id=ws_id, required_scope="admin")
    try:
        _get_ws_manager().set_quota(org_id, ws_id, req.key, req.value)
        return {"status": "updated"}
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── ExecutionContext (Platform → Runtime bridge) ───────────────────────

@workspace_router.post("/{ws_id}/context")
async def get_context(org_id: str, ws_id: str, request: Request):
    """Resolve identity → ExecutionContext for Runtime consumption."""
    user_id = getattr(request.state, "user_id", None)
    if not user_id:
        from aitest.config import config
        if not config.get_env("AITEST_API_KEY", ""):
            user_id = "anonymous"
        else:
            raise HTTPException(401, "Authentication required")
    _require_workspace_access(request, org_id=org_id, ws_id=ws_id, required_scope="read")
    ctx = _get_ws_manager().make_context(org_id, ws_id, user_id)
    return {"context": ctx.to_dict()}
