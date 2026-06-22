"""Agent planning engine — rule-based + LLM decision making.

Extracted from agent_runner.py (W01 refactor, 2026-06-17).
Contains plan() + _llm_plan() logic (~207 lines extracted).
"""

import json
import re

from aitest.agents.runner_state import Observation


def plan_next_action(skill_index: int, perception: dict, skills: list,
                     state, deep_review: bool, _review_triggered: bool,
                     max_retries: int, provider: str, logger=None) -> dict:
    """Rule-based + LLM decision for next action. Replaces AgentLoop.plan().

    Returns: {"action": "retry"|"execute"|"skip"|"abort"|"done"|"confirm_required",
              "skill_id": str, "reason": str}
    """
    last_obs = perception.get("last_obs")
    retries = state.retry_counts.get(last_obs.skill_id, 0) if last_obs else 0

    # ★ P0 (Step 4): HITL confirmation check for high-risk skills
    # Before executing, check if the skill needs user confirmation
    next_skill = skills[skill_index] if skill_index < len(skills) else ""
    if next_skill and not _is_retry_action(last_obs, retries, max_retries):
        confirm_result = _check_skill_confirmation(next_skill, state, logger)
        if confirm_result:
            return confirm_result

    # Rule 1: retry on failure (with limits)
    if last_obs and last_obs.status in ("fail", "partial") and retries < max_retries:
        if retries >= max_retries:
            return _advance(skills, skill_index, "max retries exceeded")

        # code-consistency-checker failure is deterministic — retry useless
        if last_obs.skill_id == "automation/code-consistency-checker" and last_obs.status == "fail":
            return _advance(skills, skill_index, "code check is deterministic")

        # Deep review trigger after mechanical pass
        if (last_obs.skill_id == "automation/code-consistency-checker"
                and last_obs.status == "pass" and deep_review and not _review_triggered):
            return {"action": "execute",
                    "skill_id": "automation/code-consistency-checker:review",
                    "reason": "Mechanical pass, triggering LLM adversarial review"}

        # Artifact missing after retry → advance
        if last_obs.status == "fail" and last_obs.artifacts_missing and retries >= 1:
            return _advance(skills, skill_index, "artifacts missing after retry")

        # Partial after retry → advance
        if last_obs.status == "partial" and retries >= 1:
            return _advance(skills, skill_index, "partial quality after retry")

        # LLM decision for ambiguous cases
        return _llm_decide(skill_index, perception, skills, state, provider, logger)

    # Rule 2: sequential advance
    if skill_index < len(skills):
        return {"action": "execute",
                "skill_id": skills[skill_index],
                "reason": f"Sequential ({skill_index + 1}/{len(skills)})"}

    return {"action": "done", "skill_id": "", "reason": "All skills processed"}


def _advance(skills: list, idx: int, reason: str) -> dict:
    sid = skills[idx] if idx < len(skills) else ""
    return {"action": "execute", "skill_id": sid, "reason": reason}


# ══════════════════════════════════════════════════════════════════════════
#  P0 (Step 4): HITL Confirmation — 高风险 Skill 执行前确认
# ══════════════════════════════════════════════════════════════════════════

# Skills that have been confirmed in this run (session-level cache)
_confirmed_skills: set = set()


def _is_retry_action(last_obs, retries: int, max_retries: int) -> bool:
    """Check if next action is a retry (pass-through confirmation)."""
    if not last_obs:
        return False
    return (last_obs.status in ("fail", "partial") and retries < max_retries)


def _skill_matches(registry_id: str, skill_id: str) -> bool:
    """
    Match registry ID against full skill ID.
    Handles cases where registry stores 'data-sanitization'
    but skill_id is 'execution/data-sanitization'.
    """
    if not registry_id or not skill_id:
        return False
    # Exact match
    if registry_id == skill_id:
        return True
    # Registry ID is suffix (e.g., 'data-sanitization' in 'execution/data-sanitization')
    if skill_id.endswith("/" + registry_id):
        return True
    # Registry ID contains category prefix
    if skill_id.startswith(registry_id):
        return True
    return False


def check_skill_risk_level(skill_id: str) -> tuple:
    """
    从 registry 查询 skill 的风险级别。

    返回: (risk_level: str, needs_confirm: bool)
    """
    if not skill_id:
        return ("low", False)

    # Try production registry
    try:
        import yaml
        from pathlib import Path
        registries = [
            Path(__file__).resolve().parent.parent.parent / "governance" / "skills" / "skill-registry.yaml",
            Path(__file__).resolve().parent.parent.parent / "governance" / "skills-dev" / "skill-registry-dev.yaml",
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


def _check_skill_confirmation(skill_id: str, state, logger=None) -> dict | None:
    """
    检查高风险 skill 是否需要用户确认。

    如果 skill 需要确认但尚未确认，返回 confirm_required action。
    返回 None 表示不需要确认或已确认，可以继续执行。
    """
    risk_level, needs_confirm = check_skill_risk_level(skill_id)

    # 低/中风险不需要确认
    if risk_level not in ("high", "critical") and not needs_confirm:
        return None

    # 已确认过的跳过
    confirm_key = f"{state.module}:{skill_id}"
    if confirm_key in _confirmed_skills:
        return None

    # 检查是否在 memory 中有确认记录
    if state.memory.get("confirmed_skills", {}).get(skill_id):
        _confirmed_skills.add(confirm_key)
        return None

    if logger:
        logger(f"  ⚠️  HITL: Skill '{skill_id}' risk={risk_level}, needs_confirm={needs_confirm}")
        logger(f"      等待用户确认后继续...")

    return {
        "action": "confirm_required",
        "skill_id": skill_id,
        "reason": f"HITL confirmation required: risk_level={risk_level}, needs_confirm={needs_confirm}",
        "risk_level": risk_level,
        "needs_confirm": needs_confirm,
    }


def confirm_skill(skill_id: str, module: str = "") -> None:
    """
    用户确认高风险 skill 可以执行。

    在 HITL 交互中调用，使后续该 skill 不再需要确认。

    用法:
        from aitest.agents.plan_engine import confirm_skill
        confirm_skill("automation/test-script-generator", "equipment")
    """
    key = f"{module}:{skill_id}" if module else skill_id
    _confirmed_skills.add(key)


def reset_confirmations() -> None:
    """重置所有确认状态（新 run 开始时调用）。"""
    _confirmed_skills.clear()


def _llm_decide(skill_index: int, perception: dict, skills: list,
                state, provider: str, logger=None) -> dict:
    """LLM autonomous decision for ambiguous situations. Replaces AgentLoop._llm_plan()."""
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
        from aitest.llm.provider import get_provider
        llm = get_provider(provider)
        resp = llm.complete(
            system_prompt="You are a CI test Agent planner. Output pure JSON.",
            user_prompt=prompt, temperature=0.3, max_tokens=300,
        )
        content = resp.content.strip()

        # Trace event
        try:
            from aitest.infra.trace import TraceEvent, write_trace_event, TraceContext
            event = TraceEvent.create(
                event_type="agent_decision", skill_id="", provider=provider,
                model=resp.model or "", latency_ms=getattr(resp, "latency_ms", 0),
                token_input=resp.token_usage.get("input", 0) if resp.token_usage else 0,
                token_output=resp.token_usage.get("output", 0) if resp.token_usage else 0,
                status="success" if resp.finish_reason != "error" else "error",
                prompt_preview=prompt, response_preview=content,
                run_id=TraceContext.get_run_id(), agent_name=TraceContext.get_agent_name(),
            )
            write_trace_event(event)
        except Exception:
            pass

        json_match = re.search(r'\{[^}]+\}', content)
        if json_match:
            decision = json.loads(json_match.group())
            action = decision.get("action", "execute")
            skill_id = decision.get("skill_id", "")
            reason = decision.get("reason", "LLM decision")
            adjustments = decision.get("adjustments", "")

            if action == "retry" and adjustments:
                state.memory["retry_adjustments"] = adjustments
                if logger:
                    logger(f"  LLM adjustment: {adjustments[:100]}")

            return {
                "action": action if action in ("retry", "execute", "skip", "abort") else "execute",
                "skill_id": last_obs.skill_id if action == "retry" else (
                    skills[skill_index] if skill_index < len(skills) else ""),
                "reason": f"LLM: {reason[:80]}",
            }
    except Exception as e:
        if logger:
            logger(f"  LLM plan failed ({str(e)[:60]}), fallback to sequential")

    return _advance(skills, skill_index, "LLM failed, sequential fallback")
