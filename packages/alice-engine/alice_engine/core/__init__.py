"""Core — Engine 核心逻辑。

包含:
  - AgentLoop: Agent 执行循环接口
  - Planner: 规划引擎
  - Task: 数据结构 (Observation, AgentState, AgentEvent)
  - StateMachine: Task 状态机
  - SkillLoader: Skill 加载
  - SkillExecutorImpl: Skill 执行实现
  - ToolProvider: 工具调用接口
"""

from alice_engine.core.task import Observation, AgentState, AgentEvent, AgentEventType, ArtifactRule
from alice_engine.core.state_machine import TaskState, TaskStateContext, update_agent_state
from alice_engine.core.agent_loop import AgentLoopConfig, AgentLoopProtocol, SkillResult
from alice_engine.core.tool_provider import ToolProvider, ToolDef, ToolResult

# v3.1: skill_executor 模块不存在，改为从 skill_executor_impl 导入
try:
    from alice_engine.core.skill_executor_impl import SkillExecutorImpl
except ImportError:
    SkillExecutorImpl = None

__all__ = [
    # Task
    "Observation",
    "AgentState",
    "AgentEvent",
    "AgentEventType",
    "ArtifactRule",
    # StateMachine
    "TaskState",
    "TaskStateContext",
    "update_agent_state",
    # AgentLoop
    "AgentLoopConfig",
    "AgentLoopProtocol",
    "SkillResult",
    # SkillExecutor
    "SkillExecutorImpl",
    # ToolProvider
    "ToolProvider",
    "ToolDef",
    "ToolResult",
]
