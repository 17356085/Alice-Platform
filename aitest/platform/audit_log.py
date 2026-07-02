"""
Audit Log — operational audit trail. v3.0
PostgreSQL persistence via docker exec psql.
"""

import json
import threading
from datetime import datetime, timezone, timedelta
from collections import deque
from .event_bus import get_bus
from .run_event import RunEvent
from aitest.infra.database import pg_exec, pg_query

def _escape(val):
    if val is None: return "NULL"
    return "'" + str(val).replace("'", "''") + "'"

def _escape_json(val):
    if val is None: return "'{}'"
    return "'" + json.dumps(val, ensure_ascii=False).replace("'", "''") + "'"

class AuditLogger:
    def __init__(self):
        self._active = False
        self._queue: deque = deque()
        self._flush_thread: threading.Thread | None = None
        self._flush_running = False

    def start(self):
        if self._active: return
        bus = get_bus()
        bus.subscribe("*", self._on_event)
        self._active = True
        self._flush_running = True
        self._flush_thread = threading.Thread(target=self._flush_loop, daemon=True)
        self._flush_thread.start()

    def stop(self):
        if not self._active: return
        bus = get_bus()
        bus.unsubscribe("*", self._on_event)
        self._active = False
        self._flush_running = False
        self._flush_now()

    @property
    def is_active(self) -> bool:
        return self._active

    def _on_event(self, event: RunEvent):
        try:
            self._queue.append({"event_id": event.event_id, "event_type": event.event_type, "run_id": event.run_id, "request_id": event.request_id, "org_id": event.data.get("org_id", ""), "workspace_id": event.data.get("workspace_id", ""), "user_id": event.data.get("triggered_by", ""), "timestamp": event.timestamp, "data_json": json.dumps(event.data, ensure_ascii=False)})
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
        values = []
        for e in batch:
            values.append(f"({_escape(e['event_id'])}, {_escape(e['event_type'])}, {_escape(e['run_id'])}, {_escape(e['request_id'])}, {_escape(e['org_id'])}, {_escape(e['workspace_id'])}, {_escape(e['user_id'])}, {_escape(e['timestamp'])}, {_escape_json(json.loads(e['data_json']))})")
        pg_exec(f"INSERT INTO audit_entries (event_id, event_type, run_id, request_id, org_id, workspace_id, user_id, timestamp, data_json) VALUES {', '.join(values)}")

    def query(self, *, org_id: str = "", workspace_id: str = "", event_type: str = "", run_id: str = "", limit: int = 50, offset: int = 0, since: str = "", until: str = "") -> list[dict]:
        where = ["1=1"]
        if org_id: where.append(f"org_id={_escape(org_id)}")
        if workspace_id: where.append(f"workspace_id={_escape(workspace_id)}")
        if event_type: where.append(f"event_type={_escape(event_type)}")
        if run_id: where.append(f"run_id={_escape(run_id)}")
        if since: where.append(f"timestamp >= {_escape(since)}")
        if until: where.append(f"timestamp <= {_escape(until)}")
        return pg_query(f"SELECT * FROM audit_entries WHERE {' AND '.join(where)} ORDER BY id DESC LIMIT {min(limit, 500)} OFFSET {offset}")

    def count(self, *, org_id: str = "", workspace_id: str = "", event_type: str = "") -> int:
        where = ["1=1"]
        if org_id: where.append(f"org_id={_escape(org_id)}")
        if workspace_id: where.append(f"workspace_id={_escape(workspace_id)}")
        if event_type: where.append(f"event_type={_escape(event_type)}")
        rows = pg_query(f"SELECT COUNT(*) as cnt FROM audit_entries WHERE {' AND '.join(where)}")
        return rows[0]["cnt"] if rows else 0

    def stats(self, org_id: str = "") -> dict:
        where = f"WHERE org_id={_escape(org_id)}" if org_id else ""
        by_type = pg_query(f"SELECT event_type, COUNT(*) as cnt FROM audit_entries {where} GROUP BY event_type ORDER BY cnt DESC LIMIT 20")
        total_rows = pg_query(f"SELECT COUNT(*) as cnt FROM audit_entries {where}")
        recent = pg_query(f"SELECT event_type, run_id, timestamp FROM audit_entries {where} ORDER BY id DESC LIMIT 5")
        return {"total_entries": total_rows[0]["cnt"] if total_rows else 0, "by_type": [{"type": r["event_type"], "count": r["cnt"]} for r in by_type], "recent": recent}

    def cleanup_old_entries(self, max_age_days: int = 30) -> int:
        rows = pg_query(f"SELECT COUNT(*) as cnt FROM audit_entries WHERE timestamp < NOW() - INTERVAL '{max_age_days} days'")
        count = rows[0]["cnt"] if rows else 0
        if count: pg_exec(f"DELETE FROM audit_entries WHERE timestamp < NOW() - INTERVAL '{max_age_days} days'")
        return count

_logger: AuditLogger | None = None
_logger_lock = threading.Lock()
def get_audit_logger() -> AuditLogger:
    global _logger
    with _logger_lock:
        if _logger is None: _logger = AuditLogger()
        return _logger
