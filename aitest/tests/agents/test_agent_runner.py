"""Tests for agents/agent_runner.py — core execution engine.

Tests: AgentLoop init, list_agents, list_dev_agents, run_agent,
abort signal, _finalize_session idempotency.
No real LLM — AgentLoop.run() not called (would need full mock chain).
Focuses on wiring, state, and lifecycle correctness.
"""
import threading
import pytest
from unittest.mock import MagicMock, patch

from aitest.agents.agent_runner import (
    AgentLoop, list_agents, list_dev_agents, run_agent,
    AGENT_SKILL_MAP, DEV_AGENT_SKILL_MAP,
)
from aitest.agents.runner_state import AgentState


# ══════════════════════════════════════════════════════════════════════════
#  list_agents / list_dev_agents
# ══════════════════════════════════════════════════════════════════════════


class TestListAgents:
    def test_returns_sorted_list(self):
        agents = list_agents()
        assert agents == sorted(agents)

    def test_contains_core_agents(self):
        agents = list_agents()
        for name in ["project-agent", "automation-agent", "execution-agent", "report-agent"]:
            assert name in agents, f"{name} missing from list_agents()"

    def test_no_duplicates(self):
        agents = list_agents()
        assert len(agents) == len(set(agents))

    def test_list_dev_agents(self):
        dev = list_dev_agents()
        assert isinstance(dev, list)
        # All dev agents should be strings
        for name in dev:
            assert isinstance(name, str)


# ══════════════════════════════════════════════════════════════════════════
#  AGENT_SKILL_MAP / DEV_AGENT_SKILL_MAP
# ══════════════════════════════════════════════════════════════════════════


class TestAgentSkillMaps:
    def test_core_map_has_agents(self):
        assert len(AGENT_SKILL_MAP) >= 8

    def test_all_skills_are_strings(self):
        for agent, skills in AGENT_SKILL_MAP.items():
            for skill in skills:
                assert isinstance(skill, str), f"{agent}: non-string skill"

    def test_dev_map_is_dict(self):
        assert isinstance(DEV_AGENT_SKILL_MAP, dict)


# ══════════════════════════════════════════════════════════════════════════
#  AgentLoop.__init__
# ══════════════════════════════════════════════════════════════════════════


class TestAgentLoopInit:
    def test_init_known_agent(self):
        agent = AgentLoop("project-agent", module="equipment", page="alarm")
        assert agent.agent_name == "project-agent"
        assert agent.module == "equipment"
        assert agent.page == "alarm"

    def test_init_unknown_agent_raises(self):
        with pytest.raises(ValueError, match="Unknown agent"):
            AgentLoop("nonexistent-agent-xyz")

    def test_init_with_provider(self):
        agent = AgentLoop("project-agent", provider="deepseek", module="m", page="p")
        assert agent.provider == "deepseek"

    def test_init_with_skill_subset(self):
        agent = AgentLoop("automation-agent", skill_subset=["automation/tech-analysis"],
                          module="m", page="p")
        assert agent._skill_subset == ["automation/tech-analysis"]

    def test_abort_signal_initialized(self):
        agent = AgentLoop("project-agent", module="m", page="p")
        assert isinstance(agent._abort, threading.Event)
        assert not agent._abort.is_set()

    def test_mcp_clients_initialized_empty(self):
        agent = AgentLoop("project-agent", module="m", page="p")
        assert agent._mcp_clients == []

    def test_state_initialized(self):
        agent = AgentLoop("project-agent", module="m", page="p")
        assert isinstance(agent.state, AgentState)
        assert agent.state.agent_name == "project-agent"
        assert agent.state.step == 0
        assert agent.state.done is False

    def test_skills_populated(self):
        agent = AgentLoop("project-agent", module="m", page="p")
        assert len(agent.skills) > 0
        assert all(isinstance(s, str) for s in agent.skills)

    def test_max_steps_default(self):
        agent = AgentLoop("project-agent", module="m", page="p")
        # max_steps comes from agent definition YAML (typically 8-12)
        assert agent.state.max_steps >= 5

    def test_window_monitor_initialized(self):
        agent = AgentLoop("project-agent", module="m", page="p",
                          use_window_monitor=True)
        assert agent._window_monitor is not None

    def test_window_monitor_disabled(self):
        agent = AgentLoop("project-agent", module="m", page="p",
                          use_window_monitor=False)
        assert agent._window_monitor is None

    def test_reliable_provider_initialized(self):
        agent = AgentLoop("project-agent", module="m", page="p",
                          use_reliable_provider=True)
        assert agent._reliable_provider is not None

    def test_reliable_provider_disabled(self):
        agent = AgentLoop("project-agent", module="m", page="p",
                          use_reliable_provider=False)
        assert agent._reliable_provider is None


# ══════════════════════════════════════════════════════════════════════════
#  Abort signal
# ══════════════════════════════════════════════════════════════════════════


class TestAbortSignal:
    def test_abort_initial_not_set(self):
        agent = AgentLoop("project-agent", module="m", page="p")
        assert agent._abort.is_set() is False

    def test_abort_set(self):
        agent = AgentLoop("project-agent", module="m", page="p")
        agent._abort.set()
        assert agent._abort.is_set() is True

    def test_abort_can_be_shared(self):
        """ExecutionService passes abort event to AgentLoop."""
        agent = AgentLoop("project-agent", module="m", page="p")
        external_abort = threading.Event()
        agent._abort = external_abort
        external_abort.set()
        assert agent._abort.is_set() is True


# ══════════════════════════════════════════════════════════════════════════
#  _finalize_session (idempotency)
# ══════════════════════════════════════════════════════════════════════════


class TestFinalizeSession:
    def test_finalize_is_idempotent(self):
        """_finalize_session should be safe to call multiple times."""
        agent = AgentLoop("project-agent", module="m", page="p")
        # Should not raise
        agent._finalize_session()
        agent._finalize_session()
        assert agent._session_finalized is True

    def test_finalize_sets_flag(self):
        agent = AgentLoop("project-agent", module="m", page="p")
        # _session_finalized is set in run() — _finalize_session creates it
        agent._finalize_session()
        assert agent._session_finalized is True

    def test_finalize_handles_no_mcp_clients(self):
        agent = AgentLoop("project-agent", module="m", page="p")
        agent._mcp_clients = []
        agent._finalize_session()  # Should not raise


# ══════════════════════════════════════════════════════════════════════════
#  run_agent (wrapper function)
# ══════════════════════════════════════════════════════════════════════════


class TestRunAgent:
    def test_returns_dict(self, monkeypatch):
        """run_agent returns state.to_dict()."""
        mock_state = AgentState(agent_name="test-agent", done=True, success=True)
        mock_state.step = 3
        mock_state.termination_reason = "all_skills_completed"

        mock_loop = MagicMock()
        mock_loop.run.return_value = mock_state

        monkeypatch.setattr("aitest.agents.agent_runner.AgentLoop",
                            lambda *a, **kw: mock_loop)

        result = run_agent("project-agent", provider="fake", module="m", page="p")
        assert isinstance(result, dict)
        assert result["agent_name"] == "test-agent"
        assert result["success"] is True
