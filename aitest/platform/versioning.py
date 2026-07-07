"""Platform versioning helpers for governance/config/policy traceability."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

try:  # pragma: no cover - optional dependency, available in the repo runtime
    import yaml
except Exception:  # pragma: no cover
    yaml = None


VERSION_ENV_KEYS = (
    "AITEST_GOVERNANCE_POLICY_VERSION",
    "AITEST_POLICY_VERSION",
    "ENGINE_GOVERNANCE_POLICY_VERSION",
)


def _as_path(value: str | Path | None) -> Path | None:
    if value is None:
        return None
    try:
        return Path(value)
    except Exception:
        return None


@lru_cache(maxsize=64)
def _read_yaml_version(path: str) -> str:
    target = Path(path)
    if yaml is None or not target.exists():
        return ""
    try:
        data = yaml.safe_load(target.read_text(encoding="utf-8"))
    except Exception:
        return ""
    if isinstance(data, dict):
        value = data.get("version", "")
        return str(value).strip()
    return ""


def resolve_policy_version(
    *,
    governance_path: str | Path | None = None,
    project_root: str | Path | None = None,
) -> str:
    """Resolve the active governance/policy version string.

    Resolution order:
      1. explicit env override
      2. canonical governance pack YAML version
      3. governance pack root folder name
      4. "unknown"
    """

    for key in VERSION_ENV_KEYS:
        raw = os.environ.get(key, "").strip()
        if raw:
            return raw

    if project_root is None:
        try:
            from aitest.runtime.paths import get_workstudy

            project_root = get_workstudy()
        except Exception:
            project_root = None

    from alice_engine.behavior import resolve_governance_pack_path

    root = resolve_governance_pack_path(governance_path, project_root=project_root)
    if root is None:
        return "unknown"

    for rel in (
        ("agents", "agent-definitions.yaml"),
        ("skills", "skill-registry.yaml"),
        ("context", "minimal.yaml"),
    ):
        version = _read_yaml_version(str(root.joinpath(*rel).resolve()))
        if version:
            return version

    return root.name or "unknown"


def resolve_version_metadata(
    *,
    governance_path: str | Path | None = None,
    project_root: str | Path | None = None,
) -> dict[str, str]:
    """Return a compact version metadata payload for execution records."""

    if project_root is None:
        try:
            from aitest.runtime.paths import get_workstudy

            project_root = get_workstudy()
        except Exception:
            project_root = None

    from alice_engine.behavior import resolve_governance_pack_path

    root = resolve_governance_pack_path(governance_path, project_root=project_root)
    version = resolve_policy_version(
        governance_path=governance_path,
        project_root=project_root,
    )
    return {
        "policy_version": version,
        "governance_version": version,
        "config_version": version,
        "governance_pack_root": str(root) if root is not None else "",
    }


def select_versioning_payload(records: list[dict[str, Any]]) -> dict[str, str]:
    """Extract the first meaningful versioning payload from event-like records."""

    for entry in records:
        data = entry.get("data", {}) if isinstance(entry, dict) else {}
        if not isinstance(data, dict):
            continue
        payload = {
            key: str(data.get(key, "")).strip()
            for key in ("policy_version", "governance_version", "config_version", "governance_pack_root")
            if str(data.get(key, "")).strip()
        }
        if payload:
            payload["source"] = "events"
            return payload
    return {}
