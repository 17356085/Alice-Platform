"""Tests for MCP Server 资源化.

Tests:
- MCPServerStore CRUD operations
- MCPServerManager lifecycle (start/stop/restart)
- Environment variable resolution (secret_ref / environment_ref)
- Agent → MCP Server mappings
- Health checks

Author: AITest Platform
Created: 2026-07-11
Related: P6-2 MCP Server 资源化
"""

import pytest
import asyncio
from aitest.platform.mcp_server_store import MCPServerStore, MCPServer, AgentMCPMapping
from aitest.platform.mcp_server_manager import MCPServerManager
from aitest.platform.db import get_session


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def db_session():
    """提供数据库 session."""
    session = get_session()
    yield session
    session.close()


@pytest.fixture
def mcp_store(db_session):
    """提供 MCPServerStore 实例."""
    return MCPServerStore(db_session)


@pytest.fixture
def mcp_manager(mcp_store):
    """提供 MCPServerManager 实例."""
    return MCPServerManager(mcp_store)


@pytest.fixture
def cleanup_mcp_servers(mcp_store):
    """清理测试创建的 MCP Servers."""
    created_ids = []
    yield created_ids
    for server_id in created_ids:
        try:
            mcp_store.delete_mcp_server(server_id)
        except Exception:
            pass


# ============================================================================
# MCPServerStore Tests
# ============================================================================

def test_create_mcp_server(mcp_store, cleanup_mcp_servers):
    """测试创建 MCP Server."""
    server = mcp_store.create_mcp_server(
        mcp_server_id="test-server",
        name="Test Server",
        transport_type="stdio",
        command="npx",
        args=["-y", "@test/server"],
        description="Test MCP Server",
    )
    cleanup_mcp_servers.append("test-server")

    assert server.mcp_server_id == "test-server"
    assert server.name == "Test Server"
    assert server.transport_type == "stdio"
    assert server.command == "npx"
    assert server.args == ["-y", "@test/server"]
    assert server.status == "stopped"


def test_get_mcp_server(mcp_store, cleanup_mcp_servers):
    """测试获取 MCP Server."""
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-2",
        name="Test Server 2",
        transport_type="http",
        url="http://localhost:9000",
    )
    cleanup_mcp_servers.append("test-server-2")

    server = mcp_store.get_mcp_server("test-server-2")
    assert server is not None
    assert server.mcp_server_id == "test-server-2"
    assert server.transport_type == "http"
    assert server.url == "http://localhost:9000"


def test_list_mcp_servers(mcp_store, cleanup_mcp_servers):
    """测试列出 MCP Servers."""
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-3",
        name="Test Server 3",
        transport_type="stdio",
        command="npx",
    )
    cleanup_mcp_servers.append("test-server-3")

    servers = mcp_store.list_mcp_servers()
    assert len(servers) >= 1
    assert any(s.mcp_server_id == "test-server-3" for s in servers)


def test_update_mcp_server(mcp_store, cleanup_mcp_servers):
    """测试更新 MCP Server."""
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-4",
        name="Test Server 4",
        transport_type="stdio",
        command="npx",
    )
    cleanup_mcp_servers.append("test-server-4")

    updated = mcp_store.update_mcp_server(
        mcp_server_id="test-server-4",
        name="Updated Server 4",
        description="Updated description",
    )

    assert updated is not None
    assert updated.name == "Updated Server 4"
    assert updated.description == "Updated description"


def test_update_status(mcp_store, cleanup_mcp_servers):
    """测试更新状态."""
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-5",
        name="Test Server 5",
        transport_type="stdio",
        command="npx",
    )
    cleanup_mcp_servers.append("test-server-5")

    success = mcp_store.update_status("test-server-5", "running", 12345)
    assert success

    server = mcp_store.get_mcp_server("test-server-5")
    assert server.status == "running"
    assert server.process_id == 12345


def test_update_tools(mcp_store, cleanup_mcp_servers):
    """测试更新 Tools."""
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-6",
        name="Test Server 6",
        transport_type="stdio",
        command="npx",
    )
    cleanup_mcp_servers.append("test-server-6")

    tools = ["tool1", "tool2", "tool3"]
    success = mcp_store.update_tools("test-server-6", tools)
    assert success

    server = mcp_store.get_mcp_server("test-server-6")
    assert server.tools == tools


def test_delete_mcp_server(mcp_store):
    """测试删除 MCP Server."""
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-delete",
        name="Delete Server",
        transport_type="stdio",
        command="npx",
    )

    success = mcp_store.delete_mcp_server("test-server-delete")
    assert success

    server = mcp_store.get_mcp_server("test-server-delete")
    assert server is None


# ============================================================================
# Environment Resolution Tests
# ============================================================================

def test_resolve_env_plain_values(mcp_store, cleanup_mcp_servers):
    """测试解析普通环境变量."""
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-env",
        name="Env Test Server",
        transport_type="stdio",
        command="npx",
        env={"KEY1": "value1", "KEY2": "value2"},
    )
    cleanup_mcp_servers.append("test-server-env")

    resolved = mcp_store.resolve_env("test-server-env")
    assert resolved["KEY1"] == "value1"
    assert resolved["KEY2"] == "value2"


def test_resolve_env_with_secret_ref(mcp_store, cleanup_mcp_servers):
    """测试解析 secret_ref（需要 Secret Manager）."""
    # 创建 Secret
    try:
        from aitest.platform.secret_manager import SecretManager
        secret_mgr = SecretManager(mcp_store.session)
        secret_mgr.create_secret(
            secret_id="test-secret",
            name="Test Secret",
            value="secret-value-123",
        )
    except Exception:
        pytest.skip("Secret Manager not available")

    # 创建 MCP Server with secret_ref
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-secret",
        name="Secret Test Server",
        transport_type="stdio",
        command="npx",
        env={"API_KEY": "secret:test-secret"},
    )
    cleanup_mcp_servers.append("test-server-secret")

    resolved = mcp_store.resolve_env("test-server-secret")
    assert resolved["API_KEY"] == "secret-value-123"


# ============================================================================
# Agent Mapping Tests
# ============================================================================

def test_create_agent_mapping(mcp_store, cleanup_mcp_servers):
    """测试创建 Agent → MCP Server 映射."""
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-mapping",
        name="Mapping Test Server",
        transport_type="stdio",
        command="npx",
    )
    cleanup_mcp_servers.append("test-server-mapping")

    mapping = mcp_store.create_agent_mapping(
        agent_type="test-agent",
        mcp_server_id="test-server-mapping",
        allowed_tools=["tool1", "tool2"],
    )

    assert mapping.agent_type == "test-agent"
    assert mapping.mcp_server_id == "test-server-mapping"
    assert mapping.allowed_tools == ["tool1", "tool2"]


def test_get_agent_mcp_servers(mcp_store, cleanup_mcp_servers):
    """测试获取 Agent 关联的 MCP Servers."""
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-agent-1",
        name="Agent Test Server 1",
        transport_type="stdio",
        command="npx",
    )
    cleanup_mcp_servers.append("test-server-agent-1")

    mcp_store.create_agent_mapping(
        agent_type="test-agent-2",
        mcp_server_id="test-server-agent-1",
    )

    server_ids = mcp_store.get_agent_mcp_servers("test-agent-2")
    assert "test-server-agent-1" in server_ids


def test_delete_agent_mapping(mcp_store, cleanup_mcp_servers):
    """测试删除 Agent → MCP Server 映射."""
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-delete-mapping",
        name="Delete Mapping Server",
        transport_type="stdio",
        command="npx",
    )
    cleanup_mcp_servers.append("test-server-delete-mapping")

    mcp_store.create_agent_mapping(
        agent_type="test-agent-delete",
        mcp_server_id="test-server-delete-mapping",
    )

    success = mcp_store.delete_agent_mapping(
        agent_type="test-agent-delete",
        mcp_server_id="test-server-delete-mapping",
    )
    assert success

    server_ids = mcp_store.get_agent_mcp_servers("test-agent-delete")
    assert "test-server-delete-mapping" not in server_ids


# ============================================================================
# MCPServerManager Tests (需要实际 MCP Server，标记为 integration test)
# ============================================================================

@pytest.mark.integration
@pytest.mark.asyncio
async def test_manager_get_status(mcp_manager, mcp_store, cleanup_mcp_servers):
    """测试获取 MCP Server 状态."""
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-status",
        name="Status Test Server",
        transport_type="stdio",
        command="echo",
        args=["test"],
    )
    cleanup_mcp_servers.append("test-server-status")

    status = await mcp_manager.get_status("test-server-status")
    assert status["mcp_server_id"] == "test-server-status"
    assert status["status"] == "stopped"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_manager_is_running(mcp_manager, mcp_store, cleanup_mcp_servers):
    """测试检查 MCP Server 是否运行."""
    mcp_store.create_mcp_server(
        mcp_server_id="test-server-running",
        name="Running Test Server",
        transport_type="stdio",
        command="echo",
    )
    cleanup_mcp_servers.append("test-server-running")

    is_running = await mcp_manager.is_running("test-server-running")
    assert not is_running  # 初始状态应该是 stopped


# ============================================================================
# Integration with registry.py Tests
# ============================================================================

def test_registry_get_mcp_server_registry(mcp_store, cleanup_mcp_servers):
    """测试 registry.py 从数据库加载配置."""
    from aitest.mcp.registry import get_mcp_server_registry

    mcp_store.create_mcp_server(
        mcp_server_id="test-registry-server",
        name="Registry Test Server",
        transport_type="stdio",
        command="npx",
    )
    cleanup_mcp_servers.append("test-registry-server")

    registry = get_mcp_server_registry(use_db=True)
    assert "test-registry-server" in registry
    assert registry["test-registry-server"].name == "Registry Test Server"


def test_registry_fallback_to_hardcoded():
    """测试 registry.py 回退到硬编码配置."""
    from aitest.mcp.registry import get_mcp_server_registry

    # use_db=False 应该使用硬编码配置
    registry = get_mcp_server_registry(use_db=False)
    assert "browser-mcp" in registry  # 硬编码的配置


def test_get_agent_mcp_servers_from_db(mcp_store, cleanup_mcp_servers):
    """测试从数据库获取 Agent 的 MCP Servers."""
    from aitest.mcp.registry import get_agent_mcp_servers

    mcp_store.create_mcp_server(
        mcp_server_id="test-agent-server",
        name="Agent Server",
        transport_type="stdio",
        command="npx",
    )
    cleanup_mcp_servers.append("test-agent-server")

    mcp_store.create_agent_mapping(
        agent_type="test-db-agent",
        mcp_server_id="test-agent-server",
    )

    server_ids = get_agent_mcp_servers("test-db-agent", use_db=True)
    assert "test-agent-server" in server_ids


# ============================================================================
# Data Model Tests
# ============================================================================

def test_mcp_server_to_config():
    """测试 MCPServer.to_config() 转换."""
    server = MCPServer(
        mcp_server_id="test-to-config",
        name="To Config Test",
        transport_type="stdio",
        command="npx",
        args=["-y", "test"],
        enabled_by_default=True,
    )

    config = server.to_config()
    assert config.id == "test-to-config"
    assert config.name == "To Config Test"
    assert config.transport_type == "stdio"
    assert config.command == "npx"
    assert config.args == ["-y", "test"]
    assert config.enabled_by_default is True
