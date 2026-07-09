"""Tests for executor utility modules.

Verify that executor_utils and agent_helpers work correctly.
"""

import pytest


def test_executor_utils_imports():
    """Verify all expected utilities are importable."""
    from alice_engine.core.executor_utils import (
        fix_stdout_encoding,
        get_logger,
        get_project_dir,
        get_test_project_root,
        config,
        TraceContext,
        get_tracer,
    )

    assert callable(fix_stdout_encoding)
    assert callable(get_logger)
    assert callable(get_project_dir)
    assert callable(get_test_project_root)
    assert config is not None
    assert TraceContext is not None
    assert callable(get_tracer)


def test_logger():
    """Verify logger creation."""
    from alice_engine.core.executor_utils import get_logger

    logger = get_logger("test")
    assert logger is not None
    assert logger.name == "test"


def test_config_stub():
    """Verify config stub methods."""
    from alice_engine.core.executor_utils import config

    provider = config.resolve_llm_provider()
    assert provider == "anthropic"

    model_info = config.resolve_model_for_tier("default", "claude")
    assert "model" in model_info
    assert "provider" in model_info


def test_trace_context():
    """Verify TraceContext thread-local storage."""
    from alice_engine.core.executor_utils import TraceContext

    TraceContext.set(run_id="test-123", agent_name="test-agent")
    # Can't easily verify thread-local state without internal access
    # But at least verify it doesn't crash

    version = TraceContext.get_skill_version()
    assert version == "latest"


def test_tracer_noop():
    """Verify no-op tracer."""
    from alice_engine.core.executor_utils import get_tracer

    tracer = get_tracer()
    with tracer.start_as_current_span("test") as span:
        span.set_attribute("key", "value")
    # Should not crash


def test_agent_helpers_imports():
    """Verify all agent helper functions are importable."""
    from alice_engine.core.agent_helpers import (
        get_agent_skill_map,
        get_dev_agent_skill_map,
        get_agent_definition,
        run_skill,
        list_agents,
        list_dev_agents,
    )

    assert callable(get_agent_skill_map)
    assert callable(get_dev_agent_skill_map)
    assert callable(get_agent_definition)
    assert callable(run_skill)
    assert callable(list_agents)
    assert callable(list_dev_agents)


def test_agent_skill_map():
    """Verify agent skill map loading."""
    from alice_engine.core.agent_helpers import get_agent_skill_map

    skill_map = get_agent_skill_map()
    assert isinstance(skill_map, dict)
    # Should have at least the fallback agents
    assert len(skill_map) > 0


def test_list_agents():
    """Verify agent listing."""
    from alice_engine.core.agent_helpers import list_agents, list_dev_agents

    agents = list_agents()
    assert isinstance(agents, list)
    assert len(agents) > 0
    assert all(isinstance(a, str) for a in agents)

    dev_agents = list_dev_agents()
    assert isinstance(dev_agents, list)


def test_run_skill_mock():
    """Verify run_skill with mock provider."""
    from alice_engine.core.agent_helpers import run_skill

    # Should not crash with mock provider
    result = run_skill(
        skill_id="test/skill",
        user_input="test input",
        provider="mock",
    )
    # Mock provider should return some response
    assert result is not None
