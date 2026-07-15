"""MCP Server Store — 数据库 CRUD 操作.

提供 MCP Server 的创建、查询、更新、删除操作，以及环境变量解析。

Author: AITest Platform
Created: 2026-07-11
Moved: 2026-07-14 (从 platform.mcp_server_store 移到 mcp.database，消除循环依赖)
Related: P6-2 MCP Server 资源化, Step 1.1b 循环依赖拆分
"""

import json
import logging
from datetime import datetime
from collections.abc import Callable
from typing import Optional

from aitest.mcp.types import MCPServer, AgentMCPMapping
from aitest.infra.db_session import get_session

logger = logging.getLogger(__name__)

_secret_resolver: Callable | None = None
_environment_resolver: Callable | None = None


def register_env_resolvers(
    secret_resolver: Callable | None = None,
    environment_resolver: Callable | None = None,
) -> None:
    """Register platform-backed secret/environment resolvers."""
    global _secret_resolver, _environment_resolver
    _secret_resolver = secret_resolver
    _environment_resolver = environment_resolver


# ============================================================================
# Store
# ============================================================================

class MCPServerStore:
    """MCP Server CRUD 操作."""

    def __init__(self, session=None):
        """初始化 Store.

        Args:
            session: 数据库 session，如果为 None 则自动获取
        """
        self._owns_session = session is None
        self.session = session or get_session()

    def close(self) -> None:
        """Close an internally-created DB connection; leave injected sessions alone."""
        if self._owns_session and self.session is not None:
            self.session.close()
            self.session = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()
        return False

    # ── Create ──────────────────────────────────────────────────────────────

    def create_mcp_server(
        self,
        mcp_server_id: str,
        name: str,
        transport_type: str,
        command: str = "",
        args: list[str] | None = None,
        url: str = "",
        env: dict[str, str] | None = None,
        description: str = "",
        enabled_by_default: bool = False,
        org_id: str = "default-org",
        created_by: str = "admin",
    ) -> MCPServer:
        """创建 MCP Server (不启动进程).

        Args:
            mcp_server_id: 唯一标识
            name: 显示名称
            transport_type: "stdio" | "http"
            command: stdio 启动命令
            args: stdio 命令参数
            url: http URL
            env: 环境变量 (可包含 secret_ref / environment_ref)
            description: 描述
            enabled_by_default: 是否默认启用
            org_id: 组织 ID
            created_by: 创建者

        Returns:
            创建的 MCPServer 对象
        """
        now = datetime.utcnow().isoformat()
        args_json = json.dumps(args or [])
        env_json = json.dumps(env or {})

        query = """
            INSERT INTO mcp_servers (
                mcp_server_id, name, description, transport_type,
                command, args, url, env, status, enabled_by_default,
                org_id, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        self.session.execute(
            query,
            (
                mcp_server_id, name, description, transport_type,
                command, args_json, url, env_json, "stopped",
                1 if enabled_by_default else 0,
                org_id, created_by, now, now,
            ),
        )
        self.session.commit()

        logger.info(f"MCP Server created: {mcp_server_id}")

        return self.get_mcp_server(mcp_server_id)

    # ── Read ────────────────────────────────────────────────────────────────

    def get_mcp_server(self, mcp_server_id: str) -> Optional[MCPServer]:
        """获取 MCP Server.

        Args:
            mcp_server_id: MCP Server ID

        Returns:
            MCPServer 对象，如果不存在返回 None
        """
        query = "SELECT * FROM mcp_servers WHERE mcp_server_id = ?"
        result = self.session.execute(query, (mcp_server_id,)).fetchone()

        if not result:
            return None

        return self._row_to_mcp_server(result)

    def list_mcp_servers(
        self,
        org_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> list[MCPServer]:
        """列出 MCP Servers.

        Args:
            org_id: 组织 ID 过滤
            status: 状态过滤 ("stopped" | "starting" | "running" | "error")

        Returns:
            MCPServer 列表
        """
        query = "SELECT * FROM mcp_servers WHERE 1=1"
        params = []

        if org_id:
            query += " AND org_id = ?"
            params.append(org_id)

        if status:
            query += " AND status = ?"
            params.append(status)

        query += " ORDER BY created_at DESC"

        results = self.session.execute(query, tuple(params)).fetchall()
        return [self._row_to_mcp_server(row) for row in results]

    # ── Update ──────────────────────────────────────────────────────────────

    def update_mcp_server(
        self,
        mcp_server_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        command: Optional[str] = None,
        args: Optional[list[str]] = None,
        url: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
        enabled_by_default: Optional[bool] = None,
    ) -> Optional[MCPServer]:
        """更新 MCP Server.

        Args:
            mcp_server_id: MCP Server ID
            name: 新名称
            description: 新描述
            command: 新命令
            args: 新参数
            url: 新 URL
            env: 新环境变量
            enabled_by_default: 是否默认启用

        Returns:
            更新后的 MCPServer，如果不存在返回 None
        """
        server = self.get_mcp_server(mcp_server_id)
        if not server:
            return None

        updates = []
        params = []

        if name is not None:
            updates.append("name = ?")
            params.append(name)

        if description is not None:
            updates.append("description = ?")
            params.append(description)

        if command is not None:
            updates.append("command = ?")
            params.append(command)

        if args is not None:
            updates.append("args = ?")
            params.append(json.dumps(args))

        if url is not None:
            updates.append("url = ?")
            params.append(url)

        if env is not None:
            updates.append("env = ?")
            params.append(json.dumps(env))

        if enabled_by_default is not None:
            updates.append("enabled_by_default = ?")
            params.append(1 if enabled_by_default else 0)

        if not updates:
            return server

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(mcp_server_id)

        query = f"UPDATE mcp_servers SET {', '.join(updates)} WHERE mcp_server_id = ?"
        self.session.execute(query, tuple(params))
        self.session.commit()

        logger.info(f"MCP Server updated: {mcp_server_id}")

        return self.get_mcp_server(mcp_server_id)

    def update_status(
        self,
        mcp_server_id: str,
        status: str,
        process_id: Optional[int] = None,
    ) -> bool:
        """更新状态.

        Args:
            mcp_server_id: MCP Server ID
            status: 新状态
            process_id: 进程 ID

        Returns:
            是否成功
        """
        query = """
            UPDATE mcp_servers
            SET status = ?, process_id = ?, updated_at = ?
            WHERE mcp_server_id = ?
        """

        self.session.execute(
            query,
            (status, process_id, datetime.utcnow().isoformat(), mcp_server_id),
        )
        self.session.commit()

        return True

    def update_tools(self, mcp_server_id: str, tools: list[str]) -> bool:
        """更新 Tools 列表.

        Args:
            mcp_server_id: MCP Server ID
            tools: Tools 列表

        Returns:
            是否成功
        """
        query = """
            UPDATE mcp_servers
            SET tools = ?, updated_at = ?
            WHERE mcp_server_id = ?
        """

        self.session.execute(
            query,
            (json.dumps(tools), datetime.utcnow().isoformat(), mcp_server_id),
        )
        self.session.commit()

        return True

    def update_last_health_check(self, mcp_server_id: str) -> bool:
        """更新最后健康检查时间.

        Args:
            mcp_server_id: MCP Server ID

        Returns:
            是否成功
        """
        query = """
            UPDATE mcp_servers
            SET last_health_check = ?
            WHERE mcp_server_id = ?
        """

        self.session.execute(
            query,
            (datetime.utcnow().isoformat(), mcp_server_id),
        )
        self.session.commit()

        return True

    # ── Delete ──────────────────────────────────────────────────────────────

    def delete_mcp_server(self, mcp_server_id: str) -> bool:
        """删除 MCP Server.

        注意: 删除前应先停止进程

        Args:
            mcp_server_id: MCP Server ID

        Returns:
            是否成功
        """
        query = "DELETE FROM mcp_servers WHERE mcp_server_id = ?"
        self.session.execute(query, (mcp_server_id,))
        self.session.commit()

        logger.info(f"MCP Server deleted: {mcp_server_id}")

        return True

    # ── Environment Resolution ──────────────────────────────────────────────

    def resolve_env(self, mcp_server_id: str) -> dict[str, str]:
        """解析环境变量 (自动解析 secret_ref / environment_ref).

        支持以下引用格式:
        - "secret:<secret_id>" → 从 Secret Manager 获取
        - "environment:<var_name>" → 从当前 Environment 获取

        Args:
            mcp_server_id: MCP Server ID

        Returns:
            解析后的环境变量字典
        """
        server = self.get_mcp_server(mcp_server_id)
        if not server:
            return {}

        resolved = {}

        for key, value in server.env.items():
            if value.startswith("secret:"):
                # 解析 Secret
                secret_id = value[7:]  # 去掉 "secret:" 前缀
                resolved[key] = self._resolve_secret_ref(secret_id)
            elif value.startswith("environment:"):
                # 解析 Environment 变量
                var_name = value[12:]  # 去掉 "environment:" 前缀
                resolved[key] = self._resolve_environment_ref(var_name)
            else:
                resolved[key] = value

        return resolved

    def _resolve_secret_ref(self, secret_id: str) -> str:
        """解析 Secret 引用.

        Args:
            secret_id: Secret ID

        Returns:
            Secret 值，如果不存在返回空字符串
        """
        try:
            if _secret_resolver is not None:
                return _secret_resolver(self.session, secret_id) or ""
        except Exception as e:
            logger.warning(f"Failed to resolve secret {secret_id}: {e}")

        return ""

    def _resolve_environment_ref(self, var_name: str) -> str:
        """解析 Environment 变量引用.

        Args:
            var_name: 变量名

        Returns:
            变量值，如果不存在返回空字符串
        """
        try:
            if _environment_resolver is not None:
                return _environment_resolver(self.session, var_name) or ""
        except Exception as e:
            logger.warning(f"Failed to resolve environment variable {var_name}: {e}")

        return ""

    # ── Agent Mapping ───────────────────────────────────────────────────────

    def create_agent_mapping(
        self,
        agent_type: str,
        mcp_server_id: str,
        allowed_tools: list[str] | None = None,
        org_id: str = "default-org",
    ) -> AgentMCPMapping:
        """创建 Agent → MCP Server 映射.

        Args:
            agent_type: Agent 类型
            mcp_server_id: MCP Server ID
            allowed_tools: 允许的 Tools (空表示全部允许)
            org_id: 组织 ID

        Returns:
            AgentMCPMapping 对象
        """
        now = datetime.utcnow().isoformat()
        tools_json = json.dumps(allowed_tools or [])

        query = """
            INSERT INTO agent_mcp_mappings (
                agent_type, mcp_server_id, allowed_tools, org_id, created_at
            ) VALUES (?, ?, ?, ?, ?)
        """

        self.session.execute(
            query,
            (agent_type, mcp_server_id, tools_json, org_id, now),
        )
        self.session.commit()

        logger.info(f"Agent mapping created: {agent_type} → {mcp_server_id}")

        return AgentMCPMapping(
            agent_type=agent_type,
            mcp_server_id=mcp_server_id,
            allowed_tools=allowed_tools or [],
            org_id=org_id,
            created_at=now,
        )

    def get_agent_mcp_servers(self, agent_type: str) -> list[str]:
        """获取 Agent 关联的 MCP Server IDs.

        Args:
            agent_type: Agent 类型

        Returns:
            MCP Server ID 列表
        """
        query = """
            SELECT mcp_server_id FROM agent_mcp_mappings
            WHERE agent_type = ?
        """

        results = self.session.execute(query, (agent_type,)).fetchall()
        return [row[0] for row in results]

    def delete_agent_mapping(
        self,
        agent_type: str,
        mcp_server_id: str,
    ) -> bool:
        """删除 Agent → MCP Server 映射.

        Args:
            agent_type: Agent 类型
            mcp_server_id: MCP Server ID

        Returns:
            是否成功
        """
        query = """
            DELETE FROM agent_mcp_mappings
            WHERE agent_type = ? AND mcp_server_id = ?
        """

        self.session.execute(query, (agent_type, mcp_server_id))
        self.session.commit()

        return True

    # ── Helper ──────────────────────────────────────────────────────────────

    def _row_to_mcp_server(self, row) -> MCPServer:
        """将数据库行转换为 MCPServer 对象."""
        return MCPServer(
            mcp_server_id=row[0],
            name=row[1],
            description=row[2],
            transport_type=row[3],
            command=row[4],
            args=json.loads(row[5]) if row[5] else [],
            url=row[6],
            env=json.loads(row[7]) if row[7] else {},
            tools=json.loads(row[8]) if row[8] else [],
            status=row[9],
            process_id=row[10],
            enabled_by_default=bool(row[11]),
            org_id=row[12],
            created_by=row[13],
            created_at=row[14],
            updated_at=row[15],
            last_health_check=row[16],
        )
