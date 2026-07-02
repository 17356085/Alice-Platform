"""Re-export from alice_engine.core.state_machine — 保持向后兼容。"""

from alice_engine.core.state_machine import (  # noqa: F401
    update_agent_state,
    MILESTONE_SKILLS,
)

# 兼容旧接口
def emit_cache_summary(shared_injector=None, shared_adapter=None, logger=None):
    """兼容旧接口。"""
    pass
