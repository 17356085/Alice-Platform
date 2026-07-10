"""MCP Client — connect to external MCP Servers from aitest agents.

Task 6 (P1) — APERANT_MIGRATION_PLAN.md
Port of Aperant mcp/client.ts: createMCPClient() + createMcpClientsForAgent().

Enables aitest agents to call external MCP servers (Playwright MCP,
database MCP, etc.) as tools. Complements the existing MCP Server
(aitest/mcp/) which exposes aitest tools to external AI.

Transports: stdio (subprocess) + streamable-http (remote SSE).
Graceful degradation: MCP connection failure is non-blocking.

Usage:
    from aitest.mcp.mcp_client import create_mcp_clients_for_agent

    clients = await create_mcp_clients_for_agent("qa_reviewer")
    tools = merge_mcp_tools(clients)
    await close_all_mcp_clients(clients)
"""

import logging
import json
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional

logger = logging.getLogger(__name__)


# ── Types ──────────────────────────────────────────────────────────────────

@dataclass
class McpClientResult:
    """Result of connecting to one MCP server.

    Attributes:
        server_id: MCP server identifier
        tools: tool_name → tool_definition (for LLM function calling)
        close: Async cleanup function. Must be awaited: await client.close()
        call_tool: Async tool call function. Must be awaited: await client.call_tool(name, args)
                   Signature: async (tool_name: str, arguments: dict | None) -> dict
    """
    server_id: str
    tools: dict      # tool_name → tool_definition (for LLM function calling)
    close: Callable[[], Awaitable[None]]
    call_tool: Optional[Callable[[str, Optional[dict]], Awaitable[dict]]] = None


@dataclass
class McpServerConfig:
    """Configuration for a single MCP server."""
    id: str
    name: str
    description: str = ""
    enabled_by_default: bool = False
    transport_type: str = "stdio"       # "stdio" | "streamable-http"
    command: str = ""                    # For stdio transport
    args: list[str] = field(default_factory=list)
    url: str = ""                        # For streamable-http transport
    env: dict[str, str] = field(default_factory=dict)


# ═══════════════════════════════════════════════════════════════════════════
#  Registry (lazy load from registry.py)
# ═══════════════════════════════════════════════════════════════════════════

def _get_registry(use_db: bool = True) -> dict[str, McpServerConfig]:
    """Lazy-load MCP server registry (支持数据库动态加载).

    Args:
        use_db: 是否从数据库加载（默认 True），False 则使用硬编码配置

    Returns:
        {mcp_server_id: McpServerConfig}
    """
    try:
        from aitest.mcp.registry import get_mcp_server_registry
        return get_mcp_server_registry(use_db=use_db)
    except Exception:
        return {}


# ═══════════════════════════════════════════════════════════════════════════
#  Client creation
# ═══════════════════════════════════════════════════════════════════════════

async def create_mcp_client(config: McpServerConfig) -> McpClientResult:
    """Create an MCP client for a single server configuration.

    Supports stdio (subprocess) and streamable-http transports.
    Uses Python MCP SDK if available, otherwise graceful degradation.
    """
    tools: dict = {}
    close_fn = _noop_close
    call_fn = _noop_call

    try:
        if config.transport_type == "stdio":
            tools, close_fn, call_fn = await _connect_stdio(config)
        elif config.transport_type == "streamable-http":
            tools, close_fn, call_fn = await _connect_http(config)
    except Exception as e:
        logger.warning(
            "MCP client creation failed for server=%s: %s", config.id, e,
        )

    return McpClientResult(
        server_id=config.id,
        tools=tools,
        close=close_fn,
        call_tool=call_fn,
    )


async def create_mcp_clients_for_agent(
    agent_type: str,
    env: dict[str, str] = None,
    use_db: bool = True,
) -> list[McpClientResult]:
    """Create MCP clients for all servers required by an agent type.

    Resolves which MCP servers the agent needs from registry, then
    creates clients for each. Failed connections are non-fatal —
    the agent functions without optional MCP tools.

    Args:
        agent_type: Agent type name (e.g. "qa_reviewer", "automation-agent").
        env: Optional environment variables for server processes.
        use_db: 是否从数据库加载配置（默认 True），False 则使用硬编码

    Returns:
        List of McpClientResult (successful connections only).
    """
    from aitest.mcp.registry import get_agent_mcp_servers

    server_ids = get_agent_mcp_servers(agent_type, use_db=use_db)
    registry = _get_registry(use_db=use_db)

    clients: list[McpClientResult] = []
    for sid in server_ids:
        config = registry.get(sid)
        if not config:
            continue
        try:
            client = await create_mcp_client(config)
            if client.tools:
                clients.append(client)
                logger.info(
                    "MCP client connected: %s (%d tools)", sid, len(client.tools),
                )
        except Exception as e:
            logger.warning("MCP client skipped: %s (%s)", sid, e)

    return clients


def merge_mcp_tools(clients: list[McpClientResult]) -> dict:
    """Merge tools from multiple MCP clients into a single tool map."""
    merged: dict = {}
    for c in clients:
        if c.tools:
            merged.update(c.tools)
    return merged


async def close_all_mcp_clients(clients: list[McpClientResult]) -> None:
    """Close all MCP clients gracefully. Best-effort, no exceptions."""
    for c in clients:
        try:
            await c.close()
        except Exception:
            pass


# ── Transport implementations ──────────────────────────────────────────────

async def _connect_stdio(config: McpServerConfig) -> tuple[dict, callable]:
    """Connect to an MCP server via stdio subprocess.

    Uses Python MCP SDK (mcp.client.stdio) if available.
    Returns (tools_dict, close_async_fn).
    """
    try:
        from mcp.client.stdio import stdio_client
        from mcp.client.session import ClientSession

        stack = AsyncExitStack()
        read_stream, write_stream = await stack.enter_async_context(
            stdio_client(
            command=config.command,
            args=config.args or [],
            env=config.env or None,
            )
        )
        session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()
        result = await session.list_tools()
        tools = {
            f"mcp__{config.id}__{t.name}": {
                "type": "function",
                "function": {
                    "name": f"mcp__{config.id}__{t.name}",
                    "description": t.description or "",
                    "parameters": t.inputSchema or {"type": "object", "properties": {}},
                },
                "x-mcp-server": config.id,
                "x-mcp-tool": t.name,
            }
            for t in result.tools
        }

        async def _call(tool_name: str, arguments: dict | None = None) -> dict:
            remote_name = tool_name.split(f"mcp__{config.id}__", 1)[-1]
            resp = await session.call_tool(remote_name, arguments or {})
            return {
                "call_id": tool_name,
                "success": True,
                "content": _normalize_tool_response(resp),
                "data": resp,
                "error": None,
            }

        async def _close():
            await stack.aclose()

        return tools, _close, _call
    except ImportError:
        logger.debug("MCP SDK not available for stdio client — returning empty tools")
        return {}, _noop_close, _noop_call
    except Exception as e:
        logger.debug("Stdio MCP connection failed for %s: %s", config.id, e)
        return {}, _noop_close, _noop_call


async def _connect_http(config: McpServerConfig) -> tuple[dict, callable]:
    """Connect to an MCP server via streamable HTTP (SSE).

    Uses Python MCP SDK HTTP client if available.
    Returns (tools_dict, close_async_fn).
    """
    try:
        from mcp.client.sse import sse_client
        from mcp.client.session import ClientSession

        stack = AsyncExitStack()
        read_stream, write_stream = await stack.enter_async_context(sse_client(url=config.url))
        session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
        await session.initialize()
        result = await session.list_tools()
        tools = {
            f"mcp__{config.id}__{t.name}": {
                "type": "function",
                "function": {
                    "name": f"mcp__{config.id}__{t.name}",
                    "description": t.description or "",
                    "parameters": t.inputSchema or {"type": "object", "properties": {}},
                },
                "x-mcp-server": config.id,
                "x-mcp-tool": t.name,
            }
            for t in result.tools
        }

        async def _call(tool_name: str, arguments: dict | None = None) -> dict:
            remote_name = tool_name.split(f"mcp__{config.id}__", 1)[-1]
            resp = await session.call_tool(remote_name, arguments or {})
            return {
                "call_id": tool_name,
                "success": True,
                "content": _normalize_tool_response(resp),
                "data": resp,
                "error": None,
            }

        async def _close():
            await stack.aclose()

        return tools, _close, _call
    except ImportError:
        logger.debug("MCP SDK not available for HTTP client — returning empty tools")
        return {}, _noop_close, _noop_call
    except Exception as e:
        logger.debug("HTTP MCP connection failed for %s: %s", config.id, e)
        return {}, _noop_close, _noop_call


async def _noop_close():
    pass


async def _noop_call(tool_name: str, arguments: dict | None = None) -> dict:
    return {
        "call_id": tool_name,
        "success": False,
        "content": "MCP tool unavailable",
        "data": None,
        "error": "unavailable",
    }


def _normalize_tool_response(response) -> str:
    if response is None:
        return ""
    content = getattr(response, "content", None)
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict):
                parts.append(str(item.get("text", item)))
            else:
                parts.append(str(getattr(item, "text", item)))
        return "\n".join(part for part in parts if part).strip()
    if isinstance(content, str):
        return content
    if isinstance(response, dict):
        try:
            return json.dumps(response, ensure_ascii=False)
        except Exception:
            return str(response)
    return str(response)
