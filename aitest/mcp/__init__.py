"""
MCP Server: aitest-tools
============================================================================
P3-0: 模块化架构 — 从 1369 行单体拆分为 aitest/mcp/ 包。

包结构:
  config.py          — 路径常量
  error_taxonomy.py  — ErrorCode + MCPError
  audit.py           — 审计日志 (P2-3)
  rate_limit.py      — 权限分级 + 速率控制 (P2-2)
  cancellation.py    — 长任务取消 (P2-4)
  sampling.py        — LLM-in-the-loop (P2-1)
  tools/             — 13 个 Tool handler + 注册表 (P3-2 元数据)
  prompts/           — 6 个 Prompt 模板 + 处理器 (P1-1)
  protocol.py        — list_tools + call_tool + audit/rate-limit 包装
  __init__.py        ← 你在这里: Server 创建 + entry point + 向下兼容

用法:
  python -m aitest.mcp                    # stdio transport (默认)
  python -m aitest.mcp --transport http   # HTTP transport (P3-1)
"""

import asyncio as _asyncio
import logging

logger = logging.getLogger(__name__)

# MCP Python SDK 是可选依赖：aitest.mcp.mcp_client（MCP client 侧，PH8-PR-8.5）
# 需要能在 SDK 缺失时降级导入 aitest.mcp 包下的模块。以前这里在包顶层无条件
# `from mcp.server import Server`，导致哪怕只是 `import aitest.mcp.mcp_client`
# 也会因为 aitest/mcp/__init__.py 先跑就 ImportError，client 侧自己的降级逻辑
# 根本没机会触发。因此这里改为 try/except，SDK 缺失时 Server 相关符号降级为 None，
# 只有真正调用 create_server()/run_stdio() 等 MCP Server 功能时才会报错。
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server

    from aitest.mcp.sampling import set_server as _set_sampling_server
    from aitest.mcp.protocol import build_list_tools_handler, build_call_tool_handler
    from aitest.mcp.prompts import build_list_prompts_handler, build_get_prompt_handler

    _MCP_SDK_AVAILABLE = True
except ImportError as _exc:
    logger.debug("MCP SDK not available — aitest.mcp server functionality disabled: %s", _exc)
    Server = None  # type: ignore[assignment,misc]
    stdio_server = None  # type: ignore[assignment]
    _set_sampling_server = None
    build_list_tools_handler = None
    build_call_tool_handler = None
    build_list_prompts_handler = None
    build_get_prompt_handler = None
    _MCP_SDK_AVAILABLE = False


def create_server() -> "Server":
    """工厂函数：创建并配置 MCP Server 实例。"""
    if not _MCP_SDK_AVAILABLE:
        raise RuntimeError(
            "MCP Python SDK not installed — cannot create MCP Server. "
            "Install with: pip install mcp"
        )
    server = Server("aitest-tools")

    # 注册协议处理器
    server.list_tools()(build_list_tools_handler())
    server.call_tool()(build_call_tool_handler())
    server.list_prompts()(build_list_prompts_handler())
    server.get_prompt()(build_get_prompt_handler())

    # P2-1: 设置 Sampling 所需的 Server 引用
    _set_sampling_server(server)

    return server


async def run_stdio():
    """stdio transport 入口。"""
    server = create_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


# P4-1 占位: HTTP transport + MCP Roots
async def run_http(host: str = "127.0.0.1", port: int = 9020):
    """P3-1: Streaming HTTP transport (experimental)。
    需要: pip install uvicorn starlette sse-starlette
    """
    try:
        from mcp.server.streaming_http import StreamingHttpServer
        import uvicorn
    except ImportError:
        logger.info("HTTP transport requires: pip install uvicorn starlette sse-starlette")
        logger.info("Falling back to stdio transport.")
        return await run_stdio()

    server = create_server()
    http_server = StreamingHttpServer(server)

    # P4-1: MCP Roots — 动态工作区发现
    # http_server.add_route("/roots", list_roots_handler)  # 后续实现

    config = uvicorn.Config(http_server.app, host=host, port=port, log_level="info")
    async with uvicorn.Server(config) as uvicorn_server:
        await uvicorn_server.serve()


async def main():
    """CLI 入口。"""
    import sys
    if "--transport" in sys.argv:
        idx = sys.argv.index("--transport")
        transport = sys.argv[idx + 1] if idx + 1 < len(sys.argv) else "stdio"
        if transport == "http":
            await run_http()
        else:
            await run_stdio()
    else:
        await run_stdio()


if __name__ == "__main__":
    _asyncio.run(main())
