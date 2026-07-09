from alice_engine.core.context_builder import build_context
from alice_engine.platform_ports import configure_platform_ports, reset_platform_ports


def test_build_context_includes_memory_hints(tmp_path, monkeypatch):
    project_root = tmp_path / "project"
    (project_root / "page" / "equipment_page").mkdir(parents=True)
    (project_root / "script" / "equipment").mkdir(parents=True)
    (project_root / ".tlo" / "knowledge" / "modules" / "equipment").mkdir(parents=True)
    (project_root / "script" / "equipment" / "test_alarm.py").write_text("def test_alarm(): pass", encoding="utf-8")

    reset_platform_ports()
    configure_platform_ports(
        planner_memory_context=lambda module, task_description: "memory hint text"
    )

    try:
        ctx = build_context(
            module="equipment",
            project_root=project_root,
            page="alarm",
            task_description="alarm test",
            include_memory=True,
        )
    finally:
        reset_platform_ports()

    assert ctx.memory_hints == "memory hint text"
