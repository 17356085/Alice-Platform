"""Engine 单元测试。"""

import os

import pytest
from alice_engine import Engine, ExecutionResult, KernelExecutionRequest, Project, RunResult
from alice_engine.core.runtime_environment import (
    current_llm_provider,
    current_mock_llm,
    current_workstudy,
)
from alice_engine.runtime import InMemoryKnowledgeStore, InMemoryMemoryStore
import alice_engine.core.executor as executor_module
from alice_engine.core.agent_helpers import _get_governance_root


@pytest.fixture(autouse=True)
def _isolate_engine_env():
    keys = ("MOCK_LLM", "LLM_PROVIDER", "ENGINE_WORKSTUDY", "ENGINE_GOVERNANCE_PATH")
    original = {key: os.environ.get(key) for key in keys}
    for key in keys:
        os.environ.pop(key, None)
    yield
    for key in keys:
        value = original[key]
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value


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
        """测试 Engine.run() 的公共 facade 合约。"""
        (tmp_path / ".tlo").mkdir()
        (tmp_path / ".tlo" / "project.yaml").write_text("name: test\nurl: http://test.com")

        from alice_engine.kernel import InlineExecutionKernel

        def runner(request: KernelExecutionRequest) -> ExecutionResult:
            return ExecutionResult(
                request_id=request.context.request_id or "engine-run-1",
                run_id=request.effective_run_id,
                status="completed",
                module=request.module,
                pages=request.pages,
                agent=request.agent,
                mode=request.mode,
                completed_phases=["Project Init", "Requirement"],
                summary="engine-run-ok",
                metadata={
                    "kernel": "InlineExecutionKernel",
                    "agent_outputs": {"sop": {"success": True}},
                },
            )

        project = Project(tmp_path)
        engine = Engine(
            project=project,
            llm_provider="mock",
            knowledge=InMemoryKnowledgeStore(),
            memory=InMemoryMemoryStore(),
            kernel=InlineExecutionKernel(runner),
        )

        result = engine.run("test-module", pages=["page1"])

        assert isinstance(result, RunResult)
        assert result.status == "completed"
        assert result.success is True
        assert result.run_id is not None
        assert result.metadata["kernel"] == "InlineExecutionKernel"

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

    def test_engine_run_scopes_runtime_environment_without_mutating_process_env(self, tmp_path):
        (tmp_path / ".tlo").mkdir()
        (tmp_path / ".tlo" / "project.yaml").write_text("name: scoped\nurl: http://test.com")
        os.environ["LLM_PROVIDER"] = "outer-provider"
        os.environ["ENGINE_WORKSTUDY"] = "outer-workstudy"
        os.environ.pop("MOCK_LLM", None)

        seen = {}

        class FakeKernel:
            def execute(self, request: KernelExecutionRequest) -> ExecutionResult:
                seen["provider"] = current_llm_provider()
                seen["workstudy"] = current_workstudy()
                seen["mock_llm"] = current_mock_llm()
                return ExecutionResult(
                    request_id="sdk-run-2",
                    run_id=request.effective_run_id,
                    status="completed",
                    module=request.module,
                    pages=request.pages,
                    agent=request.agent,
                    mode=request.mode,
                    summary="scoped-ok",
                    metadata={"agent_outputs": {"automation-agent": {"success": True}}},
                )

        project = Project(tmp_path)
        engine = Engine(project=project, llm_provider="mock", kernel=FakeKernel())

        result = engine.run("test-module", pages=["page1"], run_id="sdk-run-2")

        assert result.status == "completed"
        assert seen["provider"] == "mock"
        assert seen["workstudy"] == tmp_path
        assert seen["mock_llm"] is True
        assert os.environ["LLM_PROVIDER"] == "outer-provider"
        assert os.environ["ENGINE_WORKSTUDY"] == "outer-workstudy"
        assert "MOCK_LLM" not in os.environ

    def test_engine_run_with_injected_inline_kernel_is_standalone_safe(self, tmp_path):
        """Standalone facade 应可在不依赖平台接线时通过注入 kernel 正常运行。"""
        (tmp_path / ".tlo").mkdir()
        (tmp_path / ".tlo" / "project.yaml").write_text("name: standalone\nurl: http://test.com")

        def runner(request: KernelExecutionRequest) -> ExecutionResult:
            return ExecutionResult(
                request_id=request.context.request_id or "sdk-engine-1",
                run_id=request.effective_run_id,
                status="completed",
                module=request.module,
                pages=request.pages,
                agent=request.agent,
                mode=request.mode,
                completed_phases=["Requirement"],
                summary="standalone-ok",
                metadata={
                    "kernel": "InlineExecutionKernel",
                    "agent_outputs": {"sop": {"success": True}},
                },
            )

        from alice_engine.kernel import InlineExecutionKernel

        project = Project(tmp_path)
        engine = Engine(
            project=project,
            llm_provider="mock",
            kernel=InlineExecutionKernel(runner),
        )

        result = engine.run("equipment", pages=["alarm-config"], run_id="engine-standalone")

        assert result.status == "completed"
        assert result.run_id == "engine-standalone"
        assert result.metadata["kernel"] == "InlineExecutionKernel"
        assert result.module == "equipment"
        assert result.agent_outputs["sop"]["success"] is True

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

        assert _get_governance_root() == env_pack.resolve()
