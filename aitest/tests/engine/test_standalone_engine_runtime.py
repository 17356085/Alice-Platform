import os
from types import SimpleNamespace

from alice_engine.core.runtime_environment import (
    current_llm_provider,
    current_mock_llm,
    current_workstudy,
)

from aitest.engine import Engine


def test_standalone_engine_scopes_runtime_environment(monkeypatch, tmp_path):
    monkeypatch.setenv("ENGINE_WORKSTUDY", "outer-workstudy")
    monkeypatch.setenv("LLM_PROVIDER", "outer-provider")
    monkeypatch.delenv("MOCK_LLM", raising=False)

    (tmp_path / ".tlo").mkdir()
    (tmp_path / ".tlo" / "project.yaml").write_text("name: standalone\nurl: http://test.com")

    seen = {}

    class _CompiledGraph:
        def invoke(self, initial_state, config):
            seen["provider"] = current_llm_provider()
            seen["workstudy"] = current_workstudy()
            seen["mock_llm"] = current_mock_llm()
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

    engine = Engine(workstudy=str(tmp_path), llm_provider="mock")
    result = engine.run("equipment", ["alarm-config"])

    assert result["status"] == "completed"
    assert seen["provider"] == "mock"
    assert seen["workstudy"] == tmp_path
    assert seen["mock_llm"] is True
    assert os.environ["ENGINE_WORKSTUDY"] == "outer-workstudy"
    assert os.environ["LLM_PROVIDER"] == "outer-provider"
    assert "MOCK_LLM" not in os.environ
