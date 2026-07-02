"""SkillExecutor — Skill 执行引擎接口。

SDK 定义接口，平台层提供实现。

用法:
    from alice_engine.core.skill_executor import SkillExecutorProtocol, SkillResult
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable

from alice_engine.core.task import AgentState, Observation


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


def register_agent_skills(agent_name: str, skills: list[str]) -> None:
    """注册 Agent 的 Skill 映射。"""
    AGENT_SKILL_MAP[agent_name] = skills


def get_agent_skills(agent_name: str) -> list[str]:
    """获取 Agent 的 Skill 列表。"""
    return AGENT_SKILL_MAP.get(agent_name, [])
