-- Secret Manager 数据库迁移 (SQLite)
-- 创建时间: 2026-07-11
-- 相关任务: P6-5 Secret Manager

-- 创建 secrets 表
CREATE TABLE IF NOT EXISTS secrets (
    secret_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    encrypted_value TEXT NOT NULL,
    description TEXT DEFAULT '',
    tags TEXT DEFAULT '[]',
    org_id TEXT NOT NULL DEFAULT 'default-org',
    created_by TEXT NOT NULL DEFAULT 'admin',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    last_accessed_at TEXT,
    expires_at TEXT
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_secrets_type ON secrets(type);
CREATE INDEX IF NOT EXISTS idx_secrets_org_id ON secrets(org_id);
CREATE INDEX IF NOT EXISTS idx_secrets_org_type ON secrets(org_id, type);

-- 创建 secret_audit_logs 表
CREATE TABLE IF NOT EXISTS secret_audit_logs (
    log_id TEXT PRIMARY KEY,
    secret_id TEXT NOT NULL,
    action TEXT NOT NULL,
    actor TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    ip_address TEXT,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (secret_id) REFERENCES secrets(secret_id) ON DELETE CASCADE
);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_audit_secret_id ON secret_audit_logs(secret_id);
CREATE INDEX IF NOT EXISTS idx_audit_timestamp ON secret_audit_logs(timestamp);

-- 插入示例数据（占位，实际生产中由 aitest secrets init 创建）
-- INSERT INTO secrets (secret_id, name, type, encrypted_value, org_id, created_by, created_at, updated_at)
-- VALUES ('example-api-key', 'Example API Key', 'api_key', '<encrypted>', 'default-org', 'admin', datetime('now'), datetime('now'));
