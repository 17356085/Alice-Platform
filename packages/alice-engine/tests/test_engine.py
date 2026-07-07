"""Engine 单元测试。"""

import pytest
from alice_engine import Engine, ExecutionResult, KernelExecutionRequest, Project, RunResult
from alice_engine.runtime import InMemoryKnowledgeStore, InMemoryMemoryStore
import alice_engine.core.executor as executor_module


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
        assert result.metadata["kernel"] == "RuntimeExecutionKernel"

    def test_engine_run_uses_public_kernel(self, tmp_path):
        """Engine 应通过公开 Kernel 执行，而不是直接触碰私有图构建。"""
        (tmp_path / ".tlo").mkdir()
        (tmp_path / ".tlo" / "project.yaml").write_text("name: test\nurl: http://test.com")

        seen: list[KernelExecutionRequest] = []

        class FakeKernel:
            def execute(self, request: KernelExecutionRequest) -> ExecutionResult:
                seen.append(request)
                return ExecutionResult(
                    request_id="sdk-run-1",
                    run_id=request.effective_run_id,
                    status="completed",
                    module=request.module,
                    pages=request.pages,
                    agent=request.agent,
                    mode=request.mode,
                    completed_phases=["Project Init", "Requirement"],
                    summary="test-module completed",
                    metadata={"agent_outputs": {"automation-agent": {"success": True}}},
                )

        project = Project(tmp_path)
        engine = Engine(project=project, llm_provider="mock", kernel=FakeKernel())

        result = engine.run("test-module", pages=["page1"], run_id="sdk-run-1")

        assert len(seen) == 1
        assert seen[0].kind == "sop"
        assert seen[0].project_path == str(tmp_path)
        assert seen[0].context.module == "test-module"
        assert seen[0].context.pages == ["page1"]
        assert result.run_id == "sdk-run-1"
        assert result.completed_phases == ["Project Init", "Requirement"]
        assert result.agent_outputs["automation-agent"]["success"] is True

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

    def test_executor_governance_root_uses_env_pack(self, tmp_path, monkeypatch):
        env_pack = tmp_path / "env-governance"
        (env_pack / "agents").mkdir(parents=True)
        monkeypatch.setenv("ENGINE_GOVERNANCE_PATH", str(env_pack))
        monkeypatch.setattr(executor_module, "WORKSTUDY", tmp_path / "project-root")

        assert executor_module._get_governance_root() == env_pack.resolve()
