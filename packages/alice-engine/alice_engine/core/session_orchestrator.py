"""Internal single-session loop orchestration for AgentLoop."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from alice_engine.core.task import Observation
from alice_engine.events import EventType


@dataclass
class SessionIterationResult:
    next_skill_index: int
    should_continue: bool = True


class SessionLoopOrchestrator:
    """Coordinate one loop iteration without owning the full AgentLoop object."""

    def __init__(
        self,
        *,
        state,
        skills: list[str],
        agent_name: str,
        module: str,
        page: str,
        provider: str,
        abort_event,
        replay_sink,
        replay_recorder,
        perceive_fn: Callable[[str], dict],
        plan_fn: Callable[[int, dict], dict],
        act_fn: Callable[[str], Any],
        observe_fn: Callable[[str, Any], Observation],
        update_fn: Callable[[str, Observation], None],
        persist_skill_artifact_fn: Callable[[str, str], str],
        emit_obs_fn: Callable[[EventType, dict], None],
        log_fn: Callable[[str], None],
        retry_counts: dict[str, int],
        completed_skills_getter: Callable[[], list[str]],
    ) -> None:
        self.state = state
        self.skills = skills
        self.agent_name = agent_name
        self.module = module
        self.page = page
        self.provider = provider
        self.abort_event = abort_event
        self.replay_sink = replay_sink
        self.replay_recorder = replay_recorder
        self.perceive = perceive_fn
        self.plan = plan_fn
        self.act = act_fn
        self.observe = observe_fn
        self.update = update_fn
        self.persist_skill_artifact = persist_skill_artifact_fn
        self.emit_obs = emit_obs_fn
        self.log = log_fn
        self.retry_counts = retry_counts
        self.completed_skills_getter = completed_skills_getter

    def run_iteration(self, skill_index: int) -> SessionIterationResult:
        if self.abort_event is not None and self.abort_event.is_set():
            self.state.done = True
            self.state.success = False
            self.state.termination_reason = "cancelled"
            self.log("🛑 Agent cancelled via abort signal")
            return SessionIterationResult(next_skill_index=skill_index, should_continue=False)

        current_skill = self.skills[skill_index] if skill_index < len(self.skills) else ""
        perception = self.perceive(current_skill) if current_skill else {}
        plan_result = self.plan(skill_index, perception)

        if plan_result["action"] == "done":
            self.state.done = True
            self.state.success = True
            self.state.termination_reason = "all_skills_completed"
            self.log("✅ 所有 Skill 已完成")
            return SessionIterationResult(next_skill_index=skill_index, should_continue=False)

        if plan_result["action"] == "confirm_required":
            skill_id = plan_result["skill_id"]
            safe_skill = skill_id.replace("/", "_").replace(":", "_")
            task_id = plan_result.get("task_id", f"{self.module}--{safe_skill}")
            risk_level = plan_result.get("risk_level", "high")
            self.log(f"  ⏸️  HITL: 等待确认执行 '{skill_id}' (risk={risk_level}, task={task_id})")
            try:
                from alice_engine.core.planner import confirm_skill

                confirm_skill(skill_id, self.module)
                self.log(f"  ✅ Auto-confirmed '{skill_id}' (SDK mode)")
            except Exception:
                pass
            plan_result = self.plan(skill_index, perception)
            if plan_result["action"] in ("confirm_required", "done", "abort"):
                return SessionIterationResult(next_skill_index=skill_index, should_continue=True)

        if plan_result["action"] == "abort":
            self.state.done = True
            self.state.success = False
            self.state.termination_reason = f"agent_aborted: {plan_result['reason']}"
            self.log(f"🛑 Agent 中止: {plan_result['reason']}")
            return SessionIterationResult(next_skill_index=skill_index, should_continue=False)

        if plan_result["action"] == "skip":
            skill_id = plan_result["skill_id"]
            self.log(f"  ⏭️ [{skill_index + 1}/{len(self.skills)}] {skill_id} — {plan_result['reason']}")
            obs = Observation(skill_id=skill_id, status="skipped", summary=plan_result["reason"], suggestion="continue")
            self.update(skill_id, obs)
            return self._advance_index(skill_index + 1)

        skill_id = plan_result["skill_id"]
        is_retry = plan_result["action"] == "retry"
        if is_retry:
            retry_n = self.retry_counts.get(skill_id, 1)
            self.log(f"  🔄 [{skill_index + 1}/{len(self.skills)}] {skill_id} — 重试 #{retry_n}...")
            self.emit_obs(EventType.SKILL_RETRY, {"skill_id": skill_id, "attempt": retry_n})
        else:
            self.log(f"  ▶️  [{skill_index + 1}/{len(self.skills)}] {skill_id}...")
            self.emit_obs(EventType.SKILL_START, {"skill_id": skill_id})

        self.replay_sink.recorder = self.replay_recorder
        replay_step = self.replay_sink.begin_skill_step(
            skill_id=skill_id,
            skill_index=skill_index,
            module=self.module,
            page=self.page,
            agent_name=self.agent_name,
        )
        response = self.act(skill_id)
        self.replay_sink.record_skill_response(
            replay_step=replay_step,
            response=response,
            provider=self.provider,
        )

        if response.content and response.finish_reason != "error":
            saved = self.persist_skill_artifact(skill_id, response.content)
            if saved:
                self.log(f"  📄 saved: {Path(saved).name}")

        if not is_retry and response.finish_reason != "error":
            usage = getattr(response, "usage", {}) or {}
            elapsed = usage.get("elapsed_seconds", 0)
            tokens_in = usage.get("input", 0)
            tokens_out = usage.get("output", 0)
            self.log(f"✅ {elapsed:.1f}s | {tokens_in}+{tokens_out} tokens")
            self.emit_obs(
                EventType.SKILL_COMPLETE,
                {
                    "skill_id": skill_id,
                    "elapsed": elapsed,
                    "tokens_in": tokens_in,
                    "tokens_out": tokens_out,
                },
            )
        elif response.finish_reason == "error":
            self.emit_obs(
                EventType.SKILL_FAILED,
                {"skill_id": skill_id, "error": response.content[:200]},
            )

        observation = self.observe(skill_id, response)
        self.update(skill_id, observation)

        next_skill_index = skill_index if observation.suggestion == "retry" else skill_index + 1
        return self._advance_index(next_skill_index)

    def apply_max_steps_termination(self) -> None:
        if self.state.step >= self.state.max_steps and not self.state.done:
            self.state.done = True
            self.state.success = False
            self.state.termination_reason = "max_steps_reached"

    def _advance_index(self, next_skill_index: int) -> SessionIterationResult:
        if next_skill_index >= len(self.skills):
            all_pass = all(skill in self.completed_skills_getter() for skill in self.skills)
            self.state.done = True
            self.state.success = all_pass
            self.state.termination_reason = "all_skills_completed" if all_pass else "some_skills_failed"
            return SessionIterationResult(next_skill_index=next_skill_index, should_continue=False)
        return SessionIterationResult(next_skill_index=next_skill_index, should_continue=True)
