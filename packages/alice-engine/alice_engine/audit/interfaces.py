"""Audit 接口 — 运行时审计能力的抽象。

SDK 定义接口，平台层实现具体逻辑。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class SafetyFlag:
    """安全标记。"""

    severity: str = "low"  # low | medium | high | critical
    rule: str = ""
    detail: str = ""


@dataclass
class FailureCategory:
    """失败归因类别。"""

    category: str = ""  # prompt | tool_desc | schema | context_pollution | retrieval | env_permission
    confidence: float = 0.0
    detail: str = ""


@dataclass
class RunMetrics:
    """运行指标。"""

    agent_name: str = ""
    module: str = ""
    page: str = ""
    total_steps: int = 0
    completed_skills: int = 0
    failed_skills: int = 0
    elapsed_seconds: float = 0.0
    total_tokens: int = 0
    success: bool = False


@runtime_checkable
class SafetyAuditor(Protocol):
    """安全审计接口。"""

    def check_output(self, content: str, skill_id: str) -> list[SafetyFlag]:
        """检查输出安全性。

        Args:
            content: LLM 输出内容
            skill_id: Skill ID

        Returns:
            安全标记列表
        """
        ...


@runtime_checkable
class FailureAttributor(Protocol):
    """失败归因接口。"""

    def attribute(self, observation, response_content: str) -> FailureCategory:
        """归因失败原因。

        Args:
            observation: Observation
            response_content: LLM 响应内容

        Returns:
            失败归因类别
        """
        ...


@runtime_checkable
class OnlineMonitor(Protocol):
    """在线监控接口。"""

    def record_run(self, module: str, metrics: RunMetrics) -> None:
        """记录运行指标。

        Args:
            module: 模块名
            metrics: 运行指标
        """
        ...


@runtime_checkable
class CostAuditor(Protocol):
    """成本审计接口。"""

    def record_cost(self, agent_name: str, tokens_in: int, tokens_out: int,
                    model: str = "") -> None:
        """记录成本。

        Args:
            agent_name: Agent 名称
            tokens_in: 输入 token 数
            tokens_out: 输出 token 数
            model: 模型名
        """
        ...
