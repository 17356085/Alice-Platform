"""
Audit Log — operational audit trail. v2.3

Append-only subscriber of all RunEvents + Platform events.
Persists to SQLite. Queryable by org, workspace, event_type, time range.

Pure consumer. No new abstractions. No modification to ExecutionService.

Usage:
    from aitest.platform.audit_log import AuditLogger, get_audit_logger

    logger = get_audit_logger()
    logger.start()   # subscribes to EventBus, persists all events

    # Query
    entries = logger.query(org_id="my-org", event_type="run.completed", limit=50)
"""

import json
import sqlite3
import threading
from pathlib import Path
from datetime import datetime, timezone

from .event_bus import get_bus
from .run_event import RunEvent


def _audit_db_path() -> Path:
    base = Path(__file__).resolve().parent.parent.parent
    return base / "governance" / ".data" / "audit.db"


class AuditLogger:
    """Append-only audit log. Subscribes to EventBus, persists every event."""

    def __init__(self, db_path: Path | None = None):
        self._path = db_path or _audit_db_path()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._active = False
        self._init_db()

    def _init_db(self):
        with self._lock:
            conn = sqlite3.connect(str(self._path))
            conn.execute("PRAGMA journal_mode=WAL")
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS audit_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    run_id TEXT NOT NULL DEFAULT '',
                    request_id TEXT NOT NULL DEFAULT '',
                    org_id TEXT NOT NULL DEFAULT '',
                    workspace_id TEXT NOT NULL DEFAULT '',
                    user_id TEXT NOT NULL DEFAULT '',
                    timestamp TEXT NOT NULL DEFAULT '',
                    data_json TEXT NOT NULL DEFAULT '{}',
                    created_at TEXT NOT NULL DEFAULT ''
                );

                CREATE INDEX IF NOT EXISTS idx_audit_type ON audit_entries(event_type);
                CREATE INDEX IF NOT EXISTS idx_audit_org ON audit_entries(org_id);
                CREATE INDEX IF NOT EXISTS idx_audit_workspace ON audit_entries(workspace_id);
                CREATE INDEX IF NOT EXISTS idx_audit_ts ON audit_entries(timestamp);
                CREATE INDEX IF NOT EXISTS idx_audit_run ON audit_entries(run_id);
            """)
            conn.commit()
            conn.close()

    # ── Lifecycle ─────────────────────────────────────────────────────

    def start(self):
        """Subscribe to EventBus. Idempotent."""
        if self._active:
            return
        bus = get_bus()
        bus.subscribe("*", self._on_event)
        self._active = True

    def stop(self):
        """Unsubscribe from EventBus."""
        if not self._active:
            return
        bus = get_bus()
        bus.unsubscribe("*", self._on_event)
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    # ── Event handler ─────────────────────────────────────────────────

    def _on_event(self, event: RunEvent):
        """Persist event to audit log. Non-blocking, best-effort."""
        try:
            org_id = event.data.get("org_id", "")
            workspace_id = event.data.get("workspace_id", "")
            user_id = event.data.get("triggered_by", "")

            with self._lock:
                conn = sqlite3.connect(str(self._path))
                conn.execute("""
                    INSERT INTO audit_entries
                    (event_id, event_type, run_id, request_id,
                     org_id, workspace_id, user_id,
                     timestamp, data_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id, event.event_type,
                    event.run_id, event.request_id,
                    org_id, workspace_id, user_id,
                    event.timestamp,
                    json.dumps(event.data, ensure_ascii=False),
                    datetime.now(timezone.utc).isoformat(),
                ))
                conn.commit()
                conn.close()
        except Exception:
            pass  # Best-effort. Don't break event pipeline.

    # ── Query ─────────────────────────────────────────────────────────

    def query(
        self,
        *,
        org_id: str = "",
        workspace_id: str = "",
        event_type: str = "",
        run_id: str = "",
        limit: int = 50,
        offset: int = 0,
        since: str = "",
        until: str = "",
    ) -> list[dict]:
        """Query audit entries. Filterable by org, workspace, event_type, time range."""
        conn = sqlite3.connect(str(self._path))
        where = []
        params = []

        if org_id:
            where.append("org_id = ?")
            params.append(org_id)
        if workspace_id:
            where.append("workspace_id = ?")
            params.append(workspace_id)
        if event_type:
            where.append("event_type = ?")
            params.append(event_type)
        if run_id:
            where.append("run_id = ?")
            params.append(run_id)
        if since:
            where.append("timestamp >= ?")
            params.append(since)
        if until:
            where.append("timestamp <= ?")
            params.append(until)

        sql = "SELECT * FROM audit_entries"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
        params.extend([min(limit, 500), offset])

        rows = conn.execute(sql, params).fetchall()
        conn.close()

        cols = ["id", "event_id", "event_type", "run_id", "request_id",
                "org_id", "workspace_id", "user_id", "timestamp", "data_json", "created_at"]
        return [
            {**dict(zip(cols, r)), "data": json.loads(r[9])}
            for r in rows
        ]

    def count(
        self,
        *,
        org_id: str = "",
        workspace_id: str = "",
        event_type: str = "",
    ) -> int:
        """Count audit entries matching filters."""
        conn = sqlite3.connect(str(self._path))
        where = []
        params = []
        if org_id:
            where.append("org_id = ?")
            params.append(org_id)
        if workspace_id:
            where.append("workspace_id = ?")
            params.append(workspace_id)
        if event_type:
            where.append("event_type = ?")
            params.append(event_type)

        sql = "SELECT COUNT(*) FROM audit_entries"
        if where:
            sql += " WHERE " + " AND ".join(where)

        row = conn.execute(sql, params).fetchone()
        conn.close()
        return row[0] if row else 0

    def stats(self, org_id: str = "") -> dict:
        """Quick stats: event counts by type, recent activity."""
        conn = sqlite3.connect(str(self._path))
        where = "WHERE org_id = ?" if org_id else ""
        params = [org_id] if org_id else []

        # Event type breakdown
        rows = conn.execute(
            f"SELECT event_type, COUNT(*) as cnt FROM audit_entries {where} "
            f"GROUP BY event_type ORDER BY cnt DESC LIMIT 20",
            params,
        ).fetchall()

        # Recent 5
        recent = conn.execute(
            f"SELECT event_type, run_id, timestamp FROM audit_entries {where} "
            f"ORDER BY created_at DESC LIMIT 5",
            params,
        ).fetchall()

        total = conn.execute(
            f"SELECT COUNT(*) FROM audit_entries {where}", params
        ).fetchone()

        conn.close()
        return {
            "total_entries": total[0] if total else 0,
            "by_type": [{"type": r[0], "count": r[1]} for r in rows],
            "recent": [
                {"event_type": r[0], "run_id": r[1], "timestamp": r[2]}
                for r in recent
            ],
        }


# ── Singleton ────────────────────────────────────────────────────────────

_logger: AuditLogger | None = None
_logger_lock = threading.Lock()


def get_audit_logger() -> AuditLogger:
    global _logger
    with _logger_lock:
        if _logger is None:
            _logger = AuditLogger()
        return _logger
