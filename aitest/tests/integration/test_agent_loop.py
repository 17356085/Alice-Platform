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
from types import SimpleNamespace
from unittest.mock import patch, MagicMock


class TestAgentLoopInit:
    """Test AgentLoop initialization and state setup."""

    def test_init_known_agent(self):
        """AgentLoop can initialize with a known agent name."""
        from alice_engine.core.executor import AgentLoop

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

    def test_page_config_is_available_to_skill_prompt(self):
        """Persisted page URL/locators reach the skill without leaking config secrets."""
        from alice_engine.core.executor import AgentLoop

        agent = AgentLoop(
            "automation-agent",
            module="catalog",
            page="products",
            provider="mock",
            page_configs=[{
                "page_id": "products",
                 "url": "https://example.test/products",
                 "locators": {"search": "#search"},
                 "config": {"api_token": "should-not-be-in-prompt"},
                 "execution": {
                     "wait_for": ["search"],
                     "actions": [{"action": "fill", "target": "search", "value": "secret-value"}],
                 },
            }],
            verbose=False,
            use_reliable_provider=False,
            use_window_monitor=False,
        )

        prompt = agent._build_user_input("automation/tech-analysis")

        assert "https://example.test/products" in prompt
        assert '"search": "#search"' in prompt
        assert '"action": "fill"' in prompt
        assert '"target": "search"' in prompt
        assert "should-not-be-in-prompt" not in prompt
        assert "secret-value" not in prompt

    def test_init_unknown_agent_raises(self):
        """AgentLoop raises ValueError for unknown agent name."""
        from alice_engine.core.executor import AgentLoop

        with pytest.raises(ValueError) as exc:
            AgentLoop("nonexistent-agent-xyz", use_reliable_provider=False, use_window_monitor=False)
        assert "Unknown agent" in str(exc.value)

    def test_init_resolves_skills(self):
        """AgentLoop resolves skill list from AGENT_SKILL_MAP."""
        from alice_engine.core.executor import AgentLoop

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
        from alice_engine.core.executor import AgentLoop

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
        from alice_engine.core.executor import AgentLoop

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
        from alice_engine.core.executor import AgentLoop

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
        from alice_engine.core.executor import AgentLoop

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


class TestAgentLoopMockLLM:
    """Test AgentLoop with mock LLM provider — verify Plan→Act flow (P2)."""

    def test_perceive_returns_dict_for_skill(self):
        """perceive(skill_id) returns structured perception dict."""
        from alice_engine.core.executor import AgentLoop

        agent = AgentLoop(
            "project-agent",
            module="test-module",
            use_reliable_provider=False,
            use_window_monitor=False,
            verbose=False,
        )
        if agent.skills:
            ctx = agent.perceive(agent.skills[0])
            assert isinstance(ctx, dict)
            assert "skill_id" in ctx
            assert "existing_files" in ctx

    def test_build_context_vars_uses_runtime_context_builder(self):
        """AgentLoop delegates context assembly to the extracted collaborator."""
        from alice_engine.core.executor import AgentLoop

        agent = AgentLoop(
            "project-agent",
            module="test-module",
            use_reliable_provider=False,
            use_window_monitor=False,
            verbose=False,
        )
        agent._runtime_context_builder.build_context_vars = MagicMock(return_value={"module": "delegated"})

        result = agent._build_context_vars({"x": 1})

        agent._runtime_context_builder.build_context_vars.assert_called_once_with({"x": 1})
        assert result == {"module": "delegated"}

    def test_init_mcp_clients_uses_mcp_lifecycle(self):
        """AgentLoop delegates MCP connect to the extracted collaborator."""
        from alice_engine.core.executor import AgentLoop

        agent = AgentLoop(
            "project-agent",
            module="test-module",
            use_reliable_provider=False,
            use_window_monitor=False,
            verbose=False,
        )
        agent._mcp_lifecycle.connect = MagicMock(return_value=(["client"], {"tool": {"ok": True}}))

        agent._init_mcp_clients()

        agent._mcp_lifecycle.connect.assert_called_once_with()
        assert agent._mcp_clients == ["client"]
        assert agent._mcp_tools == {"tool": {"ok": True}}

    def test_init_uses_provider_lifecycle_result(self):
        """Provider lifecycle can override the final provider selection."""
        from alice_engine.core import executor as executor_module

        class StubLifecycle:
            def __init__(self, *args, **kwargs):
                pass

            def initialize(self, **kwargs):
                return {
                    "provider": "deepseek",
                    "model": "tier-model",
                    "model_tier": "max",
                    "reliable_provider": {"kind": "reliable"},
                    "window_monitor": {"kind": "window"},
                }

        original = executor_module.ProviderRuntimeLifecycle
        executor_module.ProviderRuntimeLifecycle = StubLifecycle
        try:
            agent = executor_module.AgentLoop(
                "project-agent",
                module="test-module",
                provider="anthropic",
                use_reliable_provider=True,
                use_window_monitor=True,
                verbose=False,
            )
        finally:
            executor_module.ProviderRuntimeLifecycle = original

        assert agent.provider == "deepseek"
        assert agent.state.provider == "deepseek"
        assert agent._model_tier == "max"
        assert agent._reliable_provider == {"kind": "reliable"}
        assert agent._window_monitor == {"kind": "window"}

    def test_run_single_session_builds_session_orchestrator(self):
        """AgentLoop wires the extracted session orchestrator before the loop runs."""
        from alice_engine.core import executor as executor_module

        built = {}

        class StubSessionOrchestrator:
            def __init__(self, **kwargs):
                built.update(kwargs)

            def run_iteration(self, skill_index):
                built["skill_index"] = skill_index
                built["state"].done = True
                built["state"].success = True
                built["state"].termination_reason = "all_skills_completed"
                return SimpleNamespace(next_skill_index=skill_index, should_continue=False)

            def apply_max_steps_termination(self):
                built["max_steps_checked"] = True

        original = executor_module.SessionLoopOrchestrator
        executor_module.SessionLoopOrchestrator = StubSessionOrchestrator
        try:
            agent = executor_module.AgentLoop(
                "project-agent",
                module="test-module",
                use_reliable_provider=False,
                use_window_monitor=False,
                verbose=False,
            )
            state = agent._run_single_session()
        finally:
            executor_module.SessionLoopOrchestrator = original

        assert built["agent_name"] == "project-agent"
        assert built["provider"] == agent.provider
        assert built["state"] is agent.state
        assert built["skills"] == agent.skills
        assert built["skill_index"] == 0
        assert built["max_steps_checked"] is True
        assert state.termination_reason == "all_skills_completed"

    def test_state_tracks_completed_skills(self):
        """completed_skills starts empty and can be appended."""
        from alice_engine.core.executor import AgentLoop

        agent = AgentLoop(
            "project-agent",
            module="test-module",
            use_reliable_provider=False,
            use_window_monitor=False,
            verbose=False,
        )
        assert isinstance(agent.state.completed_skills, list)
        assert len(agent.state.completed_skills) == 0
        agent.state.completed_skills.append("test/skill-1")
        assert "test/skill-1" in agent.state.completed_skills

    def test_agent_state_initial_values(self):
        """AgentState starts with correct defaults."""
        from alice_engine.core.executor import AgentLoop
        from alice_engine.core.task import AgentState

        agent = AgentLoop(
            "project-agent",
            module="test-module",
            use_reliable_provider=False,
            use_window_monitor=False,
            verbose=False,
        )
        state = agent.state
        assert isinstance(state, AgentState)
        assert state.module == "test-module"
        assert state.step == 0
        assert state.completed_skills == []
        assert state.done is False
        assert state.success is False
