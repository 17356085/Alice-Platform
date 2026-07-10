-- Migration: 017_mcp_servers
-- Description: MCP Server 资源化 - 动态管理 MCP Server 配置和进程
-- Created: 2026-07-11
-- Related: P6-2 MCP Server 资源化

-- ============================================================================
-- PostgreSQL Version
-- ============================================================================

CREATE TABLE IF NOT EXISTS mcp_servers (
    mcp_server_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    transport_type TEXT NOT NULL,              -- "stdio" | "http"
    command TEXT DEFAULT '',                    -- stdio: 启动命令 (如 "npx")
    args TEXT DEFAULT '[]',                     -- stdio: 命令参数 (JSON 数组)
    url TEXT DEFAULT '',                        -- http: MCP Server URL
    env TEXT DEFAULT '{}',                      -- 环境变量 (JSON 对象，支持 secret_ref / environment_ref)
    tools TEXT DEFAULT '[]',                    -- 暴露的 Tools (JSON 数组，从 MCP Server 动态获取)
    status TEXT DEFAULT 'stopped',              -- "stopped" | "starting" | "running" | "error"
    process_id INTEGER DEFAULT NULL,            -- 进程 ID (stdio 类型)
    enabled_by_default BOOLEAN DEFAULT FALSE,   -- 是否默认启用
    org_id TEXT NOT NULL DEFAULT 'default-org',
    created_by TEXT NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_health_check TIMESTAMP DEFAULT NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_mcp_servers_org_id ON mcp_servers(org_id);
CREATE INDEX IF NOT EXISTS idx_mcp_servers_status ON mcp_servers(status);

-- Agent → MCP Server 映射表
CREATE TABLE IF NOT EXISTS agent_mcp_mappings (
    id SERIAL PRIMARY KEY,
    agent_type TEXT NOT NULL,                   -- Agent 类型 (如 "qa_reviewer")
    mcp_server_id TEXT NOT NULL,                -- MCP Server ID
    allowed_tools TEXT DEFAULT '[]',            -- 允许的 Tools (JSON 数组，空表示全部允许)
    org_id TEXT NOT NULL DEFAULT 'default-org',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(agent_type, mcp_server_id, org_id),
    FOREIGN KEY (mcp_server_id) REFERENCES mcp_servers(mcp_server_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agent_mcp_agent_type ON agent_mcp_mappings(agent_type);
CREATE INDEX IF NOT EXISTS idx_agent_mcp_server_id ON agent_mcp_mappings(mcp_server_id);

-- ============================================================================
-- SQLite Version (与 PostgreSQL 版本相同，但使用 INTEGER PRIMARY KEY AUTOINCREMENT)
-- ============================================================================

-- SQLite 版本将在单独的文件中提供，保持与 PostgreSQL 版本的一致性
