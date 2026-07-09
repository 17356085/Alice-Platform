"""Architecture Contract Tests — 防止依赖漂移。

这些测试确保 SDK 的架构边界不被破坏:
1. Engine 不能 import workflow 内部模块
2. Workflow 不能反向依赖 engine
3. Providers 必须通过 registry 获取
4. Runtime 不能 import workflow
"""

import ast
from pathlib import Path


def get_imports(file_path: Path) -> set[str]:
    """获取文件中的所有 import 语句。"""
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read())

    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


SDK_ROOT = Path(__file__).parent.parent / "alice_engine"


class TestEngineBoundary:
    """Engine 不能 import workflow 内部模块。"""

    def test_engine_does_not_import_workflow_internals(self):
        """Engine 只能通过 workflow/__init__.py 导入。"""
        engine_file = SDK_ROOT / "engine.py"
        imports = get_imports(engine_file)

        # 但不能导入 workflow 内部模块
        for imp in imports:
            if imp.startswith("alice_engine.workflow.") and imp != "alice_engine.workflow":
                assert False, f"Engine 导入了 workflow 内部模块: {imp}"


class TestWorkflowBoundary:
    """Workflow 不能反向依赖 engine。"""

    def test_workflow_does_not_import_engine(self):
        """Workflow 不能导入 engine 模块。"""
        workflow_dir = SDK_ROOT / "workflow"
        for file in workflow_dir.glob("*.py"):
            if file.name == "__init__.py":
                continue
            imports = get_imports(file)
            for imp in imports:
                if imp.startswith("alice_engine.engine"):
                    assert False, f"Workflow 导入了 engine: {file.name} -> {imp}"


class TestRuntimeBoundary:
    """Runtime 不能 import workflow。"""

    def test_runtime_does_not_import_workflow(self):
        """Runtime 不能导入 workflow 模块。"""
        runtime_dir = SDK_ROOT / "runtime"
        for file in runtime_dir.rglob("*.py"):
            if file.name == "__init__.py":
                continue
            imports = get_imports(file)
            for imp in imports:
                if imp.startswith("alice_engine.workflow"):
                    assert False, f"Runtime 导入了 workflow: {file.name} -> {imp}"


class TestProviderRegistry:
    """Providers 必须通过 registry 获取。"""

    def test_all_provider_imports_via_registry(self):
        """所有 provider 导入都应该通过 providers 包。"""
        for file in SDK_ROOT.rglob("*.py"):
            if file.name == "__init__.py":
                continue
            if "providers" in str(file):
                continue
            imports = get_imports(file)
            for imp in imports:
                if "alice_engine.providers." in imp and imp != "alice_engine.providers":
                    # 只允许导入 providers 包本身
                    if not imp.startswith("alice_engine.providers."):
                        assert False, f"直接导入了 provider 实现: {file.name} -> {imp}"


class TestNoAitestDependency:
    """SDK 不能依赖 aitest。"""

    def test_no_aitest_imports(self):
        """SDK 中不应该有任何 aitest 导入。"""
        for file in SDK_ROOT.rglob("*.py"):
            if file.name == "__init__.py":
                continue
            imports = get_imports(file)
            for imp in imports:
                if imp.startswith("aitest"):
                    assert False, f"SDK 导入了 aitest: {file.name} -> {imp}"

    def test_no_dynamic_aitest_imports(self):
        """SDK 运行时代码不应通过字符串动态加载 aitest。"""
        forbidden = ('import_module("aitest', "import_module('aitest", '__import__("aitest', "__import__('aitest")

        for file in SDK_ROOT.rglob("*.py"):
            if "tests" in file.parts or "__pycache__" in file.parts:
                continue
            text = file.read_text(encoding="utf-8")
            for marker in forbidden:
                if marker in text:
                    assert False, f"SDK 动态导入了 aitest: {file.name} -> {marker}"


class TestExecutorBoundarySlimming:
    """New AgentLoop collaborators must not grow back-dependencies to executor."""

    def test_runtime_collaborators_do_not_import_executor_module(self):
        collaborator_files = [
            SDK_ROOT / "core" / "runtime_context_builder.py",
            SDK_ROOT / "core" / "runtime_lifecycle.py",
            SDK_ROOT / "core" / "session_orchestrator.py",
        ]

        for file in collaborator_files:
            imports = get_imports(file)
            for imp in imports:
                if imp == "alice_engine.core.executor" or imp.startswith("alice_engine.core.executor."):
                    assert False, f"内部协作者反向导入了 executor: {file.name} -> {imp}"

    def test_runtime_lifecycle_does_not_reference_executor_source_text(self):
        lifecycle_file = SDK_ROOT / "core" / "runtime_lifecycle.py"
        text = lifecycle_file.read_text(encoding="utf-8")

        forbidden = (
            "from alice_engine.core.executor import",
            "import alice_engine.core.executor",
        )
        for marker in forbidden:
            assert marker not in text, f"runtime_lifecycle.py 不应再引用 executor: {marker}"
