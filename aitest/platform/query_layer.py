"""
Query Layer — unified data query API. v3.1

v3.1: Uses parameterized queries via aitest.infra.sql (no more f-string SQL).

Usage:
    from aitest.platform.query_layer import RunQuery, BugQuery, AuditQuery

    runs = RunQuery().status("failed").module("equipment").since("30d").limit(10).run()
    bugs = BugQuery().module("equipment").severity("high").run()
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from aitest.infra.sql import safe_query


def _since_to_timestamp(since: str) -> str:
    """Convert '30d', '7d', '24h' to ISO timestamp."""
    now = datetime.now(timezone.utc)
    if since.endswith("d"):
        days = int(since[:-1])
        return (now - timedelta(days=days)).isoformat()
    elif since.endswith("h"):
        hours = int(since[:-1])
        return (now - timedelta(hours=hours)).isoformat()
    elif since.endswith("m"):
        minutes = int(since[:-1])
        return (now - timedelta(minutes=minutes)).isoformat()
    return since  # Assume ISO format


class _BaseQuery:
    """Base query builder with parameterized filters."""

    def __init__(self, table: str, order_by: str = "rowid DESC"):
        self._table = table
        self._wheres: list[str] = []
        self._params: list = []
        self._order_by: str = order_by
        self._limit_val: int = 50
        self._offset_val: int = 0

    def _add_where(self, clause: str, param=None):
        self._wheres.append(clause)
        if param is not None:
            self._params.append(param)
        return self

    def limit(self, n: int):
        self._limit_val = min(n, 500)
        return self

    def offset(self, n: int):
        self._offset_val = n
        return self

    def order_by(self, clause: str):
        self._order_by = clause
        return self

    def _build(self) -> tuple[str, list]:
        where = " AND ".join(self._wheres) if self._wheres else "1=1"
        sql = (
            f"SELECT * FROM {self._table} "
            f"WHERE {where} "
            f"ORDER BY {self._order_by} "
            f"LIMIT ? OFFSET ?"
        )
        params = self._params + [self._limit_val, self._offset_val]
        return sql, params

    def run(self) -> list[dict]:
        sql, params = self._build()
        return safe_query(sql, params)

    def count(self) -> int:
        where = " AND ".join(self._wheres) if self._wheres else "1=1"
        sql = f"SELECT COUNT(*) as cnt FROM {self._table} WHERE {where}"
        rows = safe_query(sql, self._params)
        return rows[0]["cnt"] if rows else 0


class RunQuery(_BaseQuery):
    def __init__(self):
        super().__init__("runs", order_by="created_at DESC")

    def status(self, value: str):
        return self._add_where("status = ?", value)

    def module(self, value: str):
        return self._add_where("module = ?", value)

    def workspace(self, value: str):
        return self._add_where("workspace_id = ?", value)

    def org(self, value: str):
        return self._add_where("org_id = ?", value)

    def agent(self, value: str):
        return self._add_where("agent = ?", value)

    def since(self, value: str):
        ts = _since_to_timestamp(value)
        return self._add_where("created_at >= ?", ts)

    def failed(self):
        return self.status("failed")

    def completed(self):
        return self.status("completed")

    def running(self):
        return self.status("running")


class RunEventQuery(_BaseQuery):
    def __init__(self):
        super().__init__("run_events", order_by="timestamp ASC")

    def run_id(self, value: str):
        return self._add_where("run_id = ?", value)

    def event_type(self, value: str):
        return self._add_where("event_type = ?", value)

    def since(self, value: str):
        ts = _since_to_timestamp(value)
        return self._add_where("timestamp >= ?", ts)


class BugQuery(_BaseQuery):
    def __init__(self):
        super().__init__("bugs", order_by="date DESC, created_at DESC")

    def module(self, value: str):
        return self._add_where("module = ?", value)

    def severity(self, value: str):
        return self._add_where("severity = ?", value)

    def status(self, value: str):
        return self._add_where("status = ?", value)

    def open_only(self):
        return self.status("open")

    def fixed(self):
        return self.status("fixed")

    def since(self, value: str):
        ts = _since_to_timestamp(value)
        return self._add_where("date >= ?", ts[:10])


class AuditQuery(_BaseQuery):
    def __init__(self):
        super().__init__("audit_entries", order_by="id DESC")

    def event_type(self, value: str):
        return self._add_where("event_type = ?", value)

    def run_id(self, value: str):
        return self._add_where("run_id = ?", value)

    def org(self, value: str):
        return self._add_where("org_id = ?", value)

    def workspace(self, value: str):
        return self._add_where("workspace_id = ?", value)

    def since(self, value: str):
        ts = _since_to_timestamp(value)
        return self._add_where("timestamp >= ?", ts)


class TaskQuery(_BaseQuery):
    def __init__(self):
        super().__init__("tasks", order_by="created_at DESC")

    def status(self, value: str):
        return self._add_where("status = ?", value)

    def agent(self, value: str):
        return self._add_where("agent = ?", value)

    def module(self, value: str):
        return self._add_where("module = ?", value)

    def queued(self):
        return self.status("queued")

    def running(self):
        return self.status("running")

    def failed(self):
        return self.status("failed")


class LineageQuery(_BaseQuery):
    def __init__(self):
        super().__init__("artifact_lineage", order_by="timestamp ASC")

    def project(self, value: str):
        return self._add_where("project = ?", value)

    def module(self, value: str):
        return self._add_where("module = ?", value)

    def page(self, value: str):
        return self._add_where("page = ?", value)

    def run_id(self, value: str):
        return self._add_where("run_id = ?", value)

    def generated_by(self, value: str):
        return self._add_where("generated_by = ?", value)


class SessionQuery(_BaseQuery):
    def __init__(self):
        super().__init__("chat_sessions", order_by="updated_at DESC")

    def title(self, value: str):
        return self._add_where("title LIKE ?", f"%{value}%")

    def since(self, value: str):
        ts = _since_to_timestamp(value)
        return self._add_where("created_at >= ?", ts)


def get_system_stats() -> dict:
    """Get overall system statistics."""
    rows = safe_query(
        "SELECT "
        "(SELECT COUNT(*) FROM runs) as total_runs, "
        "(SELECT COUNT(*) FROM runs WHERE status='completed') as completed_runs, "
        "(SELECT COUNT(*) FROM runs WHERE status='failed') as failed_runs, "
        "(SELECT COUNT(*) FROM run_events) as total_events, "
        "(SELECT COUNT(*) FROM bugs) as total_bugs, "
        "(SELECT COUNT(*) FROM bugs WHERE status='open') as open_bugs, "
        "(SELECT COUNT(*) FROM tasks) as total_tasks, "
        "(SELECT COUNT(*) FROM tasks WHERE status='queued') as queued_tasks, "
        "(SELECT COUNT(*) FROM audit_entries) as total_audit, "
        "(SELECT COUNT(*) FROM artifact_lineage) as total_lineage, "
        "(SELECT COUNT(*) FROM chat_sessions) as total_sessions",
    )
    if not rows:
        return {}
    r = rows[0]
    r["success_rate"] = (
        round(r["completed_runs"] / r["total_runs"] * 100, 1)
        if r["total_runs"] > 0 else 0
    )
    return r


def get_failure_summary(days: int = 30, module: str = "") -> list[dict]:
    """Get failure summary by module/page."""
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    if module:
        return safe_query(
            "SELECT r.module, r.agent, r.error_message, COUNT(*) as failure_count "
            "FROM runs r WHERE r.status='failed' AND r.created_at >= ? AND r.module = ? "
            "GROUP BY r.module, r.agent, r.error_message ORDER BY failure_count DESC LIMIT 20",
            [since, module],
        )
    return safe_query(
        "SELECT r.module, r.agent, r.error_message, COUNT(*) as failure_count "
        "FROM runs r WHERE r.status='failed' AND r.created_at >= ? "
        "GROUP BY r.module, r.agent, r.error_message ORDER BY failure_count DESC LIMIT 20",
        [since],
    )
