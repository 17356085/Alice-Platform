"""RunStore — PostgreSQL persistence for Run and RunEvent records. v3.1

v3.1: Uses parameterized queries via aitest.infra.sql (no more f-string SQL).

Usage:
    from aitest.platform.run_store import RunStore
    store = RunStore()
    store.save_run(run)
    store.save_event(event)
"""

__all__ = ["RunStore", "get_run_store", "set_run_store", "reset_run_store"]

import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from .run import Run
from .run_event import RunEvent
from .execution_request import ExecutionRequest
from aitest.infra.sql import safe_exec, safe_query, safe_literal, safe_json
from aitest.infra.config_registry import cfg

logger = logging.getLogger("run_store")


def _decode_json_field(value, default):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except Exception:
            return default
    return default


def _row_to_run(r: dict) -> Run:
    return Run(
        run_id=r["run_id"], request_id=r["request_id"],
        workspace_id=r["workspace_id"], org_id=r.get("org_id", ""),
        triggered_by=r.get("triggered_by", ""), capability=r.get("capability", "browser"),
        # Legacy fields
        agent=r.get("agent", ""), module=r.get("module", ""),
        pages=_decode_json_field(r.get("pages", []), []),
        # P7-2 Phase 2: 新字段（带向后兼容默认值）
        target_type=r.get("target_type", "agent"),
        target_id=r.get("target_id", r.get("agent", "")),  # fallback to agent
        target_version=r.get("target_version", "latest"),
        environment_id=r.get("environment_id", ""),
        parent_run_id=r.get("parent_run_id", ""),
        mode=r.get("mode", "full"),
        status=r.get("status", "running"),
        created_at=r.get("created_at", ""), completed_at=r.get("completed_at", "") or "",
        total_tokens=r.get("total_tokens", 0), total_cost=r.get("total_cost", 0.0),
        agent_runs=r.get("agent_runs", 0), artifacts=_decode_json_field(r.get("artifacts", []), []),
        error_message=r.get("error_message", ""),
    )


def _row_to_event(r: dict) -> RunEvent:
    return RunEvent(
        event_id=r["event_id"], event_type=r["event_type"],
        run_id=r.get("run_id", ""), request_id=r.get("request_id", ""),
        timestamp=r.get("timestamp", ""), data=_decode_json_field(r.get("data", {}), {}),
    )


def _row_to_request(r: dict) -> ExecutionRequest:
    pages = r.get("pages", [])
    if isinstance(pages, str):
        try:
            pages = json.loads(pages)
        except Exception:
            pages = [pages] if pages else []
    run_ids = r.get("run_ids", [])
    if isinstance(run_ids, str):
        try:
            run_ids = json.loads(run_ids)
        except Exception:
            run_ids = [run_ids] if run_ids else []
    return ExecutionRequest(
        request_id=r["request_id"], workspace_id=r["workspace_id"],
        org_id=r.get("org_id", ""), triggered_by=r.get("triggered_by", ""),
        trigger_type=r.get("trigger_type", "manual"), module=r.get("module", ""),
        agent=r.get("agent", ""),
        idempotency_key=r.get("idempotency_key", ""),
        pages=pages, mode=r.get("mode", "full"),
        provider=r.get("provider", "claude"), priority=r.get("priority", 0),
        status=r.get("status", "created"), run_ids=run_ids,
        created_at=r.get("created_at", ""), started_at=r.get("started_at"),
        completed_at=r.get("completed_at"), next_retry_at=r.get("next_retry_at") or None,
        retry_count=r.get("retry_count", 0), max_retries=r.get("max_retries", 0),
    )


class RunStore:
    def __init__(self, db_path: str | Path | None = None):
        from aitest.infra.database import init_db as _init_db

        if db_path is not None:
            from aitest.infra import database as _db
            from aitest.infra import database_sqlite as _sqlite

            _db._backend = "sqlite"
            _sqlite._DB_PATH = Path(db_path)
            _sqlite._DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        _init_db()
        self._ensure_execution_request_agent_column()

    def _ensure_execution_request_agent_column(self) -> None:
        """Backfill older databases that were created before agent persisted."""
        try:
            rows = safe_query("PRAGMA table_info(execution_requests)")
            columns = {r.get("name", "") for r in rows}
            if "agent" not in columns:
                safe_exec("ALTER TABLE execution_requests ADD COLUMN agent TEXT NOT NULL DEFAULT ''")
            if "idempotency_key" not in columns:
                safe_exec("ALTER TABLE execution_requests ADD COLUMN idempotency_key TEXT NOT NULL DEFAULT ''")
            if "next_retry_at" not in columns:
                safe_exec("ALTER TABLE execution_requests ADD COLUMN next_retry_at TEXT DEFAULT ''")
            # P7-2 Phase 2: 新资源模型字段
            self._ensure_runs_resource_fields()
        except Exception:
            # Best effort: legacy databases may not support schema migration here.
            pass

    def _ensure_runs_resource_fields(self) -> None:
        """P7-2 Phase 2: Add target_type/target_id/target_version/environment_id/parent_run_id to runs table."""
        try:
            rows = safe_query("PRAGMA table_info(runs)")
            columns = {r.get("name", "") for r in rows}

            if "target_type" not in columns:
                safe_exec("ALTER TABLE runs ADD COLUMN target_type TEXT NOT NULL DEFAULT 'agent'")
                logger.info("migration_runs_target_type_added")

            if "target_id" not in columns:
                safe_exec("ALTER TABLE runs ADD COLUMN target_id TEXT NOT NULL DEFAULT ''")
                logger.info("migration_runs_target_id_added")

            if "target_version" not in columns:
                safe_exec("ALTER TABLE runs ADD COLUMN target_version TEXT NOT NULL DEFAULT 'latest'")
                logger.info("migration_runs_target_version_added")

            if "environment_id" not in columns:
                safe_exec("ALTER TABLE runs ADD COLUMN environment_id TEXT NOT NULL DEFAULT ''")
                logger.info("migration_runs_environment_id_added")

            if "parent_run_id" not in columns:
                safe_exec("ALTER TABLE runs ADD COLUMN parent_run_id TEXT NOT NULL DEFAULT ''")
                logger.info("migration_runs_parent_run_id_added")

            # 创建索引（如果不存在）
            safe_exec("CREATE INDEX IF NOT EXISTS idx_runs_target ON runs(target_type, target_id)")
            safe_exec("CREATE INDEX IF NOT EXISTS idx_runs_environment ON runs(environment_id)")
            safe_exec("CREATE INDEX IF NOT EXISTS idx_runs_parent ON runs(parent_run_id)")

        except Exception as e:
            logger.warning("migration_runs_resource_fields_failed", error=str(e))

    def save_request(self, request: ExecutionRequest):
        safe_exec(
            "INSERT INTO execution_requests "
            "(request_id, workspace_id, org_id, triggered_by, trigger_type, agent, idempotency_key, module, pages, mode, "
            "provider, priority, status, run_ids, created_at, started_at, completed_at, next_retry_at, retry_count, max_retries) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT (request_id) DO UPDATE SET "
            "agent=EXCLUDED.agent, idempotency_key=EXCLUDED.idempotency_key, "
            "status=EXCLUDED.status, run_ids=EXCLUDED.run_ids, "
            "started_at=EXCLUDED.started_at, completed_at=EXCLUDED.completed_at, next_retry_at=EXCLUDED.next_retry_at, "
            "retry_count=EXCLUDED.retry_count, max_retries=EXCLUDED.max_retries",
            [request.request_id, request.workspace_id, request.org_id,
             request.triggered_by, request.trigger_type, request.agent, request.idempotency_key,
             request.module, json.dumps(request.pages, ensure_ascii=False), request.mode,
             request.provider or 'claude', request.priority, request.status,
             json.dumps(request.run_ids, ensure_ascii=False),
             request.created_at, request.started_at, request.completed_at,
             request.next_retry_at,
             request.retry_count, request.max_retries],
        )

    def load_request(self, request_id: str) -> Optional[ExecutionRequest]:
        rows = safe_query(
            "SELECT * FROM execution_requests WHERE request_id=?",
            [request_id],
        )
        return _row_to_request(rows[0]) if rows else None

    def find_request_by_idempotency_key(
        self,
        idempotency_key: str,
        *,
        workspace_id: str = "",
        org_id: str = "",
    ) -> Optional[ExecutionRequest]:
        if not idempotency_key:
            return None
        sql = "SELECT * FROM execution_requests WHERE idempotency_key=?"
        params: list = [idempotency_key]
        if workspace_id:
            sql += " AND workspace_id=?"
            params.append(workspace_id)
        if org_id:
            sql += " AND org_id=?"
            params.append(org_id)
        sql += " ORDER BY created_at DESC LIMIT 1"
        rows = safe_query(sql, params)
        return _row_to_request(rows[0]) if rows else None

    def list_requests(
        self,
        workspace_id: str = "",
        org_id: str = "",
        status: str = "",
        limit: int = 50,
        offset: int = 0,
    ) -> list[ExecutionRequest]:
        sql = "SELECT * FROM execution_requests WHERE 1=1"
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
        sql += " ORDER BY priority DESC, created_at ASC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        rows = safe_query(sql, params)
        return [_row_to_request(r) for r in rows]

    def claim_next_request(self) -> Optional[ExecutionRequest]:
        """Atomically claim the next queued request for worker processing."""
        from datetime import datetime, timezone

        started_at = datetime.now(timezone.utc).isoformat()
        try:
            rows = safe_query(
                "UPDATE execution_requests SET status='running', started_at=? "
                "WHERE request_id = ("
                "  SELECT request_id FROM execution_requests "
                "  WHERE status='queued' AND (next_retry_at IS NULL OR next_retry_at <= ?) "
                "  ORDER BY priority DESC, created_at ASC "
                "  LIMIT 1"
                ") AND status='queued' "
                "RETURNING *",
                [started_at, started_at],
            )
            return _row_to_request(rows[0]) if rows else None
        except Exception:
            rows = safe_query(
                "SELECT * FROM execution_requests WHERE status='queued' "
                "AND (next_retry_at IS NULL OR next_retry_at <= ?) "
                "ORDER BY priority DESC, created_at ASC LIMIT 1"
                ,
                [started_at],
            )
            if not rows:
                return None
            request = _row_to_request(rows[0])
            safe_exec(
                "UPDATE execution_requests SET status='running', started_at=?, next_retry_at='' WHERE request_id=? AND status='queued'",
                [started_at, request.request_id],
            )
            current = self.load_request(request.request_id)
            return current if current and current.status == "running" else None

    def save_run(self, run: Run):
        safe_exec(
            "INSERT INTO runs "
            "(run_id, request_id, workspace_id, org_id, triggered_by, capability, agent, "
            "module, pages, target_type, target_id, target_version, environment_id, parent_run_id, "
            "mode, status, created_at, completed_at, total_tokens, total_cost, "
            "agent_runs, artifacts, error_message) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
            "ON CONFLICT (run_id) DO UPDATE SET "
            "status=EXCLUDED.status, completed_at=EXCLUDED.completed_at, "
            "total_tokens=EXCLUDED.total_tokens, total_cost=EXCLUDED.total_cost, "
            "agent_runs=EXCLUDED.agent_runs, artifacts=EXCLUDED.artifacts, "
            "error_message=EXCLUDED.error_message",
            [run.run_id, run.request_id, run.workspace_id, run.org_id,
             run.triggered_by, run.capability, run.agent, run.module,
             json.dumps(run.pages, ensure_ascii=False),
             run.target_type, run.target_id, run.target_version,
             run.environment_id, run.parent_run_id,
             run.mode, run.status,
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

    def recover_stale_requests(self) -> int:
        """Recover running execution requests left behind by a server crash."""
        cutoff = (datetime.now(timezone.utc) - timedelta(seconds=cfg.task_stale_timeout_s)).isoformat()
        rows = safe_query(
            "SELECT request_id FROM execution_requests "
            "WHERE status='running' AND started_at IS NOT NULL AND started_at < ?",
            [cutoff],
        )
        recovered = 0
        for row in rows:
            request_id = row.get("request_id", "")
            if not request_id:
                continue
            request = self.load_request(request_id)
            if request is None or request.status != "running":
                continue
            safe_exec(
                "UPDATE runs SET status='failed', error_message='Server crash — run interrupted', "
                "completed_at=datetime('now') WHERE request_id=? AND status='running'",
                [request_id],
            )
            request.recover()
            self.save_request(request)
            recovered += 1
        if recovered:
            logger.warning(
                "stale_requests_recovered count=%s cutoff=%s",
                recovered,
                cutoff,
            )
        return recovered

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
