"""Task State Machine + State Updater — 状态管理 + 事件发射。

合并自:
  - agents/task_state_machine.py (纯 FSM 定义 + 转换)
  - agents/state_updater.py (状态更新 + 事件发射)

解耦: event_bus 通过参数传入，不再 import 平台模块。
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Callable


# ══════════════════════════════════════════════════════════════════════════
#  Task State Machine
# ══════════════════════════════════════════════════════════════════════════

class TaskState(str, Enum):
    """Task lifecycle states."""
    BACKLOG = "backlog"
    TEST_PLANNING = "test_planning"
    PLAN_REVIEW = "plan_review"
    TEST_EXECUTION = "test_execution"
    RESULT_VALIDATION = "result_validation"
    ISSUE_RETRY = "issue_retry"
    TEST_APPROVAL = "test_approval"
    DONE = "done"
    ERROR = "error"


VALID_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.BACKLOG:           {TaskState.TEST_PLANNING},
    TaskState.TEST_PLANNING:     {TaskState.PLAN_REVIEW, TaskState.TEST_EXECUTION, TaskState.ERROR},
    TaskState.PLAN_REVIEW:       {TaskState.TEST_EXECUTION, TaskState.BACKLOG, TaskState.ERROR},
    TaskState.TEST_EXECUTION:    {TaskState.RESULT_VALIDATION, TaskState.ISSUE_RETRY, TaskState.ERROR},
    TaskState.RESULT_VALIDATION: {TaskState.ISSUE_RETRY, TaskState.TEST_APPROVAL, TaskState.ERROR},
    TaskState.ISSUE_RETRY:       {TaskState.RESULT_VALIDATION, TaskState.TEST_APPROVAL, TaskState.ERROR},
    TaskState.TEST_APPROVAL:     {TaskState.DONE, TaskState.TEST_EXECUTION, TaskState.ERROR},
    TaskState.DONE:              set(),
    TaskState.ERROR:             {TaskState.TEST_PLANNING, TaskState.TEST_EXECUTION, TaskState.DONE},
}


@dataclass
class TaskStateContext:
    """Lightweight FSM state container — zero dependencies."""
    state: TaskState = TaskState.BACKLOG
    review_reason: Optional[str] = None
    error_message: Optional[str] = None
    subtask_count: int = 0
    completed_count: int = 0
    qa_iteration: int = 0
    max_qa_iterations: int = 3

    def transition(self, to_state: TaskState, reason: str = "") -> bool:
        if to_state not in VALID_TRANSITIONS.get(self.state, set()):
            return False
        self.state = to_state
        self.review_reason = reason or None
        return True

    def is_terminal(self) -> bool:
        return self.state in (TaskState.DONE, TaskState.ERROR)

    @property
    def is_backlog(self) -> bool:
        return self.state == TaskState.BACKLOG

    @property
    def is_planning(self) -> bool:
        return self.state == TaskState.TEST_PLANNING

    @property
    def is_plan_review(self) -> bool:
        return self.state == TaskState.PLAN_REVIEW

    @property
    def is_executing(self) -> bool:
        return self.state == TaskState.TEST_EXECUTION

    @property
    def is_validating(self) -> bool:
        return self.state == TaskState.RESULT_VALIDATION

    @property
    def is_retrying(self) -> bool:
        return self.state == TaskState.ISSUE_RETRY

    @property
    def is_approval(self) -> bool:
        return self.state == TaskState.TEST_APPROVAL

    @property
    def is_done(self) -> bool:
        return self.state == TaskState.DONE

    @property
    def is_error(self) -> bool:
        return self.state == TaskState.ERROR

    def to_dict(self) -> dict:
        return {
            "state": self.state.value,
            "review_reason": self.review_reason,
            "error_message": self.error_message,
            "subtask_count": self.subtask_count,
            "completed_count": self.completed_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TaskStateContext":
        return cls(
            state=TaskState(data.get("state", "backlog")),
            review_reason=data.get("review_reason"),
            error_message=data.get("error_message"),
            subtask_count=data.get("subtask_count", 0),
            completed_count=data.get("completed_count", 0),
        )


# ══════════════════════════════════════════════════════════════════════════
#  State Updater
# ══════════════════════════════════════════════════════════════════════════

# 里程碑 Skills — 这些 Skill 通过时会发射事件
# v3.1: 从 FALLBACK_AGENT_SKILL_MAP 动态生成，消除重复维护
from alice_engine.core.agent_definitions import FALLBACK_AGENT_SKILL_MAP

def _build_milestone_skills() -> list[str]:
    """从 FALLBACK_AGENT_SKILL_MAP 构建里程碑 Skill 列表。"""
    milestones = []
    for skills in FALLBACK_AGENT_SKILL_MAP.values():
        milestones.extend(skills)
    return milestones

MILESTONE_SKILLS = _build_milestone_skills()
_legacy_event_emitter: Callable[..., object] | None = None


def register_legacy_event_emitter(emitter: Callable[..., object] | None) -> None:
    """Register an optional compatibility event emitter.

    Platform-side compatibility shims can call this during import so the SDK
    stays free of reverse imports into ``aitest``.
    """
    global _legacy_event_emitter
    _legacy_event_emitter = emitter


def update_agent_state(state, skill_id: str, observation,
                       agent_name: str = "", module: str = "",
                       event_bus=None, logger=None):
    """Update AgentState after skill execution.

    Handles: pass/fail/partial/skipped transitions, retry counting,
    milestone event emission.

    Args:
        state: AgentState
        skill_id: Skill ID
        observation: Observation
        agent_name: Agent name
        module: Module name
        event_bus: EventBus instance (optional, for milestone events)
        logger: Logger function (optional)
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

    _emit_milestone(skill_id, observation, agent_name, module, event_bus, logger)


def _emit_milestone(skill_id: str, observation, agent_name: str = "", module: str = "",
                    event_bus=None, logger=None):
    """Emit AgentCompleted event when a milestone skill passes."""
    if skill_id not in MILESTONE_SKILLS or observation.status != "pass":
        return
    if event_bus:
        try:
            event_bus.emit("agent_completed", {
                "agent": agent_name,
                "module": module,
                "skill": skill_id,
                "status": "success",
                "artifacts": observation.summary,
            })
        except Exception:
            pass
        return
    if _legacy_event_emitter is not None:
        try:
            _legacy_event_emitter(
            "agent_completed",
            agent=agent_name,
            module=module,
            skill=skill_id,
            status="success",
            artifacts=observation.summary,
        )
        except Exception:
            pass


def emit_cache_summary(stats: dict | None = None, *, event_bus=None, logger=None) -> None:
    """Backward-compatible cache summary hook.

    The runtime SDK no longer owns a concrete cache bus, but old callers/tests
    still import this symbol.
    """
    payload = stats or {}
    if event_bus and hasattr(event_bus, "emit"):
        try:
            event_bus.emit("cache_summary", payload)
            return
        except Exception:
            pass
    if _legacy_event_emitter is not None:
        try:
            _legacy_event_emitter("cache_summary", payload)
        except Exception:
            pass
