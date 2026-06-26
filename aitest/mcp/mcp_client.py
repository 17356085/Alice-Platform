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
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


# ── Types ──────────────────────────────────────────────────────────────────

@dataclass
class McpClientResult:
    """Result of connecting to one MCP server."""
    server_id: str
    tools: dict      # tool_name → tool_definition (for LLM function calling)
    close: callable   # async cleanup function


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

def _get_registry() -> dict[str, McpServerConfig]:
    """Lazy-load MCP server registry."""
    try:
        from aitest.mcp.registry import MCP_SERVER_REGISTRY
        return MCP_SERVER_REGISTRY
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

    try:
        if config.transport_type == "stdio":
            tools, close_fn = await _connect_stdio(config)
        elif config.transport_type == "streamable-http":
            tools, close_fn = await _connect_http(config)
    except Exception as e:
        logger.warning(
            "MCP client creation failed for server=%s: %s", config.id, e,
        )

    return McpClientResult(
        server_id=config.id,
        tools=tools,
        close=close_fn,
    )


async def create_mcp_clients_for_agent(
    agent_type: str,
    env: dict[str, str] = None,
) -> list[McpClientResult]:
    """Create MCP clients for all servers required by an agent type.

    Resolves which MCP servers the agent needs from registry, then
    creates clients for each. Failed connections are non-fatal —
    the agent functions without optional MCP tools.

    Args:
        agent_type: Agent type name (e.g. "qa_reviewer", "automation-agent").
        env: Optional environment variables for server processes.

    Returns:
        List of McpClientResult (successful connections only).
    """
    from aitest.mcp.registry import get_agent_mcp_servers

    server_ids = get_agent_mcp_servers(agent_type)
    registry = _get_registry()

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

        async with stdio_client(
            command=config.command,
            args=config.args or [],
            env=config.env or None,
        ) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                tools = {
                    f"mcp__{config.id}__{t.name}": {
                        "description": t.description or "",
                        "inputSchema": t.inputSchema or {},
                    }
                    for t in result.tools
                }

                async def _close():
                    pass  # Session auto-closes via context manager

                return tools, _close
    except ImportError:
        logger.debug("MCP SDK not available for stdio client — returning empty tools")
        return {}, _noop_close
    except Exception as e:
        logger.debug("Stdio MCP connection failed for %s: %s", config.id, e)
        return {}, _noop_close


async def _connect_http(config: McpServerConfig) -> tuple[dict, callable]:
    """Connect to an MCP server via streamable HTTP (SSE).

    Uses Python MCP SDK HTTP client if available.
    Returns (tools_dict, close_async_fn).
    """
    try:
        from mcp.client.sse import sse_client
        from mcp.client.session import ClientSession

        async with sse_client(url=config.url) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                tools = {
                    f"mcp__{config.id}__{t.name}": {
                        "description": t.description or "",
                        "inputSchema": t.inputSchema or {},
                    }
                    for t in result.tools
                }

                async def _close():
                    pass

                return tools, _close
    except ImportError:
        logger.debug("MCP SDK not available for HTTP client — returning empty tools")
        return {}, _noop_close
    except Exception as e:
        logger.debug("HTTP MCP connection failed for %s: %s", config.id, e)
        return {}, _noop_close


async def _noop_close():
    pass
