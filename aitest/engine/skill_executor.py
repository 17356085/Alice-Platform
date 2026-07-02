"""Re-export from alice_engine.core — 保持向后兼容。"""

from alice_engine.core.agent_definitions import (  # noqa: F401
    AgentDefinitions,
    FALLBACK_AGENT_SKILL_MAP,
)

from alice_engine.core.skill_executor_impl import SkillExecutorImpl  # noqa: F401

# 兼容旧接口
_defs = None

def _get_defs():
    global _defs
    if _defs is None:
        from aitest.runtime.paths import get_workstudy
        _defs = AgentDefinitions(governance_path=get_workstudy() / "governance")
    return _defs

AGENT_SKILL_MAP = _get_defs()._load_skill_map() if _get_defs() else FALLBACK_AGENT_SKILL_MAP
DEV_AGENT_SKILL_MAP = {}
_ALL_SKILL_MAP = {**AGENT_SKILL_MAP, **DEV_AGENT_SKILL_MAP}

def get_agent_definition(agent_name: str) -> dict:
    return _get_defs().get_definition(agent_name)

def run_skill(skill_id, user_input, provider=None, context_vars=None, **kwargs):
    """兼容旧接口。"""
    from alice_engine.providers import get_provider
    from alice_engine.core.skill_loader import SkillLoader
    from aitest.runtime.paths import get_workstudy

    loader = SkillLoader(governance_path=get_workstudy() / "governance")
    prov = get_provider(provider or "mock")
    executor = SkillExecutorImpl(skill_loader=loader, provider=prov)
    return executor.execute(skill_id, user_input, context_vars=context_vars)

_shared_injector = None
_shared_adapter = None
GOVERNANCE = None
