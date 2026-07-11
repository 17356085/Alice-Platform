-- P3-5: Worker Lease/Heartbeat 表 (PostgreSQL)
-- Worker 注册、心跳状态、僵尸检测

CREATE TABLE IF NOT EXISTS workers (
    worker_id VARCHAR(64) PRIMARY KEY,
    hostname VARCHAR(255) NOT NULL,
    pid INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(32) NOT NULL DEFAULT 'running',
    started_at TIMESTAMPTZ NOT NULL,
    last_heartbeat_at TIMESTAMPTZ NOT NULL,
    heartbeat_interval_seconds INTEGER NOT NULL DEFAULT 30,
    claimed_requests JSONB NOT NULL DEFAULT '[]',
    stats JSONB NOT NULL DEFAULT '{}',
    metadata JSONB NOT NULL DEFAULT '{}',
    org_id VARCHAR(64) NOT NULL DEFAULT 'default-org'
);

CREATE INDEX IF NOT EXISTS idx_workers_status ON workers (status);
CREATE INDEX IF NOT EXISTS idx_workers_status_heartbeat ON workers (status, last_heartbeat_at);
CREATE INDEX IF NOT EXISTS idx_workers_org ON workers (org_id, status);
