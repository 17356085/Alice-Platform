"""
共享节点工厂 — 减少各 SubGraph 中的样板代码。

提供:
  make_agent_loop_node()    — ★ P0-1 统一节点：AgentLoop.run() 替代 SubGraph (推荐)
  make_pass_through_node()  — Phase 1 占位节点（内部调用 AgentLoop.run()）
  make_skill_node()         — Phase 2+ 单个 Skill 的 LLM 调用节点
  make_gate_node()          — Phase 2+ 门禁检查节点
  make_mechanical_node()    — 机械化检查节点（不调 LLM）
"""

import time
from pathlib import Path
from typing import Callable, Optional

from aitest.graphs.state import (
    SOPState, GateResult, GateLevel, AgentName, AGENT_PHASE_MAP,
    validate_phase_artifacts, MAX_PHASE_RETRY_ROUNDS,
)

WORKSTUDY = Path(__file__).resolve().parent.parent.parent


# ══════════════════════════════════════════════════════════════════════════
#  ★ P0-1: 统一 Agent 节点 — AgentLoop.run() 作为唯一执行引擎
#  ══════════════════════════════════════════════════════════════════════════

def make_agent_loop_node(
    agent_name: AgentName,
    skill_subset: list = None,
    use_context_agent: bool = False,
):
    """
    创建调用 AgentLoop.run() 的 LangGraph 节点 —— 替代整个 SubGraph。

    P0-1 架构统一：消除 AgentLoop 与 LangGraph SubGraph 的双重实现。
    P2-4 分层：Agent 内部状态封装在 agent_outputs[agent_name] (AgentResult) 中。
    P1-3 HITL: skill_subset 参数支持运行部分 Skill 链（用于 HITL 断点前后分段执行）。
    use_context_agent: 为 automation_agent 启用 ContextAgent 精准 context 注入（省 70%+ token）。
    """

    def agent_loop_node(state: SOPState) -> dict:
        from aitest.agents.agent_runner import AgentLoop
        from aitest.graphs.state import AgentResult

        page = ""
        if state.get("pages"):
            idx = state.get("current_page_index", 0)
            if idx < len(state["pages"]):
                page = state["pages"][idx]

        # ── Context Agent 精准注入（仅 automation_agent）──
        focused_context_inline = ""
        if use_context_agent and state.get("module") and page:
            try:
                from aitest.agents.context_agent import ContextAgent, TaskContext
                ctx_agent = ContextAgent()
                task = TaskContext(
                    module=state["module"],
                    pages=[page],
                    current_phase="Automation",
                )
                focused = ctx_agent.pack_focused_context(task, page=page)
                focused_context_inline = focused.to_inline_context()
            except Exception:
                pass  # 失败时降级到普通注入

        try:
            agent = AgentLoop(
                agent_name,
                provider=state.get("provider", "claude"),
                module=state["module"],
                page=page,
                verbose=False,
                skill_subset=skill_subset,  # P1-3 HITL: None=全部Skill
                focused_context=focused_context_inline or None,
            )
            loop_state = agent.run()
        except Exception as e:
            import logging
            logger = logging.getLogger("aitest.graph")
            logger.error(f"[{agent_name}] AgentLoop exception: {e}")
            phase = AGENT_PHASE_MAP.get(agent_name, "Unknown")
            err_result = AgentResult(
                agent_name=agent_name, success=False,
                termination_reason=f"exception: {str(e)[:100]}",
            )
            return {
                "fatal_error": f"{agent_name}: AgentLoop exception: {str(e)[:200]}",
                "failed_phases": [phase],
                "agent_outputs": {**state.get("agent_outputs", {}), agent_name: err_result.to_dict()},
            }

        phase = AGENT_PHASE_MAP.get(agent_name, "Unknown")

        # P2-4: 构造 AgentResult 封装 Agent 内部状态
        agent_result = AgentResult(
            agent_name=agent_name,
            success=loop_state.success,
            goal=loop_state.goal,
            module=loop_state.module,
            page=loop_state.page,
            step=loop_state.step,
            completed_skills=list(loop_state.completed_skills),
            failed_skills=dict(loop_state.failed_skills),
            retry_counts=dict(loop_state.retry_counts),
            observations=[o.to_dict() if hasattr(o, 'to_dict') else o for o in loop_state.observations],
            termination_reason=loop_state.termination_reason,
            execution_failed=(agent_name == "execution-agent" and not loop_state.success),
        )

        updates: dict = {
            "agent_outputs": {**state.get("agent_outputs", {}), agent_name: agent_result.to_dict()},
            "current_skill": "",
        }

        # ── Skill 观察结果透传 ──
        if agent_result.observations:
            updates["skill_observations"] = agent_result.observations

        # ── Phase 完成/失败 ──
        if loop_state.success:
            # ★ 硬门禁: 检查强制产物是否物理存在
            artifact_ok, missing = validate_phase_artifacts(
                phase, state["module"], state.get("pages", [])
            )
            if artifact_ok:
                updates["completed_phases"] = state.get("completed_phases", []) + [phase]
                updates["phase_retry_count"] = 0
            else:
                retry_count = state.get("phase_retry_count", 0) + 1
                if retry_count <= MAX_PHASE_RETRY_ROUNDS:
                    updates["force_retry_phase"] = phase
                    updates["phase_retry_count"] = retry_count
                    # 不标记 completed — 路由将送回当前 phase 重试
                else:
                    missing_desc = "; ".join(
                        f"{fname}" for fname, _ in missing[:5]
                    )
                    updates["fatal_error"] = (
                        f"{phase}: {len(missing)} mandatory artifact(s) missing "
                        f"after {MAX_PHASE_RETRY_ROUNDS} retries. "
                        f"Missing: {missing_desc}"
                    )
        else:
            updates["failed_phases"] = state.get("failed_phases", []) + [phase]
            if loop_state.termination_reason == "agent_aborted":
                updates["fatal_error"] = f"{agent_name}: {loop_state.termination_reason}"

        # ── execution_failed 标志（供 route_next_phase 使用）──
        if agent_result.execution_failed:
            updates["agent_outputs"]["execution_failed"] = True

        # ── Completed skills 透传（向下兼容）──
        if agent_result.completed_skills:
            updates["completed_skills"] = agent_result.completed_skills

        return updates

    agent_loop_node.__name__ = f"agent_loop_{agent_name.replace('-', '_')}"
    return agent_loop_node


# ══════════════════════════════════════════════════════════════════════════
#  Phase 1: Pass-through 节点（临时，Phase 2 替换为真正的 SubGraph）
# ══════════════════════════════════════════════════════════════════════════

def make_pass_through_node(agent_name: AgentName):
    """
    创建一个 pass-through 节点：内部调用现有 AgentLoop.run()。

    Phase 1 用此节点快速验证编排器路由逻辑。
    Phase 2 会被替换为真正的 SubGraph。
    """

    def pass_through(state: SOPState) -> dict:
        from aitest.agents.agent_runner import AgentLoop

        page = ""
        if state.get("pages"):
            idx = state.get("current_page_index", 0)
            if idx < len(state["pages"]):
                page = state["pages"][idx]

        agent = AgentLoop(
            agent_name,
            provider=state.get("provider", "claude"),
            module=state["module"],
            page=page,
            verbose=False,
        )

        result = agent.run()
        phase = AGENT_PHASE_MAP.get(agent_name, "Unknown")

        # 构建更新
        updates: dict = {
            "agent_outputs": {
                **state.get("agent_outputs", {}),
                agent_name: result.to_dict(),
            },
            "current_skill": "",
        }

        # 转换 Observation → dict
        observations = []
        for obs in result.observations:
            observations.append(obs.to_dict() if hasattr(obs, 'to_dict') else obs)

        if observations:
            updates["skill_observations"] = observations

        if result.success:
            updates["completed_phases"] = state.get("completed_phases", []) + [phase]
        else:
            updates["failed_phases"] = state.get("failed_phases", []) + [phase]
            # 不设置 fatal_error — 允许后续 Phase 继续
            if result.termination_reason == "agent_aborted":
                updates["fatal_error"] = f"{agent_name}: {result.termination_reason}"

        return updates

    # 保存 agent_name 引用以便调试
    pass_through.__name__ = f"pass_through_{agent_name.replace('-', '_')}"
    return pass_through


# ══════════════════════════════════════════════════════════════════════════
#  Phase 2+: Skill 节点工厂
# ══════════════════════════════════════════════════════════════════════════

def make_skill_node(skill_id: str, provider_field: str = "provider"):
    """
    创建一个 LLM 调用节点：执行单个 Skill。

    参数:
        skill_id:        "category/skill-name" e.g. "automation/tech-analysis"
        provider_field:  State 中 provider 字段名

    返回的节点函数:
        def skill_node(state: SOPState) -> dict
    """

    def skill_node(state: SOPState) -> dict:
        from aitest.agents.agent_runner import run_skill

        page = ""
        if state.get("pages"):
            idx = state.get("current_page_index", 0)
            if idx < len(state["pages"]):
                page = state["pages"][idx]

        provider = state.get(provider_field, "claude")

        response = run_skill(
            skill_id=skill_id,
            user_input=f"Module: {state['module']}, Page: {page}",
            provider=provider,
            context_vars={
                "module": state["module"],
                "page": page,
            },
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
        }

    skill_node.__name__ = f"skill_{skill_id.replace('/', '_').replace('-', '_')}"
    return skill_node


# ══════════════════════════════════════════════════════════════════════════
#  Phase 2+: 门禁检查节点工厂
# ══════════════════════════════════════════════════════════════════════════

def make_gate_node(
    phase: str,
    level: GateLevel = GateLevel.L2_AGENT,
    validator_fn: Optional[Callable] = None,
):
    """
    创建一个门禁检查节点。

    参数:
        phase:        阶段名
        level:        门禁层级 (L1/L2/L3)
        validator_fn: 验证函数，签名为 fn(module: str) -> CheckResult
    """

    def gate_node(state: SOPState) -> dict:
        if validator_fn is None:
            # 无验证器 — 默认通过
            result = GateResult(
                level=level,
                phase=phase,
                ok=True,
                message=f"{phase}: 无门禁检查（validator_fn 未提供）",
            )
        else:
            try:
                check = validator_fn(state["module"])
                result = GateResult(
                    level=level,
                    phase=phase,
                    ok=check.ok if hasattr(check, 'ok') else bool(check),
                    message=check.message if hasattr(check, 'message') else str(check),
                    details=check.details if hasattr(check, 'details') else {},
                )
            except Exception as e:
                result = GateResult(
                    level=level,
                    phase=phase,
                    ok=False,
                    message=f"门禁检查异常: {str(e)[:200]}",
                )

        return {
            "gate_results": [result.to_dict()],
        }

    gate_node.__name__ = f"gate_{phase.lower().replace(' ', '_')}"
    return gate_node


# ══════════════════════════════════════════════════════════════════════════
#  Phase 2+: 机械化检查节点（不调 LLM）
# ══════════════════════════════════════════════════════════════════════════

def make_mechanical_node(check_fn: Callable, node_name: str = "mechanical_check"):
    """
    创建一个不调 LLM 的机械化节点（如 code-consistency-checker）。

    参数:
        check_fn: 签名为 fn(state: SOPState) -> dict
    """

    def mechanical_node(state: SOPState) -> dict:
        return check_fn(state)

    mechanical_node.__name__ = node_name
    return mechanical_node
