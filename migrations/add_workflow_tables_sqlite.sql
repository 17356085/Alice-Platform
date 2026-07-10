-- P8-1: Workflow Tables — JSON schema-based workflow definitions
-- Migration: Add workflow table to SQLite

CREATE TABLE IF NOT EXISTS workflows (
    workflow_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT DEFAULT '',
    version TEXT NOT NULL,
    status TEXT DEFAULT 'draft',  -- "draft" | "published" | "archived"
    org_id TEXT DEFAULT '',
    created_by TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    graph_json TEXT NOT NULL  -- JSON schema
);

CREATE INDEX IF NOT EXISTS idx_workflows_org_id ON workflows(org_id);
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_version ON workflows(workflow_id, version);
