-- P5-1: Quality Loop Tables — Dataset/Evaluation/Experiment
-- Migration: Add 3 quality tables to SQLite

-- 1. datasets 表
CREATE TABLE IF NOT EXISTS datasets (
    dataset_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- "test_cases" | "conversations" | "prompts"
    project_id TEXT DEFAULT '',
    org_id TEXT DEFAULT '',
    created_by TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    examples TEXT DEFAULT '[]',  -- JSON array
    metadata TEXT DEFAULT '{}'   -- JSON object
);

CREATE INDEX IF NOT EXISTS idx_datasets_org_id ON datasets(org_id);
CREATE INDEX IF NOT EXISTS idx_datasets_project_id ON datasets(project_id);

-- 2. evaluations 表
CREATE TABLE IF NOT EXISTS evaluations (
    evaluation_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    agent_version TEXT DEFAULT 'latest',
    org_id TEXT DEFAULT '',
    created_by TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    evaluator_config TEXT DEFAULT '{}',  -- JSON object
    results TEXT DEFAULT '{}',           -- JSON object
    error_message TEXT DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_evaluations_dataset_id ON evaluations(dataset_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_org_id ON evaluations(org_id);
CREATE INDEX IF NOT EXISTS idx_evaluations_status ON evaluations(status);

-- 3. experiments 表
CREATE TABLE IF NOT EXISTS experiments (
    experiment_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    baseline_eval_id TEXT NOT NULL,
    candidate_eval_id TEXT NOT NULL,
    org_id TEXT DEFAULT '',
    created_by TEXT DEFAULT '',
    status TEXT DEFAULT 'pending',
    decision TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    comparison TEXT DEFAULT '{}',  -- JSON object
    metadata TEXT DEFAULT '{}'     -- JSON object
);

CREATE INDEX IF NOT EXISTS idx_experiments_baseline ON experiments(baseline_eval_id);
CREATE INDEX IF NOT EXISTS idx_experiments_candidate ON experiments(candidate_eval_id);
CREATE INDEX IF NOT EXISTS idx_experiments_org_id ON experiments(org_id);
