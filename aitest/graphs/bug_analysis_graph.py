"""
bug-analysis-agent LangGraph SubGraph — 自动循环修复 + Human-in-the-Loop。

图结构:
  analyze_fail → auto_fix → request_approval ─┬─approved→ verify ─┬─cycle<3→ analyze_fail
                                               │                    └─cycle=3→ report
                                               └─rejected→ report → exit

核心特性:
  - 最多 3 次自动修复循环
  - Human-in-the-loop：修复方案需人工审批
  - RAG 已知问题匹配
  - 修复后自动重跑测试验证
"""

from pathlib import Path
from typing import Literal

from langgraph.graph import StateGraph, END
from langgraph.types import interrupt

from aitest.graphs.state import SOPState, GateResult, GateLevel

from aitest.platform.paths import get_workstudy, get_test_project_root, get_governance_dir
WORKSTUDY = get_workstudy()
GOVERNANCE = get_governance_dir()


def _get_first_page(state: dict) -> str:
    """获取第一个页面 slug。"""
    pages = state.get("pages", [])
    return pages[0] if pages else ""


# ══════════════════════════════════════════════════════════════════════════
#  节点函数
# ══════════════════════════════════════════════════════════════════════════

def bug_entry(state: SOPState) -> dict:
    """入口：初始化 Bug 分析循环。"""
    return {
        "current_phase": "Bug Analysis",
        "bug_cycle_count": 0,
        "fix_approved": None,
        "interrupt_requested": False,
    }


def _classify_for_qa_loop(error_text: str, analysis_text: str = "") -> dict:
    """
    🆕 TLO QA Loop: 分类失败根因 → 决定 auto-fixable vs escalate。

    复用 QALoop 的 6 类分类逻辑。轻量级规则匹配，之后可升级为 LLM 分类。
    """
    text = (error_text + " " + analysis_text).lower()

    # LOCATOR_STALE: NoSuchElement, selector, xpath, css selector
    if any(kw in text for kw in ["nosuchelement", "no such element", "unable to locate",
                                   "selector", "xpath", "css selector"]):
        return dict(auto_fixable=True, root_cause="locator_stale", confidence=0.85,
                    suggested_fix="Update locator: check DOM for changed class/id/attribute")

    # TIMING_ISSUE: timeout, wait, stale element, not clickable
    if any(kw in text for kw in ["timeout", "timed out", "wait", "stale element",
                                   "not clickable", "not visible", "element not interactable"]):
        return dict(auto_fixable=True, root_cause="timing_issue", confidence=0.80,
                    suggested_fix="Increase WebDriverWait timeout or add explicit wait")

    # DATA_STALE: assertion, expected vs actual mismatch
    if any(kw in text for kw in ["assertion", "assert", "expected", "actual", "not equal", "mismatch"]):
        return dict(auto_fixable=True, root_cause="data_stale", confidence=0.70,
                    suggested_fix="Check test data values. Update expected values or regenerate test data.")

    # ENV_DOWN: connection refused, 500/502/503, gateway, unreachable
    if any(kw in text for kw in ["connection refused", "503", "502", "500",
                                   "gateway", "unreachable", "dns", "name or service not known"]):
        return dict(auto_fixable=False, root_cause="env_down", confidence=0.90,
                    suggested_fix="Target system unavailable. Verify service status.")

    # REAL_DEFECT: unexpected behavior that looks like a real bug
    if any(kw in text for kw in ["attributeerror", "typeerror", "keyerror", "indexerror",
                                   "null", "undefined", "not found in database"]):
        return dict(auto_fixable=False, root_cause="real_defect", confidence=0.60,
                    suggested_fix="Possible real defect. Manual investigation recommended.")

    # UNKNOWN
    return dict(auto_fixable=False, root_cause="unknown", confidence=0.30,
                suggested_fix="Manual investigation needed — error pattern not recognized")


def analyze_fail_node(state: SOPState) -> dict:
    """
    分析失败根因：RAG 匹配 + 深度分析。

    1. 搜索已知问题 (RAG)
    2. 如果没有匹配 → LLM 深度分析
    3. 汇总分析结果
    """
    module = state["module"]
    page = _get_first_page(state)

    # ── RAG 匹配已知问题 (本模块 + 跨模块) ──
    # ★ P0-2: 共享 ChromaDB client，避免重复创建连接+加载 embedding 模型
    rag_matches = []
    cross_module_hits = []
    try:
        from aitest.knowledge.rag_engine import search_known_issues, search_context, get_chroma_client

        _chroma_client = get_chroma_client()

        # 构造查询
        agent_outputs = state.get("agent_outputs", {})
        exec_result = agent_outputs.get("execution-agent", {})
        error_context = ""
        if isinstance(exec_result, dict) and exec_result.get("termination_reason"):
            error_context = exec_result["termination_reason"]

        query = f"module={module} page={page} {error_context}"

        # 1. 搜索已知问题（不限模块）
        rag_matches = search_known_issues(query, n_results=5, client=_chroma_client)

        # 2. 跨模块搜索：其他模块的技术分析中是否有类似模式
        cross_module_hits = search_context(
            query, collection_name="tech_analysis", n_results=5, client=_chroma_client
        )
        # 过滤掉当前模块（已在上面覆盖）
        cross_module_hits = [
            h for h in cross_module_hits
            if h.get("metadata", {}).get("module", "") != module
        ][:3]

        # 3. 跨模块搜索：其他模块的页面分析（相似 UI 组件）
        page_hits = search_context(
            query, collection_name="page_context", n_results=3, client=_chroma_client
        )
        page_hits = [
            h for h in page_hits
            if h.get("metadata", {}).get("module", "") != module
        ][:2]

    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("bug_analysis.analyze_fail", "rag_search", e, {"module": module, "page": page})

    # ── LLM 深度分析 ──
    from aitest.agents.agent_runner import run_skill

    cross_module_context = ""
    if cross_module_hits:
        cross_module_context = "\n跨模块相似问题:\n" + "\n".join(
            f"  - [{h.get('metadata', {}).get('module', '?')}] {h.get('document', '')[:200]}"
            for h in cross_module_hits
        )
    if page_hits:
        cross_module_context += "\n跨模块相似UI模式:\n" + "\n".join(
            f"  - [{h.get('metadata', {}).get('module', '?')}] {h.get('document', '')[:200]}"
            for h in page_hits
        )

    analysis_input = f"""模块: {module}, 页面: {page}
已知问题匹配: {len(rag_matches)} 条
{cross_module_context}
执行结果: {exec_result}
失败技能: {state.get('failed_skills', {})}"""

    response = run_skill(
        skill_id="diagnosis/bug-analysis",
        user_input=analysis_input,
        provider=state.get("provider", "claude"),
        context_vars={"module": module, "page": page},
    )

    # 🆕 TLO QA Loop: 分类失败是否可自动修复
    qa_classification = _classify_for_qa_loop(
        error_text=str(exec_result),
        analysis_text=response.content[:2000] if response.content else "",
    )

    return {
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            "bug_analysis": {
                "rag_matches": [{"id": m["id"], "document": m.get("document", "")[:200]} for m in rag_matches],
                "rag_match_count": len(rag_matches),
                "deep_analysis": response.content[:2000] if response.content else "",
                "all_known": all(
                    m.get("metadata", {}).get("has_fix", False) for m in rag_matches
                ) if rag_matches else False,
                # 🆕 QA Loop classification
                "qa_auto_fixable": qa_classification.get("auto_fixable", False),
                "qa_root_cause": qa_classification.get("root_cause", "unknown"),
                "qa_confidence": qa_classification.get("confidence", 0.0),
                "qa_suggested_fix": qa_classification.get("suggested_fix", ""),
            },
        },
        # 🆕 TLO: 不可自动修复 → 升级
        "qa_should_escalate": not qa_classification.get("auto_fixable", False),
    }


def auto_fix_node(state: SOPState) -> dict:
    """
    自动生成修复代码。

    基于分析结果，调用 automation-agent 的 fix 模式。
    """
    module = state["module"]
    page = _get_first_page(state)
    analysis = state.get("agent_outputs", {}).get("bug_analysis", {})

    # 构造修复输入
    fix_input_parts = [f"模块: {module}, 页面: {page}"]
    if analysis.get("deep_analysis"):
        fix_input_parts.append(f"根因分析:\n{analysis['deep_analysis'][:1500]}")
    if analysis.get("rag_matches"):
        fix_input_parts.append(f"已知修复:\n{analysis['rag_matches']}")

    from aitest.agents.agent_runner import run_skill

    # 使用 automation 相关的修复 skill
    response = run_skill(
        skill_id="automation/page-object-generator",
        user_input="\n\n".join(fix_input_parts),
        provider=state.get("provider", "claude"),
        context_vars={
            "module": module,
            "page": page,
            "mode": "fix",  # 修复模式
        },
    )

    cycle = state.get("bug_cycle_count", 0)
    return {
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            "bug_fix": {
                "cycle": cycle,
                "fix_content": response.content[:2000] if response.content else "",
                "fix_summary": response.content[:300] if response.content else "No fix generated",
            },
        },
    }


def request_approval_node(state: SOPState) -> dict:
    """
    Human-in-the-loop：请求人工审批修复方案。

    使用 LangGraph interrupt() 挂起执行，等待人工输入。
    审批通过 → approve，拒绝 → reject。
    """
    cycle = state.get("bug_cycle_count", 0)
    bug_cycle_max = state.get("bug_cycle_max", 3)
    fix_info = state.get("agent_outputs", {}).get("bug_fix", {})
    analysis = state.get("agent_outputs", {}).get("bug_analysis", {})

    # 触发 interrupt — 执行在此暂停
    approval = interrupt({
        "type": "bug_fix_approval",
        "cycle": f"{cycle + 1}/{bug_cycle_max}",
        "module": state["module"],
        "page": _get_first_page(state),
        "analysis_summary": analysis.get("deep_analysis", "")[:300],
        "fix_summary": fix_info.get("fix_summary", "No fix generated"),
        "options": ["approve", "reject", "skip"],
    })

    approved = approval == "approve"
    return {
        "fix_approved": approved,
        "interrupt_requested": False,
        "human_input": str(approval),
    }


def verify_node(state: SOPState) -> dict:
    """
    验证修复：重新运行相关测试。

    仅当修复被批准后才执行。
    """
    if not state.get("fix_approved"):
        return {}

    module = state["module"]
    page = _get_first_page(state)

    # 运行 pytest
    import subprocess

    zjsn = get_test_project_root()
    test_file = zjsn / "script" / module / f"test_{page.replace('-', '_')}.py" if zjsn else None
    results = {"passed": False, "output": "", "error": ""}

    if test_file and test_file.exists() and zjsn:
        try:
            result = subprocess.run(
                ["pytest", str(test_file), "-v", "--tb=short"],
                cwd=str(zjsn),
                capture_output=True,
                text=True,
                timeout=120,
            )
            results["passed"] = result.returncode == 0
            results["output"] = result.stdout[-2000:] if result.stdout else ""
            results["error"] = result.stderr[-500:] if result.stderr else ""
        except subprocess.TimeoutExpired:
            results["error"] = "Test execution timed out (120s)"
        except Exception as e:
            results["error"] = str(e)

    cycle = state.get("bug_cycle_count", 0) + 1

    return {
        "bug_cycle_count": cycle,
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            "bug_verify": {
                "cycle": cycle,
                "passed": results["passed"],
                "output_preview": results["output"][:500],
            },
        },
    }


def loop_router(state: SOPState) -> Literal["loop", "report"]:
    """
    条件路由：是否继续循环。

    继续条件:
      - cycle < max (3)
      - 修复未通过验证
      - 修复被批准

    退出条件:
      - cycle >= max
      - 修复通过
      - 修复被拒绝
    """
    cycle = state.get("bug_cycle_count", 0)
    bug_cycle_max = state.get("bug_cycle_max", 3)
    approved = state.get("fix_approved")
    verify_result = state.get("agent_outputs", {}).get("bug_verify", {})

    # 被拒绝 → 立即退出
    if approved is False:
        return "report"

    # 达到最大次数 → 退出
    if cycle >= bug_cycle_max:
        return "report"

    # 验证通过 → 退出
    if verify_result.get("passed"):
        return "report"

    # 继续循环
    return "loop"


def generate_report_node(state: SOPState) -> dict:
    """生成 Bug 分析报告。"""
    cycle = state.get("bug_cycle_count", 0)
    analysis = state.get("agent_outputs", {}).get("bug_analysis", {})
    verify = state.get("agent_outputs", {}).get("bug_verify", {})
    approved = state.get("fix_approved")

    # 确定最终状态
    if verify.get("passed"):
        resolution = "fixed"
    elif approved is False:
        resolution = "rejected_by_human"
    elif cycle >= state.get("bug_cycle_max", 3):
        resolution = "max_cycles_exceeded"
    else:
        resolution = "unknown"

    report_summary = (
        f"Bug Analysis Report\n"
        f"  Module: {state['module']}, Page: {_get_first_page(state)}\n"
        f"  Cycles: {cycle}/{state.get('bug_cycle_max', 3)}\n"
        f"  Resolution: {resolution}\n"
        f"  RAG matches: {analysis.get('rag_match_count', 0)}\n"
        f"  Fix approved: {approved}\n"
        f"  Tests passed: {verify.get('passed', False)}"
    )

    return {
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            "bug_report": {
                "resolution": resolution,
                "cycles": cycle,
                "summary": report_summary,
            },
        },
    }


def bug_exit(state: SOPState) -> dict:
    """出口：标记 Bug Analysis phase 完成。"""
    return {"completed_phases": ["Bug Analysis"]}


# ══════════════════════════════════════════════════════════════════════════
#  图构建
# ══════════════════════════════════════════════════════════════════════════

def build_bug_analysis_subgraph() -> StateGraph:
    """
    构建 bug-analysis SubGraph（含自动循环 + HITL）。

    编译时需设置 interrupt_before=["request_approval"]。
    """
    builder = StateGraph(SOPState)

    builder.add_node("entry", bug_entry)
    builder.add_node("analyze_fail", analyze_fail_node)
    builder.add_node("auto_fix", auto_fix_node)
    builder.add_node("request_approval", request_approval_node)
    builder.add_node("verify", verify_node)
    builder.add_node("report", generate_report_node)
    builder.add_node("exit", bug_exit)

    builder.set_entry_point("entry")
    builder.add_edge("entry", "analyze_fail")
    builder.add_edge("analyze_fail", "auto_fix")
    builder.add_edge("auto_fix", "request_approval")

    # 审批后 → verify（无论批准与否都进入 verify，verify 内部检查 fix_approved）
    builder.add_edge("request_approval", "verify")

    # 条件路由：继续循环 or 生成报告
    builder.add_conditional_edges("verify", loop_router, {
        "loop": "analyze_fail",
        "report": "report",
    })

    builder.add_edge("report", "exit")
    builder.add_edge("exit", END)

    return builder


def build_bug_analysis_compiled():
    """
    构建并编译 bug-analysis SubGraph。

    HITL 通过节点内部的 interrupt() 实现，不依赖 interrupt_before。
    返回编译后的图，可直接添加为父图的子图节点。
    """
    builder = build_bug_analysis_subgraph()
    return builder.compile()
