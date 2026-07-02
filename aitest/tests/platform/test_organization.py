"""Tests for platform/organization.py — Organization, roles, API keys.

Tests: Organization dataclass, ROLES, SCOPES, ROLE_DEFAULT_SCOPES,
OrganizationManager CRUD (create, get, add_member, remove_member,
create_api_key, validate_api_key).
Uses temp directory — no real governance/ dependency.
"""
import pytest
from pathlib import Path

from aitest.platform.organization import (
    Organization, OrganizationManager,
    ROLES, SCOPES, ROLE_DEFAULT_SCOPES,
    AuthError, ForbiddenError,
)


# ══════════════════════════════════════════════════════════════════════════
#  Fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def mgr(temp_dir):
    return OrganizationManager(data_dir=temp_dir / "orgs")


# ══════════════════════════════════════════════════════════════════════════
#  Constants
# ══════════════════════════════════════════════════════════════════════════


class TestConstants:
    def test_roles(self):
        assert "owner" in ROLES
        assert "admin" in ROLES
        assert "member" in ROLES
        assert "viewer" in ROLES

    def test_scopes(self):
        assert "read" in SCOPES
        assert "write" in SCOPES
        assert "execute" in SCOPES
        assert "admin" in SCOPES

    def test_role_default_scopes(self):
        assert "admin" in ROLE_DEFAULT_SCOPES["owner"]
        assert "read" in ROLE_DEFAULT_SCOPES["viewer"]
        assert "write" not in ROLE_DEFAULT_SCOPES["viewer"]


# ══════════════════════════════════════════════════════════════════════════
#  Organization dataclass
# ══════════════════════════════════════════════════════════════════════════


class TestOrganization:
    def test_defaults(self):
        org = Organization(id="test", name="Test Org", owner="user-1")
        assert org.members == {}
        assert org.api_keys == {}


# ══════════════════════════════════════════════════════════════════════════
#  OrganizationManager — create / get
# ══════════════════════════════════════════════════════════════════════════


class TestCreateAndGet:
    def test_create_org(self, mgr):
        org = mgr.create("my-org", owner="user-1")
        assert org.id == "my-org"
        assert org.owner == "user-1"
        assert org.members["user-1"] == "owner"

    def test_get_org(self, mgr):
        mgr.create("my-org", owner="user-1")
        org = mgr.get("my-org")
        assert org is not None
        assert org.id == "my-org"

    def test_get_nonexistent(self, mgr):
        assert mgr.get("nonexistent") is None

    def test_create_duplicate_raises(self, mgr):
        mgr.create("my-org", owner="user-1")
        with pytest.raises(ValueError, match="already exists"):
            mgr.create("my-org", owner="user-2")

    def test_list_orgs(self, mgr):
        mgr.create("org-1", owner="u1")
        mgr.create("org-2", owner="u2")
        orgs = mgr.list_orgs()
        assert "org-1" in orgs
        assert "org-2" in orgs


# ══════════════════════════════════════════════════════════════════════════
#  Members
# ══════════════════════════════════════════════════════════════════════════


class TestMembers:
    def test_add_member(self, mgr):
        mgr.create("my-org", owner="user-1")
        member = mgr.add_member("my-org", "user-2", role="member")
        assert member == "member"
        org = mgr.get("my-org")
        assert org.members["user-2"] == "member"

    def test_add_member_duplicate_raises(self, mgr):
        mgr.create("my-org", owner="user-1")
        mgr.add_member("my-org", "user-2", role="member")
        with pytest.raises(ValueError, match="already a member"):
            mgr.add_member("my-org", "user-2", role="admin")

    def test_remove_member(self, mgr):
        mgr.create("my-org", owner="user-1")
        mgr.add_member("my-org", "user-2", role="member")
        mgr.remove_member("my-org", "user-2")
        org = mgr.get("my-org")
        assert "user-2" not in org.members

    def test_remove_owner_raises(self, mgr):
        mgr.create("my-org", owner="user-1")
        with pytest.raises(ForbiddenError, match="owner"):
            mgr.remove_member("my-org", "user-1")

    def test_remove_nonexistent_raises(self, mgr):
        mgr.create("my-org", owner="user-1")
        with pytest.raises(ValueError, match="not a member"):
            mgr.remove_member("my-org", "nonexistent")


# ══════════════════════════════════════════════════════════════════════════
#  API Keys
# ══════════════════════════════════════════════════════════════════════════


class TestApiKeys:
    def test_create_api_key(self, mgr):
        mgr.create("my-org", owner="user-1")
        key_id, key_value = mgr.create_api_key("my-org", scopes=["read", "execute"])
        assert key_id.startswith("key_")
        assert key_value.startswith("aitest_")

    def test_validate_api_key(self, mgr):
        mgr.create("my-org", owner="user-1")
        key_id, key_value = mgr.create_api_key("my-org", scopes=["read"])
        result = mgr.validate_api_key(key_value)
        assert result is not None
        assert result["org_id"] == "my-org"
        assert "read" in result["scopes"]

    def test_validate_invalid_key(self, mgr):
        assert mgr.validate_api_key("invalid-key") is None

    def test_revoke_api_key(self, mgr):
        mgr.create("my-org", owner="user-1")
        key_id, key_value = mgr.create_api_key("my-org", scopes=["read"])
        mgr.revoke_api_key("my-org", key_id)
        assert mgr.validate_api_key(key_value) is None

    def test_list_api_keys(self, mgr):
        mgr.create("my-org", owner="user-1")
        mgr.create_api_key("my-org", scopes=["read"])
        mgr.create_api_key("my-org", scopes=["write"])
        keys = mgr.list_api_keys("my-org")
        assert len(keys) == 2
