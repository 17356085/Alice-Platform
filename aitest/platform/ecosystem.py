"""Ecosystem snapshot — platform/project/discovery compatibility baseline.

This keeps the control plane lightweight: one read-only snapshot source can
feed health, CLI, and API surfaces without introducing a heavyweight registry.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


SUPPORTED_PROJECT_SCHEMA_VERSION = 1


@dataclass
class ProjectCompatibility:
    status: str
    detail: str
    supported_schema_version: int = SUPPORTED_PROJECT_SCHEMA_VERSION


@dataclass
class EcosystemProjectSnapshot:
    project_id: str
    name: str
    path: str
    active: bool
    schema_version: int
    discovery_strategy: str
    module_count: int
    base_url: str
    compatibility: ProjectCompatibility


def _resolve_project_summary(project_id: str, raw: dict[str, Any] | None = None) -> EcosystemProjectSnapshot:
    from aitest.runtime.context import _PROJECTS_ROOT, _load_project_yaml

    raw = raw or _load_project_yaml(project_id) or {}
    config = raw.get("project", {})
    connection = raw.get("connection", {})
    discovery = raw.get("discovery", {})
    test_project = raw.get("test_project", {})

    project_dir = str(_PROJECTS_ROOT / project_id)
    modules_dir = _PROJECTS_ROOT / project_id / ".tlo" / "knowledge" / "modules"
    try:
        module_count = sum(1 for d in modules_dir.iterdir() if d.is_dir()) if modules_dir.exists() else 0
    except Exception:
        module_count = 0
    project_name = config.get("name", project_id)

    schema_version_raw = raw.get("version", SUPPORTED_PROJECT_SCHEMA_VERSION)
    try:
        schema_version = int(schema_version_raw)
    except Exception:
        schema_version = -1

    discovery_strategy = discovery.get("strategy") or test_project.get("discovery_strategy") or "browser-use"
    # ADR-001 projects created before the connection block stored their URL
    # under test_project.  Read both schemas so health does not report a
    # configured local project as incompatible.
    base_url = connection.get("base_url") or test_project.get("base_url", "")

    if schema_version == SUPPORTED_PROJECT_SCHEMA_VERSION:
        compat = ProjectCompatibility("ok", "Project schema compatible")
    elif schema_version < 0:
        compat = ProjectCompatibility("warn", "Project schema version missing or invalid")
    elif schema_version > SUPPORTED_PROJECT_SCHEMA_VERSION:
        compat = ProjectCompatibility("warn", f"Project schema v{schema_version} newer than supported v{SUPPORTED_PROJECT_SCHEMA_VERSION}")
    else:
        compat = ProjectCompatibility("ok", "Project schema compatible")

    if not base_url:
        compat = ProjectCompatibility("warn", "Project base_url is not configured", compat.supported_schema_version)

    return EcosystemProjectSnapshot(
        project_id=project_id,
        name=project_name,
        path=project_dir,
        active=False,
        schema_version=schema_version,
        discovery_strategy=discovery_strategy,
        module_count=module_count,
        base_url=base_url,
        compatibility=compat,
    )


def collect_ecosystem_snapshot() -> dict[str, Any]:
    """Collect the current platform ecosystem snapshot."""
    from aitest import __version__ as platform_version
    from aitest.runtime.context import list_projects, get_active_project_id, _load_project_yaml

    project_ids = list_projects()
    active_project_id = get_active_project_id() if project_ids else ""
    projects: list[EcosystemProjectSnapshot] = []
    overall = "healthy"

    for project_id in project_ids:
        snapshot = _resolve_project_summary(project_id, _load_project_yaml(project_id))
        snapshot.active = project_id == active_project_id
        if snapshot.compatibility.status != "ok" and overall == "healthy":
            overall = "degraded"
        projects.append(snapshot)

    try:
        from aitest.discovery.registry import DiscoveryRegistry
        strategies = DiscoveryRegistry.list()
    except Exception:
        strategies = []
        overall = "degraded"
    return {
        "status": overall,
        "platform_version": platform_version,
        "supported_project_schema_version": SUPPORTED_PROJECT_SCHEMA_VERSION,
        "active_project_id": active_project_id,
        "projects": [asdict(p) for p in projects],
        "project_count": len(projects),
        "discovery_strategies": strategies,
        "discovery_strategy_count": len(strategies),
    }
