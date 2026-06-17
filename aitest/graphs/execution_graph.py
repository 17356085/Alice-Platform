"""
execution + report + knowledge Agent LangGraph SubGraphs。

每个 Agent 使用真正的 Skill 节点（非 AgentLoop 黑盒），
让 LangGraph 对每个 Skill 的执行状态可见。
"""

from pathlib import Path
from typing import Literal

from langgraph.graph import StateGraph, END

from aitest.graphs.state import SOPState, GateResult, GateLevel

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
ZJSN_TEST = WORKSTUDY / "ZJSN_Test-master526"
GOVERNANCE = WORKSTUDY / "governance"


def _get_page(state: dict) -> str:
    pages = state.get("pages", [])
    idx = state.get("current_page_index", 0)
    if pages and idx < len(pages):
        return pages[idx]
    return ""


# ══════════════════════════════════════════════════════════════════════════
#  execution-agent: 运行 pytest（特殊——需要子进程，保留 AgentLoop）
# ══════════════════════════════════════════════════════════════════════════

def exec_entry(state: SOPState) -> dict:
    return {"current_phase": "Execute & Debug"}


def exec_act(state: SOPState) -> dict:
    """运行 pytest 测试。使用 AgentLoop 因为需要管理子进程。"""
    from aitest.agents.agent_runner import AgentLoop

    page = _get_page(state)
    agent = AgentLoop(
        "execution-agent",
        provider=state.get("provider", "claude"),
        module=state["module"],
        page=page,
        verbose=False,
    )
    result = agent.run()

    observations = []
    for obs in result.observations:
        observations.append(obs.to_dict() if hasattr(obs, 'to_dict') else obs)

    # 检测执行失败
    exec_failed = bool(result.failed_skills and len(result.failed_skills) > 0)

    return {
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            "execution-agent": result.to_dict(),
            "execution_failed": exec_failed,
        },
        "skill_observations": observations,
        "completed_skills": [s for s in result.completed_skills],
    }


def exec_gate(state: SOPState) -> dict:
    module = state["module"]
    allure_dir = ZJSN_TEST / "allure-results"
    ok = allure_dir.exists() and any(allure_dir.iterdir())
    return {"gate_results": [GateResult(
        level=GateLevel.L2_AGENT, phase="Execute & Debug", ok=ok,
        message=f"Execution gate: {'PASS' if ok else 'WARN'}",
        details={"allure_dir": str(allure_dir)},
    ).to_dict()]}


def exec_exit(state: SOPState) -> dict:
    return {"completed_phases": ["Execute & Debug"]}


def build_execution_subgraph() -> StateGraph:
    builder = StateGraph(SOPState)
    builder.add_node("entry", exec_entry)
    builder.add_node("act", exec_act)
    builder.add_node("gate", exec_gate)
    builder.add_node("exit", exec_exit)
    builder.set_entry_point("entry")
    builder.add_edge("entry", "act")
    builder.add_edge("act", "gate")
    builder.add_edge("gate", "exit")
    builder.add_edge("exit", END)
    return builder


# ══════════════════════════════════════════════════════════════════════════
#  report-agent: 1-2 skills → 轻量 Skill 节点
# ══════════════════════════════════════════════════════════════════════════

REPORT_SKILLS = ["reporting/report-generator", "reporting/excel-exporter"]


def _single_skill_act(state: dict, skill_id: str) -> dict:
    """单 Skill 执行（无循环，report 和 knowledge 各 1-2 个 skill）。"""
    from aitest.agents.agent_runner import run_skill

    module = state["module"]
    page = _get_page(state)
    provider = state.get("provider", "claude")

    response = run_skill(
        skill_id=skill_id,
        user_input=f"Module: {module}, Page: {page}",
        provider=provider,
        context_vars={"module": module, "page": page},
    )

    return {
        "current_skill": skill_id,
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            f"skill_{skill_id.replace('/', '_')}": {
                "content_preview": response.content[:500] if response.content else "",
                "token_usage": response.token_usage,
                "finish_reason": response.finish_reason,
            },
        },
        "completed_skills": [skill_id],
    }


def report_entry(state: SOPState) -> dict:
    return {"current_phase": "Report"}


def report_act(state: SOPState) -> dict:
    return _single_skill_act(state, "reporting/report-generator")


def report_act2(state: SOPState) -> dict:
    """可选的 Excel 导出。"""
    return _single_skill_act(state, "reporting/excel-exporter")


def report_exit(state: SOPState) -> dict:
    return {"completed_phases": ["Report"]}


def build_report_subgraph() -> StateGraph:
    builder = StateGraph(SOPState)
    builder.add_node("entry", report_entry)
    builder.add_node("act", report_act)
    builder.add_node("exit", report_exit)
    builder.set_entry_point("entry")
    builder.add_edge("entry", "act")
    builder.add_edge("act", "exit")
    builder.add_edge("exit", END)
    return builder


# ══════════════════════════════════════════════════════════════════════════
#  knowledge-agent: 1 skill + 事件总线处理
# ══════════════════════════════════════════════════════════════════════════

def knowledge_entry(state: SOPState) -> dict:
    return {"current_phase": "Knowledge"}


def knowledge_act(state: SOPState) -> dict:
    """知识沉淀 + 事件总线处理 + RAG 增量索引。"""
    result = _single_skill_act(state, "knowledge/knowledge-manager")

    # 处理事件总线积压
    try:
        from aitest.governance.event_bus import process_pending
        processed = process_pending()
        result["agent_outputs"]["events_processed"] = len(processed)
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("execution_graph.knowledge", "event_bus_process", e, {"module": state["module"]})

    # P2-8: RAG 索引增量更新 — 仅变更时重建，避免每次全量重索引
    # known_issues / tech_analysis / page_context 均支持 mtime 检测
    # 此处显式调用确保周期结束时所有 collection 都是最新的。
    module = state["module"]
    indexed = {}
    try:
        from aitest.knowledge.rag_engine import (
            _ensure_known_issues_synced,
            _ensure_tech_analysis_synced,
            _ensure_page_context_synced,
        )
        indexed["known_issues_updated"] = _ensure_known_issues_synced()
        indexed["tech_analysis_updated"] = _ensure_tech_analysis_synced()
        indexed["page_context_updated"] = _ensure_page_context_synced()
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("execution_graph.knowledge", "rag_index", e, {"module": state["module"]})

    if indexed:
        result["agent_outputs"]["rag_indexed"] = indexed

    return result


def knowledge_exit(state: SOPState) -> dict:
    return {"completed_phases": ["Knowledge"]}


def build_knowledge_subgraph() -> StateGraph:
    builder = StateGraph(SOPState)
    builder.add_node("entry", knowledge_entry)
    builder.add_node("act", knowledge_act)
    builder.add_node("exit", knowledge_exit)
    builder.set_entry_point("entry")
    builder.add_edge("entry", "act")
    builder.add_edge("act", "exit")
    builder.add_edge("exit", END)
    return builder
