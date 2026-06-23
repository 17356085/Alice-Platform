"""
MCP 路径配置 — delegates to aitest.platform.ProjectContext (single source of truth).

Backward compat: all constants below still work. They derive from ProjectContext.
New code should import from aitest.platform directly.

Usage (new):
    from aitest.platform import get_project
    ctx = get_project()
    modules_dir = ctx.artifacts()._modules_dir

Usage (legacy — still works):
    from aitest.mcp.config import CONTEXT_MODULES, ZJSN_TEST
"""
from pathlib import Path

# ── Root paths (platform-independent) ────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"

# ── Active-project paths — derived from ProjectContext ───────────────────
# Lazily resolved: when imported at module level, active project may not be set yet.
# Call _resolve() to force resolution for a specific project_id.

_ctx = None


def _get_ctx(project_id: str = None):
    """Lazy-load ProjectContext for path resolution."""
    global _ctx
    if _ctx is None or project_id:
        from aitest.platform.context import get_project
        _ctx = get_project(project_id)
    return _ctx


def _resolve_legacy(project_id: str = None):
    """Resolve legacy path constants from current project context."""
    ctx = _get_ctx(project_id)
    project_dir = _PROJECTS_ROOT / ctx.project_id if '_PROJECTS_ROOT' in dir() else WORKSTUDY / "governance" / "context" / "projects" / ctx.project_id
    return {
        "PROJECT_CONTEXT": project_dir / "PROJECT_CONTEXT.md",
        "MODULE_INDEX": project_dir / "MODULE_INDEX.md",
        "CONTEXT_MODULES": project_dir / "modules",
        "ZJSN_TEST": WORKSTUDY / ctx.config.test_project_code_path if ctx.config.test_project_code_path else None,
    }


_PROJECTS_ROOT = WORKSTUDY / "governance" / "context" / "projects"

# ── Default constants (resolved from active project via ProjectContext) ──
# These are resolved at import time from the active project for backward compat.
# New code should use aitest.platform.paths or get_project_paths() directly.

from aitest.platform.paths import get_test_project_root, get_context_modules, get_project_dir

# Resolve ZJSN_TEST from active project — None if no test project configured.
# Downstream callers MUST handle None (graceful error, not silent fallback).
ZJSN_TEST = get_test_project_root()

# Project-independent constants (always valid)
KNOWN_ISSUES = GOVERNANCE / "context" / "known-issues.yaml"
ENVIRONMENTS = GOVERNANCE / "context" / "environments.yaml"
ARTIFACTS_DIR = GOVERNANCE / "artifacts"
AUDIT_DIR = GOVERNANCE / "audit"
AUDIT_LOG_FILE = AUDIT_DIR / "tool-calls.jsonl"

# Project-dependent constants (resolved from active project)
CONTEXT_MODULES = get_context_modules()
_resolved_dir = get_project_dir()
PROJECT_CONTEXT = _resolved_dir / "PROJECT_CONTEXT.md"
MODULE_INDEX = _resolved_dir / "MODULE_INDEX.md"

# Tool scripts — resolved lazily; access via get_project_paths() or check ZJSN_TEST first
SOP_GATE_SCRIPT = ZJSN_TEST / "tools" / "check_sop_gate.py" if ZJSN_TEST else None
CODE_QUALITY_SCRIPT = ZJSN_TEST / "tools" / "check_code_quality.py" if ZJSN_TEST else None


def get_project_paths(project_id: str = None):
    """
    Resolve all path constants for a specific project.
    Use this in new code instead of the module-level constants.

    Returns dict with all path constants.
    """
    from aitest.platform.context import get_project
    ctx = get_project(project_id)
    project_dir = _PROJECTS_ROOT / ctx.project_id
    from aitest.platform.paths import get_test_project_root as _get_root
    zjsn = _get_root(project_id)  # may be None

    return {
        "WORKSTUDY": WORKSTUDY,
        "ZJSN_TEST": zjsn,
        "GOVERNANCE": GOVERNANCE,
        "PROJECT_CONTEXT": project_dir / "PROJECT_CONTEXT.md",
        "KNOWN_ISSUES": KNOWN_ISSUES,
        "MODULE_INDEX": project_dir / "MODULE_INDEX.md",
        "ENVIRONMENTS": ENVIRONMENTS,
        "ARTIFACTS_DIR": ARTIFACTS_DIR,
        "CONTEXT_MODULES": project_dir / "modules",
        "AUDIT_DIR": AUDIT_DIR,
        "AUDIT_LOG_FILE": AUDIT_LOG_FILE,
        "SOP_GATE_SCRIPT": zjsn / "tools" / "check_sop_gate.py",
        "CODE_QUALITY_SCRIPT": zjsn / "tools" / "check_code_quality.py",
    }
