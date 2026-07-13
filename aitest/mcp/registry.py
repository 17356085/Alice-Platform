"""MCP Server Registry — per-agent MCP server configuration.

Task 6 (P1) — APERANT_MIGRATION_PLAN.md
Port of Aperant mcp/registry.ts: server definitions + agent→server mapping.

Defines which external MCP servers each agent type can connect to.
Servers are lazily connected — connection failure is non-blocking.

Server types:
  - browser-mcp    → Playwright/Puppeteer browser automation
  - context7       → Documentation lookup
  - memory         → Knowledge graph (Graphiti sidecar)

Usage:
    from aitest.mcp.registry import get_agent_mcp_servers
    servers = get_agent_mcp_servers("qa_reviewer")  # → ["browser-mcp"]
"""

from aitest.mcp.mcp_client import McpServerConfig

# ═══════════════════════════════════════════════════════════════════════════
#  Server definitions
# ═══════════════════════════════════════════════════════════════════════════

MCP_SERVER_REGISTRY: dict[str, McpServerConfig] = {
    "browser-mcp": McpServerConfig(
        id="browser-mcp",
        name="Browser MCP",
        description="Playwright browser automation for web testing",
        enabled_by_default=False,
        transport_type="stdio",
        command="npx",
        args=["-y", "@anthropic-ai/playwright-mcp-server"],
    ),
    "context7": McpServerConfig(
        id="context7",
        name="Context7",
        description="Documentation lookup for libraries and frameworks",
        enabled_by_default=True,
        transport_type="stdio",
        command="npx",
        args=["-y", "@upstash/context7-mcp@latest"],
    ),
    "memory": McpServerConfig(
        id="memory",
        name="Memory",
        description="Knowledge graph memory for cross-session insights",
        enabled_by_default=False,
        transport_type="streamable-http",
        url="",  # From env: GRAPHITI_MCP_URL or MEMORY_MCP_URL
    ),
}


# ═══════════════════════════════════════════════════════════════════════════
#  Agent → MCP server mapping
# ═══════════════════════════════════════════════════════════════════════════

AGENT_MCP_SERVERS: dict[str, list[str]] = {
    # Test agents — browser automation for web testing
    "automation-agent":       ["browser-mcp"],
    "execution-agent":        ["browser-mcp"],
    "qa_reviewer":            ["browser-mcp"],
    "test-design-agent":      ["context7"],
    "bug-analysis-agent":     ["context7"],

    # Dev agents (TLO) — documentation + memory
    "project-agent":          ["context7", "memory"],
    "requirement-agent":      ["context7"],
    "knowledge-agent":        ["memory"],
    "report-agent":           [],

    # Dev SOP agents (platform self-development) — 9 agents
    "pm-agent":               [],
    "req-agent":              ["context7"],
    "arch-agent":             ["context7"],
    "design-agent":           [],
    "frontend-agent":         ["context7"],
    "backend-agent":          ["context7"],
    "review-agent":           [],
    "dev-test-agent":         [],
    "debug-agent":            [],
    "build-agent":            [],
}


def get_agent_mcp_servers(agent_type: str, use_db: bool = True) -> list[str]:
    """Return MCP server IDs required for an agent type.

    Args:
        agent_type: Agent type name (e.g. "automation-agent").
        use_db: 是否从数据库加载（默认 True），False 则使用硬编码配置

    Returns:
        List of server IDs (empty list if agent has no MCP servers).
    """
    # P6-2: 优先从数据库加载，回退到硬编码
    if use_db:
        try:
            from aitest.platform.mcp_server_store import MCPServerStore
            store = MCPServerStore()
            try:
                server_ids = store.get_agent_mcp_servers(agent_type)
            finally:
                store.close()
            if server_ids:
                return server_ids
        except Exception:
            # 数据库不可用，回退到硬编码
            pass

    # 硬编码配置 (向后兼容)
    # Exact match first, then fuzzy
    if agent_type in AGENT_MCP_SERVERS:
        return AGENT_MCP_SERVERS[agent_type]

    # Fuzzy: try matching suffix (e.g. "automation-agent" matches "automation-agent")
    for key in AGENT_MCP_SERVERS:
        if agent_type.endswith(key) or key.endswith(agent_type):
            return AGENT_MCP_SERVERS[key]

    return []


def get_mcp_server_registry(use_db: bool = True) -> dict[str, McpServerConfig]:
    """获取 MCP Server Registry (支持数据库动态加载).

    Args:
        use_db: 是否从数据库加载（默认 True），False 则使用硬编码配置

    Returns:
        {mcp_server_id: McpServerConfig}
    """
    # P6-2: 优先从数据库加载
    if use_db:
        try:
            from aitest.platform.mcp_server_store import MCPServerStore
            store = MCPServerStore()
            try:
                servers = store.list_mcp_servers()
            finally:
                store.close()
            if servers:
                return {s.mcp_server_id: s.to_config() for s in servers}
        except Exception:
            # 数据库不可用，回退到硬编码
            pass

    # 硬编码配置 (向后兼容)
    return MCP_SERVER_REGISTRY
