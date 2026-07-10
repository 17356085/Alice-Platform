"""MCP Server Manager — 进程管理和生命周期控制.

提供 MCP Server 的启动、停止、重启、健康检查等功能。

Author: AITest Platform
Created: 2026-07-11
Related: P6-2 MCP Server 资源化
"""

import asyncio
import logging
import subprocess
from typing import Optional

from aitest.mcp.mcp_client import create_mcp_client, McpClientResult
from aitest.platform.mcp_server_store import MCPServerStore, MCPServer

logger = logging.getLogger(__name__)


# ============================================================================
# MCP Server Manager
# ============================================================================

class MCPServerManager:
    """MCP Server 进程管理器."""

    def __init__(self, store: Optional[MCPServerStore] = None):
        """初始化 Manager.

        Args:
            store: MCPServerStore 实例，如果为 None 则自动创建
        """
        self.store = store or MCPServerStore()
        self.processes: dict[str, subprocess.Popen] = {}
        self.clients: dict[str, McpClientResult] = {}
        self.failure_counts: dict[str, int] = {}

    # ── Start / Stop ────────────────────────────────────────────────────────

    async def start_server(self, mcp_server_id: str) -> bool:
        """启动 MCP Server.

        流程:
        1. 更新状态为 "starting"
        2. 解析环境变量 (secret_ref / environment_ref)
        3. 启动进程 (stdio) 或连接 URL (http)
        4. 健康检查 (调用 list_tools 验证)
        5. 更新状态和 process_id

        Args:
            mcp_server_id: MCP Server ID

        Returns:
            是否成功
        """
        server = self.store.get_mcp_server(mcp_server_id)
        if not server:
            logger.error(f"MCP Server not found: {mcp_server_id}")
            return False

        if server.status == "running":
            logger.info(f"MCP Server already running: {mcp_server_id}")
            return True

        try:
            # 1. 更新状态
            self.store.update_status(mcp_server_id, "starting")

            # 2. 解析环境变量
            resolved_env = self.store.resolve_env(mcp_server_id)

            # 3. 创建 MCP 客户端（内部会启动进程）
            config = server.to_config()
            config.env = resolved_env  # 使用解析后的环境变量
            client = await create_mcp_client(config)

            if not client.tools:
                logger.warning(f"MCP Server started but no tools available: {mcp_server_id}")
                self.store.update_status(mcp_server_id, "error")
                return False

            # 4. 保存客户端和进程信息
            self.clients[mcp_server_id] = client

            # 如果是 stdio，尝试获取进程 ID
            process_id = None
            if server.transport_type == "stdio" and mcp_server_id in self.processes:
                process_id = self.processes[mcp_server_id].pid

            # 5. 更新状态和 Tools
            self.store.update_status(mcp_server_id, "running", process_id)
            tools = list(client.tools.keys())
            self.store.update_tools(mcp_server_id, tools)
            self.store.update_last_health_check(mcp_server_id)

            # 重置失败计数
            self.failure_counts[mcp_server_id] = 0

            logger.info(f"MCP Server started: {mcp_server_id} ({len(tools)} tools)")
            return True

        except Exception as e:
            logger.error(f"Failed to start MCP Server {mcp_server_id}: {e}")
            self.store.update_status(mcp_server_id, "error")
            return False

    async def stop_server(self, mcp_server_id: str) -> bool:
        """停止 MCP Server.

        流程:
        1. 关闭 MCP 客户端连接
        2. 终止进程 (stdio)
        3. 更新状态为 "stopped"

        Args:
            mcp_server_id: MCP Server ID

        Returns:
            是否成功
        """
        server = self.store.get_mcp_server(mcp_server_id)
        if not server:
            logger.error(f"MCP Server not found: {mcp_server_id}")
            return False

        if server.status == "stopped":
            logger.info(f"MCP Server already stopped: {mcp_server_id}")
            return True

        try:
            # 1. 关闭 MCP 客户端
            if mcp_server_id in self.clients:
                client = self.clients[mcp_server_id]
                try:
                    await client.close()
                except Exception as e:
                    logger.warning(f"Error closing MCP client {mcp_server_id}: {e}")
                del self.clients[mcp_server_id]

            # 2. 终止进程
            if mcp_server_id in self.processes:
                process = self.processes[mcp_server_id]
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except Exception as e:
                    logger.warning(f"Error terminating process for {mcp_server_id}: {e}")
                    try:
                        process.kill()
                    except Exception:
                        pass
                del self.processes[mcp_server_id]

            # 3. 更新状态
            self.store.update_status(mcp_server_id, "stopped", None)

            logger.info(f"MCP Server stopped: {mcp_server_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to stop MCP Server {mcp_server_id}: {e}")
            return False

    async def restart_server(self, mcp_server_id: str) -> bool:
        """重启 MCP Server.

        Args:
            mcp_server_id: MCP Server ID

        Returns:
            是否成功
        """
        logger.info(f"Restarting MCP Server: {mcp_server_id}")
        await self.stop_server(mcp_server_id)
        await asyncio.sleep(1)  # 等待进程完全关闭
        return await self.start_server(mcp_server_id)

    # ── Status ──────────────────────────────────────────────────────────────

    async def get_status(self, mcp_server_id: str) -> dict:
        """获取 MCP Server 状态.

        Returns:
            {
                "mcp_server_id": "...",
                "status": "running",
                "process_id": 12345,
                "tools": ["tool1", "tool2"],
                "last_health_check": "2026-07-11T15:00:00Z",
                "uptime_seconds": 1800
            }

        Args:
            mcp_server_id: MCP Server ID

        Returns:
            状态字典
        """
        server = self.store.get_mcp_server(mcp_server_id)
        if not server:
            return {"error": "MCP Server not found"}

        result = {
            "mcp_server_id": server.mcp_server_id,
            "status": server.status,
            "process_id": server.process_id,
            "tools": server.tools,
            "last_health_check": server.last_health_check,
        }

        # 计算运行时间
        if server.status == "running" and server.updated_at:
            try:
                from datetime import datetime
                updated = datetime.fromisoformat(server.updated_at)
                now = datetime.utcnow()
                uptime = (now - updated).total_seconds()
                result["uptime_seconds"] = int(uptime)
            except Exception:
                pass

        return result

    async def is_running(self, mcp_server_id: str) -> bool:
        """检查 MCP Server 是否运行中.

        Args:
            mcp_server_id: MCP Server ID

        Returns:
            是否运行中
        """
        server = self.store.get_mcp_server(mcp_server_id)
        return server is not None and server.status == "running"

    # ── Health Check ────────────────────────────────────────────────────────

    async def health_check(self, mcp_server_id: str) -> bool:
        """健康检查.

        调用 MCP Server 的 list_tools 验证连接。
        如果失败，标记为 "error"，连续 3 次失败则自动重启。

        Args:
            mcp_server_id: MCP Server ID

        Returns:
            是否健康
        """
        server = self.store.get_mcp_server(mcp_server_id)
        if not server or server.status != "running":
            return False

        try:
            # 调用 list_tools 验证连接
            tools = await self.list_tools(mcp_server_id)

            if tools:
                # 健康检查通过
                self.store.update_last_health_check(mcp_server_id)
                self.failure_counts[mcp_server_id] = 0
                return True
            else:
                # 无法获取 Tools
                raise Exception("No tools available")

        except Exception as e:
            logger.warning(f"Health check failed for {mcp_server_id}: {e}")

            # 增加失败计数
            self.failure_counts[mcp_server_id] = self.failure_counts.get(mcp_server_id, 0) + 1

            # 连续 3 次失败，自动重启
            if self.failure_counts[mcp_server_id] >= 3:
                logger.error(f"MCP Server {mcp_server_id} failed 3 times, restarting...")
                await self.restart_server(mcp_server_id)

            # 标记为 error
            self.store.update_status(mcp_server_id, "error")
            return False

    async def list_tools(self, mcp_server_id: str) -> list[str]:
        """列出 MCP Server 暴露的 Tools.

        Args:
            mcp_server_id: MCP Server ID

        Returns:
            Tool 名称列表
        """
        if mcp_server_id not in self.clients:
            return []

        client = self.clients[mcp_server_id]
        return list(client.tools.keys())

    async def call_tool(
        self,
        mcp_server_id: str,
        tool_name: str,
        arguments: dict | None = None,
    ) -> dict:
        """调用 MCP Server Tool.

        Args:
            mcp_server_id: MCP Server ID
            tool_name: Tool 名称
            arguments: Tool 参数

        Returns:
            Tool 执行结果
        """
        if mcp_server_id not in self.clients:
            return {
                "success": False,
                "error": f"MCP Server not connected: {mcp_server_id}",
            }

        client = self.clients[mcp_server_id]
        if not client.call_tool:
            return {
                "success": False,
                "error": f"MCP Server {mcp_server_id} does not support tool calls",
            }

        try:
            result = await client.call_tool(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Tool call failed: {mcp_server_id}.{tool_name}: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    # ── Batch Operations ────────────────────────────────────────────────────

    async def start_all(self, org_id: str = "default-org") -> dict[str, bool]:
        """启动所有已启用的 MCP Servers.

        Args:
            org_id: 组织 ID

        Returns:
            {mcp_server_id: success}
        """
        servers = self.store.list_mcp_servers(org_id=org_id)
        results = {}

        for server in servers:
            if server.enabled_by_default and server.status != "running":
                success = await self.start_server(server.mcp_server_id)
                results[server.mcp_server_id] = success

        return results

    async def stop_all(self, org_id: str = "default-org") -> dict[str, bool]:
        """停止所有运行中的 MCP Servers.

        Args:
            org_id: 组织 ID

        Returns:
            {mcp_server_id: success}
        """
        servers = self.store.list_mcp_servers(org_id=org_id, status="running")
        results = {}

        for server in servers:
            success = await self.stop_server(server.mcp_server_id)
            results[server.mcp_server_id] = success

        return results

    async def health_check_all(self, org_id: str = "default-org") -> dict[str, bool]:
        """对所有运行中的 MCP Servers 进行健康检查.

        Args:
            org_id: 组织 ID

        Returns:
            {mcp_server_id: is_healthy}
        """
        servers = self.store.list_mcp_servers(org_id=org_id, status="running")
        results = {}

        for server in servers:
            is_healthy = await self.health_check(server.mcp_server_id)
            results[server.mcp_server_id] = is_healthy

        return results


# ============================================================================
# Background Health Check Loop
# ============================================================================

async def health_check_loop(
    manager: MCPServerManager,
    interval_seconds: int = 60,
    org_id: str = "default-org",
):
    """后台任务：定期健康检查所有 running 状态的 MCP Servers.

    Args:
        manager: MCPServerManager 实例
        interval_seconds: 检查间隔（秒）
        org_id: 组织 ID
    """
    logger.info(f"Starting MCP Server health check loop (interval: {interval_seconds}s)")

    while True:
        try:
            results = await manager.health_check_all(org_id=org_id)

            healthy = sum(1 for v in results.values() if v)
            total = len(results)

            if total > 0:
                logger.info(f"Health check completed: {healthy}/{total} servers healthy")

        except Exception as e:
            logger.error(f"Health check loop error: {e}")

        await asyncio.sleep(interval_seconds)


# ============================================================================
# Helper Functions
# ============================================================================

def get_mcp_server_manager() -> MCPServerManager:
    """获取全局 MCPServerManager 实例（单例模式）."""
    global _manager_instance
    if "_manager_instance" not in globals():
        _manager_instance = MCPServerManager()
    return _manager_instance
