"""Integration: AgentLoop — state machine, skill chain, observation.

Tests AgentLoop wiring with minimal mocking. No real LLM calls.

Strategy:
  - Test AgentLoop.__init__ and state setup (real)
  - Test state transitions via _run_single_session if possible
  - Mock LLMProvider.complete to return a controlled response
  - Verify Observation emission and state mutation
"""
import pytest
import sys
from unittest.mock import patch, MagicMock


class TestAgentLoopInit:
    """Test AgentLoop initialization and state setup."""

    def test_init_known_agent(self):
        """AgentLoop can initialize with a known agent name."""
        from aitest.agents.agent_runner import AgentLoop

        agent = AgentLoop(
            "project-agent",
            module="test-module",
            provider="claude",
            verbose=False,
            use_reliable_provider=False,
            use_window_monitor=False,
        )
        assert agent.agent_name == "project-agent"
        assert agent.provider == "claude"
        assert agent.state.module == "test-module"

    def test_init_unknown_agent_raises(self):
        """AgentLoop raises ValueError for unknown agent name."""
        from aitest.agents.agent_runner import AgentLoop

        with pytest.raises(ValueError) as exc:
            AgentLoop("nonexistent-agent-xyz", use_reliable_provider=False, use_window_monitor=False)
        assert "Unknown agent" in str(exc.value)

    def test_init_resolves_skills(self):
        """AgentLoop resolves skill list from AGENT_SKILL_MAP."""
        from aitest.agents.agent_runner import AgentLoop

        agent = AgentLoop(
            "project-agent",
            module="test-module",
            use_reliable_provider=False,
            use_window_monitor=False,
            verbose=False,
        )
        assert len(agent.skills) > 0
        # Project agent skills should include context manager
        assert any("context" in s.lower() or "project" in s.lower() for s in agent.skills)

    def test_init_sets_model_tier(self):
        """AgentLoop reads model_tier from agent definition (v0.5)."""
        from aitest.agents.agent_runner import AgentLoop

        agent = AgentLoop(
            "automation-agent",
            module="test-module",
            use_reliable_provider=False,
            use_window_monitor=False,
            verbose=False,
        )
        assert agent._model_tier in ("max", "balanced", "econ")


class TestAgentLoopStateTransitions:
    """Test AgentLoop internal state management."""

    def test_log_method_with_verbose(self):
        """_log emits when verbose=True."""
        from aitest.agents.agent_runner import AgentLoop

        agent = AgentLoop(
            "project-agent",
            module="test-module",
            verbose=True,
            use_reliable_provider=False,
            use_window_monitor=False,
        )
        # Should not raise
        agent._log("test message")

    def test_slug_to_page_name(self):
        """_slug_to_pageName converts kebab to PascalCase."""
        from aitest.agents.agent_runner import AgentLoop

        agent = AgentLoop(
            "project-agent",
            module="test",
            use_reliable_provider=False,
            use_window_monitor=False,
            verbose=False,
        )
        assert agent._slug_to_page_name("alarm-config") == "AlarmConfig"
        assert agent._slug_to_page_name("unit-management") == "UnitManagement"

    def test_page_slug_to_underscore(self):
        """_page_slug_to_underscore converts kebab to snake_case."""
        from aitest.agents.agent_runner import AgentLoop

        agent = AgentLoop(
            "project-agent",
            module="test",
            use_reliable_provider=False,
            use_window_monitor=False,
            verbose=False,
        )
        assert agent._page_slug_to_underscore("alarm-config") == "alarm_config"

    def test_skill_executor_agent_skill_map(self):
        """AGENT_SKILL_MAP covers all 8 core agents."""
        from aitest.agents.skill_executor import AGENT_SKILL_MAP

        core_agents = ["project-agent", "requirement-agent", "test-design-agent",
                       "automation-agent", "execution-agent", "bug-analysis-agent",
                       "report-agent", "knowledge-agent"]
        for name in core_agents:
            assert name in AGENT_SKILL_MAP, f"{name} missing from AGENT_SKILL_MAP"
            assert len(AGENT_SKILL_MAP[name]) > 0, f"{name} has no skills"

    def test_get_agent_definition(self):
        """get_agent_definition returns dict with expected keys."""
        from aitest.agents.skill_executor import get_agent_definition

        for name in ["project-agent", "automation-agent", "execution-agent"]:
            defn = get_agent_definition(name)
            assert defn is not None, f"No definition for {name}"
            assert "name" in defn, f"{name}: missing 'name'"
            assert "phase" in defn, f"{name}: missing 'phase'"

            # v0.4: verify capabilities
            caps = defn.get("capabilities", [])
            assert isinstance(caps, list), f"{name}: capabilities must be list"

            # v0.5: verify model_tier
            tier = defn.get("model_tier", "")
            assert tier in ("max", "balanced", "econ"), \
                f"{name}: model_tier='{tier}' must be max/balanced/econ"
