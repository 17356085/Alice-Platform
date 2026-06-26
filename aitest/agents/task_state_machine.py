"""Task State Machine — pure declarative FSM (Layer 1).

Task 4 (P1) — APERANT_MIGRATION_PLAN.md
Port of Aperant task-machine.ts, adapted to aitest test-execution semantics.

Architecture (three-layer separation):
  Layer 1 (this file):  Pure state definitions + transitions. Zero I/O.
  Layer 2:              pipeline_router.py reads FSM state, drives execution.
  Layer 3:              pause_handler.py handles sentinel file communication.

States (aitest-semantic, per migration plan §语义映射):
  backlog → test_planning → plan_review → test_execution →
  result_validation → test_approval → done

Design: zero external dependencies. Unit-testable without mocking.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TaskState(str, Enum):
    """Task lifecycle states — aitest test-execution semantics."""
    BACKLOG = "backlog"
    TEST_PLANNING = "test_planning"
    PLAN_REVIEW = "plan_review"           # HITL gate — user must approve
    TEST_EXECUTION = "test_execution"     # Running test skills
    RESULT_VALIDATION = "result_validation"  # Verify test results
    ISSUE_RETRY = "issue_retry"           # Retry failed tests
    TEST_APPROVAL = "test_approval"       # Final HITL gate
    DONE = "done"
    ERROR = "error"


# Valid transitions — immutable lookup
VALID_TRANSITIONS: dict[TaskState, set[TaskState]] = {
    TaskState.BACKLOG:           {TaskState.TEST_PLANNING},
    TaskState.TEST_PLANNING:     {TaskState.PLAN_REVIEW, TaskState.TEST_EXECUTION, TaskState.ERROR},
    TaskState.PLAN_REVIEW:       {TaskState.TEST_EXECUTION, TaskState.BACKLOG, TaskState.ERROR},
    TaskState.TEST_EXECUTION:    {TaskState.RESULT_VALIDATION, TaskState.ISSUE_RETRY, TaskState.ERROR},
    TaskState.RESULT_VALIDATION: {TaskState.ISSUE_RETRY, TaskState.TEST_APPROVAL, TaskState.ERROR},
    TaskState.ISSUE_RETRY:       {TaskState.RESULT_VALIDATION, TaskState.TEST_APPROVAL, TaskState.ERROR},
    TaskState.TEST_APPROVAL:     {TaskState.DONE, TaskState.TEST_EXECUTION, TaskState.ERROR},
    TaskState.DONE:              set(),   # Terminal
    TaskState.ERROR:             {TaskState.TEST_PLANNING, TaskState.TEST_EXECUTION, TaskState.DONE},
}


@dataclass
class TaskStateContext:
    """Lightweight FSM state container — zero dependencies."""
    state: TaskState = TaskState.BACKLOG
    review_reason: Optional[str] = None   # Why we're in plan_review or test_approval
    error_message: Optional[str] = None
    subtask_count: int = 0
    completed_count: int = 0
    qa_iteration: int = 0
    max_qa_iterations: int = 3

    # ── Transition ──

    def transition(self, to_state: TaskState, reason: str = "") -> bool:
        """Attempt a state transition. Returns True if valid, False if invalid."""
        if to_state not in VALID_TRANSITIONS.get(self.state, set()):
            return False
        self.state = to_state
        self.review_reason = reason or None
        return True

    def is_terminal(self) -> bool:
        return self.state in (TaskState.DONE, TaskState.ERROR)

    # ── Convenience predicates ──

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

    # ── Serialization ──

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
