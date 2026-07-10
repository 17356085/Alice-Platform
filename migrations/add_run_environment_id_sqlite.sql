-- 为 runs 表添加 environment_id 字段 (SQLite)
-- 创建时间: 2026-07-11
-- 相关任务: P6-4 Environment 资源化

-- 添加 environment_id 字段（可选，向后兼容）
ALTER TABLE runs ADD COLUMN environment_id TEXT DEFAULT NULL;
