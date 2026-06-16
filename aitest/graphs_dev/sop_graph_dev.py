"""
DevSOPGraph — 开发 SOP LangGraph 编排器 (完整版 9 Agent / 10 Phase)。

图结构:
  START → entry → cond_route ─┬→ pm_agent → cond_route
                              ├→ req_agent → cond_route
                              ├→ arch_agent → cond_route
                              ├→ design_agent → cond_route
                              ├→ frontend_agent → cond_route
                              ├→ backend_agent → cond_route
                              ├→ review_agent → cond_route
                              ├→ dev_test_agent → cond_route
                              ├→ debug_agent → cond_route
                              ├→ build_agent → cond_route
                              └→ exit → END

Phase 流水线: Plan → Requirements → Architecture → Component Design
  → Frontend Impl → Backend Impl → Code Review → Dev Test → Debug & Fix → Build
"""

from pathlib import Path
from langgraph.graph import StateGraph, END
from aitest.graphs_dev.state_dev import (
    DEV_CANONICAL_PHASES, DEV_PHASE_TO_NODE, ALL_DEV_AGENT_NODES,
    DEV_MODE_SKIP_MAP, DevPhaseName,
)

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
CONTEXT_DEV = GOVERNANCE / "context" / "projects" / "dev-platform"


# ═══════════════════════════════════════════════════════════════
# Entry / Exit nodes
# ═══════════════════════════════════════════════════════════════

def entry_node(state: dict) -> dict:
    mode = state.get("mode", "full")
    skip_phases = list(DEV_MODE_SKIP_MAP.get(mode, []))
    return {"skip_phases": skip_phases, "current_phase": "Plan", "status": "running"}


def exit_node(state: dict) -> dict:
    completed = state.get("completed_phases", [])
    failed = state.get("failed_phases", [])
    fatal = state.get("fatal_error")
    if fatal:
        final_status = "failed"
    elif failed:
        final_status = "completed_with_issues"
    else:
        final_status = "completed"
    return {
        "status": final_status,
        "current_phase": "Complete",
        "fatal_error": fatal if final_status == "failed" else None,
    }


# ═══════════════════════════════════════════════════════════════
# Conditional routing
# ═══════════════════════════════════════════════════════════════

def dev_route_next_phase(state: dict) -> str:
    if state.get("fatal_error"):
        return "exit"
    if state.get("mode") == "status":
        return "exit"

    completed = set(state.get("completed_phases", []))
    skipped = set(state.get("skip_phases", []))
    agent_outputs = state.get("agent_outputs", {})

    # Debug & Fix: only trigger if review found issues
    review_result = agent_outputs.get("review-agent", {})
    has_issues = isinstance(review_result, dict) and not review_result.get("success", True)

    for phase in DEV_CANONICAL_PHASES:
        if phase in completed or phase in skipped:
            continue
        if phase == "Debug & Fix" and not has_issues:
            continue  # Skip debug if no issues
        node_name = DEV_PHASE_TO_NODE.get(phase)
        if node_name:
            return node_name
    return "exit"


# ═══════════════════════════════════════════════════════════════
# Graph builder
# ═══════════════════════════════════════════════════════════════

def build_dev_sop_graph() -> StateGraph:
    builder = StateGraph(dict)

    from aitest.graphs.nodes import make_agent_loop_node

    # ── Entry / Exit ──
    builder.add_node("entry", entry_node)
    builder.add_node("exit", exit_node)

    # ── Agent nodes ──
    builder.add_node("pm_agent", make_agent_loop_node("pm-agent"))
    builder.add_node("req_agent", make_agent_loop_node("req-agent"))
    builder.add_node("arch_agent", make_agent_loop_node("arch-agent"))
    builder.add_node("design_agent", make_agent_loop_node("design-agent"))
    builder.add_node("frontend_agent", make_agent_loop_node("frontend-agent"))
    builder.add_node("backend_agent", make_agent_loop_node("backend-agent"))
    builder.add_node("review_agent", make_agent_loop_node("review-agent"))
    builder.add_node("dev_test_agent", make_agent_loop_node("dev-test-agent"))
    builder.add_node("debug_agent", make_agent_loop_node("debug-agent"))
    builder.add_node("build_agent", make_agent_loop_node("build-agent"))

    # ── Edges ──
    builder.set_entry_point("entry")
    route_map = {name: name for name in ALL_DEV_AGENT_NODES}
    route_map["exit"] = "exit"

    builder.add_conditional_edges("entry", dev_route_next_phase, route_map)
    for node_name in ALL_DEV_AGENT_NODES:
        builder.add_conditional_edges(node_name, dev_route_next_phase, route_map)
    builder.add_edge("exit", END)

    return builder


def build_compiled_dev_graph(checkpointer=None):
    if checkpointer is None:
        from aitest.graphs.checkpoint import get_checkpointer
        checkpointer = get_checkpointer()
    return build_dev_sop_graph().compile(checkpointer=checkpointer)
