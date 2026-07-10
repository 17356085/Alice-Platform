-- Environment 数据库迁移 (SQLite)
-- 创建时间: 2026-07-11
-- 相关任务: P6-4 Environment 资源化

-- 创建 environments 表
CREATE TABLE IF NOT EXISTS environments (
    environment_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    base_url TEXT NOT NULL,
    description TEXT DEFAULT '',
    variables TEXT DEFAULT '{}',
    tags TEXT DEFAULT '[]',
    org_id TEXT NOT NULL DEFAULT 'default-org',
    created_by TEXT NOT NULL DEFAULT 'admin',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    is_default INTEGER DEFAULT 0
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_environments_org_id ON environments(org_id);
CREATE INDEX IF NOT EXISTS idx_environments_is_default ON environments(is_default);
CREATE INDEX IF NOT EXISTS idx_environments_org_default ON environments(org_id, is_default);

-- 插入示例数据（可选）
-- INSERT INTO environments (environment_id, name, base_url, org_id, created_by, created_at, updated_at, is_default)
-- VALUES ('default', 'Default Environment', 'https://example.com', 'default-org', 'system', datetime('now'), datetime('now'), 1);
