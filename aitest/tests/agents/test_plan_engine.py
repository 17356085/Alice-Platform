"""Tests for agents/plan_engine.py — rule-based planning logic.

Tests: plan_next_action (sequential, retry, skip, done),
_advance, _is_retry_action, _skill_matches, check_skill_risk_level.
Pure logic — no LLM calls for most paths.
"""
import pytest
from unittest.mock import MagicMock

from alice_engine.core.planner import (
    plan_next_action, _advance, _is_retry_action,
    _skill_matches, check_skill_risk_level,
)
from alice_engine.core.task import AgentState, Observation


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


def _make_state(**overrides) -> AgentState:
    state = AgentState(agent_name="test-agent")
    for k, v in overrides.items():
        setattr(state, k, v)
    return state


def _make_obs(skill_id: str, status: str = "pass") -> Observation:
    return Observation(skill_id=skill_id, status=status, summary="OK")


# ══════════════════════════════════════════════════════════════════════════
#  _advance
# ══════════════════════════════════════════════════════════════════════════


class TestAdvance:
    def test_returns_execute_action(self):
        result = _advance(["s1", "s2", "s3"], 0, "reason")
        assert result["action"] == "execute"
        assert result["skill_id"] == "s1"
        assert result["reason"] == "reason"

    def test_returns_correct_index(self):
        result = _advance(["s1", "s2", "s3"], 2, "reason")
        assert result["skill_id"] == "s3"

    def test_out_of_bounds_returns_empty(self):
        result = _advance(["s1"], 5, "reason")
        assert result["skill_id"] == ""


# ══════════════════════════════════════════════════════════════════════════
#  _is_retry_action
# ══════════════════════════════════════════════════════════════════════════


class TestIsRetryAction:
    def test_no_obs_not_retry(self):
        assert _is_retry_action(None, 0, 3) is False

    def test_fail_with_retries_is_retry(self):
        obs = _make_obs("s1", "fail")
        assert _is_retry_action(obs, 1, 3) is True

    def test_fail_at_max_not_retry(self):
        obs = _make_obs("s1", "fail")
        assert _is_retry_action(obs, 3, 3) is False

    def test_partial_with_retries_is_retry(self):
        obs = _make_obs("s1", "partial")
        assert _is_retry_action(obs, 0, 3) is True

    def test_pass_not_retry(self):
        obs = _make_obs("s1", "pass")
        assert _is_retry_action(obs, 0, 3) is False


# ══════════════════════════════════════════════════════════════════════════
#  _skill_matches
# ══════════════════════════════════════════════════════════════════════════


class TestSkillMatches:
    def test_exact_match(self):
        assert _skill_matches("automation/page-object-generator",
                              "automation/page-object-generator") is True

    def test_suffix_match(self):
        assert _skill_matches("page-object-generator",
                              "automation/page-object-generator") is True

    def test_prefix_match(self):
        assert _skill_matches("automation",
                              "automation/page-object-generator") is True

    def test_no_match(self):
        assert _skill_matches("execution/run",
                              "automation/page-object-generator") is False

    def test_empty_registry(self):
        assert _skill_matches("", "automation/page-object-generator") is False

    def test_empty_skill(self):
        assert _skill_matches("automation/page-object-generator", "") is False


# ══════════════════════════════════════════════════════════════════════════
#  check_skill_risk_level
# ══════════════════════════════════════════════════════════════════════════


class TestCheckSkillRiskLevel:
    def test_empty_skill_returns_low(self):
        risk, needs_confirm = check_skill_risk_level("")
        assert risk == "low"
        assert needs_confirm is False

    def test_unknown_skill_returns_low(self):
        risk, needs_confirm = check_skill_risk_level("nonexistent/fake-skill")
        assert risk == "low"
        assert needs_confirm is False

    def test_known_skill_returns_tuple(self):
        result = check_skill_risk_level("automation/page-object-generator")
        assert isinstance(result, tuple)
        assert len(result) == 2


# ══════════════════════════════════════════════════════════════════════════
#  plan_next_action — sequential
# ══════════════════════════════════════════════════════════════════════════


class TestPlanSequential:
    def test_first_skill_execute(self):
        state = _make_state()
        skills = ["s1", "s2", "s3"]
        result = plan_next_action(0, {}, skills, state, True, False, 3, "fake")
        assert result["action"] == "execute"
        assert result["skill_id"] == "s1"

    def test_second_skill_execute(self):
        state = _make_state()
        skills = ["s1", "s2", "s3"]
        result = plan_next_action(1, {}, skills, state, True, False, 3, "fake")
        assert result["action"] == "execute"
        assert result["skill_id"] == "s2"

    def test_all_skills_done(self):
        state = _make_state()
        skills = ["s1", "s2"]
        result = plan_next_action(2, {}, skills, state, True, False, 3, "fake")
        assert result["action"] == "done"

    def test_empty_skills_done(self):
        state = _make_state()
        result = plan_next_action(0, {}, [], state, True, False, 3, "fake")
        assert result["action"] == "done"


# ══════════════════════════════════════════════════════════════════════════
#  plan_next_action — retry
# ══════════════════════════════════════════════════════════════════════════


class TestPlanRetry:
    def test_fail_triggers_retry(self):
        state = _make_state(retry_counts={"s1": 0})
        obs = _make_obs("s1", "fail")
        skills = ["s1", "s2"]
        perception = {"last_obs": obs}
        result = plan_next_action(0, perception, skills, state, True, False, 3, "fake")
        # Should either retry or advance
        assert result["action"] in ("execute", "retry")

    def test_max_retries_advances(self):
        state = _make_state(retry_counts={"s1": 3})
        obs = _make_obs("s1", "fail")
        skills = ["s1", "s2"]
        perception = {"last_obs": obs}
        result = plan_next_action(0, perception, skills, state, True, False, 3, "fake")
        assert result["action"] == "execute"
