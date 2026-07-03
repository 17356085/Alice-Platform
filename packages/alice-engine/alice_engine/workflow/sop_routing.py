"""SOP Routing — phase routing logic and constants.

Extracted from sop_graph.py for single-responsibility.
"""

from alice_engine.workflow.state import SOPState, CANONICAL_PHASES


# Phase → Agent 节点名映射
PHASE_TO_NODE: dict[str, str] = {
    "Project Init": "project_agent",
    "Requirement": "requirement_agent",
    "Test Design": "test_design_agent",
    "Automation": "automation_agent_pre",
    "Execute & Debug": "execution_agent",
    "Bug Analysis": "bug_analysis_agent",
    "Data Sanitization": "data_sanitization_agent",
    "Report": "report_agent",
    "Knowledge": "knowledge_agent",
}

# 所有可能的 agent 节点名
ALL_AGENT_NODES = list(PHASE_TO_NODE.values()) + ["automation_agent_post"]

# 有自定义边的节点（不在通用循环中添加条件边）
_CUSTOM_EDGE_NODES = {
    "automation_agent_pre",
    "automation_strategy_approval",
    "automation_agent_post",
    "testcase_approval",
    "testcase_quality_gate",
    "test_design_agent",
    "page_advance",
    "bug_analysis_agent",
}


def route_next_phase(state: SOPState) -> str:
    """条件边函数：根据 completed_phases + skip_phases + 执行结果 决定下一个节点。"""
    if state.get("fatal_error"):
        return "exit"

    if state.get("mode") == "status":
        return "exit"

    force_retry = state.get("force_retry_phase")
    if force_retry:
        node_name = PHASE_TO_NODE.get(force_retry)
        if node_name:
            return node_name

    completed = set(state.get("completed_phases", []))
    skipped = set(state.get("skip_phases", []))

    agent_outputs = state.get("agent_outputs", {})
    execution_failed = agent_outputs.get("execution_failed", False)
    if not execution_failed:
        exec_result = agent_outputs.get("execution-agent", {})
        if isinstance(exec_result, dict):
            execution_failed = exec_result.get("execution_failed", False) or not exec_result.get("success", True)

    for phase in CANONICAL_PHASES:
        if phase in completed or phase in skipped:
            continue
        if phase == "Bug Analysis" and not execution_failed:
            continue
        if phase == "Automation":
            from alice_engine.workflow.sop_nodes import _load_p0_modules
            p0_modules = _load_p0_modules()
            if state["module"] in p0_modules and not state.get("test_cases_approved"):
                return "testcase_approval"

        node_name = PHASE_TO_NODE.get(phase)
        if node_name:
            return node_name

    return "exit"
