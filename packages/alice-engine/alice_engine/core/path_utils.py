"""Path Utilities — 路径解析工具函数。

从 executor.py 迁出，供 executor_impl.py 和 state_updater.py 共用。
无业务依赖，只做字符串/路径变换。
"""

import os
from pathlib import Path

from alice_engine.core.runtime_environment import current_context_modules, current_workstudy
from alice_engine.workflow.state import get_test_project_root

# 向后兼容：executor_impl.py / runtime_context_builder.py 仍以模块级常量方式导入。
# 这些值在模块加载时求值一次（与旧版行为一致），线程局部覆盖 (runtime_environment_scope)
# 场景下请直接调用 current_workstudy() / current_context_modules() 而非这些常量。
_WORKSTUDY: Path = current_workstudy()
_CONTEXT_MODULES: Path = current_context_modules()
_GOVERNANCE: Path = _WORKSTUDY / "governance"


def _get_project_dir() -> Path:
    """获取项目目录。通过环境变量注入，不 import aitest（保持 engine 独立可发布）。
    平台层启动时设置 AITEST_PROJECT_DIR 即可。"""
    return Path(os.environ.get("AITEST_PROJECT_DIR", str(current_workstudy())))


def slug_to_page_name(slug: str) -> str:
    """alarm-config → AlarmConfig"""
    return "".join(part.capitalize() for part in slug.replace("-", " ").split())


def page_slug_to_underscore(slug: str) -> str:
    """alarm-config → alarm_config"""
    return slug.replace("-", "_")


def resolve_artifact_path(
    pattern: str, module: str, page: str, agent_name: str, dev_agent_map: set,
) -> str:
    """将 glob pattern 中的变量替换为实际值。"""
    page_name = slug_to_page_name(page)
    if not page_name and module:
        page_name = slug_to_page_name(module)
    page_slug = page or module
    resolved = pattern
    governance_root = current_workstudy() / "governance"
    if agent_name in dev_agent_map:
        module_dir = str(governance_root / "context" / "projects" / "dev-platform")
    else:
        module_dir = str(current_context_modules() / module)
    resolved = resolved.replace("{module_dir}", module_dir)
    resolved = resolved.replace("{module}", module)
    resolved = resolved.replace("{page}", page_slug)
    resolved = resolved.replace("{PageName}", page_name)
    resolved = resolved.replace("{page_underscore}", page_slug_to_underscore(page_slug))
    zjsn = get_test_project_root()
    if zjsn:
        resolved = resolved.replace("{test_project_root}", str(zjsn))
    return resolved


def resolve_path(
    pattern: str, module: str, page: str, agent_name: str, dev_agent_map: set,
) -> Path:
    """将 pattern 解析为绝对路径。"""
    resolved = resolve_artifact_path(pattern, module, page, agent_name, dev_agent_map)
    workstudy = current_workstudy()
    if not Path(resolved).is_absolute() and not resolved.startswith(str(workstudy)):
        resolved = str(workstudy / resolved)
    return Path(resolved)
