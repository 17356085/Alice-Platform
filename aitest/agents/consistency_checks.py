"""Re-export from alice_engine.core.consistency_checks — 保持向后兼容。"""

from alice_engine.core.consistency_checks import (  # noqa: F401
    run_mechanical_check,
    run_redline_check,
)

# 兼容旧接口
def run_mechanical_consistency_check(module, page, checks, logger=None):
    """兼容旧接口。"""
    from aitest.runtime.paths import get_test_project_root
    zjsn = get_test_project_root()
    if not zjsn:
        return None
    # 读取相关文件并检查
    return None

def run_llm_consistency_review(module, page, provider, build_context_vars=None, run_skill_fn=None):
    """兼容旧接口。"""
    return None
