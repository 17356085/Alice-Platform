"""Tests for platform/artifacts.py — ArtifactStore file read/write.

Tests: ArtifactStore construction, path resolution, read/write,
exists, glob, list_modules, list_pages.
Uses temp directory — no real governance/ dependency.
"""
import pytest
from pathlib import Path

from aitest.platform.artifacts import ArtifactStore


# ══════════════════════════════════════════════════════════════════════════
#  Fixtures
# ══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def store(temp_dir, monkeypatch):
    """ArtifactStore with temp directory as root."""
    monkeypatch.setattr("aitest.platform.artifacts.get_workstudy", lambda: temp_dir)
    return ArtifactStore(project_id="test-project")


# ══════════════════════════════════════════════════════════════════════════
#  Construction
# ══════════════════════════════════════════════════════════════════════════


class TestConstruction:
    def test_project_id(self, store):
        assert store.project_id == "test-project"

    def test_project_dir_resolved(self, store):
        assert "test-project" in str(store._project_dir)

    def test_modules_dir_resolved(self, store):
        assert "modules" in str(store._modules_dir)


# ══════════════════════════════════════════════════════════════════════════
#  path / project_path
# ══════════════════════════════════════════════════════════════════════════


class TestPathResolution:
    def test_path_relative_to_modules(self, store):
        p = store.path("equipment", "alarm", "PAGE_CONTEXT.md")
        assert "equipment" in str(p)
        assert "alarm" in str(p)
        assert "PAGE_CONTEXT.md" in str(p)

    def test_project_path_relative_to_project(self, store):
        p = store.project_path("PROJECT_CONTEXT.md")
        assert "test-project" in str(p)
        assert "PROJECT_CONTEXT.md" in str(p)

    def test_discovery_path(self, store):
        p = store.discovery_path("pages.json")
        assert "pages.json" in str(p)


# ══════════════════════════════════════════════════════════════════════════
#  read / write
# ══════════════════════════════════════════════════════════════════════════


class TestReadWrite:
    def test_write_and_read(self, store):
        store.write("## Page Context\nAlarm config page", "equipment", "alarm", "PAGE_CONTEXT.md")
        content = store.read("equipment", "alarm", "PAGE_CONTEXT.md")
        assert content == "## Page Context\nAlarm config page"

    def test_read_nonexistent_returns_none(self, store):
        assert store.read("nonexistent", "file.md") is None

    def test_write_creates_parent_dirs(self, store):
        store.write("content", "deep", "nested", "path", "file.txt")
        assert store.read("deep", "nested", "path", "file.txt") == "content"

    def test_write_project(self, store):
        store.write_project("Project context", "PROJECT_CONTEXT.md")
        content = store.read_project("PROJECT_CONTEXT.md")
        assert content == "Project context"


# ══════════════════════════════════════════════════════════════════════════
#  exists
# ══════════════════════════════════════════════════════════════════════════


class TestExists:
    def test_exists_after_write(self, store):
        store.write("content", "test.md")
        assert store.exists("test.md") is True

    def test_exists_nonexistent(self, store):
        assert store.exists("nonexistent.md") is False


# ══════════════════════════════════════════════════════════════════════════
#  glob
# ══════════════════════════════════════════════════════════════════════════


class TestGlob:
    def test_glob_finds_files(self, store):
        store.write("a", "equipment", "a.md")
        store.write("b", "equipment", "b.md")
        results = store.glob("equipment/*.md")
        assert len(results) >= 2

    def test_glob_empty(self, store):
        results = store.glob("nonexistent/*.md")
        assert results == []


# ══════════════════════════════════════════════════════════════════════════
#  list_modules / list_pages
# ══════════════════════════════════════════════════════════════════════════


class TestDiscovery:
    def test_list_modules_empty(self, store):
        modules = store.list_modules()
        assert isinstance(modules, list)

    def test_list_pages_empty(self, store):
        pages = store.list_pages("nonexistent")
        assert isinstance(pages, list)

    def test_list_modules_merges_discovery_cache_and_persisted_dirs(self, store):
        store.discovery_path("pages.json").parent.mkdir(parents=True, exist_ok=True)
        store.discovery_path("pages.json").write_text(
            '[{"id": "cached-page", "menu_path": ["cached-module"]}]',
            encoding="utf-8",
        )
        store.write("page", "persisted-module", "pages", "page-a", "PAGE_CONTEXT.md")

        assert store.list_modules() == ["cached-module", "persisted-module"]

    def test_list_pages_merges_discovery_cache_and_persisted_dirs(self, store):
        store.discovery_path("pages.json").parent.mkdir(parents=True, exist_ok=True)
        store.discovery_path("pages.json").write_text(
            '[{"id": "cached-page", "menu_path": ["module"]}]',
            encoding="utf-8",
        )
        store.write("page", "module", "pages", "persisted-page", "PAGE_CONTEXT.md")

        assert store.list_pages("module") == ["cached-page", "persisted-page"]
