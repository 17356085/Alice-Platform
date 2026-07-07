"""SDK boundary regression tests.

These tests protect the Phase 4.5 goal:
- importing alice_engine should be lightweight
- provider base imports should not pull the workflow stack
- the SDK should stay free of direct aitest imports
"""

from __future__ import annotations

import builtins
import importlib


def test_alice_engine_import_is_lazy():
    module = importlib.import_module("alice_engine")

    assert "Engine" not in module.__dict__
    assert "Project" not in module.__dict__
    assert module.__version__ == "1.0.0"


def test_provider_base_import_does_not_pull_workflow_stack():
    base = importlib.import_module("alice_engine.providers.base")

    assert base.LLMProvider.__name__ == "LLMProvider"
    assert base.ProviderContract.__name__ == "ProviderContract"


def test_platform_bridge_is_optional():
    bridge = importlib.import_module("alice_engine.platform_bridge")

    assert hasattr(bridge, "get_planner_memory_context")
    assert hasattr(bridge, "create_capability_router")


def test_platform_bridge_can_use_explicit_ports():
    bridge = importlib.import_module("alice_engine.platform_bridge")
    ports = importlib.import_module("alice_engine.platform_ports")

    class FakeMemoryStore:
        def available(self):
            return False

    class FakeKnowledge:
        def available(self):
            return False

    ports.reset_platform_ports()
    ports.configure_platform_ports(
        planner_memory_context=lambda module, task: f"{module}:{task}",
        capability_router_factory=lambda: {"router": "ok"},
        mcp_clients_factory=lambda agent: (["client"], {"tool": {"name": agent}}),
        testing_memory_store_factory=lambda: FakeMemoryStore(),
        knowledge_service_factory=lambda: FakeKnowledge(),
    )

    assert bridge.get_planner_memory_context("equipment", "plan") == "equipment:plan"
    assert bridge.create_capability_router() == {"router": "ok"}
    assert bridge.create_mcp_clients_for_agent("automation-agent")[0] == ["client"]
    assert bridge.create_testing_memory_store().available() is False
    assert bridge.get_knowledge_service().available() is False

    ports.reset_platform_ports()


def test_kernel_contract_module_is_public():
    kernel = importlib.import_module("alice_engine.kernel")

    assert hasattr(kernel, "ExecutionKernel")
    assert hasattr(kernel, "KernelExecutionRequest")
    assert hasattr(kernel, "InlineExecutionKernel")


def test_behavior_pack_falls_back_to_governance_default_without_alice_governance(monkeypatch):
    behavior = importlib.import_module("alice_engine.behavior")
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "alice_governance" or name.startswith("alice_governance."):
            raise ImportError("alice_governance intentionally unavailable")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.delenv("ENGINE_GOVERNANCE_PATH", raising=False)
    monkeypatch.delenv("AITEST_GOVERNANCE_PATH", raising=False)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    pack = behavior.load_behavior_pack(None)

    assert pack.root == behavior.get_default_pack_path()
    assert pack.skills_dir is not None
    assert pack.agents_yaml is not None


def test_governance_router_uses_default_pack_without_alice_governance(monkeypatch):
    router_module = importlib.import_module("alice_engine.router")
    behavior = importlib.import_module("alice_engine.behavior")
    real_import = builtins.__import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "alice_governance" or name.startswith("alice_governance."):
            raise ImportError("alice_governance intentionally unavailable")
        return real_import(name, globals, locals, fromlist, level)

    monkeypatch.delenv("ENGINE_GOVERNANCE_PATH", raising=False)
    monkeypatch.delenv("AITEST_GOVERNANCE_PATH", raising=False)
    monkeypatch.setattr(builtins, "__import__", guarded_import)

    router = router_module.GovernanceRouter(auto_discover=True)
    skill = router.resolve_skill("project/context-sync")
    agent = router.resolve_agent_skills("project-agent")

    assert skill.found is True
    assert skill.source is router_module.Source.DEFAULT
    assert agent.all_found is True
    assert agent.source is router_module.Source.DEFAULT
    assert router.diagnose()["default_path"] == str(behavior.get_default_pack_path())
