"""
RunStore — simple SQLite persistence for Run and RunEvent records. v2.2

Design: plain functions, no Repository Pattern. sqlite3 (sync) is fine —
ExecutionService calls are synchronous. Extract interface later if DB changes.

Usage:
    from aitest.platform.run_store import RunStore
    store = RunStore()
    store.save_run(run)
    store.save_event(event)
"""

import json
import sqlite3
import threading
from pathlib import Path
from datetime import datetime, timezone

from .run import Run
from .run_event import RunEvent
from .execution_request import ExecutionRequest


# ── DB path ──────────────────────────────────────────────────────────────

def _default_db_path() -> Path:
    """Same directory as session_store DB."""
    base = Path(__file__).resolve().parent.parent.parent
    return base / "governance" / ".data" / "runs.db"


# ── Store ────────────────────────────────────────────────────────────────

class RunStore:
    """Simple SQLite store for Run + RunEvent records."""

    def __init__(self, db_path: Path | None = None):
        self._path = db_path or _default_db_path()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(str(self._path))
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    request_id TEXT NOT NULL,
                    workspace_id TEXT NOT NULL,
                    org_id TEXT NOT NULL DEFAULT '',
                    triggered_by TEXT NOT NULL DEFAULT '',
                    capability TEXT NOT NULL DEFAULT 'browser',
                    agent TEXT NOT NULL DEFAULT '',
                    module TEXT NOT NULL DEFAULT '',
                    pages TEXT NOT NULL DEFAULT '[]',
                    mode TEXT NOT NULL DEFAULT 'full',
                    status TEXT NOT NULL DEFAULT 'running',
                    created_at TEXT NOT NULL DEFAULT '',
                    completed_at TEXT NOT NULL DEFAULT '',
                    total_tokens INTEGER NOT NULL DEFAULT 0,
                    total_cost REAL NOT NULL DEFAULT 0.0,
                    agent_runs INTEGER NOT NULL DEFAULT 0,
                    artifacts TEXT NOT NULL DEFAULT '[]',
                    error_message TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS run_events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    run_id TEXT NOT NULL DEFAULT '',
                    request_id TEXT NOT NULL DEFAULT '',
                    timestamp TEXT NOT NULL DEFAULT '',
                    data TEXT NOT NULL DEFAULT '{}'
                );

                CREATE INDEX IF NOT EXISTS idx_runs_workspace ON runs(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_runs_org ON runs(org_id);
                CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status);
                CREATE INDEX IF NOT EXISTS idx_events_run ON run_events(run_id);
                CREATE INDEX IF NOT EXISTS idx_events_type ON run_events(event_type);

                CREATE TABLE IF NOT EXISTS execution_requests (
                    request_id TEXT PRIMARY KEY,
                    workspace_id TEXT NOT NULL,
                    org_id TEXT NOT NULL DEFAULT '',
                    triggered_by TEXT NOT NULL DEFAULT '',
                    trigger_type TEXT NOT NULL DEFAULT 'manual',
                    module TEXT NOT NULL DEFAULT '',
                    pages TEXT NOT NULL DEFAULT '[]',
                    mode TEXT NOT NULL DEFAULT 'full',
                    provider TEXT NOT NULL DEFAULT 'claude',
                    priority INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'created',
                    run_ids TEXT NOT NULL DEFAULT '[]',
                    created_at TEXT NOT NULL DEFAULT '',
                    started_at TEXT,
                    completed_at TEXT,
                    retry_count INTEGER NOT NULL DEFAULT 0,
                    max_retries INTEGER NOT NULL DEFAULT 0
                );

                CREATE INDEX IF NOT EXISTS idx_req_workspace ON execution_requests(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_req_org ON execution_requests(org_id);
                CREATE INDEX IF NOT EXISTS idx_req_status ON execution_requests(status);
            """)
            conn.commit()
            conn.close()

    # ── Run CRUD ──────────────────────────────────────────────────────

    def save_request(self, request: ExecutionRequest):
        with self._lock:
            conn = sqlite3.connect(str(self._path))
            conn.execute("""
                INSERT OR REPLACE INTO execution_requests
                (request_id, workspace_id, org_id, triggered_by, trigger_type,
                 module, pages, mode, provider, priority,
                 status, run_ids, created_at, started_at, completed_at,
                 retry_count, max_retries)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.request_id, request.workspace_id, request.org_id,
                request.triggered_by, request.trigger_type,
                request.module, json.dumps(request.pages, ensure_ascii=False),
                request.mode, request.provider, request.priority,
                request.status, json.dumps(request.run_ids, ensure_ascii=False),
                request.created_at, request.started_at, request.completed_at,
                request.retry_count, request.max_retries,
            ))
            conn.commit()
            conn.close()

    def load_request(self, request_id: str) -> ExecutionRequest | None:
        conn = sqlite3.connect(str(self._path))
        row = conn.execute(
            "SELECT * FROM execution_requests WHERE request_id = ?", (request_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        cols = [
            "request_id", "workspace_id", "org_id", "triggered_by", "trigger_type",
            "module", "pages", "mode", "provider", "priority",
            "status", "run_ids", "created_at", "started_at", "completed_at",
            "retry_count", "max_retries",
        ]
        d = dict(zip(cols, row))
        d["pages"] = json.loads(d.get("pages", "[]"))
        d["run_ids"] = json.loads(d.get("run_ids", "[]"))
        return ExecutionRequest(**d)

    def save_run(self, run: Run):
        with self._lock:
            conn = sqlite3.connect(str(self._path))
            conn.execute("""
                INSERT OR REPLACE INTO runs
                (run_id, request_id, workspace_id, org_id, triggered_by,
                 capability, agent, module, pages, mode,
                 status, created_at, completed_at,
                 total_tokens, total_cost, agent_runs, artifacts, error_message)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                run.run_id, run.request_id, run.workspace_id, run.org_id,
                run.triggered_by,
                run.capability, run.agent, run.module,
                json.dumps(run.pages, ensure_ascii=False), run.mode,
                run.status, run.created_at, run.completed_at,
                run.total_tokens, run.total_cost, run.agent_runs,
                json.dumps(run.artifacts, ensure_ascii=False),
                run.error_message,
            ))
            conn.commit()
            conn.close()

    def load_run(self, run_id: str) -> Run | None:
        conn = sqlite3.connect(str(self._path))
        row = conn.execute(
            "SELECT * FROM runs WHERE run_id = ?", (run_id,)
        ).fetchone()
        conn.close()
        if row is None:
            return None
        return self._row_to_run(row)

    def list_runs(
        self,
        workspace_id: str = "",
        org_id: str = "",
        status: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> list[Run]:
        conn = sqlite3.connect(str(self._path))
        where = []
        params = []
        if workspace_id:
            where.append("workspace_id = ?")
            params.append(workspace_id)
        if org_id:
            where.append("org_id = ?")
            params.append(org_id)
        if status:
            where.append("status = ?")
            params.append(status)

        sql = "SELECT * FROM runs"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [self._row_to_run(r) for r in rows]

    def count_runs(self, workspace_id: str = "", org_id: str = "") -> int:
        conn = sqlite3.connect(str(self._path))
        where = []
        params = []
        if workspace_id:
            where.append("workspace_id = ?")
            params.append(workspace_id)
        if org_id:
            where.append("org_id = ?")
            params.append(org_id)

        sql = "SELECT COUNT(*) FROM runs"
        if where:
            sql += " WHERE " + " AND ".join(where)

        row = conn.execute(sql, params).fetchone()
        conn.close()
        return row[0] if row else 0

    # ── Event CRUD ────────────────────────────────────────────────────

    def save_event(self, event: RunEvent):
        with self._lock:
            conn = sqlite3.connect(str(self._path))
            conn.execute("""
                INSERT OR REPLACE INTO run_events
                (event_id, event_type, run_id, request_id, timestamp, data)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                event.event_id, event.event_type, event.run_id,
                event.request_id, event.timestamp,
                json.dumps(event.data, ensure_ascii=False),
            ))
            conn.commit()
            conn.close()

    def list_events(
        self,
        run_id: str = "",
        event_type: str = "",
        limit: int = 100,
    ) -> list[RunEvent]:
        conn = sqlite3.connect(str(self._path))
        where = []
        params = []
        if run_id:
            where.append("run_id = ?")
            params.append(run_id)
        if event_type:
            where.append("event_type = ?")
            params.append(event_type)

        sql = "SELECT * FROM run_events"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY timestamp ASC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [self._row_to_event(r) for r in rows]

    # ── Internal ──────────────────────────────────────────────────────

    def _row_to_run(self, row) -> Run:
        cols = [
            "run_id", "request_id", "workspace_id", "org_id", "triggered_by",
            "capability", "agent", "module", "pages", "mode",
            "status", "created_at", "completed_at",
            "total_tokens", "total_cost", "agent_runs", "artifacts",
            "error_message",
        ]
        d = dict(zip(cols, row))
        d["pages"] = json.loads(d.get("pages", "[]"))
        d["artifacts"] = json.loads(d.get("artifacts", "[]"))
        return Run(**d)

    def _row_to_event(self, row) -> RunEvent:
        cols = [
            "event_id", "event_type", "run_id", "request_id", "timestamp", "data",
        ]
        d = dict(zip(cols, row))
        d["data"] = json.loads(d.get("data", "{}"))
        return RunEvent(**d)


# ── Singleton ────────────────────────────────────────────────────────────

_store: RunStore | None = None
_store_lock = threading.Lock()


def get_run_store() -> RunStore:
    global _store
    with _store_lock:
        if _store is None:
            _store = RunStore()
        return _store
