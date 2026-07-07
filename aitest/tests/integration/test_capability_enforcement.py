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

    def test_agent_capability_contracts_are_discoverable(self):
        """Verify core agents resolve to discoverable capability contracts."""
        from aitest.platform.capability_router import create_router

        router = create_router()
        for agent_name, caps in router._agent_capabilities.items():
            contracts = router.capability_contracts_for_agent(agent_name)
            assert isinstance(caps, list)
            assert contracts, f"{agent_name} should have discoverable contracts"
            for contract in contracts:
                assert contract.capability in caps
