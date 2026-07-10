-- Run 表添加 provider_id 字段 (P6-1)
-- 数据库: SQLite

ALTER TABLE runs ADD COLUMN provider_id TEXT DEFAULT NULL;

-- 注释: provider_id 可选，向后兼容
-- 如果为 NULL，则 fallback 到 provider 字段或环境变量
