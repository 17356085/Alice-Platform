"""
aitest/graphs — LangGraph 编排层 (P0-1 统一架构)

用 LangGraph StateGraph 做顶层 Phase 编排，AgentLoop 作为 Skill 链唯一执行引擎。

结构 (P0-1 重构后):
  state.py              — 共享 TypedDict + dataclass
  checkpoint.py         — SqliteSaver 工厂
  nodes.py              — 共享节点工厂 (含 make_agent_loop_node)
  sop_graph.py          — ★ 顶层编排器
  bug_analysis_graph.py — HITL 自动循环修复 (保留)
  execution_graph.py    — execution/report/knowledge (保留: EventBus + RAG)
  _archived/            — P0-1 归档: project/requirement/test-design/automation SubGraphs

用法:
  from aitest.graphs.sop_graph import build_sop_graph
  graph = build_sop_graph().compile(checkpointer=...)
  result = graph.invoke(initial_state, config)
"""

from aitest.graphs.state import (
    SOPState,
    SOPMode,
    PhaseName,
    GateResult,
    GateLevel,
    SkillObservation,
    AgentResult,
)
from aitest.graphs.checkpoint import (
    get_checkpointer,
    list_runs,
    CHECKPOINT_DIR,
    DB_PATH,
)

from aitest.graphs.nodes import make_agent_loop_node

from aitest.graphs.sop_graph import (
    build_sop_graph,
    build_compiled_graph,
)

__all__ = [
    "SOPState",
    "SOPMode",
    "PhaseName",
    "GateResult",
    "GateLevel",
    "SkillObservation",
    "AgentResult",
    "get_checkpointer",
    "list_runs",
    "CHECKPOINT_DIR",
    "DB_PATH",
    "build_sop_graph",
    "build_compiled_graph",
    "make_agent_loop_node",
]
