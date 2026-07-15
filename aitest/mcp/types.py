"""MCP 类型定义 — 中立数据层，无依赖。

定义 MCP Server 的配置和结果类型，供 platform 和 mcp 模块共享。

Author: AITest Platform
Created: 2026-07-14
Related: 循环依赖拆分 Step 1
"""

from dataclasses import dataclass, field
from typing import Awaitable, Callable, Optional


@dataclass
class McpServerConfig:
    """MCP Server 配置."""

    id: str
    name: str
    description: str = ""
    enabled_by_default: bool = False
    transport_type: str = "stdio"       # "stdio" | "streamable-http"
    command: str = ""                    # For stdio transport
    args: list[str] = field(default_factory=list)
    url: str = ""                        # For streamable-http transport
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class McpClientResult:
    """MCP 客户端连接结果.

    Attributes:
        server_id: MCP server 标识符
        tools: tool_name → tool_definition (用于 LLM function calling)
        close: 异步清理函数。必须 await: await client.close()
        call_tool: 异步工具调用函数。必须 await: await client.call_tool(name, args)
                   签名: async (tool_name: str, arguments: dict | None) -> dict
    """

    server_id: str
    tools: dict      # tool_name → tool_definition
    close: Callable[[], Awaitable[None]]
    call_tool: Optional[Callable[[str, Optional[dict]], Awaitable[dict]]] = None


@dataclass
class MCPServer:
    """MCP Server 数据模型 (数据库实体)."""

    mcp_server_id: str
    name: str
    description: str = ""
    transport_type: str = "stdio"              # "stdio" | "http"
    command: str = ""                           # stdio: 启动命令
    args: list[str] = field(default_factory=list)
    url: str = ""                               # http: MCP Server URL
    env: dict[str, str] = field(default_factory=dict)
    tools: list[str] = field(default_factory=list)
    status: str = "stopped"                     # "stopped" | "starting" | "running" | "error"
    process_id: Optional[int] = None
    enabled_by_default: bool = False
    org_id: str = "default-org"
    created_by: str = "admin"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_health_check: Optional[str] = None

    def to_config(self) -> McpServerConfig:
        """转换为 McpServerConfig (用于 mcp_client.py)."""
        return McpServerConfig(
            id=self.mcp_server_id,
            name=self.name,
            description=self.description,
            enabled_by_default=self.enabled_by_default,
            transport_type=self.transport_type,
            command=self.command,
            args=self.args,
            url=self.url,
            env=self.env,
        )


@dataclass
class AgentMCPMapping:
    """Agent → MCP Server 映射."""

    id: Optional[int] = None
    agent_type: str = ""
    mcp_server_id: str = ""
    allowed_tools: list[str] = field(default_factory=list)  # 空列表表示全部允许
    org_id: str = "default-org"
    created_at: Optional[str] = None
