"""SOPGraph — 顶层 LangGraph 编排器。

替换 full-sop.workflow.js + workflow_engine.py 的编排逻辑。

图结构:
  START → entry → preflight → cond_route ─┬→ project_agent ─→ cond_route
                                          ├→ requirement_agent ─→ cond_route
                                          ├→ test_design_agent ─→ cond_route
                                          ├→ automation_agent ─→ cond_route
                                          ├→ execution_agent ─→ cond_route
                                          ├→ bug_analysis_agent ─→ cond_route
                                          ├→ report_agent ─→ cond_route
                                          ├→ knowledge_agent ─→ cond_route
                                          └→ exit → END

模块拆分:
  - sop_preflight.py: PreflightCache + mtime 扫描
  - sop_nodes.py: 节点函数 (entry, preflight, exit, page_advance 等)
  - sop_hitl.py: HITL 审批 + 质量门禁节点
  - sop_routing.py: 路由逻辑 + 常量
  - sop_graph.py: 图构建 (本文件)
"""

import logging
from pathlib import Path

from langgraph.graph import StateGraph, END

logger = logging.getLogger(__name__)

from alice_engine.workflow.state import SOPState
from alice_engine.workflow.nodes import make_agent_loop_node

# Import from split modules
from alice_engine.workflow.sop_nodes import (
    entry_node, preflight_node, exit_node,
    data_sanitization_node, page_advance_node, _route_after_page_advance,
)
from alice_engine.workflow.sop_hitl import (
    automation_strategy_approval_node, testcase_approval_node,
    testcase_quality_gate_node, qa_loop_decision_node,
)
from alice_engine.workflow.sop_routing import (
    PHASE_TO_NODE, ALL_AGENT_NODES, _CUSTOM_EDGE_NODES, route_next_phase,
)


def _get_artifacts_dir() -> Path:
    """获取 artifacts 目录 — 通过 behavior pack 解析。"""
    pack = get_behavior_pack()
    if pack and pack.artifacts_dir:
        return pack.artifacts_dir
    return WORKSTUDY / "artifacts"


def build_sop_graph() -> StateGraph:
    """
    构建完整的 SOP 编排图。

    所有 Agent 节点使用 make_agent_loop_node (AgentLoop 作为 Skill 链的唯一执行引擎)。
    execution/report/knowledge 使用 LangGraph 子图。
    bug-analysis 保留 HITL interrupt + 自动循环修复。

    返回:
        未编译的 StateGraph（调用者负责 compile + checkpointer）
    """
    builder = StateGraph(SOPState)

    # ── 添加节点 ──
    builder.add_node("entry", entry_node)
    builder.add_node("preflight", preflight_node)

    # ── P0-1 架构统一: AgentLoop 作为 Skill 链的唯一执行引擎 ──
    # project / requirement / test-design → make_agent_loop_node (完整链)
    builder.add_node("project_agent", make_agent_loop_node("project-agent"))
    builder.add_node("requirement_agent", make_agent_loop_node("requirement-agent"))
    builder.add_node("test_design_agent", make_agent_loop_node("test-design-agent"))

    # P1-3 HITL: automation-agent 拆分为 pre/approval/post 三段
    # pre:  tech-analysis + auto-strategy
    # approval: HITL interrupt（人工审批 AUTO_STRATEGY.md）
    # post: page-object-generator + test-script-generator + code-consistency-checker
    builder.add_node("automation_agent_pre", make_agent_loop_node(
        "automation-agent",
        skill_subset=["automation/tech-analysis", "automation/auto-strategy"],
    ))
    builder.add_node("automation_strategy_approval", automation_strategy_approval_node)
    builder.add_node("automation_agent_post", make_agent_loop_node(
        "automation-agent",
        skill_subset=[
            "automation/page-object-generator",
            "automation/test-script-generator",
            "automation/code-consistency-checker",
        ],
        use_context_agent=True,  # ContextAgent: 只看本页 context，省 70%+ token
    ))

    # P1-3 HITL: P0 模块测试用例审批节点
    builder.add_node("testcase_approval", testcase_approval_node)

    # P2-5: 业务覆盖质量门禁 (L3 Validator)
    builder.add_node("testcase_quality_gate", testcase_quality_gate_node)

    # ★ 页面迭代节点：automation_agent_post 完成后推进 current_page_index
    builder.add_node("page_advance", page_advance_node)

    # execution / report / knowledge → 保留 execution_graph
    from alice_engine.workflow.execution_graph import (
        build_execution_subgraph,
        build_report_subgraph,
        build_knowledge_subgraph,
    )
    builder.add_node("execution_agent", build_execution_subgraph().compile())
    builder.add_node("report_agent", build_report_subgraph().compile())
    builder.add_node("knowledge_agent", build_knowledge_subgraph().compile())

    # bug-analysis → 保留（HITL interrupt + 自动循环修复，无法用 AgentLoop 替代）
    from alice_engine.workflow.bug_analysis_graph import build_bug_analysis_compiled
    builder.add_node("bug_analysis_agent", build_bug_analysis_compiled())

    # H5: QA Loop decision node — Bug Analysis 后的状态机
    builder.add_node("qa_loop_decision", qa_loop_decision_node)

    # data-sanitization → 清理节点（离线扫描残留数据，不调用 LLM）
    builder.add_node("data_sanitization_agent", data_sanitization_node)

    builder.add_node("exit", exit_node)

    # ── 添加边 ──
    builder.set_entry_point("entry")
    builder.add_edge("entry", "preflight")

    # 条件路由映射
    all_routable_nodes = list(ALL_AGENT_NODES) + list(_CUSTOM_EDGE_NODES) + ["page_advance"]
    route_map = {name: name for name in all_routable_nodes}
    route_map["exit"] = "exit"

    # preflight → 条件路由
    builder.add_conditional_edges("preflight", route_next_phase, route_map)

    # 每个 Agent 完成后 → 条件路由（跳过有自定义边的节点）
    for node_name in ALL_AGENT_NODES:
        if node_name not in _CUSTOM_EDGE_NODES:
            builder.add_conditional_edges(node_name, route_next_phase, route_map)

    # ── P1-3 HITL: 定制边覆盖（后添加 → 优先）──
    # automation-agent 内部管线: pre → approval → post
    builder.add_edge("automation_agent_pre", "automation_strategy_approval")
    builder.add_conditional_edges(
        "automation_strategy_approval",
        lambda s: "automation_agent_post" if s.get("auto_strategy_approved") else "exit",
        {"automation_agent_post": "automation_agent_post", "exit": "exit"},
    )

    # testcase_approval → automation_agent_pre（审批通过）/ exit（拒绝）
    builder.add_conditional_edges(
        "testcase_approval",
        lambda s: "automation_agent_pre" if s.get("test_cases_approved") else "exit",
        {"automation_agent_pre": "automation_agent_pre", "exit": "exit"},
    )

    # ★ 页面迭代路由: automation_agent_post → page_advance → next page or next phase
    builder.add_edge("automation_agent_post", "page_advance")
    builder.add_conditional_edges(
        "page_advance",
        _route_after_page_advance,
        {**route_map, "automation_agent_pre": "automation_agent_pre"},
    )

    # ── H5: QA Loop 路由 ──
    # bug_analysis_agent → qa_loop_decision (state machine) → next
    builder.add_edge("bug_analysis_agent", "qa_loop_decision")
    builder.add_conditional_edges(
        "qa_loop_decision",
        lambda s: s.get("qa_loop_decision", "next_phase"),
        {
            "automation": "automation_agent_pre",
            "report": "report_agent",
            "next_phase": "data_sanitization_agent",  # canonical next after Bug Analysis
        },
    )

    # ── P2-5 业务覆盖质量门禁路由 ──
    # test_design_agent → testcase_quality_gate（优先于通用条件的定制边）
    builder.add_edge("test_design_agent", "testcase_quality_gate")
    # quality_gate → page_advance（页面迭代）/ test_design_agent（打回重做）/ route_next_phase（所有页面完成）
    def _route_quality_gate(state):
        if not state.get("test_cases_approved") or state.get("force_retry_phase") == "Test Design":
            return "test_design_agent"
        # 页面迭代: 如果还有页面未处理，推进到下一页
        pages = state.get("pages", [])
        idx = state.get("current_page_index", 0)
        if idx < len(pages) - 1:
            return "page_advance"
        return route_next_phase(state)
    builder.add_conditional_edges(
        "testcase_quality_gate",
        _route_quality_gate,
        {**route_map, "test_design_agent": "test_design_agent", "page_advance": "page_advance"},
    )

    # exit → END
    builder.add_edge("exit", END)

    return builder




def build_compiled_graph(checkpointer=None):
    """
    构建并编译完整的 SOP 图（便捷函数）。

    参数:
        checkpointer: SqliteSaver 实例（默认：创建新的）

    返回:
        编译后的 CompiledGraph
    """
    if checkpointer is None:
        from alice_engine.runtime.checkpoint import CheckpointManager; get_checkpointer = lambda: CheckpointManager(".").get_checkpointer()
        checkpointer = get_checkpointer()

    builder = build_sop_graph()
    return builder.compile(checkpointer=checkpointer)


# ══════════════════════════════════════════════════════════════════════════
#  ★ v2.0: Complexity Routing — 自适应 SOP 流水线
# ══════════════════════════════════════════════════════════════════════════



def resolve_sop_pipeline(module: str, pages: list[str] = None,
                         discovery_data: dict = None) -> dict:
    """根据页面复杂度推荐 SOP 流水线。

    用法:
        result = resolve_sop_pipeline("equipment", ["alarm-config"])
        # → {"tier": "standard", "pipeline": ["requirement-agent", ...], "estimated_tokens": 100000}

    三档:
      - SIMPLE:   2 agent (automation + execution) → ~15K tokens/page
      - STANDARD: 5 agent → ~100K tokens/page
      - COMPLEX:  8 agent (完整) → ~130K tokens/page
    """
    pass  # complexity_assess removed
    pass  # ComplexityTier removed

    pages = pages or []
    result = {"module": module, "pages": {}, "overall_tier": "standard"}

    for page_slug in pages:
        # 尝试读取 discovery 数据
        page_data = {}
        page_dir = get_page_dir(module, page_slug)
        discovery_file = page_dir / ".discovery" / "pages.json" if page_dir else None
        if discovery_file and discovery_file.exists():
            try:
                import json
                with open(discovery_file) as f:
                    all_pages = json.load(f)
                page_data = _find_page_data(all_pages, page_slug)
            except Exception:
                pass

        assessment = complexity_assess(page_data, page_title=page_slug)
        result["pages"][page_slug] = assessment

    # 整体复杂度 = max(各页面复杂度)
    tiers = [p["tier"] for p in result["pages"].values()]
    if "complex" in tiers:
        result["overall_tier"] = "complex"
    elif "standard" in tiers:
        result["overall_tier"] = "standard"
    else:
        result["overall_tier"] = "simple"

    # 汇总 pipeline
    pass  # pipeline_for_tier removed
    all_tiers = set(tiers)
    if len(all_tiers) == 1:
        tier = ComplexityTier(list(all_tiers)[0])
    elif "complex" in all_tiers:
        tier = ComplexityTier.COMPLEX
    elif "standard" in all_tiers:
        tier = ComplexityTier.STANDARD
    else:
        tier = ComplexityTier.SIMPLE

    result["pipeline"] = pipeline_for_tier(tier)
    result["estimated_tokens_per_page"] = {
        "simple": 15000, "standard": 100000, "complex": 130000,
    }[tier.value]

    return result




def _find_page_data(all_pages: list, page_slug: str) -> dict:
    """从 pages.json 中找到指定 page 的数据。"""
    for p in all_pages:
        name = p.get("slug", p.get("name", p.get("title", "")))
        if page_slug in name or name in page_slug:
            return p
    return all_pages[0] if all_pages else {}
