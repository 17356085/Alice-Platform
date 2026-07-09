"""Agent definition helpers — skill maps, agent lookup, skill execution.

This module provides:
- Agent skill map loading
- Agent definition lookup
- Skill execution wrapper

Extracted from executor.py to improve modularity.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from alice_engine.behavior import resolve_governance_pack_path
from alice_engine.core.agent_definitions import AgentDefinitions, FALLBACK_AGENT_SKILL_MAP
from alice_engine.core.runtime_environment import current_workstudy


# ══════════════════════════════════════════════════════════════════════════
#  Governance Root
# ══════════════════════════════════════════════════════════════════════════


def _get_governance_root() -> Path:
    """获取 governance 根目录。"""
    workstudy = current_workstudy()
    resolved = resolve_governance_pack_path(project_root=workstudy)
    return resolved or (workstudy / "governance")


# ══════════════════════════════════════════════════════════════════════════
#  Agent Definitions (Singleton)
# ══════════════════════════════════════════════════════════════════════════


_defs_instance: Optional[AgentDefinitions] = None


def _get_defs() -> AgentDefinitions:
    """获取 AgentDefinitions 单例。"""
    global _defs_instance
    if _defs_instance is None:
        _defs_instance = AgentDefinitions(governance_path=_get_governance_root())
    return _defs_instance


def get_agent_skill_map() -> dict[str, list[str]]:
    """获取测试 Agent skill map。"""
    defs = _get_defs()
    return defs._load_skill_map() if defs else FALLBACK_AGENT_SKILL_MAP


def get_dev_agent_skill_map() -> dict[str, list[str]]:
    """获取开发 Agent skill map（当前为空，未来从 governance 加载）。"""
    return {}


def get_agent_definition(agent_name: str) -> dict:
    """获取 agent 定义。"""
    return _get_defs().get_definition(agent_name)


# ══════════════════════════════════════════════════════════════════════════
#  Skill Execution
# ══════════════════════════════════════════════════════════════════════════


def run_skill(skill_id: str, user_input: str, provider=None, context_vars=None, **kwargs):
    """执行单个 skill。

    这是一个便利包装器，内部构建 SkillExecutorImpl。
    """
    from alice_engine.providers import get_provider as _get_provider
    from alice_engine.core.skill_loader import SkillLoader
    from alice_engine.core.skill_executor_impl import SkillExecutorImpl

    loader = SkillLoader(governance_path=_get_governance_root())
    try:
        prov = _get_provider(provider or "mock")
    except Exception:
        prov = _get_provider("mock")
    executor = SkillExecutorImpl(skill_loader=loader, provider=prov)
    return executor.execute(skill_id, user_input, context_vars=context_vars, **kwargs)


# ══════════════════════════════════════════════════════════════════════════
#  Agent Listing
# ══════════════════════════════════════════════════════════════════════════


def list_agents() -> list[str]:
    """列出所有可用的 Agent 名称（含测试 + 开发）。"""
    test_agents = list(get_agent_skill_map().keys())
    dev_agents = list(get_dev_agent_skill_map().keys())
    return sorted(set(test_agents + dev_agents))


def list_dev_agents() -> list[str]:
    """列出所有开发 Agent 名称。"""
    return sorted(get_dev_agent_skill_map().keys())
