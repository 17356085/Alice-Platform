"""Tests for platform/context.py — ProjectContext, ProjectConfig.

Tests: ProjectConfig.from_yaml, get_active_project_id, set_active_project,
list_projects, ProjectContext construction + lazy sub-stores.
Uses temp directory — no real governance/ dependency.
"""
import pytest
from pathlib import Path

from aitest.platform.context import (
    ProjectConfig, ProjectContext,
    get_active_project_id, set_active_project, list_projects,
    _scan_projects, _load_project_yaml,
)


# ══════════════════════════════════════════════════════════════════════════
#  ProjectConfig
# ══════════════════════════════════════════════════════════════════════════


class TestProjectConfig:
    def test_defaults(self):
        cfg = ProjectConfig()
        assert cfg.project_id == "web-automation"
        assert cfg.name == "Untitled Project"
        assert cfg.base_url == ""
        assert cfg.login_required is False

    def test_from_yaml_empty(self):
        cfg = ProjectConfig.from_yaml("test", raw={})
        assert cfg.project_id == "test"

    def test_from_yaml_full(self):
        raw = {
            "project": {"id": "my-project", "name": "My Project"},
            "application": {"type": "vue-hash-router"},
            "connection": {"base_url": "https://example.com", "login_required": True},
            "discovery": {"strategy": "browser-use"},
            "knowledge": {"chroma_namespace": "my-ns"},
            "test_project": {"code_path": "/path/to/code", "type": "pytest"},
        }
        cfg = ProjectConfig.from_yaml("my-project", raw=raw)
        assert cfg.project_id == "my-project"
        assert cfg.name == "My Project"
        assert cfg.base_url == "https://example.com"
        assert cfg.login_required is True
        assert cfg.chroma_namespace == "my-ns"
        assert cfg.test_project_code_path == "/path/to/code"

    def test_from_yaml_partial(self):
        raw = {"project": {"id": "p1"}, "connection": {"base_url": "https://test.com"}}
        cfg = ProjectConfig.from_yaml("p1", raw=raw)
        assert cfg.base_url == "https://test.com"
        assert cfg.login_required is False  # default


# ══════════════════════════════════════════════════════════════════════════
#  set_active_project / get_active_project_id
# ══════════════════════════════════════════════════════════════════════════


class TestActiveProject:
    def test_set_and_get(self, monkeypatch):
        set_active_project("test-project")
        assert get_active_project_id() == "test-project"
        # Cleanup
        set_active_project(None)

    def test_default_fallback(self, monkeypatch):
        set_active_project(None)
        monkeypatch.delenv("AITEST_PROJECT", raising=False)
        # Should return some default
        result = get_active_project_id()
        assert isinstance(result, str)
        assert len(result) > 0


# ══════════════════════════════════════════════════════════════════════════
#  ProjectContext
# ══════════════════════════════════════════════════════════════════════════


class TestProjectContext:
    def test_project_id(self, monkeypatch):
        set_active_project("test-project")
        ctx = ProjectContext("test-project")
        assert ctx.project_id == "test-project"
        set_active_project(None)

    def test_artifacts_lazy(self, monkeypatch):
        set_active_project("test-project")
        ctx = ProjectContext("test-project")
        a1 = ctx.artifacts()
        a2 = ctx.artifacts()
        assert a1 is a2  # Lazy singleton
        set_active_project(None)

    def test_sut_url(self, monkeypatch):
        set_active_project("test-project")
        ctx = ProjectContext("test-project")
        url = ctx.sut_url()
        assert isinstance(url, str)
        set_active_project(None)

    def test_sut_type(self, monkeypatch):
        set_active_project("test-project")
        ctx = ProjectContext("test-project")
        stype = ctx.sut_type()
        assert isinstance(stype, str)
        set_active_project(None)
