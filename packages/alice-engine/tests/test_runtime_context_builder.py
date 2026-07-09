from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from alice_engine.core.runtime_context_builder import RuntimeContextBuilder
from alice_engine.core.task import AgentState


class _MemoryStore:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def available(self):
        return True

    def search_multi(self, queries, top_k):
        self.calls += 1
        assert top_k == 3
        assert [item["collection"] for item in queries] == [
            "known_bugs",
            "historical_failures",
            "workflow_recipes",
        ]
        return self.payload


class _KnowledgeService:
    def __init__(self, payload):
        self.payload = payload
        self.calls = 0

    def available(self):
        return True

    def search(self, *, query, collection, top_k):
        self.calls += 1
        assert query
        assert collection == "all"
        assert top_k == 5
        return self.payload


def test_build_runtime_context_caches_memory_and_knowledge_results():
    state = AgentState(agent_name="project-agent", goal="diagnose alarm flow", module="equipment", page="alarm-config")
    memory_store = _MemoryStore({"known_bugs": [{"id": "kb-1"}]})
    knowledge = _KnowledgeService([{"id": "doc-1"}])
    logs: list[str] = []

    builder = RuntimeContextBuilder(
        state=state,
        module="equipment",
        page="alarm-config",
        goal=state.goal,
        focused_context=None,
        token_budget=30000,
        log_fn=logs.append,
        create_testing_memory_store_fn=lambda: memory_store,
        get_knowledge_service_fn=lambda: knowledge,
    )

    first = builder.build_runtime_context()
    second = builder.build_runtime_context()

    assert first is second
    assert memory_store.calls == 1
    assert knowledge.calls == 1
    assert first["memory_context"] == {"known_bugs": [{"id": "kb-1"}]}
    assert first["knowledge_context"] == {"results": [{"id": "doc-1"}]}
    assert first["context_sources"] == ["memory", "knowledge"]
    assert state.memory["runtime_context"] is first


def test_build_context_vars_includes_runtime_context_paths_and_budget(tmp_path: Path):
    project_root = tmp_path / "workspace"
    page_dir = project_root / "page" / "equipment_page"
    script_dir = project_root / "script" / "equipment"
    page_dir.mkdir(parents=True)
    script_dir.mkdir(parents=True)
    (project_root / "PROJECT_CONTEXT.md").write_text("project", encoding="utf-8")
    (page_dir / "AlarmConfigPage.py").write_text("class AlarmConfigPage: pass", encoding="utf-8")
    (script_dir / "test_alarm_config.py").write_text("def test_demo(): pass", encoding="utf-8")
    context_modules = tmp_path / "context"
    (context_modules / "equipment" / "pages" / "alarm-config").mkdir(parents=True)

    state = AgentState(agent_name="project-agent", goal="stabilize alarm", module="equipment", page="alarm-config")
    state.step = 4
    state.memory["prev_output"] = "x" * 5000
    state.memory["tech_analysis_summary"] = "summary"
    state.memory["runtime_context"] = {
        "memory_context": {"bugs": [1]},
        "knowledge_context": {"results": [2]},
        "context_sources": ["memory", "knowledge"],
    }
    builder_context = SimpleNamespace(source_count=2, patterns=["*.py"], memory_hints=["hint"])

    builder = RuntimeContextBuilder(
        state=state,
        module="equipment",
        page="alarm-config",
        goal=state.goal,
        focused_context="focus",
        token_budget=12000,
        log_fn=lambda _msg: None,
        context_modules=context_modules,
        get_test_project_root_fn=lambda: project_root,
        get_project_dir_fn=lambda: project_root,
        build_context_fn=lambda **_kwargs: builder_context,
    )

    vars_ = builder.build_context_vars({"custom": "value"})

    assert vars_["module"] == "equipment"
    assert vars_["page"] == "alarm-config"
    assert vars_["prev_output"] == "x" * 3000
    assert vars_["tech_analysis_summary"] == "summary"
    assert vars_["memory_context"] == {"bugs": [1]}
    assert vars_["knowledge_context"] == {"results": [2]}
    assert vars_["context_sources"] == ["memory", "knowledge"]
    assert vars_["focused_context"] == "focus"
    assert vars_["token_budget_remaining"] == 4000
    assert vars_["project_context_path"].endswith("PROJECT_CONTEXT.md")
    assert vars_["po_path"].endswith("AlarmConfigPage.py")
    assert vars_["test_path"].endswith("test_alarm_config.py")
    assert vars_["po_dir"].endswith("equipment_page")
    assert vars_["test_dir"].endswith(str(Path("script") / "equipment"))
    assert vars_["page_dir"].endswith(str(Path("equipment") / "pages" / "alarm-config"))
    assert vars_["builder_context"] is builder_context
    assert vars_["custom"] == "value"
