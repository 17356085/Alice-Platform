"""Interactive SOP runner — HITL event generator.

Extracted from agent_runner.py (W01 refactor, 2026-06-17).
"""

from collections.abc import Generator
from aitest.agents.runner_state import AgentEvent


def run_interactive_loop(agent) -> Generator[AgentEvent, None, "AgentState"]:
    """Interactive SOP execution with HITL support. Delegated from AgentLoop.run_interactive()."""
    import time
    from aitest.agents.runner_state import AgentEventType
    from aitest.agents.skill_executor import run_skill

    agent.state.status = "running"
    agent._is_cancelled = False
    agent._review_triggered = False

    yield AgentEvent(type="agent_start", content=f"Agent {agent.agent_name} started",
                     agent_name=agent.agent_name, module=agent.module)

    skill_index = 0
    phase_index = 0
    while skill_index < len(agent.skills) and not agent._is_cancelled:
        skill_id = agent.skills[skill_index]
        agent._log(f"[{skill_index+1}/{len(agent.skills)}] {skill_id}")

        # Perceive
        perception = agent.perceive(skill_id)
        yield AgentEvent(type="agent_phase", content=f"Perceiving: {skill_id}",
                         skill_id=skill_id, phase="perceive")

        # Plan
        decision = agent.plan(skill_index, perception)
        action = decision.get("action", "execute")

        if action == "skip":
            agent._log(f"  Skip: {decision.get('reason', '')}")
            skill_index += 1
            continue
        elif action == "abort":
            agent._log(f"  Abort: {decision.get('reason', '')}")
            yield AgentEvent(type="agent_abort", content=decision.get("reason", ""))
            break
        elif action == "retry":
            agent._log(f"  Retry: {decision.get('reason', '')[:80]}")
            # Stay on same skill
            pass
        else:
            # execute — normal progression
            pass

        # Check for HITL interrupt
        if agent._interaction_queue and not agent._interaction_queue.empty():
            try:
                user_msg = agent._interaction_queue.get_nowait()
                yield AgentEvent(type="interaction_received", content=user_msg)
            except Exception:
                pass

        # Act
        yield AgentEvent(type="agent_phase", content=f"Executing: {skill_id}",
                         skill_id=skill_id, phase="act",
                         progress={"step": phase_index, "total": len(agent.skills)})

        try:
            if agent._should_stream(skill_id):
                response = agent._act_stream(skill_id)
                if response:
                    from aitest.llm.provider import StreamEvent
                    if isinstance(response, Generator):
                        for chunk in response:
                            if isinstance(chunk, StreamEvent):
                                yield AgentEvent(type="stream_token", content=chunk.text,
                                                 skill_id=skill_id)
                            elif hasattr(chunk, "content"):
                                yield AgentEvent(type="stream_token", content=str(chunk.content)[:500],
                                                 skill_id=skill_id)
                        # Get final response
                        response = agent._act_stream_final(skill_id)
                    if response and hasattr(response, "content"):
                        pass  # Use as final response
            else:
                response = agent.act(skill_id)
        except Exception as e:
            agent._log(f"  Error: {e}")
            response = type("LLMResponse", (), {"content": f"ERROR: {e}", "finish_reason": "error",
                         "model": "error", "token_usage": {"input": 0, "output": 0}})()

        # Observe
        observation = agent.observe(skill_id, response)
        yield AgentEvent(type="agent_phase", content=f"Observed: {skill_id} — {observation.status}",
                         skill_id=skill_id, phase="observe",
                         observation={"status": observation.status, "summary": observation.summary})

        # Update
        agent.update(skill_id, observation)

        # Progress
        if action != "retry":
            if observation.status == "pass":
                skill_index += 1
            elif observation.status in ("fail", "partial"):
                retries = agent.state.retry_counts.get(skill_id, 0)
                if retries >= agent.MAX_RETRIES:
                    skill_index += 1

        phase_index += 1

    # Complete
    agent.state.status = "completed" if not agent._is_cancelled else "cancelled"
    agent.state.completed_at = time.time()

    # Emit cache summary
    try:
        from aitest.agents.state_updater import emit_cache_summary
        emit_cache_summary(None, None, logger=agent._log)
    except Exception:
        pass

    yield AgentEvent(type="agent_complete",
                     content=f"Completed: {len(agent.state.completed_skills)}/{len(agent.skills)} skills",
                     agent_name=agent.agent_name,
                     state={"completed": agent.state.completed_skills,
                            "failed": list(agent.state.failed_skills.keys())})

    return agent.state
