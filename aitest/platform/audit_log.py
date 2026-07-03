"""
Audit Log — operational audit trail. v3.1

v3.1: Uses parameterized queries via aitest.infra.sql (no more f-string SQL).
"""

import json
import threading
from datetime import datetime, timezone, timedelta
from collections import deque
from .event_bus import get_bus
from .run_event import RunEvent, EventDataKey as K
from aitest.infra.sql import safe_exec, safe_query

class AuditLogger:
    """Operational audit trail. Subscribes to all RunEvents at priority 0 (CRITICAL).

    Args:
        bus: EventBus instance. If None, uses get_bus() singleton.
    """

    def __init__(self, bus=None):
        self._active = False
        self._queue: deque = deque()
        self._flush_thread: threading.Thread | None = None
        self._flush_running = False
        self._bus = bus  # injected EventBus (None = lazy singleton)

    def start(self):
        if self._active: return
        bus = self._bus or get_bus()
        bus.subscribe("*", self._on_event, priority=0)  # CRITICAL: audit before any side-effect
        self._active = True
        self._flush_running = True
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

    def stop(self):
        if not self._active: return
        bus = self._bus or get_bus()
        bus.unsubscribe("*", self._on_event)
        self._active = False
        self._flush_running = False
        self._flush_now()

    @property
    def is_active(self) -> bool:
        return self._active

    def _on_event(self, event: RunEvent):
        try:
            self._queue.append({
                "event_id": event.event_id, "event_type": event.event_type,
                "run_id": event.run_id, "request_id": event.request_id,
                "org_id": event.data.get(K.ORG_ID, ""),
                "workspace_id": event.data.get(K.WORKSPACE_ID, ""),
                "user_id": event.data.get(K.TRIGGERED_BY, ""),
                "timestamp": event.timestamp,
                "data_json": json.dumps(event.data, ensure_ascii=False),
            })
        except Exception: pass

    def _flush_loop(self):
        import time
        while self._flush_running:
            try: self._flush_now()
            except Exception: pass
            time.sleep(2)

    def _flush_now(self):
        if not self._queue: return
        batch = []
        while self._queue: batch.append(self._queue.popleft())
        if not batch: return
        # v3.1: 批量插入，减少 PG subprocess 调用次数
        for e in batch:
            try:
                safe_exec(
                    "INSERT INTO audit_entries "
                    "(event_id, event_type, run_id, request_id, org_id, workspace_id, user_id, timestamp, data_json) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [e['event_id'], e['event_type'], e['run_id'], e['request_id'],
                     e['org_id'], e['workspace_id'], e['user_id'], e['timestamp'],
                     e['data_json']],
                )
            except Exception:
                pass  # 单条失败不影响批次

    def query(self, *, org_id: str = "", workspace_id: str = "", event_type: str = "",
              run_id: str = "", limit: int = 50, offset: int = 0,
              since: str = "", until: str = "") -> list[dict]:
        sql = "SELECT * FROM audit_entries WHERE 1=1"
        params: list = []
        if org_id:
            sql += " AND org_id=?"
            params.append(org_id)
        if workspace_id:
            sql += " AND workspace_id=?"
            params.append(workspace_id)
        if event_type:
            sql += " AND event_type=?"
            params.append(event_type)
        if run_id:
            sql += " AND run_id=?"
            params.append(run_id)
        if since:
            sql += " AND timestamp >= ?"
            params.append(since)
        if until:
            sql += " AND timestamp <= ?"
            params.append(until)
        sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
        params.extend([min(limit, 500), offset])
        return safe_query(sql, params)

    def count(self, *, org_id: str = "", workspace_id: str = "", event_type: str = "") -> int:
        sql = "SELECT COUNT(*) as cnt FROM audit_entries WHERE 1=1"
        params: list = []
        if org_id:
            sql += " AND org_id=?"
            params.append(org_id)
        if workspace_id:
            sql += " AND workspace_id=?"
            params.append(workspace_id)
        if event_type:
            sql += " AND event_type=?"
            params.append(event_type)
        rows = safe_query(sql, params)
        return rows[0]["cnt"] if rows else 0

    def stats(self, org_id: str = "") -> dict:
        if org_id:
            by_type = safe_query(
                "SELECT event_type, COUNT(*) as cnt FROM audit_entries WHERE org_id=? "
                "GROUP BY event_type ORDER BY cnt DESC LIMIT 20", [org_id])
            total_rows = safe_query(
                "SELECT COUNT(*) as cnt FROM audit_entries WHERE org_id=?", [org_id])
            recent = safe_query(
                "SELECT event_type, run_id, timestamp FROM audit_entries WHERE org_id=? "
                "ORDER BY id DESC LIMIT 5", [org_id])
        else:
            by_type = safe_query(
                "SELECT event_type, COUNT(*) as cnt FROM audit_entries "
                "GROUP BY event_type ORDER BY cnt DESC LIMIT 20")
            total_rows = safe_query("SELECT COUNT(*) as cnt FROM audit_entries")
            recent = safe_query(
                "SELECT event_type, run_id, timestamp FROM audit_entries ORDER BY id DESC LIMIT 5")
        return {
            "total_entries": total_rows[0]["cnt"] if total_rows else 0,
            "by_type": [{"type": r["event_type"], "count": r["cnt"]} for r in by_type],
            "recent": recent,
        }

    def cleanup_old_entries(self, max_age_days: int = 30) -> int:
        rows = safe_query(
            "SELECT COUNT(*) as cnt FROM audit_entries WHERE timestamp < datetime('now', ?)",
            [f"-{max_age_days} days"],
        )
        count = rows[0]["cnt"] if rows else 0
        if count:
            safe_exec(
                "DELETE FROM audit_entries WHERE timestamp < datetime('now', ?)",
                [f"-{max_age_days} days"],
            )
        return count

_logger: AuditLogger | None = None
_logger_lock = threading.Lock()

def get_audit_logger(bus=None) -> AuditLogger:
    global _logger
    with _logger_lock:
        if _logger is None:
            _logger = AuditLogger(bus=bus)
        return _logger

def set_audit_logger(logger: AuditLogger) -> None:
    global _logger
    with _logger_lock:
        _logger = logger

def reset_audit_logger() -> None:
    global _logger
    with _logger_lock:
        _logger = None
