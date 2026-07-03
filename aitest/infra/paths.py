"""
Infra path resolution — infra layer's entry point for path functions.

v3.2: Created to break infra → platform reverse dependency.
Infra modules import from here instead of aitest.platform.paths.

Usage:
    from aitest.infra.paths import get_workstudy, get_governance_dir
"""

from aitest.runtime._paths_core import get_workstudy, get_governance_dir  # noqa: F401
