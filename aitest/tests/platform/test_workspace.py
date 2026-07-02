"""Tests for platform/workspace.py — ExecutionContext, WorkspaceManager.

Tests: ExecutionContext (has_scope, require, to_dict),
WorkspaceManager CRUD (create, get, list_workspaces).
Uses temp directory — no real governance/ dependency.
"""
import pytest
from pathlib import Path

from aitest.platform.workspace import (
    ExecutionContext, WorkspaceManager,
)


# ══════════════════════════════════════════════════════════════════════════
#  ExecutionContext
# ══════════════════════════════════════════════════════════════════════════


class TestExecutionContext:
    def test_defaults(self):
        ctx = ExecutionContext(workspace_id="ws-1")
        assert ctx.user_id == "anonymous"
        assert ctx.org_id == ""
        assert "read" in ctx.scopes
        assert "execute" in ctx.scopes

    def test_has_scope(self):
        ctx = ExecutionContext(workspace_id="ws-1", scopes=["read", "write"])
        assert ctx.has_scope("read") is True
        assert ctx.has_scope("write") is True
        assert ctx.has_scope("admin") is False

    def test_admin_has_all_scopes(self):
        ctx = ExecutionContext(workspace_id="ws-1", scopes=["admin"])
        assert ctx.has_scope("read") is True
        assert ctx.has_scope("write") is True
        assert ctx.has_scope("execute") is True
        assert ctx.has_scope("admin") is True

    def test_require_passes(self):
        ctx = ExecutionContext(workspace_id="ws-1", scopes=["read", "execute"])
        ctx.require("read")  # Should not raise

    def test_require_fails(self):
        ctx = ExecutionContext(workspace_id="ws-1", scopes=["read"])
        with pytest.raises(PermissionError, match="lacks scope"):
            ctx.require("admin")

    def test_to_dict(self):
        ctx = ExecutionContext(workspace_id="ws-1", user_id="alice",
                              scopes=["read"], org_id="org-1")
        d = ctx.to_dict()
        assert d["workspace_id"] == "ws-1"
        assert d["user_id"] == "alice"
        assert d["org_id"] == "org-1"


# ══════════════════════════════════════════════════════════════════════════
#  WorkspaceManager
# ══════════════════════════════════════════════════════════════════════════


class TestWorkspaceManager:
    def test_create_workspace(self, temp_dir):
        mgr = WorkspaceManager(data_dir=temp_dir / "workspaces")
        ws = mgr.create("ws-1", org_id="org-1", name="My Workspace")
        assert ws["workspace_id"] == "ws-1"
        assert ws["org_id"] == "org-1"

    def test_get_workspace(self, temp_dir):
        mgr = WorkspaceManager(data_dir=temp_dir / "workspaces")
        mgr.create("ws-1", org_id="org-1")
        ws = mgr.get("ws-1")
        assert ws is not None
        assert ws["workspace_id"] == "ws-1"

    def test_get_nonexistent(self, temp_dir):
        mgr = WorkspaceManager(data_dir=temp_dir / "workspaces")
        assert mgr.get("nonexistent") is None

    def test_list_workspaces(self, temp_dir):
        mgr = WorkspaceManager(data_dir=temp_dir / "workspaces")
        mgr.create("ws-1", org_id="org-1")
        mgr.create("ws-2", org_id="org-1")
        ws_list = mgr.list_workspaces(org_id="org-1")
        assert len(ws_list) == 2

    def test_list_workspaces_by_org(self, temp_dir):
        mgr = WorkspaceManager(data_dir=temp_dir / "workspaces")
        mgr.create("ws-1", org_id="org-1")
        mgr.create("ws-2", org_id="org-2")
        ws_list = mgr.list_workspaces(org_id="org-1")
        assert len(ws_list) == 1
        assert ws_list[0]["workspace_id"] == "ws-1"

    def test_create_duplicate_raises(self, temp_dir):
        mgr = WorkspaceManager(data_dir=temp_dir / "workspaces")
        mgr.create("ws-1", org_id="org-1")
        with pytest.raises(ValueError, match="already exists"):
            mgr.create("ws-1", org_id="org-1")
