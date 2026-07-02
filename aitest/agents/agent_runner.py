"""Re-export — 保持向后兼容。"""

from alice_engine.core.task import (  # noqa: F401
    AgentState,
    Observation,
)

from alice_engine.core.executor import AgentLoop  # noqa: F401

from aitest.engine.skill_executor import (  # noqa: F401
    AGENT_SKILL_MAP,
    run_skill,
)

# 兼容旧接口
def run_agent(agent_name, provider=None, verbose=True, **kwargs):
    """兼容旧接口。"""
    from aitest.engine.executor import run_agent as _run_agent
    return _run_agent(agent_name, provider=provider, verbose=verbose, **kwargs)

def list_agents():
    """兼容旧接口。"""
    return sorted(AGENT_SKILL_MAP.keys())

def list_dev_agents():
    """兼容旧接口。"""
    return []
