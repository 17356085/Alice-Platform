"""Tests for platform/capability_router/ — CapabilityRouter + ToolDef.

Tests: ToolDef serialization, CapabilityRouter registration,
enforce_capability, tool_defs_for_agent, execute, resolve.
No real providers — uses FakeProvider matching CapabilityProvider interface.
"""
import pytest
from unittest.mock import MagicMock

from aitest.platform.capability_router.router import (
    CapabilityRouter, CapabilityProvider, ToolDef, ToolCall, ToolResult,
    CapabilityUnavailableError,
)
from aitest.platform.capability_router.agent_capabilities import AGENT_CAPABILITIES


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


class _FakeProvider:
    """Minimal CapabilityProvider for testing."""
    def __init__(self, cap_name: str, priority: int = 100, available: bool = True):
        self.capability = cap_name
        self.provider_name = f"fake-{cap_name}"
        self.priority = priority
        self._available = available
        self._last_call: ToolCall | None = None

    def get_tool_def(self) -> ToolDef:
        return ToolDef(
            name=f"test__{self.capability.replace('.', '_')}",
            description=f"Fake {self.capability} tool",
            parameters={"type": "object", "properties": {}},
            capability=self.capability,
        )

    def available(self, context: dict) -> bool:
        return self._available

    def truncation_limit(self) -> int:
        return 8000

    def execute(self, call: ToolCall, context: dict) -> ToolResult:
        self._last_call = call
        return ToolResult(
            call_id=call.id, success=True,
            content=f"Executed {call.name}",
        )


# ══════════════════════════════════════════════════════════════════════════
#  ToolDef
# ══════════════════════════════════════════════════════════════════════════


class TestToolDef:
    def test_to_openai_format(self):
        td = ToolDef(
            name="browser__navigate",
            description="Navigate to URL",
            parameters={"type": "object", "properties": {"url": {"type": "string"}}},
            capability="browser.navigate",
        )
        result = td.to_openai_format()
        assert result["type"] == "function"
        assert result["function"]["name"] == "browser__navigate"
        assert "url" in str(result["function"]["parameters"])

    def test_defaults(self):
        td = ToolDef(name="test", description="desc", parameters={})
        assert td.capability == ""
        assert td.side_effect == "read"
        assert td.requires_confirmation is False


# ══════════════════════════════════════════════════════════════════════════
#  CapabilityRouter — registration
# ══════════════════════════════════════════════════════════════════════════


class TestRouterRegistration:
    def test_register_adds_capability(self):
        router = CapabilityRouter(load_plugins=False)
        router.register(_FakeProvider("browser.navigate"))
        assert "browser.navigate" in router.list_capabilities()

    def test_register_sorts_by_priority(self):
        router = CapabilityRouter(load_plugins=False)
        router.register(_FakeProvider("test.cap", priority=50))
        router.register(_FakeProvider("test.cap", priority=10))
        providers = router._registry["test.cap"]
        assert providers[0].priority <= providers[1].priority

    def test_set_agent_capabilities(self):
        router = CapabilityRouter(load_plugins=False)
        router.set_agent_capabilities({"test-agent": ["browser", "codegen"]})
        assert router.list_agents() == ["test-agent"]

    def test_agent_capabilities_loaded_from_module(self):
        """AGENT_CAPABILITIES module has entries for all 8 core agents."""
        assert len(AGENT_CAPABILITIES) >= 8
        for agent_name in ["automation-agent", "execution-agent", "report-agent"]:
            assert agent_name in AGENT_CAPABILITIES


# ══════════════════════════════════════════════════════════════════════════
#  enforce_capability
# ══════════════════════════════════════════════════════════════════════════


class TestEnforceCapability:
    def test_allows_all_when_no_declaration(self):
        router = CapabilityRouter(load_plugins=False)
        assert router.enforce_capability("any-agent", "anything") is True

    def test_allows_declared_capability(self):
        router = CapabilityRouter(load_plugins=False)
        router.set_agent_capabilities({"test-agent": ["browser", "codegen"]})
        assert router.enforce_capability("test-agent", "browser") is True

    def test_denies_undeclared_capability(self):
        router = CapabilityRouter(load_plugins=False)
        router.set_agent_capabilities({"test-agent": ["browser"]})
        with pytest.raises(PermissionError) as exc:
            router.enforce_capability("test-agent", "codegen")
        assert "not authorized" in str(exc.value)


# ══════════════════════════════════════════════════════════════════════════
#  tool_defs_for_agent
# ══════════════════════════════════════════════════════════════════════════


class TestToolDefsForAgent:
    def test_undeclared_agent_gets_all(self):
        router = CapabilityRouter(load_plugins=False)
        router.register(_FakeProvider("browser.navigate"))
        router.register(_FakeProvider("codegen.page_object"))
        tools = router.tool_defs_for_agent("unknown-agent")
        assert len(tools) == 2

    def test_declared_agent_gets_filtered(self):
        router = CapabilityRouter(load_plugins=False)
        router.set_agent_capabilities({"my-agent": ["browser.navigate"]})
        router.register(_FakeProvider("browser.navigate"))
        router.register(_FakeProvider("codegen.page_object"))
        tools = router.tool_defs_for_agent("my-agent")
        assert len(tools) == 1
        assert "browser" in tools[0]["function"]["name"]

    def test_no_duplicate_tool_names(self):
        router = CapabilityRouter(load_plugins=False)
        router.register(_FakeProvider("test.cap", priority=10))
        router.register(_FakeProvider("test.cap", priority=20))
        tools = router.tool_defs_for_agent("any")
        # Only highest priority provider per capability
        assert len(tools) == 1


# ══════════════════════════════════════════════════════════════════════════
#  resolve
# ══════════════════════════════════════════════════════════════════════════


class TestResolve:
    def test_resolves_available_provider(self):
        router = CapabilityRouter(load_plugins=False)
        router.register(_FakeProvider("test.cap"))
        provider = router.resolve("test.cap", {})
        assert provider.capability == "test.cap"

    def test_raises_for_unavailable(self):
        router = CapabilityRouter(load_plugins=False)
        router.register(_FakeProvider("test.cap", available=False))
        with pytest.raises(CapabilityUnavailableError):
            router.resolve("test.cap", {})

    def test_raises_for_unknown_capability(self):
        router = CapabilityRouter(load_plugins=False)
        with pytest.raises(CapabilityUnavailableError):
            router.resolve("nonexistent", {})


# ══════════════════════════════════════════════════════════════════════════
#  execute
# ══════════════════════════════════════════════════════════════════════════


class TestExecute:
    def test_executes_known_tool(self):
        router = CapabilityRouter(load_plugins=False)
        router.register(_FakeProvider("browser.navigate"))
        call = ToolCall(id="c1", name="test__browser_navigate", arguments={})
        result = router.execute(call, {})
        assert result.success is True
        assert "Executed" in result.content

    def test_unknown_tool_returns_error(self):
        router = CapabilityRouter(load_plugins=False)
        call = ToolCall(id="c1", name="unknown__tool", arguments={})
        result = router.execute(call, {})
        assert result.success is False
        assert "Unknown tool" in result.content

    def test_truncation(self):
        router = CapabilityRouter(load_plugins=False)
        provider = _FakeProvider("test.cap")
        long_content = "x" * 10000
        # Override execute to return long content
        provider.execute = lambda c, ctx: ToolResult(
            call_id=c.id, success=True, content=long_content,
        )
        router.register(provider)
        call = ToolCall(id="c1", name="test__test_cap", arguments={})
        result = router.execute(call, {})
        assert result.truncated is True
        assert len(result.content) < len(long_content)

    def test_provider_exception_returns_error(self):
        router = CapabilityRouter(load_plugins=False)
        provider = _FakeProvider("test.cap")
        provider.execute = lambda c, ctx: (_ for _ in ()).throw(RuntimeError("boom"))
        router.register(provider)
        call = ToolCall(id="c1", name="test__test_cap", arguments={})
        result = router.execute(call, {})
        assert result.success is False
        assert "boom" in result.error

    def test_execute_tool_calls_batch(self):
        router = CapabilityRouter(load_plugins=False)
        router.register(_FakeProvider("browser.navigate"))
        router.register(_FakeProvider("codegen.test"))
        tcs = [
            {"id": "c1", "name": "test__browser_navigate", "arguments": {}},
            {"id": "c2", "name": "test__codegen_test", "arguments": {}},
        ]
        results = router.execute_tool_calls(tcs, {}, agent_name="test-agent")
        assert len(results) == 2
        assert results[0].success is True
        assert results[1].success is True

    def test_execute_tool_calls_handles_function_format(self):
        router = CapabilityRouter(load_plugins=False)
        router.register(_FakeProvider("browser.navigate"))
        tcs = [
            {"id": "c1", "function": {"name": "test__browser_navigate", "arguments": {"url": "/"}}},
        ]
        results = router.execute_tool_calls(tcs, {})
        assert len(results) == 1
        assert results[0].success is True


# ══════════════════════════════════════════════════════════════════════════
#  ToolCall + ToolResult dataclasses
# ══════════════════════════════════════════════════════════════════════════


class TestToolCall:
    def test_default_timestamp(self):
        tc = ToolCall(id="c1", name="test.tool", arguments={})
        assert tc.timestamp > 0

    def test_agent_name_default(self):
        tc = ToolCall(id="c1", name="test", arguments={})
        assert tc.agent_name == ""


class TestToolResult:
    def test_success_result(self):
        r = ToolResult(call_id="c1", success=True, content="done")
        assert r.error is None
        assert r.truncated is False

    def test_failure_result(self):
        r = ToolResult(call_id="c1", success=False, content="", error="timeout")
        assert r.error == "timeout"

    def test_defaults(self):
        r = ToolResult(call_id="c1", success=True, content="x")
        assert r.data is None
        assert r.duration_ms == 0.0
