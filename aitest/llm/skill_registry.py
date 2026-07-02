"""Re-export from alice_engine.core.skill_registry — 保持向后兼容。"""

from alice_engine.core.skill_registry import (  # noqa: F401
    get_skill_requirements,
    check_provider_compatibility,
    list_skills_by_tier,
    get_skill_stats,
)

# 兼容旧接口
def register_skill(*args, **kwargs):
    """兼容旧接口。"""
    pass
