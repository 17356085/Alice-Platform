"""ToolProvider — 工具调用接口。

SDK 定义接口，平台层实现具体工具协议 (MCP, Function Calling, etc.)。

用法:
    from alice_engine.core.tool_provider import ToolProvider, AsyncToolProvider, ToolDef, ToolResult

    class MyToolProvider(ToolProvider):
        def list_tools(self, agent_name: str) -> list[ToolDef]:
            return [ToolDef(name="search", description="搜索知识库")]

        def call_tool(self, name: str, arguments: dict, **kwargs) -> ToolResult:
            return ToolResult(content="搜索结果", success=True)

    class MyAsyncToolProvider(AsyncToolProvider):
        def list_tools(self, agent_name: str) -> list[ToolDef]:
            return [ToolDef(name="mcp_tool", description="MCP工具")]

        async def call_tool_async(self, name: str, arguments: dict, **kwargs) -> ToolResult:
            result = await some_async_call(name, arguments)
            return ToolResult(content=result, success=True)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Awaitable, Protocol, runtime_checkable


@dataclass
class ToolDef:
    """工具定义。"""
    name: str = ""
    description: str = ""
    parameters: dict = field(default_factory=dict)
    required: list[str] = field(default_factory=list)


@dataclass
class ToolResult:
    """工具执行结果。"""
    content: str = ""
    success: bool = True
    error: str = ""
    metadata: dict = field(default_factory=dict)


@runtime_checkable
class ToolProvider(Protocol):
    """工具调用接口。

    平台层实现此协议，提供工具调用能力。
    """

    def list_tools(self, agent_name: str = "") -> list[ToolDef]:
        """列出可用工具。

        Args:
            agent_name: Agent 名称 (可选，用于过滤)

        Returns:
            工具定义列表
        """
        ...

    def call_tool(self, name: str, arguments: dict, **kwargs) -> ToolResult:
        """调用工具。

        Args:
            name: 工具名称
            arguments: 工具参数
            **kwargs: 额外参数

        Returns:
            工具执行结果
        """
        ...

    def supports_agent(self, agent_name: str) -> bool:
        """是否支持指定 Agent。

        Args:
            agent_name: Agent 名称

        Returns:
            是否支持
        """
        ...


@runtime_checkable
class AsyncToolProvider(Protocol):
    """异步工具调用接口，用于 MCP 等原生异步工具协议。

    MCP 客户端是异步的（连接、关闭、调用均为 coroutine），无法适配
    同步 ToolProvider 协议。AsyncToolProvider 表达这一差异，让调用
    方可以在类型层面区分同步/异步工具来源。

    实现要求:
        - list_tools() 仍为同步（只是返回工具元数据，无 I/O）
        - call_tool_async() 为 async，必须 await
        - close_async() 为 async，必须 await（清理连接）
    """

    def list_tools(self, agent_name: str = "") -> list[ToolDef]:
        """列出可用工具（同步，无 I/O）。"""
        ...

    async def call_tool_async(
        self, name: str, arguments: dict, **kwargs
    ) -> ToolResult:
        """异步调用工具。

        Args:
            name: 工具名称
            arguments: 工具参数
            **kwargs: 额外参数

        Returns:
            工具执行结果
        """
        ...

    async def close_async(self) -> None:
        """释放底层连接（如 MCP stdio/HTTP session）。

        必须在 Agent 运行结束后 await，否则会泄漏子进程或 HTTP 连接。
        """
        ...
