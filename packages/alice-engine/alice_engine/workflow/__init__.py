"""Workflow — SOP 编排层。

LangGraph 编排 + 状态管理 + 并行执行。
"""

from alice_engine.workflow.state import (
    SOPState,
    SOPMode,
    PhaseName,
    AgentName,
    GateLevel,
    GateResult,
    CommonSOPStage,
    CANONICAL_PHASES,
    create_initial_state,
    configure_paths,
    configure_behavior_pack,
)
from alice_engine.workflow.sop_graph import build_sop_graph
from alice_engine.workflow.sop_runner import SOPRunner
from alice_engine.workflow.parallel import compile_parallel_sop
from alice_engine.workflow.nodes import make_agent_loop_node

__all__ = [
    "SOPState",
    "SOPMode",
    "PhaseName",
    "AgentName",
    "GateLevel",
    "GateResult",
    "CommonSOPStage",
    "CANONICAL_PHASES",
    "create_initial_state",
    "configure_paths",
    "configure_behavior_pack",
    "build_sop_graph",
    "SOPRunner",
    "compile_parallel_sop",
    "make_agent_loop_node",
]
