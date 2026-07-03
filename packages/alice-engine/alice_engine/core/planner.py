"""Planner — Agent 规划引擎。

规则 + LLM 混合决策，决定下一步执行哪个 Skill。

解耦: LLM provider 和路径通过参数传入。

用法:
    from alice_engine.core.planner import plan_next_action, PlannerConfig

    config = PlannerConfig(max_retries=3, provider="mock")
    decision = plan_next_action(
        skill_index=0, perception=perception, skills=skills,
        state=state, config=config,
    )
    # decision = {"action": "execute", "skill_id": "...", "reason": "..."}
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable

from alice_engine.core.task import Observation

logger = logging.getLogger(__name__)


@dataclass
class PlannerConfig:
    """规划器配置。"""

    max_retries: int = 3
    provider: str = "anthropic"
    deep_review: bool = True
    governance_path: str | None = None
    llm_complete: Callable | None = None  # (system_prompt, user_prompt) -> LLMResponse


# HITL 确认缓存 — v3.1: 线程本地，避免并发 AgentLoop 竞态
import threading
_confirmed_skills_local = threading.local()

def _get_confirmed_skills() -> set:
    """获取当前线程的 confirmed_skills 集合。"""
    if not hasattr(_confirmed_skills_local, "skills"):
        _confirmed_skills_local.skills = set()
    return _confirmed_skills_local.skills


def plan_next_action(
    skill_index: int,
    perception: dict,
    skills: list,
    state,
    config: PlannerConfig = None,
    event_bus=None,
    logger_fn=None,
) -> dict:
    """规划下一步动作。

    Args:
        skill_index: 当前 skill 索引
        perception: 感知结果 (last_obs, etc.)
        skills: Skill 列表
        state: AgentState
        config: PlannerConfig
        event_bus: EventBus (可选)
        logger_fn: 日志函数 (可选)

    Returns:
        {"action": "retry"|"execute"|"skip"|"abort"|"done"|"confirm_required",
         "skill_id": str, "reason": str}
    """
    if config is None:
        config = PlannerConfig()

    max_retries = config.max_retries
    last_obs = perception.get("last_obs")
    retries = state.retry_counts.get(last_obs.skill_id, 0) if last_obs else 0

    # HITL 确认检查
    next_skill = skills[skill_index] if skill_index < len(skills) else ""
    if next_skill and not _is_retry_action(last_obs, retries, max_retries):
        if os.environ.get("MOCK_LLM") != "1":
            confirm_result = _check_skill_confirmation(
                next_skill, state, config.governance_path, logger_fn
            )
            if confirm_result:
                return confirm_result

    # 规则 1: 失败重试
    if last_obs and last_obs.status in ("fail", "partial") and retries < max_retries:
        if retries >= max_retries:
            return _advance(skills, skill_index, "max retries exceeded")

        # code-consistency-checker 失败是确定性的，重试无用
        if last_obs.skill_id == "automation/code-consistency-checker" and last_obs.status == "fail":
            return _advance(skills, skill_index, "code check is deterministic")

        # 重试后仍缺产物 → 推进
        if last_obs.status == "fail" and last_obs.artifacts_missing and retries >= 1:
            return _advance(skills, skill_index, "artifacts missing after retry")

        # 重试后仍部分 → 推进
        if last_obs.status == "partial" and retries >= 1:
            return _advance(skills, skill_index, "partial quality after retry")

        # LLM 决策
        return _llm_decide(skill_index, perception, skills, state, config, logger_fn)

    # 规则 2: 顺序推进
    current_task_state = getattr(state, "task_state", "backlog")

    if skill_index < len(skills):
        return {
            "action": "execute",
            "skill_id": skills[skill_index],
            "task_state": current_task_state,
            "reason": f"Sequential ({skill_index + 1}/{len(skills)})",
        }

    return {"action": "done", "skill_id": "", "reason": "All skills processed"}


def _advance(skills: list, idx: int, reason: str) -> dict:
    sid = skills[idx] if idx < len(skills) else ""
    return {"action": "execute", "skill_id": sid, "reason": reason}


# ═══════════════════════════════════════════════════════════
#  HITL 确认
# ═══════════════════════════════════════════════════════════

def _is_retry_action(last_obs, retries: int, max_retries: int) -> bool:
    if not last_obs:
        return False
    return last_obs.status in ("fail", "partial") and retries < max_retries


def _skill_matches(registry_id: str, skill_id: str) -> bool:
    if not registry_id or not skill_id:
        return False
    if registry_id == skill_id:
        return True
    if skill_id.endswith("/" + registry_id):
        return True
    if skill_id.startswith(registry_id):
        return True
    return False


def check_skill_risk_level(skill_id: str, governance_path: str | Path = None) -> tuple:
    """从 registry 查询 skill 的风险级别。"""
    if not skill_id:
        return ("low", False)

    try:
        import yaml
        from pathlib import Path

        if governance_path is None:
            return ("low", False)

        gov = Path(governance_path)
        registries = [
            gov / "skills" / "skill-registry.yaml",
            gov / "skills-dev" / "skill-registry-dev.yaml",
        ]
        for rp in registries:
            if not rp.exists():
                continue
            with open(rp, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            skills = data.get("skills", {})
            if isinstance(skills, list):
                for s in skills:
                    sid = s.get("id", "")
                    if _skill_matches(sid, skill_id):
                        return (s.get("risk_level", "low"), s.get("needs_confirm", False))
            elif isinstance(skills, dict):
                for sid, s in skills.items():
                    if _skill_matches(sid, skill_id):
                        return (s.get("risk_level", "low"), s.get("needs_confirm", False))
    except Exception:
        pass

    return ("low", False)


def _check_skill_confirmation(skill_id: str, state, governance_path: str | None = None,
                               logger_fn=None) -> dict | None:
    """检查高风险 skill 是否需要用户确认。"""
    risk_level, needs_confirm = check_skill_risk_level(skill_id, governance_path)

    if risk_level not in ("high", "critical") and not needs_confirm:
        return None

    confirm_key = f"{state.module}:{skill_id}"
    confirmed = _get_confirmed_skills()
    if confirm_key in confirmed:
        return None

    if state.memory.get("confirmed_skills", {}).get(skill_id):
        confirmed.add(confirm_key)
        return None

    if logger_fn:
        logger_fn(f"  HITL: Skill '{skill_id}' risk={risk_level}, needs_confirm={needs_confirm}")

    module = getattr(state, "module", "") or ""
    safe_skill = skill_id.replace("/", "_").replace(":", "_")
    task_id = f"{module}--{safe_skill}" if module else safe_skill

    return {
        "action": "confirm_required",
        "skill_id": skill_id,
        "task_id": task_id,
        "reason": f"HITL confirmation required: risk_level={risk_level}",
        "risk_level": risk_level,
        "needs_confirm": needs_confirm,
    }


def confirm_skill(skill_id: str, module: str = "") -> None:
    """用户确认高风险 skill 可以执行。"""
    key = f"{module}:{skill_id}" if module else skill_id
    _get_confirmed_skills().add(key)


def reset_confirmations() -> None:
    """重置所有确认状态。"""
    _get_confirmed_skills().clear()


# ═══════════════════════════════════════════════════════════
#  LLM 决策
# ═══════════════════════════════════════════════════════════

def _llm_decide(skill_index: int, perception: dict, skills: list,
                state, config: PlannerConfig, logger_fn=None) -> dict:
    """LLM 自主决策。"""
    last_obs = perception.get("last_obs")
    if not last_obs:
        return _advance(skills, skill_index, "no observation, advancing")

    skills_summary = "\n".join(
        f"  [{i+1}] {s} — "
        f"{'done' if s in state.completed_skills else ('fail' if s in state.failed_skills else 'pending')}"
        for i, s in enumerate(skills)
    )

    quality_issues = "\n".join(
        f"  - {i}" for i in last_obs.quality_issues[:5]
    ) if last_obs.quality_issues else "none"

    prompt = f"""You are an Agent planner. Decide next action.

## Goal
{state.goal}

## Skills
{skills_summary}

## Current
{last_obs.skill_id} — status: {last_obs.status}

## Quality issues
{quality_issues}

## Missing artifacts
{', '.join(last_obs.artifacts_missing) if last_obs.artifacts_missing else 'none'}

## Output JSON
{{"action": "retry"|"execute"|"skip"|"abort", "skill_id": "...", "reason": "...", "adjustments": "..."}}"""

    try:
        if config.llm_complete:
            resp = config.llm_complete(
                system_prompt="You are a CI test Agent planner. Output pure JSON.",
                user_prompt=prompt,
            )
            content = resp.content.strip()

            json_match = re.search(r'\{[^}]+\}', content)
            if json_match:
                decision = json.loads(json_match.group())
                action = decision.get("action", "execute")
                skill_id = decision.get("skill_id", "")
                reason = decision.get("reason", "LLM decision")
                adjustments = decision.get("adjustments", "")

                if action == "retry" and adjustments:
                    state.memory["retry_adjustments"] = adjustments

                return {
                    "action": action if action in ("retry", "execute", "skip", "abort") else "execute",
                    "skill_id": last_obs.skill_id if action == "retry" else (
                        skills[skill_index] if skill_index < len(skills) else ""),
                    "reason": f"LLM: {reason[:80]}",
                }
    except Exception as e:
        if logger_fn:
            logger_fn(f"  LLM plan failed ({str(e)[:60]}), fallback to sequential")

    return _advance(skills, skill_index, "LLM failed, sequential fallback")
