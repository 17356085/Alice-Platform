"""MCP Store — MCP 层访问数据库的接口层.

提供 MCP 模块访问 MCPServerStore 的桥接，避免直接依赖 platform 层。

Author: AITest Platform
Created: 2026-07-14
Related: 循环依赖拆分 Step 1
"""

from typing import Optional


def get_mcp_server_store():
    """获取 MCPServerStore 实例（延迟导入避免循环依赖）.

    Returns:
        MCPServerStore 实例
    """
    from aitest.mcp.database import MCPServerStore
    return MCPServerStore()
