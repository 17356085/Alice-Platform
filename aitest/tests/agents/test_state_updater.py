"""Tests for agents/state_updater.py — state transitions after skill execution.

Tests: update_agent_state (pass/fail/partial/skipped),
_emit_milestone, emit_cache_summary, MILESTONE_SKILLS.
Pure logic — no LLM calls.
"""
import pytest
from unittest.mock import MagicMock

from aitest.agents.state_updater import (
    update_agent_state, _emit_milestone, emit_cache_summary,
    MILESTONE_SKILLS,
)
from aitest.agents.runner_state import AgentState, Observation


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


def _make_state(**overrides) -> AgentState:
    state = AgentState(agent_name="test-agent")
    for k, v in overrides.items():
        setattr(state, k, v)
    return state


def _make_obs(skill_id: str, status: str = "pass", summary: str = "OK") -> Observation:
    return Observation(skill_id=skill_id, status=status, summary=summary)


# ══════════════════════════════════════════════════════════════════════════
#  update_agent_state — step increment (C4 fix)
# ══════════════════════════════════════════════════════════════════════════


class TestStepIncrement:
    def test_step_increments_by_one(self):
        state = _make_state(step=0)
        update_agent_state(state, "skill-1", _make_obs("skill-1"))
        assert state.step == 1

    def test_step_increments_twice(self):
        state = _make_state(step=0)
        update_agent_state(state, "s1", _make_obs("s1"))
        update_agent_state(state, "s2", _make_obs("s2"))
        assert state.step == 2

    def test_step_does_not_double_increment(self):
        """C4 fix: step should only increment once per call."""
        state = _make_state(step=5)
        update_agent_state(state, "s1", _make_obs("s1"))
        assert state.step == 6  # Not 7


# ══════════════════════════════════════════════════════════════════════════
#  update_agent_state — pass
# ══════════════════════════════════════════════════════════════════════════


class TestPassTransition:
    def test_pass_adds_to_completed(self):
        state = _make_state()
        update_agent_state(state, "skill-1", _make_obs("skill-1", "pass"))
        assert "skill-1" in state.completed_skills

    def test_pass_clears_retry_count(self):
        state = _make_state(retry_counts={"skill-1": 2})
        update_agent_state(state, "skill-1", _make_obs("skill-1", "pass"))
        assert "skill-1" not in state.retry_counts

    def test_pass_stores_prev_output(self):
        state = _make_state()
        update_agent_state(state, "skill-1", _make_obs("skill-1", "pass", summary="Result text"))
        assert state.memory["prev_output"] == "Result text"

    def test_pass_does_not_add_to_failed(self):
        state = _make_state()
        update_agent_state(state, "skill-1", _make_obs("skill-1", "pass"))
        assert "skill-1" not in state.failed_skills


# ══════════════════════════════════════════════════════════════════════════
#  update_agent_state — fail
# ══════════════════════════════════════════════════════════════════════════


class TestFailTransition:
    def test_fail_increments_retry_count(self):
        state = _make_state()
        update_agent_state(state, "skill-1", _make_obs("skill-1", "fail"))
        assert state.retry_counts["skill-1"] == 1

    def test_fail_accumulates_retries(self):
        state = _make_state(retry_counts={"skill-1": 2})
        update_agent_state(state, "skill-1", _make_obs("skill-1", "fail"))
        assert state.retry_counts["skill-1"] == 3

    def test_fail_adds_to_failed_skills(self):
        state = _make_state()
        update_agent_state(state, "skill-1", _make_obs("skill-1", "fail", summary="Error msg"))
        assert state.failed_skills["skill-1"] == "Error msg"

    def test_fail_does_not_add_to_completed(self):
        state = _make_state()
        update_agent_state(state, "skill-1", _make_obs("skill-1", "fail"))
        assert "skill-1" not in state.completed_skills


# ══════════════════════════════════════════════════════════════════════════
#  update_agent_state — partial
# ══════════════════════════════════════════════════════════════════════════


class TestPartialTransition:
    def test_partial_increments_retry(self):
        state = _make_state()
        update_agent_state(state, "skill-1", _make_obs("skill-1", "partial"))
        assert state.retry_counts["skill-1"] == 1

    def test_partial_adds_to_failed(self):
        state = _make_state()
        update_agent_state(state, "skill-1", _make_obs("skill-1", "partial", summary="Partial"))
        assert state.failed_skills["skill-1"] == "Partial"


# ══════════════════════════════════════════════════════════════════════════
#  update_agent_state — skipped
# ══════════════════════════════════════════════════════════════════════════


class TestSkippedTransition:
    def test_skipped_adds_to_completed(self):
        state = _make_state()
        update_agent_state(state, "skill-1", _make_obs("skill-1", "skipped"))
        assert "skill-1" in state.completed_skills

    def test_skipped_does_not_add_to_failed(self):
        state = _make_state()
        update_agent_state(state, "skill-1", _make_obs("skill-1", "skipped"))
        assert "skill-1" not in state.failed_skills


# ══════════════════════════════════════════════════════════════════════════
#  update_agent_state — observation tracking
# ══════════════════════════════════════════════════════════════════════════


class TestObservationTracking:
    def test_observation_appended(self):
        state = _make_state()
        obs = _make_obs("skill-1", "pass")
        update_agent_state(state, "skill-1", obs)
        assert len(state.observations) == 1
        assert state.observations[0] is obs

    def test_current_skill_updated(self):
        state = _make_state()
        update_agent_state(state, "skill-1", _make_obs("skill-1"))
        assert state.current_skill == "skill-1"

    def test_multiple_observations_tracked(self):
        state = _make_state()
        update_agent_state(state, "s1", _make_obs("s1"))
        update_agent_state(state, "s2", _make_obs("s2"))
        update_agent_state(state, "s3", _make_obs("s3"))
        assert len(state.observations) == 3


# ══════════════════════════════════════════════════════════════════════════
#  MILESTONE_SKILLS
# ══════════════════════════════════════════════════════════════════════════


class TestMilestoneSkills:
    def test_contains_core_skills(self):
        assert "automation/page-object-generator" in MILESTONE_SKILLS
        assert "automation/test-script-generator" in MILESTONE_SKILLS
        assert "execution/allure-report-analyzer" in MILESTONE_SKILLS

    def test_all_are_strings(self):
        for skill in MILESTONE_SKILLS:
            assert isinstance(skill, str)


# ══════════════════════════════════════════════════════════════════════════
#  _emit_milestone
# ══════════════════════════════════════════════════════════════════════════


class TestEmitMilestone:
    def test_does_not_emit_for_non_milestone(self):
        """Non-milestone skill should not trigger event."""
        obs = _make_obs("nonexistent/skill", "pass")
        # Should not raise
        _emit_milestone("nonexistent/skill", obs, "test-agent", "equipment")

    def test_does_not_emit_for_fail(self):
        """Failed milestone should not trigger event."""
        obs = _make_obs("automation/page-object-generator", "fail")
        _emit_milestone("automation/page-object-generator", obs, "test-agent", "equipment")

    def test_emits_for_milestone_pass(self, monkeypatch):
        """Milestone skill pass should trigger AgentCompleted event."""
        mock_emit = MagicMock()
        monkeypatch.setattr("aitest.agents.state_updater.emit", mock_emit)
        obs = _make_obs("automation/page-object-generator", "pass")
        _emit_milestone("automation/page-object-generator", obs, "test-agent", "equipment")
        mock_emit.assert_called_once()
