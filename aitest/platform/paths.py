"""
Platform path resolution — single source of truth for all project paths.

Replaces 35+ hardcoded ZJSN_Test-master526 / web-automation path constants
across the codebase. All path constants derive from ProjectContext.

Usage:
    from aitest.platform.paths import get_test_project_root, get_context_modules

    zjsn = get_test_project_root()           # Optional[Path]
    modules = get_context_modules()          # Path
    workstudy = get_workstudy()              # Path

Migration pattern (replace module-level constants with lazy calls):
    # Before:
    WORKSTUDY = Path(__file__).resolve().parent.parent.parent
    ZJSN_TEST = WORKSTUDY / "ZJSN_Test-master526"

    # After:
    from aitest.platform.paths import get_test_project_root, get_workstudy
    WORKSTUDY = get_workstudy()
    # ... use zjsn = get_test_project_root() at call site
"""

import warnings
from pathlib import Path
from typing import Optional

_WORKSTUDY = Path(__file__).resolve().parent.parent.parent


def get_workstudy() -> Path:
    """Return WorkStudy root directory (absolute path)."""
    return _WORKSTUDY


def get_test_project_root(project_id: str = None) -> Optional[Path]:
    """Return test project code_path for the active (or specified) project.

    Reads test_project.code_path from project.yaml.
    Returns None if not configured or path does not exist on disk.
    """
    from aitest.platform.context import get_project
    ctx = get_project(project_id)
    code_path = ctx.config.test_project_code_path
    if code_path:
        p = _WORKSTUDY / code_path
        if p.exists():
            return p.resolve()
    return None


def get_tlo_dir(project_root: Path = None, project_id: str = None) -> Optional[Path]:
    """Return .tlo/ directory inside the project root (if it exists).

    This is the new project-intelligence directory per ADR-001.
    Accepts either project_root (Path) or project_id (str).
    Returns None if project has no .tlo/ yet.
    """
    root = project_root or get_test_project_root(project_id=project_id)
    if root:
        tlo = root / ".tlo"
        if tlo.exists():
            return tlo
    return None


def ensure_tlo_dir(project_root: Path = None, project_id: str = None) -> Optional[Path]:
    """Return .tlo/ directory, creating it if necessary."""
    root = project_root or get_test_project_root(project_id=project_id)
    if root and root.exists():
        tlo = root / ".tlo"
        tlo.mkdir(parents=True, exist_ok=True)
        return tlo
    return None


def resolve_path(category: str, *parts: str, project_id: str = None) -> Path:
    """
    Unified path resolution with fallback chain.

    Priority:
      1. .tlo/<category>/<parts>  (new ADR-001 location)
      2. governance/context/projects/<id>/<category>/<parts>  (legacy)
      3. Raise FileNotFoundError

    Category is one of: knowledge/modules, context, runtime, cache, artifacts
    """
    # Priority 1: .tlo/
    tlo = get_tlo_dir(project_id=project_id)
    if tlo:
        p = tlo / category / Path(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    # Priority 2: Legacy governance/context/projects/<id>/
    from aitest.platform.context import get_active_project_id
    pid = project_id or get_active_project_id()
    legacy = _WORKSTUDY / "governance" / "context" / "projects" / pid / category
    p = legacy / Path(*parts)
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def get_context_modules(project_id: str = None) -> Path:
    """Return modules directory for the active (or specified) project.

    Priority: .tlo/knowledge/modules/ → governance/context/projects/<id>/modules/
    """
    tlo = get_tlo_dir(project_id=project_id)
    if tlo and (tlo / "knowledge" / "modules").exists():
        return tlo / "knowledge" / "modules"

    # Fallback: legacy governance/context/projects/<id>/modules/
    from aitest.platform.context import get_active_project_id
    pid = project_id or get_active_project_id()
    return _WORKSTUDY / "governance" / "context" / "projects" / pid / "modules"


def get_sop_status_dir(project_id: str = None) -> Path:
    """Return SOP status directory for the active (or specified) project.

    Priority: .tlo/runtime/sop-status/ → governance/artifacts/sop-status/<id>/
    """
    tlo = get_tlo_dir(project_id=project_id)
    if tlo:
        d = tlo / "runtime" / "sop-status"
        d.mkdir(parents=True, exist_ok=True)
        return d

    from aitest.platform.context import get_active_project_id
    pid = project_id or get_active_project_id()
    d = _WORKSTUDY / "governance" / "artifacts" / "sop-status" / pid
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_project_dir(project_id: str = None) -> Path:
    """Return project directory: .tlo/ or governance/context/projects/<id>/."""
    tlo = get_tlo_dir(project_id=project_id)
    if tlo:
        return tlo
    from aitest.platform.context import get_active_project_id
    pid = project_id or get_active_project_id()
    return _WORKSTUDY / "governance" / "context" / "projects" / pid


def _legacy_modules_dir(project_id: str = None) -> Path:
    """Legacy modules directory — for migration compatibility."""
    from aitest.platform.context import get_active_project_id
    pid = project_id or get_active_project_id()
    return _WORKSTUDY / "governance" / "context" / "projects" / pid / "modules"


def get_governance_dir() -> Path:
    """Return governance/ directory."""
    return _WORKSTUDY / "governance"


# ── LEGACY: deprecated module-level constant ────────────────────────────────
# ZJSN_Test-master526 has moved to D:\Desktop\WorkStudy2\.
# Use get_test_project_root() instead of this constant.

def __getattr__(name: str):
    """Module-level __getattr__ for deprecated ZJSN_TEST constant.

    Supports both `from aitest.platform.paths import ZJSN_TEST` and
    `paths.ZJSN_TEST` access patterns with deprecation warning.
    """
    if name == "ZJSN_TEST":
        import warnings
        warnings.warn(
            "ZJSN_TEST is deprecated. Use get_test_project_root() which reads from project.yaml.",
            DeprecationWarning,
            stacklevel=2,
        )
        root = get_test_project_root("web-automation")
        if root:
            return root
        raise RuntimeError(
            "ZJSN_TEST is not available: no active project with configured test_project_code_path. "
            "Use aitest project set --id=<project> to configure an active project."
        )
    raise AttributeError(f"module 'aitest.platform.paths' has no attribute {name!r}")
