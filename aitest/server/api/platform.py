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
    """Extract user identity. In production, from JWT/OAuth. For now, from header or default."""
    return request.headers.get("X-User-Id", "admin")


# ── Organization CRUD ──────────────────────────────────────────────────

@platform_router.post("/orgs")
async def create_org(req: CreateOrgRequest):
    try:
        org = _get_org_manager().create(req.id, req.name, req.owner)
        return {"status": "created", "org": org.__dict__}
    except ValueError as e:
        raise HTTPException(409, str(e))


@platform_router.get("/orgs")
async def list_orgs():
    orgs = _get_org_manager().list()
    return {"orgs": [{"id": o.id, "name": o.name, "owner": o.owner,
                       "members": len(o.members), "keys": len(o.api_keys),
                       "created_at": o.created_at} for o in orgs]}


@platform_router.get("/orgs/{org_id}")
async def get_org(org_id: str):
    org = _get_org_manager().get(org_id)
    if not org:
        raise HTTPException(404, f"Organization '{org_id}' not found")
    return {"org": org.__dict__}


@platform_router.delete("/orgs/{org_id}")
async def delete_org(org_id: str):
    _get_org_manager().delete(org_id)
    return {"status": "deleted"}


# ── Members ────────────────────────────────────────────────────────────

@platform_router.post("/orgs/{org_id}/members")
async def add_member(org_id: str, req: AddMemberRequest):
    try:
        org = _get_org_manager().add_member(org_id, req.user_id, req.role)
        return {"status": "added", "members": org.members}
    except ValueError as e:
        raise HTTPException(400, str(e))


@platform_router.delete("/orgs/{org_id}/members/{user_id}")
async def remove_member(org_id: str, user_id: str):
    try:
        _get_org_manager().remove_member(org_id, user_id)
        return {"status": "removed"}
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── API Keys ───────────────────────────────────────────────────────────

@platform_router.post("/orgs/{org_id}/keys")
async def create_key(org_id: str, req: CreateKeyRequest, request: Request):
    try:
        user = _get_current_user(request)
        key_id, raw_key = _get_org_manager().create_api_key(org_id, user, req.scopes)
        return {"status": "created", "key_id": key_id, "api_key": raw_key,
                "warning": "Store this key securely. It will not be shown again."}
    except ValueError as e:
        raise HTTPException(400, str(e))


@platform_router.get("/orgs/{org_id}/keys")
async def list_keys(org_id: str):
    try:
        keys = _get_org_manager().list_api_keys(org_id)
        return {"keys": keys}
    except ValueError as e:
        raise HTTPException(404, str(e))


@platform_router.delete("/orgs/{org_id}/keys/{key_id}")
async def revoke_key(org_id: str, key_id: str):
    try:
        _get_org_manager().revoke_api_key(org_id, key_id)
        return {"status": "revoked"}
    except ValueError as e:
        raise HTTPException(400, str(e))
