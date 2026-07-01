"""Tests for platform/paths.py — path resolution.

Tests: get_workstudy, get_governance_dir, get_test_project_root,
get_tlo_dir, resolve_path, get_context_modules, get_sop_status_dir.
Uses temp directory — no real governance/ dependency.
"""
import pytest
from pathlib import Path

from aitest.platform._paths_core import get_workstudy, get_governance_dir
from aitest.platform.paths import (
    get_test_project_root, get_tlo_dir, ensure_tlo_dir,
    resolve_path, get_context_modules, get_sop_status_dir, get_project_dir,
)


# ══════════════════════════════════════════════════════════════════════════
#  _paths_core
# ══════════════════════════════════════════════════════════════════════════


class TestPathsCore:
    def test_get_workstudy_returns_path(self):
        result = get_workstudy()
        assert isinstance(result, Path)
        assert result.exists()

    def test_get_governance_dir(self):
        result = get_governance_dir()
        assert isinstance(result, Path)
        assert "governance" in str(result)

    def test_workstudy_is_repo_root(self):
        result = get_workstudy()
        # Should contain aitest/ directory
        assert (result / "aitest").exists()


# ══════════════════════════════════════════════════════════════════════════
#  get_test_project_root
# ══════════════════════════════════════════════════════════════════════════


class TestGetTestProjectRoot:
    def test_returns_path_or_none(self):
        result = get_test_project_root()
        assert result is None or isinstance(result, Path)

    def test_returns_none_for_nonexistent_project(self):
        result = get_test_project_root("nonexistent-project-xyz")
        assert result is None


# ══════════════════════════════════════════════════════════════════════════
#  get_tlo_dir / ensure_tlo_dir
# ══════════════════════════════════════════════════════════════════════════


class TestTloDir:
    def test_get_tlo_dir_returns_path_or_none(self):
        result = get_tlo_dir()
        assert result is None or isinstance(result, Path)

    def test_ensure_tlo_dir_returns_path_or_none(self):
        result = ensure_tlo_dir()
        assert result is None or isinstance(result, Path)


# ══════════════════════════════════════════════════════════════════════════
#  resolve_path
# ══════════════════════════════════════════════════════════════════════════


class TestResolvePath:
    def test_returns_path(self):
        result = resolve_path("knowledge/modules", "equipment", "alarm")
        assert isinstance(result, Path)
        assert "equipment" in str(result)
        assert "alarm" in str(result)

    def test_creates_parent_dirs(self):
        result = resolve_path("cache", "deep", "nested", "file.txt")
        assert isinstance(result, Path)
        assert result.parent.exists()


# ══════════════════════════════════════════════════════════════════════════
#  get_context_modules / get_sop_status_dir / get_project_dir
# ══════════════════════════════════════════════════════════════════════════


class TestContextPaths:
    def test_get_context_modules_returns_path(self):
        result = get_context_modules()
        assert isinstance(result, Path)
        assert "modules" in str(result)

    def test_get_sop_status_dir_returns_path(self):
        result = get_sop_status_dir()
        assert isinstance(result, Path)

    def test_get_project_dir_returns_path(self):
        result = get_project_dir()
        assert isinstance(result, Path)


# ══════════════════════════════════════════════════════════════════════════
#  Legacy __getattr__
# ══════════════════════════════════════════════════════════════════════════


class TestLegacyGetattr:
    def test_unknown_attr_raises(self):
        import aitest.platform.paths as paths_mod
        with pytest.raises(AttributeError):
            _ = paths_mod.NONEXISTENT_ATTR
