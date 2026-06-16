"""
project-agent + requirement-agent LangGraph SubGraphs。

每个 Agent 包含真正的 Perceive→Plan→Act→Observe 循环，
每个 Skill 作为独立节点执行，LangGraph 对每一步可见。
"""

import re
from pathlib import Path
from typing import Literal

from langgraph.graph import StateGraph, END

from aitest.graphs.state import SOPState, GateResult, GateLevel

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
CONTEXT_MODULES = GOVERNANCE / "context" / "projects" / "web-automation" / "modules"
ZJSN_TEST = WORKSTUDY / "ZJSN_Test-master526"


def _skill_act(state: dict, skill_id: str, extra_context: dict = None) -> dict:
    """通用 Skill 执行节点：调用 LLM + 保存产出。"""
    from aitest.agent_runner import run_skill

    module = state["module"]
    provider = state.get("provider", "claude")
    context_vars = {"module": module}
    if extra_context:
        context_vars.update(extra_context)

    response = run_skill(
        skill_id=skill_id,
        user_input=f"Module: {module}",
        provider=provider,
        context_vars=context_vars,
    )

    return {
        "current_skill": skill_id,
        "agent_outputs": {
            **state.get("agent_outputs", {}),
            f"skill_{skill_id.replace('/', '_').replace('-', '_')}": {
                "content_preview": response.content[:500] if response.content else "",
                "token_usage": response.token_usage,
                "finish_reason": response.finish_reason,
            },
        },
    }


def _skill_observe(state: dict, file_paths: dict) -> dict:
    """通用 Skill 观察：检查产出文件存在性。"""
    skill_id = state.get("current_skill", "")
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

    expected = file_paths.get(skill_id, [])
    for path in expected:
        if Path(path).exists() and Path(path).stat().st_size > 0:
            obs["artifacts_found"].append(str(path))
        else:
            obs["artifacts_missing"].append(str(path))
            obs["status"] = "fail"
            obs["suggestion"] = "retry"
            obs["summary"] = f"Missing: {Path(path).name}"

    if not expected:
        obs["summary"] = "No file output expected"

    return {"skill_observations": [obs]}


def _skill_update(state: dict) -> dict:
    """通用状态更新：记录完成/失败。"""
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
        summary = last.get("summary", "") if isinstance(last, dict) else getattr(last, "summary", "")
        if status == "pass":
            updates["completed_skills"] = [skill_id]
            updates["failed_skills"].pop(skill_id, None)
            updates["retry_counts"].pop(skill_id, None)
        elif status in ("fail", "partial"):
            updates["failed_skills"][skill_id] = summary
            updates["retry_counts"][skill_id] = updates["retry_counts"].get(skill_id, 0) + 1
    return updates


def _router(state: dict) -> Literal["continue", "retry", "gate_check"]:
    """通用 Skill 路由。"""
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


# ══════════════════════════════════════════════════════════════════════════
#  project-agent SubGraph: 3 skills → proper cycle
# ══════════════════════════════════════════════════════════════════════════

PROJECT_SKILLS = [
    "project/project-context-manager",
    "project/context-sync",
    "project/completeness-check",
]

PROJECT_FILES = {
    "project/project-context-manager": [str(GOVERNANCE / "context" / "projects" / "web-automation" / "PROJECT_CONTEXT.md")],
    "project/context-sync": [],
    "project/completeness-check": [],
}


def proj_entry(state: SOPState) -> dict:
    return {"current_skill": "", "current_phase": "Project Init"}


def proj_perceive(state: SOPState) -> dict:
    """检查已有产物，跳过已完成的 skill。"""
    existing = []
    for skill_id, paths in PROJECT_FILES.items():
        if paths and all(Path(p).exists() and Path(p).stat().st_size > 0 for p in paths):
            existing.append(skill_id)
    return {"agent_outputs": {**state.get("agent_outputs", {}), "proj_existing": existing}}


def proj_plan(state: SOPState) -> dict:
    existing = set(state.get("agent_outputs", {}).get("proj_existing", []))
    completed = set(state.get("completed_skills", []))
    failed = state.get("failed_skills", {})
    for sid in PROJECT_SKILLS:
        if sid in existing or sid in completed:
            continue
        if sid in failed and state.get("retry_counts", {}).get(sid, 0) >= 3:
            continue
        return {"current_skill": sid}
    return {"current_skill": ""}


def proj_act(state: SOPState) -> dict:
    sid = state.get("current_skill", "")
    if not sid:
        return {}
    return _skill_act(state, sid)


def proj_observe(state: SOPState) -> dict:
    return _skill_observe(state, PROJECT_FILES)


def proj_update(state: SOPState) -> dict:
    return _skill_update(state)


def proj_router(state: SOPState) -> Literal["continue", "retry", "gate_check"]:
    return _router(state)


def proj_gate(state: SOPState) -> dict:
    module = state["module"]
    pc = GOVERNANCE / "context" / "projects" / "web-automation" / "PROJECT_CONTEXT.md"
    mc = CONTEXT_MODULES / module / "MODULE_CONTEXT.md"
    ok = pc.exists() and mc.exists()
    return {"gate_results": [GateResult(
        level=GateLevel.L2_AGENT, phase="Project Init", ok=ok,
        message=f"Project gate: {'PASS' if ok else 'FAIL'}",
        details={"project_context": str(pc), "module_context": str(mc)},
    ).to_dict()]}


def proj_exit(state: SOPState) -> dict:
    return {"completed_phases": ["Project Init"], "completed_skills": [], "current_skill": ""}


def build_project_subgraph() -> StateGraph:
    builder = StateGraph(SOPState)
    for name, fn in [
        ("entry", proj_entry), ("perceive", proj_perceive), ("plan", proj_plan),
        ("act", proj_act), ("observe", proj_observe), ("update", proj_update),
        ("gate", proj_gate), ("exit", proj_exit),
    ]:
        builder.add_node(name, fn)

    builder.set_entry_point("entry")
    builder.add_edge("entry", "perceive")
    builder.add_edge("perceive", "plan")
    builder.add_edge("plan", "act")
    builder.add_edge("act", "observe")
    builder.add_edge("observe", "update")
    builder.add_conditional_edges("update", proj_router, {
        "continue": "plan", "retry": "plan", "gate_check": "gate",
    })
    builder.add_edge("gate", "exit")
    builder.add_edge("exit", END)
    return builder


# ══════════════════════════════════════════════════════════════════════════
#  requirement-agent SubGraph: 2 skills → proper cycle
# ══════════════════════════════════════════════════════════════════════════

REQ_SKILLS = ["requirements/module-modeling", "requirements/requirement-analysis"]

REQ_FILES = {
    "requirements/module-modeling": [],  # 由 context-vars 指定产出路径
    "requirements/requirement-analysis": [],
}


def req_entry(state: SOPState) -> dict:
    return {"current_skill": "", "current_phase": "Requirement"}


def req_perceive(state: SOPState) -> dict:
    module = state["module"]
    mc = CONTEXT_MODULES / module / "MODULE_CONTEXT.md"
    existing = []
    if mc.exists() and mc.stat().st_size > 0:
        existing.append("requirements/module-modeling")
    return {"agent_outputs": {**state.get("agent_outputs", {}), "req_existing": existing}}


def req_plan(state: SOPState) -> dict:
    existing = set(state.get("agent_outputs", {}).get("req_existing", []))
    completed = set(state.get("completed_skills", []))
    failed = state.get("failed_skills", {})
    for sid in REQ_SKILLS:
        if sid in existing or sid in completed:
            continue
        if sid in failed and state.get("retry_counts", {}).get(sid, 0) >= 3:
            continue
        return {"current_skill": sid}
    return {"current_skill": ""}


def req_act(state: SOPState) -> dict:
    sid = state.get("current_skill", "")
    if not sid:
        return {}
    return _skill_act(state, sid)


def req_observe(state: SOPState) -> dict:
    return _skill_observe(state, REQ_FILES)


def req_update(state: SOPState) -> dict:
    return _skill_update(state)


def req_router(state: SOPState) -> Literal["continue", "retry", "gate_check"]:
    return _router(state)


def req_gate(state: SOPState) -> dict:
    module = state["module"]
    mc = CONTEXT_MODULES / module / "MODULE_CONTEXT.md"
    ok = mc.exists() and mc.stat().st_size > 0
    return {"gate_results": [GateResult(
        level=GateLevel.L2_AGENT, phase="Requirement", ok=ok,
        message=f"Requirement gate: {'PASS' if ok else 'FAIL'}",
        details={"module_context": str(mc)},
    ).to_dict()]}


def req_exit(state: SOPState) -> dict:
    return {"completed_phases": ["Requirement"], "completed_skills": [], "current_skill": ""}


def build_requirement_subgraph() -> StateGraph:
    builder = StateGraph(SOPState)
    for name, fn in [
        ("entry", req_entry), ("perceive", req_perceive), ("plan", req_plan),
        ("act", req_act), ("observe", req_observe), ("update", req_update),
        ("gate", req_gate), ("exit", req_exit),
    ]:
        builder.add_node(name, fn)

    builder.set_entry_point("entry")
    builder.add_edge("entry", "perceive")
    builder.add_edge("perceive", "plan")
    builder.add_edge("plan", "act")
    builder.add_edge("act", "observe")
    builder.add_edge("observe", "update")
    builder.add_conditional_edges("update", req_router, {
        "continue": "plan", "retry": "plan", "gate_check": "gate",
    })
    builder.add_edge("gate", "exit")
    builder.add_edge("exit", END)
    return builder
