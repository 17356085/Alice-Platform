"""Tests for platform/ecosystem.py — ecosystem control plane snapshot."""

from pathlib import Path

from aitest.platform.ecosystem import collect_ecosystem_snapshot
from aitest.discovery.registry import DiscoveryRegistry


def test_collect_ecosystem_snapshot_reports_project_compatibility(monkeypatch, tmp_path):
    projects_root = tmp_path / "governance" / "context" / "projects"
    project_dir = projects_root / "demo-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "project:",
                "  id: demo-project",
                "  name: Demo Project",
                "connection:",
                "  base_url: https://example.test",
                "discovery:",
                "  strategy: browser-use",
            ]
        ),
        encoding="utf-8",
    )

    import aitest.runtime.context as runtime_context

    monkeypatch.setattr(runtime_context, "_PROJECTS_ROOT", projects_root, raising=False)
    monkeypatch.setattr(runtime_context, "list_projects", lambda: ["demo-project"], raising=False)
    monkeypatch.setattr(runtime_context, "get_active_project_id", lambda: "demo-project", raising=False)
    monkeypatch.setattr(DiscoveryRegistry, "list", classmethod(lambda cls: ["browser-use", "source-vue"]))

    snapshot = collect_ecosystem_snapshot()

    assert snapshot["status"] == "healthy"
    assert snapshot["platform_version"]
    assert snapshot["project_count"] == 1
    assert snapshot["discovery_strategy_count"] == 2
    project = snapshot["projects"][0]
    assert project["project_id"] == "demo-project"
    assert project["compatibility"]["status"] == "ok"
    assert project["schema_version"] == 1


def test_collect_ecosystem_snapshot_warns_on_newer_schema(monkeypatch, tmp_path):
    projects_root = tmp_path / "governance" / "context" / "projects"
    project_dir = projects_root / "future-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.yaml").write_text(
        "\n".join(
            [
                "version: 2",
                "project:",
                "  id: future-project",
                "  name: Future Project",
                "connection:",
                "  base_url: https://example.test",
            ]
        ),
        encoding="utf-8",
    )

    import aitest.runtime.context as runtime_context

    monkeypatch.setattr(runtime_context, "_PROJECTS_ROOT", projects_root, raising=False)
    monkeypatch.setattr(runtime_context, "list_projects", lambda: ["future-project"], raising=False)
    monkeypatch.setattr(runtime_context, "get_active_project_id", lambda: "future-project", raising=False)
    monkeypatch.setattr(DiscoveryRegistry, "list", classmethod(lambda cls: ["browser-use"]))

    snapshot = collect_ecosystem_snapshot()

    assert snapshot["status"] == "degraded"
    assert snapshot["projects"][0]["compatibility"]["status"] == "warn"


def test_collect_ecosystem_snapshot_handles_empty_workspace(monkeypatch, tmp_path):
    import aitest.runtime.context as runtime_context

    monkeypatch.setattr(runtime_context, "_PROJECTS_ROOT", tmp_path / "governance" / "context" / "projects", raising=False)
    monkeypatch.setattr(runtime_context, "list_projects", lambda: [], raising=False)
    monkeypatch.setattr(runtime_context, "get_active_project_id", lambda: "", raising=False)
    monkeypatch.setattr(DiscoveryRegistry, "list", classmethod(lambda cls: []))

    snapshot = collect_ecosystem_snapshot()

    assert snapshot["status"] == "healthy"
    assert snapshot["project_count"] == 0
    assert snapshot["active_project_id"] == ""
    assert snapshot["projects"] == []
    assert snapshot["discovery_strategy_count"] == 0


def test_collect_ecosystem_snapshot_degrades_when_registry_fails(monkeypatch, tmp_path):
    projects_root = tmp_path / "governance" / "context" / "projects"
    project_dir = projects_root / "broken-project"
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "project.yaml").write_text(
        "\n".join(
            [
                "version: 1",
                "project:",
                "  id: broken-project",
                "  name: Broken Project",
                "connection:",
                "  base_url: https://example.test",
            ]
        ),
        encoding="utf-8",
    )

    import aitest.runtime.context as runtime_context

    monkeypatch.setattr(runtime_context, "_PROJECTS_ROOT", projects_root, raising=False)
    monkeypatch.setattr(runtime_context, "list_projects", lambda: ["broken-project"], raising=False)
    monkeypatch.setattr(runtime_context, "get_active_project_id", lambda: "broken-project", raising=False)
    monkeypatch.setattr(DiscoveryRegistry, "list", classmethod(lambda cls: (_ for _ in ()).throw(RuntimeError("boom"))))

    snapshot = collect_ecosystem_snapshot()

    assert snapshot["status"] == "degraded"
    assert snapshot["discovery_strategy_count"] == 0
    assert snapshot["projects"][0]["compatibility"]["status"] == "ok"
