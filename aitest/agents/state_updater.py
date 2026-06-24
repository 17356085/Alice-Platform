"""Agent state updater — status transitions + event emission.

Extracted from agent_runner.py (W01 refactor, 2026-06-17).
Contains: update() + _maybe_emit_event() + _emit_cache_summary() (~119 lines extracted).
"""

import time


def update_agent_state(state, skill_id: str, observation,
                       agent_name: str = "", module: str = "", logger=None):
    """Update AgentState after skill execution. Replaces AgentLoop.update().

    Handles: pass/fail/partial/skipped transitions, retry counting,
    milestone event emission.
    """
    state.step += 1
    state.current_skill = skill_id
    state.observations.append(observation)

    if observation.status == "pass":
        state.completed_skills.append(skill_id)
        state.retry_counts.pop(skill_id, None)
        state.memory["prev_output"] = observation.summary

    elif observation.status in ("fail", "partial"):
        retries = state.retry_counts.get(skill_id, 0)
        state.retry_counts[skill_id] = retries + 1
        if skill_id not in state.completed_skills:
            state.failed_skills[skill_id] = observation.summary

    elif observation.status == "skipped":
        state.completed_skills.append(skill_id)

    # Emit milestone event for key skills
    _emit_milestone(skill_id, observation, agent_name, module, logger)


# Skills that trigger AgentCompleted event on pass
MILESTONE_SKILLS = [
    "project/project-context-manager",
    "requirements/module-modeling",
    "requirements/requirement-analysis",
    "test-design/page-analysis",
    "test-design/risk-modeling",
    "test-design/testcase-design",
    "automation/tech-analysis",
    "automation/auto-strategy",
    "automation/page-object-generator",
    "automation/test-script-generator",
    "automation/code-consistency-checker",
    "execution/allure-report-analyzer",
    "diagnosis/bug-analysis",
]


def _emit_milestone(skill_id: str, observation, agent_name: str = "", module: str = "", logger=None):
    """Emit AgentCompleted event when a milestone skill passes."""
    if skill_id not in MILESTONE_SKILLS or observation.status != "pass":
        return
    try:
        from aitest.audit_engine.event_bus import emit
        emit("AgentCompleted",
             agent=agent_name,
             module=module,
             skill=skill_id,
             status="success",
             artifacts=observation.summary)
    except Exception:
        pass


def emit_cache_summary(shared_injector=None, shared_adapter=None, logger=None):
    """Emit ContextUpdated event with cache statistics. Best-effort."""
    try:
        from aitest.audit_engine.event_bus import emit
        hits = 0
        calls = 0
        if shared_injector and hasattr(shared_injector, "cache_stats"):
            hits = shared_injector.cache_stats().get("hits", 0)
        if shared_adapter and hasattr(shared_adapter, "stats"):
            calls = shared_adapter.stats().get("calls", 0)
        emit("ContextUpdated",
             file="<cache>",
             changes=f"Cache: hits={hits}, calls={calls}",
             content_hash=str(hash(str(time.time()))))
    except Exception:
        pass
