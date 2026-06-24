"""
Organization & Identity — v2.0 Platform Foundation.

Manages organizations, users, roles, and API keys.
Runtime (v1.x) is a capability within an organization's workspace.

Data model:
  Organization
    ├── Members (user_id → role)
    ├── API Keys (key_id → scopes)
    └── Workspaces → Projects (existing .tlo/ projects)

Roles: owner | admin | member | viewer
Scopes: read | write | execute | admin

Storage: JSON file (per-org). Future: SQLite.

Usage:
    from aitest.platform.organization import OrganizationManager, get_org_manager

    mgr = get_org_manager()
    org = mgr.create("my-org", owner="user-1")
    member = mgr.add_member("my-org", "user-2", role="member")
    key = mgr.create_api_key("my-org", scopes=["read", "execute"])
"""

from __future__ import annotations

import json
import secrets
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field


# ── Data ───────────────────────────────────────────────────────────────

@dataclass
class Organization:
    id: str
    name: str
    owner: str
    members: dict[str, str] = field(default_factory=dict)  # user_id → role
    api_keys: dict[str, dict] = field(default_factory=dict)  # key_id → {key_hash, scopes, created_by}
    created_at: str = ""
    updated_at: str = ""


ROLES = ["owner", "admin", "member", "viewer"]
SCOPES = ["read", "write", "execute", "admin"]

ROLE_DEFAULT_SCOPES = {
    "owner": ["read", "write", "execute", "admin"],
    "admin": ["read", "write", "execute", "admin"],
    "member": ["read", "write", "execute"],
    "viewer": ["read"],
}


class AuthError(Exception):
    pass


class ForbiddenError(AuthError):
    pass


# ── Manager ────────────────────────────────────────────────────────────

class OrganizationManager:
    """Manages organizations, members, and API keys."""

    def __init__(self, data_dir: Path = None):
        self._data_dir = data_dir or (Path(__file__).resolve().parent.parent.parent / "governance" / ".data" / "orgs")
        self._data_dir.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    # ── Organization CRUD ────────────────────────────────────────────

    def create(self, org_id: str, name: str, owner: str) -> Organization:
        key = org_id.lower().replace(" ", "-")
        path = self._data_dir / f"{key}.json"
        if path.exists():
            raise ValueError(f"Organization '{key}' already exists")

        org = Organization(
            id=key, name=name, owner=owner,
            members={owner: "owner"},
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._save(org)
        return org

    def get(self, org_id: str) -> Optional[Organization]:
        path = self._data_dir / f"{org_id}.json"
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return Organization(**data)

    def list(self) -> list[Organization]:
        orgs = []
        for path in sorted(self._data_dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                orgs.append(Organization(**data))
            except Exception:
                pass
        return orgs

    def delete(self, org_id: str):
        path = self._data_dir / f"{org_id}.json"
        if path.exists():
            path.unlink()

    # ── Members ──────────────────────────────────────────────────────

    def add_member(self, org_id: str, user_id: str, role: str = "member") -> Organization:
        if role not in ROLES:
            raise ValueError(f"Invalid role '{role}'. Must be one of {ROLES}")
        org = self._get_or_raise(org_id)
        org.members[user_id] = role
        org.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(org)
        return org

    def remove_member(self, org_id: str, user_id: str):
        org = self._get_or_raise(org_id)
        if user_id == org.owner:
            raise ValueError("Cannot remove the organization owner")
        org.members.pop(user_id, None)
        org.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(org)

    def get_role(self, org_id: str, user_id: str) -> str:
        org = self._get_or_raise(org_id)
        return org.members.get(user_id, "")

    def get_scopes(self, org_id: str, user_id: str) -> list[str]:
        role = self.get_role(org_id, user_id)
        return ROLE_DEFAULT_SCOPES.get(role, [])

    # ── API Keys ─────────────────────────────────────────────────────

    def create_api_key(self, org_id: str, created_by: str, scopes: list[str] = None) -> tuple[str, str]:
        """Create an API key. Returns (key_id, raw_key). Raw key is NOT stored."""
        org = self._get_or_raise(org_id)
        scopes = scopes or ["read", "execute"]

        raw_key = "aitest_" + secrets.token_urlsafe(32)
        key_hash = self._hash_key(raw_key)
        key_id = secrets.token_hex(8)

        org.api_keys[key_id] = {
            "key_hash": key_hash,
            "scopes": scopes,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "last_used": None,
        }
        org.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(org)
        return key_id, raw_key

    def validate_api_key(self, raw_key: str) -> Optional[dict]:
        """Validate an API key. Returns {org_id, scopes, key_id} or None."""
        key_hash = self._hash_key(raw_key)
        for org in self.list():
            for kid, kd in org.api_keys.items():
                if kd["key_hash"] == key_hash:
                    # Update last_used
                    kd["last_used"] = datetime.now(timezone.utc).isoformat()
                    self._save(org)
                    return {"org_id": org.id, "scopes": kd["scopes"], "key_id": kid}
        return None

    def revoke_api_key(self, org_id: str, key_id: str):
        org = self._get_or_raise(org_id)
        org.api_keys.pop(key_id, None)
        org.updated_at = datetime.now(timezone.utc).isoformat()
        self._save(org)

    def list_api_keys(self, org_id: str) -> list[dict]:
        org = self._get_or_raise(org_id)
        return [
            {"key_id": kid, "scopes": kd["scopes"], "created_by": kd["created_by"],
             "created_at": kd["created_at"], "last_used": kd.get("last_used")}
            for kid, kd in org.api_keys.items()
        ]

    # ── RBAC check ───────────────────────────────────────────────────

    def require_scope(self, org_id: str, user_id: str, required_scope: str):
        """Raise ForbiddenError if user lacks the required scope."""
        scopes = self.get_scopes(org_id, user_id)
        if required_scope not in scopes and "admin" not in scopes:
            raise ForbiddenError(
                f"User '{user_id}' lacks scope '{required_scope}' in org '{org_id}'"
            )

    # ── Internal ─────────────────────────────────────────────────────

    def _get_or_raise(self, org_id: str) -> Organization:
        org = self.get(org_id)
        if org is None:
            raise ValueError(f"Organization '{org_id}' not found")
        return org

    def _save(self, org: Organization):
        path = self._data_dir / f"{org.id}.json"
        # Don't store raw keys
        data = {k: v for k, v in org.__dict__.items()}
        with self._lock:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str), encoding="utf-8")

    @staticmethod
    def _hash_key(key: str) -> str:
        import hashlib
        return hashlib.sha256(key.encode()).hexdigest()


# ── Singleton ──────────────────────────────────────────────────────────

_org_manager: Optional[OrganizationManager] = None
_om_lock = threading.Lock()


def get_org_manager() -> OrganizationManager:
    global _org_manager
    with _om_lock:
        if _org_manager is None:
            _org_manager = OrganizationManager()
        return _org_manager
