"""SkillExecutor — Skill 执行引擎接口。

SDK 定义接口，平台层提供实现。

用法:
    from alice_engine.core.skill_executor import SkillExecutorProtocol, SkillResult
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol, runtime_checkable

from alice_engine.behavior import resolve_governance_pack_path
from alice_engine.core.agent_definitions import AgentDefinitions, FALLBACK_AGENT_SKILL_MAP
from alice_engine.core.skill_executor_impl import SkillExecutorImpl
from alice_engine.core.skill_loader import SkillLoader
from alice_engine.core.task import AgentState, Observation
from alice_engine.providers import get_provider


@dataclass
class SkillResult:
    """单个 Skill 的执行结果。"""

    skill_id: str = ""
    status: str = "pending"  # pass | fail | partial | skipped
    observation: Observation | None = None
    raw_output: str = ""
    token_usage: dict = field(default_factory=dict)
    elapsed_seconds: float = 0.0


@runtime_checkable
class SkillExecutorProtocol(Protocol):
    """Skill 执行器协议。

    平台层实现此协议，提供 Skill 的加载和执行能力。
    """

    def execute(self, skill_id: str, state: AgentState, context: dict = None) -> SkillResult:
        """执行单个 Skill。

        Args:
            skill_id: Skill ID (如 "automation/page-object-generator")
            state: 当前 Agent 状态
            context: 额外上下文 (knowledge_context, memory_context 等)

        Returns:
            SkillResult
        """
        ...

    def get_skills(self, agent_name: str) -> list[str]:
        """获取 Agent 的 Skill 列表。

        Args:
            agent_name: Agent 名称 (如 "automation-agent")

        Returns:
            Skill ID 列表
        """
        ...


# Agent → Skill 映射 (通用框架层)
AGENT_SKILL_MAP: dict[str, list[str]] = {}
DEV_AGENT_SKILL_MAP: dict[str, list[str]] = {}
_FALLBACK_AGENT_SKILL_MAP: dict[str, list[str]] = FALLBACK_AGENT_SKILL_MAP.copy()
_ALL_SKILL_MAP: dict[str, list[str]] = {}
_DEFS: AgentDefinitions | None = None


def _get_governance_root() -> Path:
    root = resolve_governance_pack_path(project_root=Path.cwd())
    if root is None:
        root = Path(__file__).resolve().parent.parent / "governance_default"
    return root


def _get_defs() -> AgentDefinitions:
    global _DEFS
    if _DEFS is None:
        _DEFS = AgentDefinitions(governance_path=_get_governance_root())
    return _DEFS


def _refresh_skill_maps() -> None:
    global AGENT_SKILL_MAP, _ALL_SKILL_MAP
    AGENT_SKILL_MAP = _get_defs()._load_skill_map() or _FALLBACK_AGENT_SKILL_MAP.copy()
    _ALL_SKILL_MAP = {**AGENT_SKILL_MAP, **DEV_AGENT_SKILL_MAP}


def _load_agent_definitions() -> dict[str, dict]:
    return _get_defs()._load_definitions()


def _load_dev_agent_definitions() -> dict[str, dict]:
    return {}


def _get_all_definitions() -> dict[str, dict]:
    merged = dict(_load_agent_definitions())
    merged.update(_load_dev_agent_definitions())
    return merged


def register_agent_skills(agent_name: str, skills: list[str]) -> None:
    """注册 Agent 的 Skill 映射。"""
    AGENT_SKILL_MAP[agent_name] = skills
    _ALL_SKILL_MAP[agent_name] = skills


def get_agent_skills(agent_name: str) -> list[str]:
    """获取 Agent 的 Skill 列表。"""
    return AGENT_SKILL_MAP.get(agent_name, [])


def get_agent_definition(agent_name: str) -> dict:
    return _get_defs().get_definition(agent_name)


def run_skill(
    skill_id: str,
    user_input: str,
    provider=None,
    context_vars=None,
    **kwargs,
):
    loader = SkillLoader(governance_path=_get_governance_root())
    llm = get_provider(provider or "mock")
    executor = SkillExecutorImpl(skill_loader=loader, provider=llm)
    return executor.execute(skill_id, user_input, context_vars=context_vars, **kwargs)


_refresh_skill_maps()
