"""Parallel SOP Graph — 多页面并行执行 (LangGraph Send API)。

Week 3 Day 1-2: 替换顺序页面迭代，N个页面同时走SOP流水线。

用法:
    from alice_engine.workflow.parallel import compile_parallel_sop
    graph = compile_parallel_sop()
    result = graph.invoke(create_initial_state("equipment", ["alarm-config", "camera", "key-param"]))
"""
import time
import logging
from pathlib import Path
from typing import Optional

from langgraph.graph import StateGraph, END
from langgraph.types import Send

from alice_engine.workflow.state import SOPState, create_initial_state, CANONICAL_PHASES
from alice_engine.workflow.nodes import make_agent_loop_node
from alice_engine.workflow.sop_nodes import preflight_node

logger = logging.getLogger(__name__)

# ── Phase slug → canonical PhaseName mapping ──
_PHASE_SLUG_TO_CANONICAL: dict[str, str] = {
    "project_init": "Project Init",
    "requirement": "Requirement",
    "test_design": "Test Design",
    "automation": "Automation",
    "execution": "Execute & Debug",
    "bug_analysis": "Bug Analysis",
    "data_sanitization": "Data Sanitization",
    "report": "Report",
    "knowledge": "Knowledge",
}

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

    返回仅包含有 reducer 的键 (per_page_results, completed_phases)，
    避免覆盖父 state 的共享字段 (status 等)。

    H7 fix: 任一 phase 失败 → 停止后续 phase，标记页面为 failed。
    C6 fix: 使用规范 PhaseName 而非 slug。
    """
    module = state.get("module", "")
    pages = state.get("pages", [])
    page = pages[0] if pages else ""
    provider = state.get("provider", "claude")

    if not page:
        return {
            "per_page_results": [{"page": "unknown", "status": "failed", "error": "No page specified"}],
        }

    logger.info(f"[{page}] Starting single-page SOP (parallel mode)")
    phases_completed: list[str] = []
    errors: dict[str, str] = {}
    first_failure: str = ""

    phases: list[tuple[str, str]] = [
        ("project_init", "project-agent"),
        ("requirement", "requirement-agent"),
        ("test_design", "test-design-agent"),
        ("automation", "automation-agent"),
        ("execution", "execution-agent"),
        ("report", "report-agent"),
    ]

    for phase_slug, agent_name in phases:
        try:
            _run_agent(agent_name, module, page, provider)
            canonical = _PHASE_SLUG_TO_CANONICAL.get(phase_slug, phase_slug)
            phases_completed.append(canonical)
        except Exception as e:
            logger.error(f"[{page}] {agent_name} failed: {e}")
            errors[f"{phase_slug}_error"] = str(e)
            if not first_failure:
                first_failure = f"{agent_name}: {e}"
            # H7: 错误传播 — 失败后停止后续 phase
            break

    # 判断页面状态
    total_expected = len(phases)
    actual_done = len(phases_completed)
    if actual_done == total_expected:
        page_status = "completed"
    elif actual_done == 0:
        page_status = "failed"
    else:
        page_status = "partial"
    logger.info(
        f"[{page}] Single-page SOP {page_status}: {actual_done}/{total_expected} phases"
        + (f" (first failure: {first_failure})" if first_failure else "")
    )

    page_result = {
        "page": page,
        "status": page_status,
        "phases_completed": phases_completed,
        "first_failure": first_failure,
        **errors,
    }
    # per_page_results: Annotated[List[Dict], operator.add] — 跨页面累积
    # completed_phases: Annotated[List[PhaseName], _unique_list] — 跨页面累积
    return {
        "per_page_results": [page_result],
        "completed_phases": phases_completed,
    }


def _run_agent(agent_name: str, module: str, page: str, provider: str) -> dict:
    """运行单个 Agent。"""
    from alice_engine.core.executor import AgentLoop
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
    """合并所有页面的并行结果。per_page_results 通过 operator.add reducer 累积。

    C6 fix: 不覆盖顶层 status (SOPState.status 语义不同)。
    写入 agent_outputs["parallel_merge"] 供下游读取。
    """
    pages = state.get("pages", [])
    page_results = state.get("per_page_results", [])

    completed = [p for p in page_results if p.get("status") == "completed"]
    failed = [p for p in page_results if p.get("status") == "failed"]
    partial = [p for p in page_results if p.get("status") == "partial"]

    merged_status = "completed" if len(failed) == 0 and len(partial) == 0 else \
                    "partial_failure" if len(completed) > 0 else "all_failed"

    merge_result = {
        "parallel_status": merged_status,
        "total_pages": len(pages),
        "completed_pages": len(completed),
        "failed_pages": len(failed),
        "partial_pages": len(partial),
        "page_results": page_results,
    }

    logger.info(
        f"Merge: {merge_result['completed_pages']}/{merge_result['total_pages']} completed, "
        f"{merge_result['failed_pages']} failed, {merge_result['partial_pages']} partial"
    )

    # Write to agent_outputs to avoid overwriting SOPState.status (which is
    # "running"|"completed"|"failed"|"paused" — different semantic space)
    existing_outputs = state.get("agent_outputs", {})
    return {
        "agent_outputs": {**existing_outputs, "parallel_merge": merge_result},
    }


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
        from alice_engine.runtime.checkpoint import CheckpointManager; get_checkpointer = lambda: CheckpointManager(".").get_checkpointer()
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
