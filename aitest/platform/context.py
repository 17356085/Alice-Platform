# Re-export — 原 context.py 已搬到 runtime/context.py，此文件保证向后兼容
from aitest.runtime.context import (  # noqa: F401
    ProjectConfig,
    ProjectContext,
    get_project,
    get_active_project_id,
    set_active_project,
    list_projects,
    _load_project_yaml,
    _scan_projects,
)
