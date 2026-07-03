"""RunStore — PostgreSQL persistence for Run and RunEvent records. v3.1

v3.1: Uses parameterized queries via aitest.infra.sql (no more f-string SQL).

Usage:
    from aitest.platform.run_store import RunStore
    store = RunStore()
    store.save_run(run)
    store.save_event(event)
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from .run import Run
from .run_event import RunEvent
from .execution_request import ExecutionRequest
from aitest.infra.sql import safe_exec, safe_query, safe_literal, safe_json

logger = logging.getLogger("run_store")


def _row_to_run(r: dict) -> Run:
    return Run(
        run_id=r["run_id"], request_id=r["request_id"],
        workspace_id=r["workspace_id"], org_id=r.get("org_id", ""),
        triggered_by=r.get("triggered_by", ""), capability=r.get("capability", "browser"),
        agent=r.get("agent", ""), module=r.get("module", ""),
        pages=r.get("pages", []), mode=r.get("mode", "full"),
        status=r.get("status", "running"),
        created_at=r.get("created_at", ""), completed_at=r.get("completed_at", "") or "",
        total_tokens=r.get("total_tokens", 0), total_cost=r.get("total_cost", 0.0),
        agent_runs=r.get("agent_runs", 0), artifacts=r.get("artifacts", []),
        error_message=r.get("error_message", ""),
    )


def _row_to_event(r: dict) -> RunEvent:
    return RunEvent(
        event_id=r["event_id"], event_type=r["event_type"],
        run_id=r.get("run_id", ""), request_id=r.get("request_id", ""),
        timestamp=r.get("timestamp", ""), data=r.get("data", {}),
    )


def _row_to_request(r: dict) -> ExecutionRequest:
    return ExecutionRequest(
        request_id=r["request_id"], workspace_id=r["workspace_id"],
        org_id=r.get("org_id", ""), triggered_by=r.get("triggered_by", ""),
        trigger_type=r.get("trigger_type", "manual"), module=r.get("module", ""),
        pages=r.get("pages", []), mode=r.get("mode", "full"),
        provider=r.get("provider", "claude"), priority=r.get("priority", 0),
        status=r.get("status", "created"), run_ids=r.get("run_ids", []),
        created_at=r.get("created_at", ""), started_at=r.get("started_at"),
        completed_at=r.get("completed_at"),
        retry_count=r.get("retry_count", 0), max_retries=r.get("max_retries", 0),
    )


class RunStore:
    def save_request(self, request: ExecutionRequest):
        safe_exec(
            "INSERT INTO execution_requests "
            "(request_id, workspace_id, org_id, triggered_by, trigger_type, module, pages, mode, "
            "provider, priority, status, run_ids, created_at, started_at, completed_at, retry_count, max_retries) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT (request_id) DO UPDATE SET "
            "status=EXCLUDED.status, run_ids=EXCLUDED.run_ids, "
            "started_at=EXCLUDED.started_at, completed_at=EXCLUDED.completed_at",
            [request.request_id, request.workspace_id, request.org_id,
             request.triggered_by, request.trigger_type, request.module,
             json.dumps(request.pages, ensure_ascii=False), request.mode,
             request.provider or 'claude', request.priority, request.status,
             json.dumps(request.run_ids, ensure_ascii=False),
             request.created_at, request.started_at, request.completed_at,
             request.retry_count, request.max_retries],
        )

    def load_request(self, request_id: str) -> Optional[ExecutionRequest]:
        rows = safe_query(
            "SELECT * FROM execution_requests WHERE request_id=?",
            [request_id],
        )
        return _row_to_request(rows[0]) if rows else None

    def save_run(self, run: Run):
        safe_exec(
            "INSERT INTO runs "
            "(run_id, request_id, workspace_id, org_id, triggered_by, capability, agent, "
            "module, pages, mode, status, created_at, completed_at, total_tokens, total_cost, "
            "agent_runs, artifacts, error_message) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT (run_id) DO UPDATE SET "
            "status=EXCLUDED.status, completed_at=EXCLUDED.completed_at, "
            "total_tokens=EXCLUDED.total_tokens, total_cost=EXCLUDED.total_cost, "
            "agent_runs=EXCLUDED.agent_runs, artifacts=EXCLUDED.artifacts, "
            "error_message=EXCLUDED.error_message",
            [run.run_id, run.request_id, run.workspace_id, run.org_id,
             run.triggered_by, run.capability, run.agent, run.module,
             json.dumps(run.pages, ensure_ascii=False), run.mode, run.status,
             run.created_at, run.completed_at, run.total_tokens, run.total_cost,
             run.agent_runs, json.dumps(run.artifacts, ensure_ascii=False),
             run.error_message],
        )

    def load_run(self, run_id: str) -> Optional[Run]:
        rows = safe_query("SELECT * FROM runs WHERE run_id=?", [run_id])
        return _row_to_run(rows[0]) if rows else None

    def list_runs(self, workspace_id: str = "", org_id: str = "", status: str = "",
                  request_id: str = "", limit: int = 50, offset: int = 0) -> list[Run]:
        sql = "SELECT * FROM runs WHERE 1=1"
        params: list = []
        if workspace_id:
            sql += " AND workspace_id=?"
            params.append(workspace_id)
        if org_id:
            sql += " AND org_id=?"
            params.append(org_id)
        if status:
            sql += " AND status=?"
            params.append(status)
        if request_id:
            sql += " AND request_id=?"
            params.append(request_id)
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = safe_query(sql, params)
        return [_row_to_run(r) for r in rows]

    def count_runs(self, workspace_id: str = "", org_id: str = "") -> int:
        sql = "SELECT COUNT(*) as cnt FROM runs WHERE 1=1"
        params: list = []
        if workspace_id:
            sql += " AND workspace_id=?"
            params.append(workspace_id)
        if org_id:
            sql += " AND org_id=?"
            params.append(org_id)
        rows = safe_query(sql, params)
        return rows[0]["cnt"] if rows else 0

    def save_event(self, event: RunEvent):
        safe_exec(
            "INSERT INTO run_events (event_id, event_type, run_id, request_id, timestamp, data, correlation_id) "
            "VALUES (?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT (event_id) DO NOTHING",
            [event.event_id, event.event_type, event.run_id, event.request_id,
             event.timestamp, json.dumps(event.data, ensure_ascii=False),
             event.run_id or ''],
        )

    def list_events(self, run_id: str = "", event_type: str = "", limit: int = 100) -> list[RunEvent]:
        sql = "SELECT * FROM run_events WHERE 1=1"
        params: list = []
        if run_id:
            sql += " AND run_id=?"
            params.append(run_id)
        if event_type:
            sql += " AND event_type=?"
            params.append(event_type)
        sql += " ORDER BY timestamp ASC LIMIT ?"
        params.append(limit)
        rows = safe_query(sql, params)
        return [_row_to_event(r) for r in rows]

    def cleanup_old_runs(self, max_age_days: int = 30) -> int:
        rows = safe_query(
            "SELECT run_id FROM runs WHERE status IN ('completed','failed','cancelled','timed_out') "
            "AND completed_at < datetime('now', ?)",
            [f"-{max_age_days} days"],
        )
        for r in rows:
            safe_exec("DELETE FROM run_events WHERE run_id=?", [r['run_id']])
            safe_exec("DELETE FROM runs WHERE run_id=?", [r['run_id']])
        return len(rows)

    def recover_crashed_runs(self) -> int:
        safe_exec(
            "UPDATE runs SET status='failed', error_message='Server crash — run interrupted', "
            "completed_at=datetime('now') WHERE status='running'",
        )
        rows = safe_query(
            "SELECT COUNT(*) as cnt FROM runs WHERE status='failed' "
            "AND error_message='Server crash — run interrupted'",
        )
        return rows[0]["cnt"] if rows else 0

    def get_stats(self) -> dict:
        rows = safe_query(
            "SELECT "
            "(SELECT COUNT(*) FROM runs) as run_count, "
            "(SELECT COUNT(*) FROM run_events) as event_count, "
            "(SELECT COUNT(*) FROM execution_requests) as request_count",
        )
        return {"backend": "sqlite", **rows[0]} if rows else {"backend": "sqlite"}


_store: RunStore | None = None
_store_lock = __import__('threading').Lock()

def get_run_store() -> RunStore:
    """Get the global RunStore singleton. Creates one on first call."""
    global _store
    with _store_lock:
        if _store is None:
            _store = RunStore()
        return _store

def set_run_store(store: RunStore) -> None:
    """Inject a custom RunStore instance (for testing or plugin replacement)."""
    global _store
    with _store_lock:
        _store = store

def reset_run_store() -> None:
    """Reset to default singleton (next get_run_store() creates a fresh instance)."""
    global _store
    with _store_lock:
        _store = None
