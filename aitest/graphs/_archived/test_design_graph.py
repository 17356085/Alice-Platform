"""
test-design-agent LangGraph SubGraph。

对每个页面执行 4 个 Skill:
  page-analysis → risk-modeling → testcase-design → page-interface-generator

内包含 Perceive→Plan→Act→Observe 循环 + per-page 迭代。
"""

import re
from pathlib import Path
from typing import Literal

from langgraph.graph import StateGraph, END

from aitest.graphs.state import SOPState, GateResult, GateLevel

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
CONTEXT_MODULES = GOVERNANCE / "context" / "projects" / "web-automation" / "modules"

TEST_DESIGN_SKILLS = [
    "test-design/page-analysis",
    "test-design/risk-modeling",
    "test-design/testcase-design",
    "test-design/page-interface-generator",
]

SKILL_OUTPUT_MAP = {
    "test-design/page-analysis": "{module_dir}/pages/{page}/PAGE_CONTEXT.md",
    "test-design/risk-modeling": "{module_dir}/pages/{page}/RISK_MODEL.md",
    "test-design/testcase-design": "{module_dir}/pages/{page}/TEST_CASES.md",
    "test-design/page-interface-generator": "{module_dir}/pages/{page}/PAGE_INTERFACE.yaml",
}


def _get_current_page(state: dict) -> str:
    pages = state.get("pages", [])
    idx = state.get("current_page_index", 0)
    if pages and idx < len(pages):
        return pages[idx]
    return ""


def _resolve_path(pattern: str, module: str, page: str) -> Path:
    resolved = pattern.replace("{module_dir}", str(CONTEXT_MODULES / module))
    resolved = resolved.replace("{module}", module)
    resolved = resolved.replace("{page}", page)
    return Path(resolved)


# ══════════════════════════════════════════════════════════════════════════
#  节点函数
# ══════════════════════════════════════════════════════════════════════════

def td_entry(state: SOPState) -> dict:
    return {"current_skill": "", "current_phase": "Test Design"}


def td_perceive(state: SOPState) -> dict:
    """检查已有产物（幂等跳过）。"""
    module = state["module"]
    page = _get_current_page(state)
    existing = []
    for skill_id, pattern in SKILL_OUTPUT_MAP.items():
        path = _resolve_path(pattern, module, page)
        if path.exists() and path.stat().st_size > 0:
            existing.append(skill_id)
    return {"agent_outputs": {**state.get("agent_outputs", {}), "td_existing_skills": existing}}


def td_plan(state: SOPState) -> dict:
    """决定下一个 Skill。"""
    existing = state.get("agent_outputs", {}).get("td_existing_skills", [])
    completed = state.get("completed_skills", [])
    failed = state.get("failed_skills", {})
    for skill_id in TEST_DESIGN_SKILLS:
        if skill_id in existing or skill_id in completed:
            continue
        if skill_id in failed and state.get("retry_counts", {}).get(skill_id, 0) >= 3:
            continue
        return {"current_skill": skill_id}
    return {"current_skill": ""}


def td_act(state: SOPState) -> dict:
    """执行 Skill（LLM 调用 + 文件保存）。"""
    skill_id = state.get("current_skill", "")
    if not skill_id:
        return {}

    module = state["module"]
    page = _get_current_page(state)
    provider = state.get("provider", "claude")

    from aitest.agents.agent_runner import run_skill

    response = run_skill(
        skill_id=skill_id,
        user_input=f"模块: {module}, 页面: {page}",
        provider=provider,
        context_vars={"module": module, "page": page},
    )

    # 保存产出
    pattern = SKILL_OUTPUT_MAP.get(skill_id)
    saved_path = ""
    if pattern and response.finish_reason != "error" and response.content:
        path = _resolve_path(pattern, module, page)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(response.content, encoding="utf-8")
        saved_path = str(path)

    return {
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            f"skill_{skill_id.replace('/', '_')}": {
                "content_preview": response.content[:500] if response.content else "",
                "token_usage": response.token_usage,
                "finish_reason": response.finish_reason,
                "saved_path": saved_path,
            },
        },
    }


def td_observe(state: SOPState) -> dict:
    """验证产出。"""
    skill_id = state.get("current_skill", "")
    module = state["module"]
    page = _get_current_page(state)

    obs = {
        "skill_id": skill_id,
        "status": "pass",
        "artifacts_found": [],
        "artifacts_missing": [],
        "quality_issues": [],
        "summary": "",
        "suggestion": "continue",
        "token_usage": {},
    }

    pattern = SKILL_OUTPUT_MAP.get(skill_id)
    if pattern:
        path = _resolve_path(pattern, module, page)
        if path.exists() and path.stat().st_size > 0:
            obs["artifacts_found"].append(str(path))
        else:
            obs["artifacts_missing"].append(str(path))
            obs["status"] = "fail"
            obs["suggestion"] = "retry"
            obs["summary"] = f"Missing: {path.name}"

    return {"skill_observations": [obs]}


def td_skill_router(state: SOPState) -> Literal["continue", "retry", "gate_check"]:
    skill_id = state.get("current_skill", "")
    if not skill_id:
        return "gate_check"
    observations = state.get("skill_observations", [])
    if not observations:
        return "continue"
    last = observations[-1]
    suggestion = last.get("suggestion", "continue") if isinstance(last, dict) else getattr(last, "suggestion", "continue")
    if suggestion == "retry" and state.get("retry_counts", {}).get(skill_id, 0) < 3:
        return "retry"
    if suggestion in ("continue", "skip"):
        return "continue"
    return "gate_check"


def td_update(state: SOPState) -> dict:
    skill_id = state.get("current_skill", "")
    observations = state.get("skill_observations", [])
    updates: dict = {
        "completed_skills": [],
        "failed_skills": dict(state.get("failed_skills", {})),
        "retry_counts": dict(state.get("retry_counts", {})),
    }
    if observations and skill_id:
        last = observations[-1]
        status = last.get("status", "") if isinstance(last, dict) else getattr(last, "status", "")
        if status == "pass":
            updates["completed_skills"] = [skill_id]
            updates["failed_skills"].pop(skill_id, None)
            updates["retry_counts"].pop(skill_id, None)
        elif status in ("fail", "partial"):
            updates["failed_skills"][skill_id] = last.get("summary", "") if isinstance(last, dict) else last.summary
            updates["retry_counts"][skill_id] = updates["retry_counts"].get(skill_id, 0) + 1
    return updates


def td_review(state: SOPState) -> dict:
    """
    对抗性审查：LLM 以测试架构师身份批判测试设计产出。

    检查维度:
      - 风险覆盖是否完整？有无遗漏边界场景？
      - 测试数据是否覆盖有效/无效/边界三类？
      - 用例是否可执行？（定位器是否对应 PAGE_CONTEXT 中的元素）

    严重问题 → interrupt() 挂起，等待人工确认是否继续。
    """
    module = state["module"]
    page = _get_current_page(state)
    page_dir = CONTEXT_MODULES / module / "pages" / page
    provider = state.get("provider", "claude")

    # 读取已生成的产物
    artifacts = {}
    for fname in ["PAGE_CONTEXT.md", "RISK_MODEL.md", "TEST_CASES.md"]:
        fpath = page_dir / fname
        if fpath.exists():
            artifacts[fname] = fpath.read_text(encoding="utf-8")[:2000]

    if not artifacts:
        return {"agent_outputs": {**state.get("agent_outputs", {}), "td_review": {"passed": True, "note": "No artifacts to review"}}}

    # 对抗性审查 prompt
    from aitest.agents.agent_runner import run_skill

    review_input = f"""你是资深测试架构师，请**批判**下面这份测试设计，找出遗漏和问题：

模块: {module}, 页面: {page}

## PAGE_CONTEXT
{artifacts.get('PAGE_CONTEXT.md', '(缺失)')[:1500]}

## RISK_MODEL
{artifacts.get('RISK_MODEL.md', '(缺失)')[:1000]}

## TEST_CASES
{artifacts.get('TEST_CASES.md', '(缺失)')[:1500]}

## 审查要求
1. 找出至少 3 个潜在的遗漏场景（边界/异常/并发）
2. 指出哪些用例的测试数据不充分
3. 判断整体质量：PASS / WARN（有小问题但可继续）/ FAIL（严重问题需重做）

输出 JSON:
{{"severity": "PASS"|"WARN"|"FAIL",
 "issues": ["具体问题1", "具体问题2", ...],
 "missing_scenarios": ["遗漏场景1", ...],
 "suggestion": "一句话建议"}}"""

    response = run_skill(
        skill_id="test-design/page-analysis",
        user_input=review_input,
        provider=provider,
        context_vars={"module": module, "page": page},
    )

    # 解析审查结果
    import json, re
    review_result = {"severity": "WARN", "issues": [], "suggestion": ""}
    try:
        json_match = re.search(r'\{[^{}]*"severity"[^{}]*\}', response.content, re.DOTALL)
        if json_match:
            review_result = json.loads(json_match.group())
    except Exception:
        review_result = {"severity": "WARN", "issues": ["审查解析失败"], "suggestion": response.content[:200]}

    severity = review_result.get("severity", "WARN")

    # 严重问题 → HITL
    if severity == "FAIL":
        from langgraph.types import interrupt
        interrupt({
            "type": "test_design_review",
            "module": module,
            "page": page,
            "severity": "FAIL",
            "issues": review_result.get("issues", [])[:5],
            "suggestion": review_result.get("suggestion", ""),
            "options": ["continue_anyway", "redo"],
        })

    return {
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            "td_review": {
                "passed": severity != "FAIL",
                "severity": severity,
                "issues": review_result.get("issues", [])[:5],
                "suggestion": review_result.get("suggestion", ""),
            },
        },
    }


def td_gate_check(state: SOPState) -> dict:
    module = state["module"]
    page = _get_current_page(state)
    page_dir = CONTEXT_MODULES / module / "pages" / page

    required = {
        "PAGE_CONTEXT.md": page_dir / "PAGE_CONTEXT.md",
        "RISK_MODEL.md": page_dir / "RISK_MODEL.md",
        "TEST_CASES.md": page_dir / "TEST_CASES.md",
    }
    missing = [label for label, p in required.items() if not p.exists() or p.stat().st_size == 0]
    ok = len(missing) == 0

    result = GateResult(
        level=GateLevel.L2_AGENT,
        phase="Test Design",
        ok=ok,
        message=f"Test Design gate for {module}/{page}: {'PASS' if ok else 'FAIL'}",
        details={"missing_files": missing, "module": module, "page": page},
    )
    return {"gate_results": [result.to_dict()]}


def td_exit(state: SOPState) -> dict:
    page = _get_current_page(state)
    idx = state.get("current_page_index", 0)
    pages = state.get("pages", [])
    next_idx = idx + 1

    updates: dict = {
        "current_page_index": next_idx,
        "completed_skills": [],
        "current_skill": "",
    }

    if next_idx >= len(pages):
        updates["completed_phases"] = ["Test Design"]
        updates["current_page_index"] = 0

    return updates


# ══════════════════════════════════════════════════════════════════════════
#  图构建
# ══════════════════════════════════════════════════════════════════════════

def build_test_design_subgraph() -> StateGraph:
    builder = StateGraph(SOPState)
    builder.add_node("entry", td_entry)
    builder.add_node("perceive", td_perceive)
    builder.add_node("plan", td_plan)
    builder.add_node("act", td_act)
    builder.add_node("observe", td_observe)
    builder.add_node("update", td_update)
    builder.add_node("gate_check", td_gate_check)
    builder.add_node("review", td_review)
    builder.add_node("exit", td_exit)

    builder.set_entry_point("entry")
    builder.add_edge("entry", "perceive")
    builder.add_edge("perceive", "plan")
    builder.add_edge("plan", "act")
    builder.add_edge("act", "observe")
    builder.add_edge("observe", "update")
    builder.add_conditional_edges("update", td_skill_router, {
        "continue": "plan",
        "retry": "plan",
        "gate_check": "gate_check",
    })
    builder.add_edge("gate_check", "review")
    builder.add_edge("review", "exit")
    builder.add_edge("exit", END)
    return builder
