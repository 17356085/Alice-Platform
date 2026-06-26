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


def get_agent_mcp_servers(agent_type: str) -> list[str]:
    """Return MCP server IDs required for an agent type.

    Args:
        agent_type: Agent type name (e.g. "automation-agent").

    Returns:
        List of server IDs (empty list if agent has no MCP servers).
    """
    # Exact match first, then fuzzy
    if agent_type in AGENT_MCP_SERVERS:
        return AGENT_MCP_SERVERS[agent_type]

    # Fuzzy: try matching suffix (e.g. "automation-agent" matches "automation-agent")
    for key in AGENT_MCP_SERVERS:
        if agent_type.endswith(key) or key.endswith(agent_type):
            return AGENT_MCP_SERVERS[key]

    return []
