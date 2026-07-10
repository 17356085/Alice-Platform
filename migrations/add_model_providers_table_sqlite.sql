-- ModelProvider 表迁移 (P6-1)
-- 数据库: SQLite

CREATE TABLE IF NOT EXISTS model_providers (
    provider_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    config TEXT NOT NULL,  -- JSON (SQLite uses TEXT for JSONB)
    status TEXT NOT NULL DEFAULT 'active',
    org_id TEXT NOT NULL DEFAULT '',
    created_by TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_model_providers_type ON model_providers(type);
CREATE INDEX IF NOT EXISTS idx_model_providers_status ON model_providers(status);
CREATE INDEX IF NOT EXISTS idx_model_providers_org_status ON model_providers(org_id, status);

-- 示例数据（可选）
INSERT INTO model_providers (provider_id, name, type, config, status, org_id, created_by, created_at, updated_at)
VALUES (
    'anthropic-default',
    'Anthropic Default',
    'anthropic',
    '{"default_model": "claude-3-5-sonnet-20241022", "max_tokens": 4096, "timeout_seconds": 60}',
    'active',
    'default-org',
    'system',
    datetime('now'),
    datetime('now')
);
