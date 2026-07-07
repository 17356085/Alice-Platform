"""Tests for agents/task_state_machine.py — declarative FSM.

Tests: TaskState enum, VALID_TRANSITIONS (all valid + invalid paths),
TaskStateContext, transition validation.
Pure logic — zero dependencies.
"""
import pytest

from alice_engine.core.state_machine import (
    TaskState, TaskStateContext, VALID_TRANSITIONS,
)


# ══════════════════════════════════════════════════════════════════════════
#  TaskState enum
# ══════════════════════════════════════════════════════════════════════════


class TestTaskState:
    def test_all_values_are_strings(self):
        for state in TaskState:
            assert isinstance(state.value, str)
            assert state.value == state.value.lower()

    def test_terminal_states(self):
        """DONE has no outgoing transitions."""
        assert VALID_TRANSITIONS[TaskState.DONE] == set()

    def test_error_can_recover(self):
        """ERROR allows retry — not a dead end."""
        transitions = VALID_TRANSITIONS[TaskState.ERROR]
        assert TaskState.TEST_PLANNING in transitions
        assert TaskState.TEST_EXECUTION in transitions
        assert TaskState.DONE in transitions


# ══════════════════════════════════════════════════════════════════════════
#  VALID_TRANSITIONS
# ══════════════════════════════════════════════════════════════════════════


class TestValidTransitions:
    def test_all_states_have_defined_transitions(self):
        for state in TaskState:
            assert state in VALID_TRANSITIONS, f"{state} missing from VALID_TRANSITIONS"

    def test_backlog_only_goes_to_test_planning(self):
        assert VALID_TRANSITIONS[TaskState.BACKLOG] == {TaskState.TEST_PLANNING}

    def test_test_execution_goes_to_validation_or_retry(self):
        trans = VALID_TRANSITIONS[TaskState.TEST_EXECUTION]
        assert TaskState.RESULT_VALIDATION in trans
        assert TaskState.ISSUE_RETRY in trans
        assert TaskState.ERROR in trans

    def test_result_validation_goes_to_retry_or_approval(self):
        trans = VALID_TRANSITIONS[TaskState.RESULT_VALIDATION]
        assert TaskState.ISSUE_RETRY in trans
        assert TaskState.TEST_APPROVAL in trans

    def test_issue_retry_returns_to_validation_or_approval(self):
        trans = VALID_TRANSITIONS[TaskState.ISSUE_RETRY]
        assert TaskState.RESULT_VALIDATION in trans
        assert TaskState.TEST_APPROVAL in trans

    def test_plan_review_is_hitl_gate(self):
        """Plan review can go back to backlog or forward to execution."""
        trans = VALID_TRANSITIONS[TaskState.PLAN_REVIEW]
        assert TaskState.TEST_EXECUTION in trans  # approved
        assert TaskState.BACKLOG in trans           # rejected → back

    def test_complete_cycle_exists(self):
        """There is a path from BACKLOG → ... → DONE."""
        # BACKLOG → TEST_PLANNING → PLAN_REVIEW → TEST_EXECUTION →
        # RESULT_VALIDATION → TEST_APPROVAL → DONE
        path = [
            TaskState.BACKLOG,
            TaskState.TEST_PLANNING,
            TaskState.PLAN_REVIEW,
            TaskState.TEST_EXECUTION,
            TaskState.RESULT_VALIDATION,
            TaskState.TEST_APPROVAL,
            TaskState.DONE,
        ]
        for i in range(len(path) - 1):
            current = path[i]
            next_state = path[i + 1]
            assert next_state in VALID_TRANSITIONS[current], \
                f"Cannot transition {current} → {next_state}"

    def test_retry_cycle(self):
        """TEST_EXECUTION → ISSUE_RETRY → RESULT_VALIDATION is valid."""
        assert TaskState.ISSUE_RETRY in VALID_TRANSITIONS[TaskState.TEST_EXECUTION]
        assert TaskState.RESULT_VALIDATION in VALID_TRANSITIONS[TaskState.ISSUE_RETRY]

    def test_no_self_transitions(self):
        """No state should transition to itself (infinite loop prevention)."""
        for state, targets in VALID_TRANSITIONS.items():
            assert state not in targets, f"{state} should not self-transition"


# ══════════════════════════════════════════════════════════════════════════
#  TaskStateContext
# ══════════════════════════════════════════════════════════════════════════


class TestTaskStateContext:
    def test_defaults(self):
        ctx = TaskStateContext()
        assert ctx.state == TaskState.BACKLOG
        assert ctx.subtask_count == 0
        assert ctx.completed_count == 0
        assert ctx.qa_iteration == 0
        assert ctx.max_qa_iterations == 3

    def test_custom_state(self):
        ctx = TaskStateContext(state=TaskState.TEST_EXECUTION, subtask_count=5)
        assert ctx.state == TaskState.TEST_EXECUTION
        assert ctx.subtask_count == 5

    def test_error_message_starts_none(self):
        ctx = TaskStateContext()
        assert ctx.error_message is None

    def test_review_reason_starts_none(self):
        ctx = TaskStateContext()
        assert ctx.review_reason is None
