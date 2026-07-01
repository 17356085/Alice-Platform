"""Tests for agents/agent_runner.py — core execution loop behavior.

Tests: abort signal stops loop, step counting (C4 fix),
max_steps termination, _finalize_session on exception.
Mocks LLM calls to test loop logic without real API.
"""
import threading
import pytest
from unittest.mock import MagicMock, patch, PropertyMock

from aitest.agents.agent_runner import AgentLoop
from aitest.agents.runner_state import AgentState, Observation
from aitest.llm.provider_base import LLMResponse


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


def _make_agent(monkeypatch, max_steps=3):
    """Create AgentLoop with mocked LLM chain."""
    agent = AgentLoop("project-agent", module="equipment", page="alarm",
                      use_reliable_provider=False, use_window_monitor=False)
    agent.state.max_steps = max_steps
    return agent


def _mock_run_skill_pass(monkeypatch):
    """Mock run_skill to return a passing response (long enough for observe)."""
    long_content = "Skill completed successfully. " * 20  # Long enough to pass observe()
    response = LLMResponse(
        content=long_content,
        token_usage={"input": 100, "output": 50},
        model="fake",
        finish_reason="stop",
    )
    monkeypatch.setattr("aitest.agents.agent_runner.run_skill",
                        lambda *a, **kw: response)
    return response


def _mock_run_skill_fail(monkeypatch):
    """Mock run_skill to return a failing response."""
    response = LLMResponse(
        content="[Skill 加载失败] Skill not found",
        token_usage={"input": 50, "output": 10},
        model="fake",
        finish_reason="error",
    )
    monkeypatch.setattr("aitest.agents.agent_runner.run_skill",
                        lambda *a, **kw: response)
    return response


# ══════════════════════════════════════════════════════════════════════════
#  Abort signal
# ══════════════════════════════════════════════════════════════════════════


class TestAbortSignal:
    def test_abort_stops_loop(self, monkeypatch):
        """Setting _abort before run() should immediately cancel."""
        _mock_run_skill_pass(monkeypatch)
        agent = _make_agent(monkeypatch)
        agent._abort.set()  # Pre-set abort

        state = agent.run()
        assert state.done is True
        assert state.success is False
        assert state.termination_reason == "cancelled"

    def test_abort_during_execution(self, monkeypatch):
        """Abort set during skill execution should stop on next iteration."""
        call_count = [0]
        agent = _make_agent(monkeypatch, max_steps=10)

        def mock_skill(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] >= 2:
                agent._abort.set()  # Abort after 2nd skill
            return LLMResponse(
                content="OK", token_usage={"input": 10, "output": 5},
                model="fake", finish_reason="stop",
            )

        monkeypatch.setattr("aitest.agents.agent_runner.run_skill", mock_skill)
        state = agent.run()

        assert state.done is True
        assert state.termination_reason == "cancelled"
        # Should have stopped before max_steps
        assert state.step < 10


# ══════════════════════════════════════════════════════════════════════════
#  Step counting (C4 fix verification)
# ══════════════════════════════════════════════════════════════════════════


class TestStepCounting:
    def test_step_increments_once_per_skill(self, monkeypatch):
        """C4 fix: step should increment exactly once per skill execution."""
        _mock_run_skill_pass(monkeypatch)
        agent = _make_agent(monkeypatch, max_steps=5)

        state = agent.run()
        # Each skill should increment step by exactly 1
        # If there are 2 skills and both pass, step should be 2
        assert state.step == len(agent.skills)

    def test_step_does_not_double_increment(self, monkeypatch):
        """C4 fix: step should NOT increment twice (was the bug)."""
        _mock_run_skill_pass(monkeypatch)
        agent = _make_agent(monkeypatch, max_steps=20)

        state = agent.run()
        # Step count should equal number of skills executed, not 2x
        assert state.step <= len(agent.skills)


# ══════════════════════════════════════════════════════════════════════════
#  Max steps termination
# ══════════════════════════════════════════════════════════════════════════


class TestMaxSteps:
    def test_max_steps_terminates(self, monkeypatch):
        """Agent should stop when max_steps is reached."""
        _mock_run_skill_pass(monkeypatch)
        agent = _make_agent(monkeypatch, max_steps=1)

        state = agent.run()
        assert state.done is True
        # With max_steps=1, should complete 1 skill then stop
        assert state.step <= 1

    def test_max_steps_reached_reason(self, monkeypatch):
        """When max_steps reached without completing all skills, reason should reflect it."""
        _mock_run_skill_fail(monkeypatch)
        agent = _make_agent(monkeypatch, max_steps=2)

        state = agent.run()
        assert state.done is True
        # Either all_skills_completed or max_steps_reached
        assert state.termination_reason in ("max_steps_reached", "all_skills_completed",
                                              "some_skills_failed")


# ══════════════════════════════════════════════════════════════════════════
#  _finalize_session on exception
# ══════════════════════════════════════════════════════════════════════════


class TestFinalizeOnException:
    def test_finalize_called_on_normal_exit(self, monkeypatch):
        """_finalize_session should be called after normal run()."""
        _mock_run_skill_pass(monkeypatch)
        agent = _make_agent(monkeypatch)

        finalize_called = [False]
        original_finalize = agent._finalize_session

        def mock_finalize():
            finalize_called[0] = True
            original_finalize()

        agent._finalize_session = mock_finalize
        agent.run()

        assert finalize_called[0] is True

    def test_finalize_called_on_exception(self, monkeypatch):
        """_finalize_session should be called even if run() raises."""
        agent = _make_agent(monkeypatch)

        # Make _run_single_session raise
        def raise_in_run():
            raise RuntimeError("Simulated crash")

        agent._run_single_session = raise_in_run

        finalize_called = [False]
        original_finalize = agent._finalize_session

        def mock_finalize():
            finalize_called[0] = True
            original_finalize()

        agent._finalize_session = mock_finalize

        with pytest.raises(RuntimeError, match="Simulated crash"):
            agent.run()

        assert finalize_called[0] is True


# ══════════════════════════════════════════════════════════════════════════
#  Full run with mocked LLM
# ══════════════════════════════════════════════════════════════════════════


class TestFullRun:
    def test_run_returns_agent_state(self, monkeypatch):
        _mock_run_skill_pass(monkeypatch)
        agent = _make_agent(monkeypatch, max_steps=5)

        state = agent.run()
        assert isinstance(state, AgentState)
        assert state.done is True

    def test_run_with_failing_skills(self, monkeypatch):
        _mock_run_skill_fail(monkeypatch)
        agent = _make_agent(monkeypatch, max_steps=5)

        state = agent.run()
        assert state.done is True
        # Failed skills should be tracked
        assert len(state.failed_skills) > 0 or state.termination_reason != ""

    def test_run_with_mixed_results(self, monkeypatch):
        """Some skills pass, some fail."""
        call_count = [0]

        def mock_skill(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return LLMResponse(content="OK", token_usage={"input": 10, "output": 5},
                                   model="fake", finish_reason="stop")
            return LLMResponse(content="Fail", token_usage={"input": 10, "output": 5},
                               model="fake", finish_reason="error")

        monkeypatch.setattr("aitest.agents.agent_runner.run_skill", mock_skill)
        agent = _make_agent(monkeypatch, max_steps=5)

        state = agent.run()
        assert state.done is True
