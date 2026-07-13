"""Platform API — v2.0 Identity & Organization management.

Endpoints:
  POST   /api/platform/orgs              — Create organization
  GET    /api/platform/orgs              — List organizations
  GET    /api/platform/orgs/:id          — Get organization
  DELETE /api/platform/orgs/:id          — Delete organization
  POST   /api/platform/orgs/:id/members  — Add member
  DELETE /api/platform/orgs/:id/members/:uid — Remove member
  POST   /api/platform/orgs/:id/keys     — Create API key
  GET    /api/platform/orgs/:id/keys     — List API keys
  DELETE /api/platform/orgs/:id/keys/:kid — Revoke API key
"""
import os

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

platform_router = APIRouter(prefix="/api/platform", tags=["Platform v2.0"])


class CreateOrgRequest(BaseModel):
    id: str
    name: str
    owner: str = "admin"


class AddMemberRequest(BaseModel):
    user_id: str
    role: str = "member"


class CreateKeyRequest(BaseModel):
    scopes: list[str] = ["read", "execute"]


def _get_org_manager():
    from aitest.platform.organization import get_org_manager
    return get_org_manager()


def _get_current_user(request: Request) -> str:
    """Extract user identity from auth middleware (request.state.user_id).

    Falls back to "admin" only when auth is explicitly disabled
    (no AITEST_API_KEY configured).
    """
    user = getattr(request.state, "user_id", None)
    if user:
        return user
    # Auth disabled — dev mode fallback
    from aitest.config import config
    if not config.get_env("AITEST_API_KEY", ""):
        return "admin"
    raise HTTPException(401, "Authentication required")


def _require_org_scope(request: Request, org_id: str, required_scope: str) -> None:
    """Enforce org RBAC for every organization control-plane endpoint."""
    strict = os.environ.get("AITEST_RBAC_REQUIRED", "0").lower() in {"1", "true", "yes"}
    user_id = getattr(request.state, "user_id", None)
    request_org = getattr(request.state, "org_id", None)
    scopes = list(getattr(request.state, "scopes", []) or [])
    if not strict and not user_id and not request.headers.get("X-Org-Id"):
        return
    if request_org and request_org not in {org_id, "*"}:
        raise HTTPException(403, f"Request org '{request_org}' cannot access org '{org_id}'")
    if request_org == "*":
        scopes = ["read", "write", "execute", "admin"]
    if required_scope not in scopes and "admin" not in scopes:
        raise HTTPException(403, f"User '{user_id or 'anonymous'}' lacks scope '{required_scope}' in org '{org_id}'")


def _require_global_admin(request: Request) -> None:
    strict = os.environ.get("AITEST_RBAC_REQUIRED", "0").lower() in {"1", "true", "yes"}
    if not strict and not getattr(request.state, "user_id", None):
        return
    scopes = list(getattr(request.state, "scopes", []) or [])
    if "admin" not in scopes:
        raise HTTPException(403, "Global admin scope is required")


@platform_router.get("/ecosystem")
async def ecosystem_snapshot():
    from aitest.platform.ecosystem import collect_ecosystem_snapshot

    return collect_ecosystem_snapshot()


# ── Organization CRUD ──────────────────────────────────────────────────

@platform_router.post("/orgs")
async def create_org(req: CreateOrgRequest, request: Request):
    _require_global_admin(request)
    try:
        org = _get_org_manager().create(req.id, req.name, req.owner)
        return {"status": "created", "org": org.__dict__}
    except ValueError as e:
        raise HTTPException(409, str(e))


@platform_router.get("/orgs")
async def list_orgs(request: Request):
    _require_global_admin(request)
    orgs = _get_org_manager().list()
    return {"orgs": [{"id": o.id, "name": o.name, "owner": o.owner,
                       "members": len(o.members), "keys": len(o.api_keys),
                       "created_at": o.created_at} for o in orgs]}


@platform_router.get("/orgs/{org_id}")
async def get_org(org_id: str, request: Request):
    _require_org_scope(request, org_id, "read")
    org = _get_org_manager().get(org_id)
    if not org:
        raise HTTPException(404, f"Organization '{org_id}' not found")
    return {"org": org.__dict__}


@platform_router.delete("/orgs/{org_id}")
async def delete_org(org_id: str, request: Request):
    _require_org_scope(request, org_id, "admin")
    _get_org_manager().delete(org_id)
    return {"status": "deleted"}


# ── Members ────────────────────────────────────────────────────────────

@platform_router.post("/orgs/{org_id}/members")
async def add_member(org_id: str, req: AddMemberRequest, request: Request):
    _require_org_scope(request, org_id, "admin")
    try:
        _get_org_manager().add_member(org_id, req.user_id, req.role)
        org = _get_org_manager().get(org_id)
        return {"status": "added", "members": org.members}
    except ValueError as e:
        raise HTTPException(400, str(e))


@platform_router.delete("/orgs/{org_id}/members/{user_id}")
async def remove_member(org_id: str, user_id: str, request: Request):
    _require_org_scope(request, org_id, "admin")
    try:
        _get_org_manager().remove_member(org_id, user_id)
        return {"status": "removed"}
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── API Keys ───────────────────────────────────────────────────────────

@platform_router.post("/orgs/{org_id}/keys")
async def create_key(org_id: str, req: CreateKeyRequest, request: Request):
    _require_org_scope(request, org_id, "admin")
    try:
        user = _get_current_user(request)
        key_id, raw_key = _get_org_manager().create_api_key(org_id, user, req.scopes)
        return {"status": "created", "key_id": key_id, "api_key": raw_key,
                "warning": "Store this key securely. It will not be shown again."}
    except ValueError as e:
        raise HTTPException(400, str(e))


@platform_router.get("/orgs/{org_id}/keys")
async def list_keys(org_id: str, request: Request):
    _require_org_scope(request, org_id, "read")
    try:
        keys = _get_org_manager().list_api_keys(org_id)
        return {"keys": keys}
    except ValueError as e:
        raise HTTPException(404, str(e))


@platform_router.delete("/orgs/{org_id}/keys/{key_id}")
async def revoke_key(org_id: str, key_id: str, request: Request):
    _require_org_scope(request, org_id, "admin")
    try:
        _get_org_manager().revoke_api_key(org_id, key_id)
        return {"status": "revoked"}
    except ValueError as e:
        raise HTTPException(400, str(e))
