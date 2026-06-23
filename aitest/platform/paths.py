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
            return p
    return None


def get_context_modules(project_id: str = None) -> Path:
    """Return modules directory for the active (or specified) project.

    Points to governance/context/projects/<project_id>/modules/.
    """
    from aitest.platform.context import get_project
    ctx = get_project(project_id)
    return ctx.artifacts()._modules_dir


def get_project_dir(project_id: str = None) -> Path:
    """Return project directory: governance/context/projects/<project_id>/."""
    from aitest.platform.context import get_project
    ctx = get_project(project_id)
    return _WORKSTUDY / "governance" / "context" / "projects" / ctx.project_id


def get_governance_dir() -> Path:
    """Return governance/ directory."""
    return _WORKSTUDY / "governance"
