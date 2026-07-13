"""
Audit Log — operational audit trail. v3.2

v3.1: Uses parameterized queries via aitest.infra.sql (no more f-string SQL).
v3.2: Synchronous PG writes — eliminates 2s flush window data loss risk.
      Audit entries are written immediately on event, no deque buffering.
"""

__all__ = ["AuditLogger", "get_audit_logger", "set_audit_logger", "reset_audit_logger"]

import json
import hashlib
import threading
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from .event_bus import get_bus
from .run_event import RunEvent, EventDataKey as K
from aitest.infra.sql import safe_exec, safe_query


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


def _normalize_entry(row: dict) -> dict:
    entry = dict(row)
    data = _decode_json_field(entry.get("data_json", {}), {})
    entry["data"] = data
    if K.REPLAY_SESSION_ID in data:
        entry["replay_session_id"] = data.get(K.REPLAY_SESSION_ID, "")
    return entry

class AuditLogger:
    """Operational audit trail. Subscribes to all RunEvents at priority 0 (CRITICAL).

    v3.2: Synchronous writes — each event writes to PG immediately.
    No deque, no flush thread, no data loss on crash.

    Args:
        bus: EventBus instance. If None, uses get_bus() singleton.
    """

    def __init__(self, bus=None, db_path: str | Path | None = None):
        self._active = False
        self._append_lock = threading.Lock()
        self._bus = bus  # injected EventBus (None = lazy singleton)
        if db_path is not None:
            from aitest.infra import database as _db
            from aitest.infra import database_sqlite as _sqlite
            _db._backend = "sqlite"
            _sqlite._DB_PATH = Path(db_path)
            _sqlite._DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            safe_exec("SELECT 1")
        self._ensure_integrity_columns()

    def _ensure_integrity_columns(self) -> None:
        """Migrate older audit tables to the hash-chain contract."""
        try:
            from aitest.infra.database import get_backend
            if get_backend() == "sqlite":
                columns = {row["name"] for row in safe_query("PRAGMA table_info(audit_entries)")}
                for name in ("prev_hash", "entry_hash"):
                    if name not in columns:
                        safe_exec(f"ALTER TABLE audit_entries ADD COLUMN {name} TEXT NOT NULL DEFAULT ''")
            else:
                safe_exec("ALTER TABLE audit_entries ADD COLUMN IF NOT EXISTS prev_hash TEXT NOT NULL DEFAULT ''")
                safe_exec("ALTER TABLE audit_entries ADD COLUMN IF NOT EXISTS entry_hash TEXT NOT NULL DEFAULT ''")
        except Exception:
            # The main schema initializer may run after logger construction.
            pass

    def start(self):
        if self._active: return
        bus = self._bus or get_bus()
        bus.subscribe("*", self._on_event, priority=0)  # CRITICAL: audit before any side-effect
        self._active = True

    def stop(self):
        if not self._active: return
        bus = self._bus or get_bus()
        bus.unsubscribe("*", self._on_event)
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def _on_event(self, event: RunEvent):
        """Write audit entry synchronously to PG. No buffering, no data loss."""
        try:
            self._append_entry({
                "event_id": event.event_id,
                "event_type": event.event_type,
                "run_id": event.run_id,
                "request_id": event.request_id,
                "org_id": event.data.get(K.ORG_ID, ""),
                "workspace_id": event.data.get(K.WORKSPACE_ID, ""),
                "user_id": event.data.get(K.TRIGGERED_BY, ""),
                "timestamp": event.timestamp,
                "data_json": json.dumps(event.data, ensure_ascii=False),
            })
        except Exception:
            pass  # Audit failure must not break execution

    def record_action(
        self,
        *,
        action: str,
        actor: str = "anonymous",
        org_id: str = "",
        resource_type: str = "",
        resource_id: str = "",
        request_id: str = "",
        outcome: str = "success",
        metadata: dict | None = None,
    ) -> None:
        """Persist a control-plane action in the same append-only audit table."""
        data = {
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "outcome": outcome,
            **(metadata or {}),
        }
        try:
            self._append_entry({
                "event_id": f"control_{uuid.uuid4().hex}",
                "event_type": "control.action",
                "run_id": "",
                "request_id": request_id,
                "org_id": org_id,
                "workspace_id": "",
                "user_id": actor,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "data_json": json.dumps(data, ensure_ascii=False),
            })
        except Exception:
            # Audit must not make a control-plane request fail.
            pass

    def _append_entry(self, fields: dict) -> None:
        """Append an entry with a tamper-evident previous/current hash pair."""
        with self._append_lock:
            try:
                previous = safe_query("SELECT entry_hash FROM audit_entries ORDER BY id DESC LIMIT 1")
            except Exception:
                # Keeps audit recording observable even while the schema is being initialized.
                previous = []
            prev_hash = (previous[0].get("entry_hash") or "") if previous else ""
            canonical = json.dumps({**fields, "prev_hash": prev_hash}, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
            entry_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            if fields["event_type"] == "control.action":
                # Keep the established control-audit parameter contract; run/workspace
                # remain empty via schema defaults while still participating in the hash.
                safe_exec(
                    "INSERT INTO audit_entries "
                    "(event_id, event_type, request_id, org_id, user_id, timestamp, data_json, prev_hash, entry_hash) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [fields["event_id"], fields["event_type"], fields["request_id"], fields["org_id"],
                     fields["user_id"], fields["timestamp"], fields["data_json"], prev_hash, entry_hash],
                )
            else:
                safe_exec(
                    "INSERT INTO audit_entries "
                    "(event_id, event_type, run_id, request_id, org_id, workspace_id, user_id, timestamp, data_json, prev_hash, entry_hash) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    [fields["event_id"], fields["event_type"], fields["run_id"], fields["request_id"],
                     fields["org_id"], fields["workspace_id"], fields["user_id"], fields["timestamp"],
                     fields["data_json"], prev_hash, entry_hash],
                )

    def verify_integrity(self) -> dict:
        """Verify the append-only hash chain, returning an auditable result."""
        rows = safe_query("SELECT * FROM audit_entries ORDER BY id ASC")
        previous = ""
        for row in rows:
            if not row.get("entry_hash"):
                return {"valid": False, "checked": row.get("id", 0), "error": "legacy entry has no hash"}
            fields = {key: row.get(key, "") for key in (
                "event_id", "event_type", "run_id", "request_id", "org_id", "workspace_id",
                "user_id", "timestamp", "data_json",
            )}
            expected = hashlib.sha256(json.dumps({**fields, "prev_hash": previous}, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")).hexdigest()
            if row.get("prev_hash", "") != previous or row.get("entry_hash") != expected:
                return {"valid": False, "checked": row.get("id", 0), "error": "audit hash chain mismatch"}
            previous = row["entry_hash"]
        return {"valid": True, "checked": len(rows), "last_hash": previous}

    def archive_old_entries(self, destination: str | Path, max_age_days: int = 30) -> int:
        """Write old entries to an integrity-stamped JSONL archive, then delete them."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).isoformat()
        rows = safe_query("SELECT * FROM audit_entries WHERE timestamp < ? ORDER BY id ASC", [cutoff])
        if not rows:
            return 0
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
        archive_hash = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        destination.write_text(payload, encoding="utf-8")
        destination.with_suffix(destination.suffix + ".sha256").write_text(archive_hash, encoding="ascii")
        safe_exec("DELETE FROM audit_entries WHERE timestamp < ?", [cutoff])
        return len(rows)

    def query(self, *, org_id: str = "", workspace_id: str = "", event_type: str = "",
              run_id: str = "", replay_session_id: str = "", limit: int = 50, offset: int = 0,
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
        rows = safe_query(sql, params)
        entries = [_normalize_entry(row) for row in rows]
        if replay_session_id:
            entries = [
                entry for entry in entries
                if entry.get("data", {}).get(K.REPLAY_SESSION_ID, "") == replay_session_id
            ]
        return entries

    def count(self, *, org_id: str = "", workspace_id: str = "", event_type: str = "",
              run_id: str = "", replay_session_id: str = "") -> int:
        if replay_session_id:
            return len(self.query(
                org_id=org_id,
                workspace_id=workspace_id,
                event_type=event_type,
                run_id=run_id,
                replay_session_id=replay_session_id,
                limit=500,
                offset=0,
            ))
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
        if run_id:
            sql += " AND run_id=?"
            params.append(run_id)
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
