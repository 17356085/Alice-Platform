# [LAYER:Runtime/Paths] 从 aitest/platform/_paths_core.py 搬入
"""Core path functions — no dependency on context or any platform module.

Leaf module: imported by both paths.py and context.py.
Extracted from paths.py to break the context ⇄ paths circular dependency.
"""
from pathlib import Path

_WORKSTUDY = Path(__file__).resolve().parent.parent.parent


def get_workstudy() -> Path:
    """Return WorkStudy root directory (absolute path)."""
    return _WORKSTUDY


def get_governance_dir() -> Path:
    """Return governance/ directory."""
    return _WORKSTUDY / "governance"
