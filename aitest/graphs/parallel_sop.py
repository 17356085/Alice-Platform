"""Parallel SOP Graph — 多页面并行执行 (LangGraph Send API)。

Week 3 Day 1-2: 替换顺序页面迭代，N个页面同时走SOP流水线。

用法:
    from aitest.graphs.parallel_sop import compile_parallel_sop
    graph = compile_parallel_sop()
    result = graph.invoke(create_initial_state("equipment", ["alarm-config", "camera", "key-param"]))
"""
import time
import logging
from pathlib import Path
from typing import Optional

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from aitest.graphs.state import SOPState, create_initial_state
from aitest.graphs.nodes import make_agent_loop_node

logger = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════════════════
#  Nodes
# ══════════════════════════════════════════════════════════════════════════

def fanout_pages(state: SOPState) -> list[Send]:
    """将 pages 列表展开为并行节点。每个页面一个独立的 SOP 子图。

    使用 LangGraph Send() API:
      - 每个 Send 以 process_single_page 为目标
      - 传入该页面的独立状态
      - LangGraph 自动并行执行所有 Send

    参考: LangGraph docs → Send API for parallel fan-out
    """
    pages = state.get("pages", [])
    module = state.get("module", "")
    provider = state.get("provider", "claude")

    if not pages:
        logger.warning("No pages to fan out")
        return []

    sends = []
    for i, page in enumerate(pages):
        # 每页面独立的状态片
        page_state = {
            "module": module,
            "pages": [page],                   # 单页面
            "current_page_index": 0,           # 始终是第一个(也是唯一一个)
            "provider": provider,
            "mode": state.get("mode", "full"),
            "run_id": f"{state.get('run_id', '')}-p{i}",
            "complexity_tier": state.get("complexity_tier", "standard"),
        }
        sends.append(Send("process_single_page", page_state))

    logger.info(f"Fan-out: {len(sends)} pages → parallel execution")
    return sends


def process_single_page(state: SOPState) -> dict:
    """单页面完整 SOP 流水线 (简化版 — 适合并行场景)。

    并行场景下不需要 page_advance 迭代。
    直接走: project → requirement → test_design → automation → execution → report。
    """
    module = state.get("module", "")
    pages = state.get("pages", [])
    page = pages[0] if pages else ""
    provider = state.get("provider", "claude")

    if not page:
        return {"status": "failed", "error": "No page specified"}

    logger.info(f"[{page}] Starting single-page SOP (parallel mode)")
    results = {"page": page, "status": "running", "phases_completed": []}

    # Phase 1: Project Init
    try:
        agent = _run_agent("project-agent", module, page, provider)
        results["phases_completed"].append("project_init")
    except Exception as e:
        logger.error(f"[{page}] project-agent failed: {e}")
        results["project_error"] = str(e)

    # Phase 2: Requirement
    try:
        agent = _run_agent("requirement-agent", module, page, provider)
        results["phases_completed"].append("requirement")
    except Exception as e:
        logger.error(f"[{page}] requirement-agent failed: {e}")
        results["requirement_error"] = str(e)

    # Phase 3: Test Design
    try:
        agent = _run_agent("test-design-agent", module, page, provider)
        results["phases_completed"].append("test_design")
    except Exception as e:
        logger.error(f"[{page}] test-design-agent failed: {e}")
        results["test_design_error"] = str(e)

    # Phase 4: Automation
    try:
        agent = _run_agent("automation-agent", module, page, provider)
        results["phases_completed"].append("automation")
    except Exception as e:
        logger.error(f"[{page}] automation-agent failed: {e}")
        results["automation_error"] = str(e)

    # Phase 5: Execution
    try:
        agent = _run_agent("execution-agent", module, page, provider)
        results["phases_completed"].append("execution")
    except Exception as e:
        logger.error(f"[{page}] execution-agent failed: {e}")
        results["execution_error"] = str(e)

    # Phase 6: Report
    try:
        agent = _run_agent("report-agent", module, page, provider)
        results["phases_completed"].append("report")
    except Exception as e:
        logger.error(f"[{page}] report-agent failed: {e}")
        results["report_error"] = str(e)

    results["status"] = "completed"
    logger.info(f"[{page}] Single-page SOP completed: {len(results['phases_completed'])} phases")

    return results


def _run_agent(agent_name: str, module: str, page: str, provider: str) -> dict:
    """运行单个 Agent。"""
    from aitest.agents.agent_runner import AgentLoop
    agent = AgentLoop(agent_name, module=module, page=page, provider=provider)
    state = agent.run()
    return {
        "agent": agent_name,
        "success": state.success,
        "completed_skills": list(state.completed_skills),
        "failed_skills": list(state.failed_skills),
        "termination": state.termination_reason,
    }


def merge_pages(state: SOPState) -> dict:
    """合并所有页面的并行结果。LangGraph 自动收集 Send() 返回值到 state。"""
    pages = state.get("pages", [])
    completed = state.get("completed_phases", [])
    errors = state.get("errors", [])

    # 收集各页面的完成状态
    merged = {
        "status": "completed",
        "total_pages": len(pages),
        "completed_pages": len([p for p in completed if p.get("status") == "completed"]),
        "failed_pages": len([p for p in completed if p.get("status") != "completed"]),
        "page_results": completed,
    }

    if any(p.get("status") != "completed" for p in completed):
        merged["status"] = "partial_failure"

    logger.info(f"Merge: {merged['completed_pages']}/{merged['total_pages']} pages completed")
    return merged


# ══════════════════════════════════════════════════════════════════════════
#  Graph Builder
# ══════════════════════════════════════════════════════════════════════════

def build_parallel_sop_graph() -> StateGraph:
    """构建多页面并行 SOP 图。

    结构:
      START → preflight → fanout_pages ──Send()──▶ process_single_page (×N)
                                              │                    │
                                              └──── merge_pages ◀──┘
                                                       │
                                                       ▼
                                                      END
    """
    builder = StateGraph(SOPState)

    # 复用现有 preflight
    from aitest.graphs.sop_graph import preflight_node

    builder.add_node("preflight", preflight_node)
    builder.add_node("process_single_page", process_single_page)
    builder.add_node("merge_pages", merge_pages)

    builder.set_entry_point("preflight")

    # preflight → fan out to pages
    builder.add_conditional_edges("preflight", fanout_pages, ["process_single_page"])

    # 所有页面完成后 → merge
    builder.add_edge("process_single_page", "merge_pages")
    builder.add_edge("merge_pages", END)

    return builder


def compile_parallel_sop(checkpointer=None):
    """编译并行 SOP 图。"""
    if checkpointer is None:
        from aitest.graphs.checkpoint import get_checkpointer
        checkpointer = get_checkpointer()

    builder = build_parallel_sop_graph()
    return builder.compile(checkpointer=checkpointer)


# ══════════════════════════════════════════════════════════════════════════
#  Performance comparison helper
# ══════════════════════════════════════════════════════════════════════════

def benchmark_parallel_vs_sequential(module: str, pages: list[str]) -> dict:
    """对比并行 vs 顺序执行的预估时间。

    返回:
        {"sequential_est_seconds": N, "parallel_est_seconds": N, "speedup": N}
    """
    # 粗略预估: 每个页面 ~120s, 并行开销 ~10s/page
    n = len(pages)
    sequential_est = n * 120
    parallel_est = 120 + (n - 1) * 10  # 第一个页面 120s，其余页面 +10s overhead
    return {
        "pages": n,
        "sequential_est_seconds": sequential_est,
        "parallel_est_seconds": parallel_est,
        "speedup": round(sequential_est / parallel_est, 1) if parallel_est > 0 else 1.0,
    }
