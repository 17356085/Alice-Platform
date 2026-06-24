"""Integration: Capability Enforcement v0.4.

Verifies that the CapabilityRouter correctly enforces agent→capability
mapping loaded from agent-definitions.yaml.

No real LLM calls. Tests the routing + enforcement wiring.
"""
import pytest
from aitest.platform.capability_router.router import CapabilityRouter


class _FakeProvider:
    """Minimal fake provider matching CapabilityProvider interface."""
    def __init__(self, cap_name: str, priority: int = 10):
        self._cap = cap_name
        self._priority = priority

    @property
    def capability(self) -> str:
        return self._cap

    @property
    def priority(self) -> int:
        return self._priority

    def available(self, context: dict) -> bool:
        return True

    def get_tool_def(self):
        from aitest.platform.capability_router.router import ToolDef
        return ToolDef(
            name=f"test__{self._cap}",
            description=f"Fake {self._cap} tool",
            parameters={"type": "object", "properties": {}},
            capability=self._cap,
        )


class TestCapabilityEnforcement:
    """Test that enforcement works when capabilities are declared."""

    def test_undeclared_agent_gets_all_capabilities(self):
        """Agent without declared capabilities gets all (backward compat)."""
        router = CapabilityRouter(load_plugins=False)
        router.register(_FakeProvider("browser"))
        router.register(_FakeProvider("codegen"))

        tools = router.tool_defs_for_agent("unknown-agent")
        assert len(tools) >= 2

    def test_declared_agent_only_gets_own_capabilities(self):
        """Agent with declared capabilities only gets those tools."""
        router = CapabilityRouter(load_plugins=False)
        router.set_agent_capabilities({"project-agent": ["project", "knowledge"]})
        router.register(_FakeProvider("project"))
        router.register(_FakeProvider("knowledge"))
        router.register(_FakeProvider("browser"))  # should be filtered out

        tools = router.tool_defs_for_agent("project-agent")
        tool_names = [t["function"]["name"] for t in tools]
        assert "test__project" in tool_names
        assert "test__knowledge" in tool_names
        assert "test__browser" not in tool_names  # filtered

    def test_enforce_allows_declared(self):
        """enforce_capability returns True for declared capability."""
        router = CapabilityRouter(load_plugins=False)
        router.set_agent_capabilities({"test-agent": ["analyze", "report"]})

        assert router.enforce_capability("test-agent", "analyze") is True
        assert router.enforce_capability("test-agent", "report") is True

    def test_enforce_denies_undeclared(self):
        """enforce_capability raises PermissionError for undeclared."""
        router = CapabilityRouter(load_plugins=False)
        router.set_agent_capabilities({"test-agent": ["analyze"]})

        with pytest.raises(PermissionError) as exc:
            router.enforce_capability("test-agent", "browser")
        assert "not authorized" in str(exc.value)
        assert "browser" in str(exc.value)

    def test_enforce_allows_when_no_mapping_set(self):
        """When no mapping is declared at all, all capabilities allowed (backward compat)."""
        router = CapabilityRouter(load_plugins=False)
        # No capabilities mapped — should allow everything
        assert router.enforce_capability("any-agent", "anything") is True

    def test_agent_capabilities_loaded_from_yaml(self):
        """Verify the real YAML has capabilities for all 8 core agents."""
        import yaml
        from pathlib import Path

        yaml_path = Path(__file__).resolve().parent.parent.parent.parent / \
                    "governance" / "agents" / "agent-definitions.yaml"
        data = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

        agents_with_caps = 0
        for name, cfg in data["agents"].items():
            caps = cfg.get("capabilities", [])
            if caps:
                agents_with_caps += 1
                assert isinstance(caps, list), f"{name}: capabilities must be a list"
                for c in caps:
                    assert c in ("project", "analyze", "codegen", "execute", "report", "knowledge", "browser"), \
                        f"{name}: unknown capability '{c}'"

        assert agents_with_caps >= 8, f"Expected >=8 agents with capabilities, got {agents_with_caps}"
