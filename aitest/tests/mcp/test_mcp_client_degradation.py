"""Tests for MCP client graceful degradation paths.

PH8-PR-8.5 Change 4: Verify ImportError (MCP SDK missing) and asyncio event-loop
conflict paths both degrade gracefully without crashing the agent.

No real MCP server needed — all external calls are mocked or patched.
"""
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ══════════════════════════════════════════════════════════════════════════
#  McpClientResult — type annotation contract
# ══════════════════════════════════════════════════════════════════════════


class TestMcpClientResultAnnotations:
    """McpClientResult.close and .call_tool must express async semantics."""

    def test_close_field_annotation_is_callable_returning_awaitable(self):
        """close annotation must NOT be bare 'callable'."""
        import inspect
        from aitest.mcp.mcp_client import McpClientResult

        hints = McpClientResult.__dataclass_fields__
        close_type = str(hints["close"].type)
        assert "Awaitable" in close_type or "Coroutine" in close_type, (
            f"McpClientResult.close annotation should express async semantics, got: {close_type}"
        )

    def test_call_tool_field_annotation_is_callable_returning_awaitable(self):
        """call_tool annotation must NOT be bare 'callable'."""
        from aitest.mcp.mcp_client import McpClientResult

        hints = McpClientResult.__dataclass_fields__
        call_tool_type = str(hints["call_tool"].type)
        assert "Awaitable" in call_tool_type or "Coroutine" in call_tool_type, (
            f"McpClientResult.call_tool annotation should express async semantics, got: {call_tool_type}"
        )

    def test_noop_close_is_awaitable(self):
        """_noop_close must be a coroutine function (await-able)."""
        from aitest.mcp.mcp_client import _noop_close
        assert asyncio.iscoroutinefunction(_noop_close)

    def test_noop_call_is_awaitable(self):
        """_noop_call must be a coroutine function (await-able)."""
        from aitest.mcp.mcp_client import _noop_call
        assert asyncio.iscoroutinefunction(_noop_call)


# ══════════════════════════════════════════════════════════════════════════
#  ImportError degradation — MCP SDK not installed
# ══════════════════════════════════════════════════════════════════════════


class TestMcpSdkMissingDegradation:
    """When the 'mcp' package is not installed, all paths degrade gracefully."""

    @pytest.mark.asyncio
    async def test_connect_stdio_import_error_returns_empty_tools(self):
        """_connect_stdio returns ({}, noop, noop) when mcp SDK is absent."""
        from aitest.mcp.mcp_client import McpServerConfig, _noop_call, _noop_close

        config = McpServerConfig(
            id="test-server",
            name="Test",
            transport_type="stdio",
            command="npx",
            args=["some-mcp-server"],
        )

        with patch.dict(sys.modules, {"mcp": None, "mcp.client.stdio": None, "mcp.client.session": None}):
            from aitest.mcp import mcp_client as _mod
            with patch("aitest.mcp.mcp_client._connect_stdio") as mock_connect:
                mock_connect.return_value = ({}, _noop_close, _noop_call)
                tools, close_fn, call_fn = await mock_connect(config)

        assert tools == {}
        assert asyncio.iscoroutinefunction(close_fn)
        assert asyncio.iscoroutinefunction(call_fn)

    @pytest.mark.asyncio
    async def test_connect_stdio_import_error_path_directly(self, monkeypatch):
        """_connect_stdio ImportError branch: returns empty tools, no exception raised."""
        from aitest.mcp.mcp_client import McpServerConfig

        config = McpServerConfig(
            id="test-server",
            name="Test",
            transport_type="stdio",
            command="npx",
            args=[],
        )

        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def _raise_on_mcp(name, *args, **kwargs):
            if name.startswith("mcp"):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=_raise_on_mcp):
            from aitest.mcp import mcp_client
            tools, close_fn, call_fn = await mcp_client._connect_stdio(config)

        assert tools == {}
        assert asyncio.iscoroutinefunction(close_fn)
        assert asyncio.iscoroutinefunction(call_fn)

    @pytest.mark.asyncio
    async def test_connect_http_import_error_path_directly(self, monkeypatch):
        """_connect_http ImportError branch: returns empty tools, no exception raised."""
        from aitest.mcp.mcp_client import McpServerConfig

        config = McpServerConfig(
            id="test-server",
            name="Test",
            transport_type="streamable-http",
            url="http://localhost:9999/mcp",
        )

        original_import = __builtins__.__import__ if hasattr(__builtins__, "__import__") else __import__

        def _raise_on_mcp(name, *args, **kwargs):
            if name.startswith("mcp"):
                raise ImportError(f"No module named '{name}'")
            return original_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=_raise_on_mcp):
            from aitest.mcp import mcp_client
            tools, close_fn, call_fn = await mcp_client._connect_http(config)

        assert tools == {}
        assert asyncio.iscoroutinefunction(close_fn)
        assert asyncio.iscoroutinefunction(call_fn)

    @pytest.mark.asyncio
    async def test_create_mcp_client_returns_result_with_empty_tools_on_sdk_missing(self):
        """create_mcp_client returns McpClientResult with empty tools when SDK absent."""
        from aitest.mcp.mcp_client import McpServerConfig, create_mcp_client

        config = McpServerConfig(
            id="no-sdk-server",
            name="No SDK",
            transport_type="stdio",
            command="npx",
            args=[],
        )

        async def _degraded(cfg):
            from aitest.mcp.mcp_client import _noop_close, _noop_call
            return {}, _noop_close, _noop_call

        with patch("aitest.mcp.mcp_client._connect_stdio", side_effect=_degraded):
            result = await create_mcp_client(config)

        assert result.server_id == "no-sdk-server"
        assert result.tools == {}
        assert asyncio.iscoroutinefunction(result.close)

    @pytest.mark.asyncio
    async def test_create_mcp_clients_for_agent_empty_when_sdk_missing(self):
        """create_mcp_clients_for_agent returns [] when all clients have no tools."""
        from aitest.mcp.mcp_client import McpClientResult, _noop_close, _noop_call

        async def _empty_client(config):
            return McpClientResult(
                server_id=config.id,
                tools={},
                close=_noop_close,
                call_tool=_noop_call,
            )

        # get_agent_mcp_servers is imported locally inside create_mcp_clients_for_agent
        # (from aitest.mcp.registry import get_agent_mcp_servers), so it must be patched
        # at its source module, not as a pre-imported attribute on aitest.mcp.mcp_client.
        with patch("aitest.mcp.mcp_client.create_mcp_client", side_effect=_empty_client):
            with patch("aitest.mcp.registry.get_agent_mcp_servers", return_value=["playwright"]):
                with patch("aitest.mcp.mcp_client._get_registry", return_value={
                    "playwright": MagicMock(id="playwright", transport_type="stdio", command="npx", args=[])
                }):
                    from aitest.mcp.mcp_client import create_mcp_clients_for_agent
                    clients = await create_mcp_clients_for_agent("qa_reviewer")

        assert clients == []


# ══════════════════════════════════════════════════════════════════════════
#  sdk_ports._mcp_clients_factory — event loop conflict degradation
# ══════════════════════════════════════════════════════════════════════════


class TestMcpClientsFactoryEventLoopConflict:
    """_mcp_clients_factory handles asyncio.run() in a running loop (FastAPI context).

    The old code: bare `except RuntimeError: clients = []` — silent, no log, no fallback.
    The new code: detect 'running event loop' message, use thread-based fallback;
                  any unexpected error logs WARNING with agent name.
    """

    def test_factory_returns_empty_on_non_loop_runtime_error(self, caplog):
        """Non-loop RuntimeError → logs warning with agent name, returns ([], {})."""
        import logging

        with patch("asyncio.run", side_effect=RuntimeError("some unrelated error")):
            with caplog.at_level(logging.WARNING, logger="aitest.platform.sdk_ports"):
                from aitest.platform.sdk_ports import _mcp_clients_factory
                clients, tools = _mcp_clients_factory("test-agent")

        assert clients == []
        assert tools == {}
        assert any("test-agent" in r.message for r in caplog.records)

    def test_factory_routes_to_thread_fallback_on_running_loop_error(self, caplog):
        """'running event loop' RuntimeError → thread fallback, not silent swallow."""
        import logging
        import concurrent.futures

        def fake_run(coro):
            coro.close()
            raise RuntimeError("asyncio.run() cannot be called from a running event loop")

        mock_pool = MagicMock()
        mock_pool.__enter__ = lambda s: s
        mock_pool.__exit__ = MagicMock(return_value=False)
        mock_future = MagicMock()
        mock_future.result.side_effect = RuntimeError("thread pool also failed")
        mock_pool.submit.return_value = mock_future

        with patch("asyncio.run", side_effect=fake_run):
            with patch("concurrent.futures.ThreadPoolExecutor", return_value=mock_pool):
                with caplog.at_level(logging.WARNING, logger="aitest.platform.sdk_ports"):
                    from aitest.platform import sdk_ports
                    clients, tools = sdk_ports._mcp_clients_factory("my-agent")

        assert clients == []
        assert tools == {}
        warning_messages = [r.message for r in caplog.records if r.levelno >= logging.WARNING]
        assert any("my-agent" in m for m in warning_messages), (
            f"Expected WARNING mentioning 'my-agent', got: {warning_messages}"
        )

    def test_factory_does_not_raise_on_unexpected_exception(self):
        """Factory never raises — unexpected exceptions produce ([], {})."""
        with patch("asyncio.run", side_effect=OSError("disk read error")):
            from aitest.platform.sdk_ports import _mcp_clients_factory
            try:
                clients, tools = _mcp_clients_factory("ghost-agent")
            except Exception as e:
                pytest.fail(f"_mcp_clients_factory raised unexpectedly: {e}")

        assert clients == []
        assert tools == {}


# ══════════════════════════════════════════════════════════════════════════
#  AsyncToolProvider — Protocol contract
# ══════════════════════════════════════════════════════════════════════════


class TestAsyncToolProviderProtocol:
    """AsyncToolProvider Protocol is importable and structurally correct."""

    def test_async_tool_provider_importable(self):
        from alice_engine.core.tool_provider import AsyncToolProvider
        assert AsyncToolProvider is not None

    def test_async_tool_provider_is_runtime_checkable(self):
        from alice_engine.core.tool_provider import AsyncToolProvider
        assert not isinstance(object(), AsyncToolProvider)

    def test_async_tool_provider_has_async_call_tool(self):
        """Protocol must declare async call_tool_async and close_async."""
        from alice_engine.core.tool_provider import AsyncToolProvider

        assert asyncio.iscoroutinefunction(AsyncToolProvider.call_tool_async), (
            "AsyncToolProvider.call_tool_async must be an async def"
        )
        assert asyncio.iscoroutinefunction(AsyncToolProvider.close_async), (
            "AsyncToolProvider.close_async must be an async def"
        )

    def test_conforming_class_satisfies_protocol(self):
        """A class implementing the async methods satisfies isinstance check."""
        from alice_engine.core.tool_provider import AsyncToolProvider, ToolResult

        class MyAsyncProvider:
            def list_tools(self, agent_name: str = "") -> list:
                return []

            async def call_tool_async(self, name: str, arguments: dict, **kwargs):
                return ToolResult(content="ok", success=True)

            async def close_async(self) -> None:
                return None

        provider = MyAsyncProvider()
        assert isinstance(provider, AsyncToolProvider)
