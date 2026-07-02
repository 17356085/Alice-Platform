"""Engine 单元测试。"""

import pytest
from alice_engine import Engine, Project, RunResult
from alice_engine.runtime import InMemoryKnowledgeStore, InMemoryMemoryStore


class TestEngine:
    """Engine 测试。"""

    def test_engine_init(self, tmp_path):
        """测试 Engine 初始化。"""
        # 创建最小项目结构
        (tmp_path / ".tlo").mkdir()
        (tmp_path / ".tlo" / "project.yaml").write_text("name: test\nurl: http://test.com")

        project = Project(tmp_path)
        engine = Engine(project=project, llm_provider="mock")

        assert engine.project.name == "test"
        assert engine.llm_provider == "mock"

    def test_engine_run(self, tmp_path):
        """测试 Engine.run()。"""
        (tmp_path / ".tlo").mkdir()
        (tmp_path / ".tlo" / "project.yaml").write_text("name: test\nurl: http://test.com")

        project = Project(tmp_path)
        engine = Engine(
            project=project,
            llm_provider="mock",
            knowledge=InMemoryKnowledgeStore(),
            memory=InMemoryMemoryStore(),
        )

        result = engine.run("test-module", pages=["page1"])

        assert isinstance(result, RunResult)
        assert result.status == "completed"
        assert result.success is True
        assert result.run_id is not None
        assert len(result.completed_phases) > 0

    def test_engine_validate(self, tmp_path):
        """测试 Engine.validate()。"""
        (tmp_path / ".tlo").mkdir()
        (tmp_path / ".tlo" / "project.yaml").write_text("name: test\nurl: http://test.com")

        project = Project(tmp_path)
        engine = Engine(project=project, llm_provider="mock")

        validation = engine.validate()
        assert validation.valid is True

    def test_engine_list_modules(self, tmp_path):
        """测试 Engine.list_modules()。"""
        (tmp_path / ".tlo").mkdir()
        (tmp_path / ".tlo" / "project.yaml").write_text("name: test\nmodules:\n  - mod1\n  - mod2")

        project = Project(tmp_path)
        engine = Engine(project=project, llm_provider="mock")

        modules = engine.list_modules()
        assert "mod1" in modules
        assert "mod2" in modules
