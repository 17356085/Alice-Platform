# [LAYER:Runtime/Paths] 从 aitest/platform/paths.py 搬入
"""
Platform path resolution — single source of truth for all project paths.

Replaces 35+ hardcoded ZJSN_Test-master526 / web-automation path constants
across the codebase. All path constants derive from ProjectContext.

Usage:
    from aitest.runtime.paths import get_test_project_root, get_context_modules

    zjsn = get_test_project_root()           # Optional[Path]
    modules = get_context_modules()          # Path
    workstudy = get_workstudy()              # Path

Migration pattern (replace module-level constants with lazy calls):
    # Before:
    WORKSTUDY = get_workstudy()
    ZJSN_TEST = WORKSTUDY / "ZJSN_Test-master526"

    # After:
    from aitest.runtime.paths import get_test_project_root, get_workstudy
    WORKSTUDY = get_workstudy()
    # ... use zjsn = get_test_project_root() at call site
"""

import warnings
from pathlib import Path
from typing import Optional
from aitest.runtime._paths_core import _WORKSTUDY, get_workstudy, get_governance_dir  # noqa: F401

# ── Project resolver (injected by platform layer to break runtime→platform cycle) ──
_project_resolver = None  # Optional[Callable[[str], ProjectContext]]


def register_project_resolver(resolver) -> None:
    """注册项目解析器（由平台层注入）。"""
    global _project_resolver
    _project_resolver = resolver


def _get_project(project_id: str = None):
    """获取项目上下文——优先使用注入的 resolver，回退到 platform import。"""
    if _project_resolver is not None:
        return _project_resolver(project_id)
    from aitest.platform.context import get_project
    return get_project(project_id)


def _get_active_project_id() -> str:
    """获取活跃项目 ID——优先使用注入的 resolver。"""
    if _project_resolver is not None:
        ctx = _project_resolver(None)
        return ctx.project_id
    from aitest.platform.context import get_active_project_id
    return get_active_project_id()


def get_test_project_root(project_id: str = None) -> Optional[Path]:
    """Return test project code_path for the active (or specified) project.

    Reads test_project.code_path from project.yaml.
    Returns None if not configured or path does not exist on disk.
    """
    ctx = _get_project(project_id)
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
    pid = project_id or _get_active_project_id()
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
    pid = project_id or _get_active_project_id()
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

    pid = project_id or _get_active_project_id()
    d = _WORKSTUDY / "governance" / "artifacts" / "sop-status" / pid
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_project_dir(project_id: str = None) -> Path:
    """Return project directory: .tlo/ or governance/context/projects/<id>/."""
    tlo = get_tlo_dir(project_id=project_id)
    if tlo:
        return tlo
    pid = project_id or _get_active_project_id()
    return _WORKSTUDY / "governance" / "context" / "projects" / pid


def _legacy_modules_dir(project_id: str = None) -> Path:
    """Legacy modules directory — for migration compatibility."""
    pid = project_id or _get_active_project_id()
    return _WORKSTUDY / "governance" / "context" / "projects" / pid / "modules"


# ── LEGACY: deprecated module-level constant ────────────────────────────────
# ZJSN_Test-master526 has moved to D:\Desktop\WorkStudy2\.
# Use get_test_project_root() instead of this constant.

def __getattr__(name: str):
    """Module-level __getattr__ for deprecated ZJSN_TEST constant.

    Supports both `from aitest.runtime.paths import ZJSN_TEST` and
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
    raise AttributeError(f"module 'aitest.runtime.paths' has no attribute {name!r}")
