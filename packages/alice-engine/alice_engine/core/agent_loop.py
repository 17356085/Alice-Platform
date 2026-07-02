"""AgentLoop — Agent 执行循环接口。

SDK 定义接口和核心数据结构，具体实现由平台层提供。

用法:
    from alice_engine.core.agent_loop import AgentLoopProtocol, AgentLoopConfig

    # 平台实现
    class MyAgentLoop(AgentLoopProtocol):
        def run(self) -> AgentState: ...
        def run_interactive(self) -> Generator: ...

    # SDK 用户
    config = AgentLoopConfig(agent_name="automation-agent", module="equipment")
    loop = MyAgentLoop(config)
    state = loop.run()
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generator, Protocol, runtime_checkable

from alice_engine.core.task import AgentState, AgentEvent, Observation


@dataclass
class AgentLoopConfig:
    """AgentLoop 配置。"""

    agent_name: str = ""
    provider: str = "anthropic"
    module: str = ""
    page: str = ""
    goal: str = ""
    skill_subset: list[str] | None = None
    deep_review: bool = True
    token_budget: int = 30000
    max_steps: int = 24
    model: str | None = None
    context: dict = field(default_factory=dict)


@runtime_checkable
class AgentLoopProtocol(Protocol):
    """AgentLoop 协议 — 定义 Agent 执行循环的接口。

    平台层实现此协议，SDK 通过此接口调用 Agent。
    """

    @property
    def state(self) -> AgentState:
        """当前 Agent 状态。"""
        ...

    @property
    def skills(self) -> list[str]:
        """当前 Agent 的 Skill 列表。"""
        ...

    def run(self) -> AgentState:
        """同步执行所有 Skills。

        Returns:
            最终 AgentState
        """
        ...

    def run_interactive(self) -> Generator[AgentEvent, str | None, None]:
        """交互式执行，产生事件流。

        Yields:
            AgentEvent — 每个执行步骤的事件

        Receives:
            用户输入 (可选)
        """
        ...

    def abort(self) -> None:
        """中止执行。"""
        ...


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
            skill_id: Skill ID
            state: 当前 Agent 状态
            context: 额外上下文

        Returns:
            SkillResult
        """
        ...

    def get_skills(self, agent_name: str) -> list[str]:
        """获取 Agent 的 Skill 列表。"""
        ...
