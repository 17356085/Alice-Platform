# Re-export — 原 paths.py 已搬到 runtime/paths.py，此文件保证向后兼容
from aitest.runtime.paths import (  # noqa: F401
    get_workstudy,
    get_governance_dir,
    get_test_project_root,
    get_tlo_dir,
    ensure_tlo_dir,
    resolve_path,
    get_context_modules,
    get_sop_status_dir,
    get_project_dir,
    _legacy_modules_dir,
)
from aitest.runtime._paths_core import _WORKSTUDY  # noqa: F401
