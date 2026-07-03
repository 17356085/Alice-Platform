"""
UI Projection — AgentEvent → user-visible SSE event mapping. v2.5

Maps engine-level AgentEvent types to frontend-consumable UI events.
The frontend listens for named SSE events (ui.skill_started, ui.thinking_chunk, etc.)
via EventSource.addEventListener(), not es.onmessage.

Bridge:  AgentEvent → map_agent_event() → SSE dict → yield → EventSource → addEventListener

Usage:
    from aitest.platform.ui_projection import map_agent_event, UIEventType

    for agent_event in agent.run_interactive():
        sse_event = map_agent_event(agent_event)
        if sse_event:
            yield sse_event
"""

from __future__ import annotations

import json
from typing import Any, Optional


# ── UI Event Types (SSE event names) ────────────────────────────────────

class UIEventType:
    """Named SSE events the frontend listens for via addEventListener().

    Naming convention: ui.<domain>.<lifecycle>
    - ui.thinking.*  — agent reasoning / planning
    - ui.skill.*     — skill execution lifecycle
    - ui.phase.*     — SOP phase transitions
    - ui.message.*   — user-facing messages
    - ui.interaction — HITL pause
    - ui.lifecycle   — stream start/end
    """
    THINKING_STARTED = "ui.thinking_started"
    THINKING_CHUNK   = "ui.thinking_chunk"
    THINKING_ENDED   = "ui.thinking_ended"
    SKILL_STARTED    = "ui.skill_started"
    SKILL_PROGRESS   = "ui.skill_progress"
    SKILL_ENDED      = "ui.skill_ended"
    OBSERVATION      = "ui.observation"
    PHASE_CHANGED    = "ui.phase_changed"
    MESSAGE          = "ui.message"
    INTERACTION      = "ui.interaction"
    DONE             = "ui.done"
    ERROR            = "ui.error"


# ── Mapping ─────────────────────────────────────────────────────────────

def _sse(event_type: str, data: dict[str, Any]) -> dict:
    """Build an SSE dict for EventSourceResponse yield."""
    return {"event": event_type, "data": json.dumps(data, ensure_ascii=False)}


def map_agent_event(agent_event) -> Optional[dict]:
    """Map an AgentEvent to a UI SSE event dict.

    v3.1: agent_event 遵循 AgentEventProtocol（定义在 alice_engine.core.task）。
    字段: type, skill_id, content, status, summary, progress, token_usage, error,
          interaction_id, interaction_type, interaction_prompt, interaction_options

    Returns None for events that should be silently consumed (e.g. observe).
    """
    t = agent_event.type

    # ── Thinking / Planning ──
    if t == "agent_start":
        return _sse(UIEventType.THINKING_STARTED, {
            "message": "正在分析任务...",
            "agent": getattr(agent_event, "skill_id", ""),
        })

    if t in ("plan", "plan_result"):
        return _sse(UIEventType.THINKING_CHUNK, {
            "content": agent_event.content or "",
            "phase": "planning",
        })

    # ── Skill lifecycle ──
    if t == "skill_start":
        return _sse(UIEventType.SKILL_STARTED, {
            "skill_id": agent_event.skill_id,
            "label": agent_event.content or agent_event.skill_id,
            "progress": agent_event.progress or {},
        })

    if t == "skill_chunk":
        return _sse(UIEventType.SKILL_PROGRESS, {
            "content": agent_event.content or "",
            "skill_id": getattr(agent_event, "skill_id", ""),
            "progress": getattr(agent_event, "progress", {}),
        })

    if t == "skill_end":
        return _sse(UIEventType.SKILL_ENDED, {
            "skill_id": agent_event.skill_id,
            "status": "pass" if not agent_event.error else "fail",
            "summary": (agent_event.content or "")[:200],
            "token_usage": agent_event.token_usage or {},
        })

    # ── Observation ──
    if t == "observation":
        return _sse(UIEventType.OBSERVATION, {
            "skill_id": agent_event.skill_id,
            "status": agent_event.status or "",
            "summary": agent_event.summary or "",
        })

    if t == "observation_issue":
        return _sse(UIEventType.OBSERVATION, {
            "skill_id": agent_event.skill_id,
            "status": "issue",
            "summary": agent_event.summary or agent_event.content or "",
        })

    # ── SOP phases ──
    if t == "sop_start":
        return _sse(UIEventType.PHASE_CHANGED, {
            "content": agent_event.content or "",
            "phase": "start",
        })

    if t == "sop_phase":
        return _sse(UIEventType.PHASE_CHANGED, {
            "content": agent_event.content or "",
            "progress": agent_event.progress or {},
            "status": agent_event.status or "",
            "phase_id": agent_event.skill_id or "",
        })

    if t == "sop_complete":
        # Terminal event — emit as done (chat stream ends here)
        return _sse(UIEventType.DONE, {
            "success": agent_event.status not in ("failed", "completed_with_issues", "fail"),
            "summary": agent_event.summary or agent_event.content or "",
            "error": agent_event.error or "",
        })

    if t == "phase_complete":
        return _sse(UIEventType.PHASE_CHANGED, {
            "content": agent_event.content or "",
            "phase": "phase_complete",
            "phase_id": agent_event.skill_id or "",
        })

    # ── HITL interaction ──
    if t == "interaction_required":
        return _sse(UIEventType.INTERACTION, {
            "interaction_id": agent_event.interaction_id,
            "type": agent_event.interaction_type,
            "prompt": agent_event.interaction_prompt,
            "options": agent_event.interaction_options or [],
            "skill_id": agent_event.skill_id,
        })

    # ── Messages ──
    if t == "agent_message":
        return _sse(UIEventType.MESSAGE, {
            "role": "assistant",
            "type": "text",
            "content": agent_event.content or "",
        })

    # ── Lifecycle ──
    if t == "agent_end":
        # Emit final message + done in one shot
        return _sse(UIEventType.DONE, {
            "success": agent_event.status == "pass",
            "summary": agent_event.summary or agent_event.content or "",
            "error": agent_event.error or "",
        })

    if t == "perceive":
        # Silent — agent internal state, not user-visible
        return None

    # Fallback: pass through as thinking chunk
    if agent_event.content:
        return _sse(UIEventType.THINKING_CHUNK, {
            "content": agent_event.content,
            "phase": t,
        })

    return None
