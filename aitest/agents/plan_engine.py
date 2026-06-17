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

    Returns: {"action": "retry"|"execute"|"skip"|"abort"|"done",
              "skill_id": str, "reason": str}
    """
    last_obs = perception.get("last_obs")
    retries = state.retry_counts.get(last_obs.skill_id, 0) if last_obs else 0

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
