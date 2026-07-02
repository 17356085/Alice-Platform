"""Re-export from alice_engine.core.output_persistence — 保持向后兼容。"""

from alice_engine.core.output_persistence import (  # noqa: F401
    save_skill_output,
    extract_code_block,
    extract_yaml_block,
)

# 兼容旧接口
def persist_consistency_report(module, page, lines, issues):
    """兼容旧接口。"""
    pass

def persist_review_report(module, page, content):
    """兼容旧接口。"""
    pass
