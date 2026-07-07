import sys
import types

from alice_engine.core.context_builder import build_context


def test_build_context_includes_memory_hints(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    (project_root / "page" / "equipment_page").mkdir(parents=True)
    (project_root / "script" / "equipment").mkdir(parents=True)
    (project_root / ".tlo" / "knowledge" / "modules" / "equipment").mkdir(parents=True)
    (project_root / "script" / "equipment" / "test_alarm.py").write_text("def test_alarm(): pass", encoding="utf-8")

    fake_rag = types.ModuleType("aitest.knowledge.rag_engine")
    fake_rag.build_planner_memory_context = lambda module, task_description: "memory hint text"
    monkeypatch.setitem(sys.modules, "aitest.knowledge.rag_engine", fake_rag)

    ctx = build_context(
        module="equipment",
        project_root=project_root,
        page="alarm",
        task_description="alarm test",
        include_memory=True,
    )

    assert ctx.memory_hints == "memory hint text"
