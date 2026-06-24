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
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

workspace_router = APIRouter(prefix="/api/platform/orgs/{org_id}/workspaces", tags=["Workspace v2.1"])


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


# ── CRUD ───────────────────────────────────────────────────────────────

@workspace_router.post("")
async def create_workspace(org_id: str, req: CreateWorkspaceRequest):
    try:
        ws = _get_ws_manager().create(org_id, req.id, req.name, req.description)
        return {"status": "created", "workspace": ws.__dict__}
    except ValueError as e:
        raise HTTPException(409, str(e))


@workspace_router.get("")
async def list_workspaces(org_id: str):
    workspaces = _get_ws_manager().list(org_id)
    return {"org_id": org_id, "workspaces": [
        {"id": w.id, "name": w.name, "description": w.description,
         "members": len(w.members), "created_at": w.created_at}
        for w in workspaces
    ]}


@workspace_router.get("/{ws_id}")
async def get_workspace(org_id: str, ws_id: str):
    ws = _get_ws_manager().get(org_id, ws_id)
    if not ws:
        raise HTTPException(404, f"Workspace '{ws_id}' not found")
    return {"workspace": ws.__dict__}


@workspace_router.delete("/{ws_id}")
async def delete_workspace(org_id: str, ws_id: str):
    _get_ws_manager().delete(org_id, ws_id)
    return {"status": "deleted"}


# ── Members ────────────────────────────────────────────────────────────

@workspace_router.post("/{ws_id}/members")
async def add_member(org_id: str, ws_id: str, req: AddMemberRequest):
    try:
        _get_ws_manager().add_member(org_id, ws_id, req.user_id, req.role)
        return {"status": "added"}
    except ValueError as e:
        raise HTTPException(400, str(e))


@workspace_router.get("/{ws_id}/members")
async def list_members(org_id: str, ws_id: str):
    try:
        members = _get_ws_manager().list_members(org_id, ws_id)
        return {"members": members}
    except ValueError as e:
        raise HTTPException(404, str(e))


@workspace_router.delete("/{ws_id}/members/{user_id}")
async def remove_member(org_id: str, ws_id: str, user_id: str):
    try:
        _get_ws_manager().remove_member(org_id, ws_id, user_id)
        return {"status": "removed"}
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── Quotas ─────────────────────────────────────────────────────────────

@workspace_router.get("/{ws_id}/quotas")
async def get_quotas(org_id: str, ws_id: str):
    try:
        return {"quotas": _get_ws_manager().get_quotas(org_id, ws_id)}
    except ValueError as e:
        raise HTTPException(404, str(e))


@workspace_router.put("/{ws_id}/quotas")
async def set_quota(org_id: str, ws_id: str, req: SetQuotaRequest):
    try:
        _get_ws_manager().set_quota(org_id, ws_id, req.key, req.value)
        return {"status": "updated"}
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── ExecutionContext (Platform → Runtime bridge) ───────────────────────

@workspace_router.post("/{ws_id}/context")
async def get_context(org_id: str, ws_id: str, request: Request):
    """Resolve identity → ExecutionContext for Runtime consumption."""
    user_id = request.headers.get("X-User-Id", "anonymous")
    try:
        ctx = _get_ws_manager().make_context(org_id, ws_id, user_id)
        return {"context": ctx.to_dict()}
    except ValueError as e:
        raise HTTPException(404, str(e))
