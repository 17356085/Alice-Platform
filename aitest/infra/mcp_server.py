"""
MCP Server: aitest-tools  (向下兼容)
═══════════════════════════════════════════════════════════
P3-0: 主逻辑已迁移至 aitest/mcp/ 包。此文件保留作为向下兼容入口。

用法维持不变:
  python -m aitest.infra.mcp_server          # stdio transport
  python -m aitest.mcp                 # 新入口（推荐）
  python -m aitest.mcp --transport http # HTTP transport (experimental)
"""
from aitest.mcp import main

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
