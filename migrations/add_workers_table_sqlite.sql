-- P3-5: Worker Lease/Heartbeat 表 (SQLite)
-- Worker 注册、心跳状态、僵尸检测

CREATE TABLE IF NOT EXISTS workers (
    worker_id TEXT PRIMARY KEY,
    hostname TEXT NOT NULL,
    pid INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'running',  -- running | draining | stopped | dead
    started_at TEXT NOT NULL,
    last_heartbeat_at TEXT NOT NULL,
    heartbeat_interval_seconds INTEGER NOT NULL DEFAULT 30,
    claimed_requests TEXT NOT NULL DEFAULT '[]',  -- JSON list[str]
    stats TEXT NOT NULL DEFAULT '{}',             -- JSON dict
    metadata TEXT NOT NULL DEFAULT '{}',          -- JSON dict
    org_id TEXT NOT NULL DEFAULT 'default-org'
);

CREATE INDEX IF NOT EXISTS idx_workers_status ON workers (status);
CREATE INDEX IF NOT EXISTS idx_workers_heartbeat ON workers (last_heartbeat_at);
CREATE INDEX IF NOT EXISTS idx_workers_org ON workers (org_id, status);
