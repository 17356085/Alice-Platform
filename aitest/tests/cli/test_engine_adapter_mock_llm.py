"""Test Engine adapter mock_llm parameter propagation."""

import os
from types import SimpleNamespace
from pathlib import Path

import pytest

from aitest.cli.adapters.engine_adapter import LiveEngineAdapter


@pytest.fixture
def mock_project_dir(tmp_path, monkeypatch):
    """Create a minimal project directory with .tlo/project.yaml."""
    tlo = tmp_path / ".tlo"
    tlo.mkdir()
    (tlo / "project.yaml").write_text("name: test\nurl: http://test.com")

    # Mock graph execution to avoid real SOP dependencies
    class _CompiledGraph:
        def invoke(self, initial_state, config):
            return {
                "status": "completed",
                "completed_phases": ["Requirement"],
                "failed_phases": [],
                "pages": initial_state.get("pages", []),
                "agent_outputs": {"sop": {"success": True}},
            }

    class _Graph:
        def compile(self, checkpointer=None):
            return _CompiledGraph()

    monkeypatch.setattr("aitest.graphs.state.create_initial_state", lambda module, pages, mode="full": {
        "module": module,
        "pages": pages,
        "mode": mode,
    })
    monkeypatch.setattr("alice_engine.workflow.sop_graph.build_sop_graph", lambda: _Graph())
    monkeypatch.setattr("aitest.graphs.checkpoint.get_checkpointer", lambda: SimpleNamespace())

    return tmp_path


def test_adapter_explicit_mock_llm_parameter(mock_project_dir, monkeypatch):
    """Verify explicit mock_llm=True parameter works without env."""
    monkeypatch.delenv("MOCK_LLM", raising=False)

    adapter = LiveEngineAdapter(
        project_path=str(mock_project_dir),
        mock_llm=True,
    )

    # Should not raise, and should use mock provider
    result = adapter.run("equipment", pages=["alarm-config"])
    assert result["status"] == "completed"
    assert "MOCK_LLM" not in os.environ


def test_adapter_mock_llm_in_run_kwargs(mock_project_dir, monkeypatch):
    """Verify mock_llm can also be passed as run() kwarg."""
    monkeypatch.delenv("MOCK_LLM", raising=False)

    adapter = LiveEngineAdapter(project_path=str(mock_project_dir))
    result = adapter.run("equipment", pages=["alarm-config"], mock_llm=True)

    assert result["status"] == "completed"
    assert "MOCK_LLM" not in os.environ


def test_adapter_no_mock_llm_uses_default_provider(mock_project_dir, monkeypatch):
    """Verify when mock_llm=False, adapter uses default provider."""
    monkeypatch.delenv("MOCK_LLM", raising=False)
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    adapter = LiveEngineAdapter(
        project_path=str(mock_project_dir),
        mock_llm=False,
    )

    result = adapter.run("equipment", pages=["alarm-config"])
    assert result["status"] == "completed"


def test_engine_explicit_mock_llm_overrides_env(mock_project_dir, monkeypatch):
    """Verify explicit mock_llm=True takes precedence over env."""
    monkeypatch.setenv("MOCK_LLM", "0")  # env says no
    monkeypatch.setenv("LLM_PROVIDER", "anthropic")

    from aitest.engine import Engine
    engine = Engine(workstudy=str(mock_project_dir), mock_llm=True)

    assert engine.llm_provider == "mock"


def test_engine_env_mock_llm_still_works_with_deprecation_warning(mock_project_dir, monkeypatch, caplog):
    """Verify os.environ['MOCK_LLM'] still works but logs deprecation warning."""
    monkeypatch.setenv("MOCK_LLM", "1")

    from aitest.engine import Engine

    with caplog.at_level("WARNING"):
        engine = Engine(workstudy=str(mock_project_dir))

    assert engine.llm_provider == "mock"
    assert any("Deprecated" in record.message and "MOCK_LLM" in record.message for record in caplog.records)


def test_engine_explicit_mock_llm_no_warning(mock_project_dir, monkeypatch, caplog):
    """Verify explicit mock_llm=True does NOT log deprecation warning."""
    monkeypatch.delenv("MOCK_LLM", raising=False)

    from aitest.engine import Engine

    with caplog.at_level("WARNING"):
        engine = Engine(workstudy=str(mock_project_dir), mock_llm=True)

    assert engine.llm_provider == "mock"
    assert not any("Deprecated" in record.message for record in caplog.records)
