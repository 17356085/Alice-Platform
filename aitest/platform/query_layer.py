"""
Query Layer — unified data query API.

Abstracts SQL away from callers. Each query builder generates SQL
internally and delegates to database.pg_query().

Usage:
    from aitest.platform.query_layer import RunQuery, BugQuery, AuditQuery

    # Fluent API
    runs = RunQuery.status("failed").module("equipment").since("30d").limit(10).run()

    # Simple queries
    bugs = BugQuery.module("equipment").severity("high").run()
    events = AuditQuery.event_type("run.completed").limit(50).run()
"""

import json
from datetime import datetime, timezone, timedelta
from typing import Optional

from aitest.infra.database import pg_query


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
    """Base query builder with common filters."""

    def __init__(self, table: str, order_by: str = "rowid DESC"):
        self._table = table
        self._wheres: list[str] = []
        self._order_by: str = order_by
        self._limit_val: int = 50
        self._offset_val: int = 0

    def _add_where(self, clause: str):
        self._wheres.append(clause)
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

    def _build_sql(self, select: str = "*") -> str:
        where = " AND ".join(self._wheres) if self._wheres else "1=1"
        return (
            f"SELECT {select} FROM {self._table} "
            f"WHERE {where} "
            f"ORDER BY {self._order_by} "
            f"LIMIT {self._limit_val} OFFSET {self._offset_val}"
        )

    def run(self) -> list[dict]:
        return pg_query(self._build_sql())

    def count(self) -> int:
        rows = pg_query(self._build_sql(select="COUNT(*) as cnt"))
        return rows[0]["cnt"] if rows else 0


class RunQuery(_BaseQuery):
    """Query runs table."""

    def __init__(self):
        super().__init__("runs", order_by="created_at DESC")

    def status(self, value: str):
        return self._add_where(f"status = '{value}'")

    def module(self, value: str):
        return self._add_where(f"module = '{value}'")

    def workspace(self, value: str):
        return self._add_where(f"workspace_id = '{value}'")

    def org(self, value: str):
        return self._add_where(f"org_id = '{value}'")

    def agent(self, value: str):
        return self._add_where(f"agent = '{value}'")

    def since(self, value: str):
        ts = _since_to_timestamp(value)
        return self._add_where(f"created_at >= '{ts}'")

    def failed(self):
        return self.status("failed")

    def completed(self):
        return self.status("completed")

    def running(self):
        return self.status("running")


class RunEventQuery(_BaseQuery):
    """Query run_events table."""

    def __init__(self):
        super().__init__("run_events", order_by="timestamp ASC")

    def run_id(self, value: str):
        return self._add_where(f"run_id = '{value}'")

    def event_type(self, value: str):
        return self._add_where(f"event_type = '{value}'")

    def since(self, value: str):
        ts = _since_to_timestamp(value)
        return self._add_where(f"timestamp >= '{ts}'")


class BugQuery(_BaseQuery):
    """Query bugs table."""

    def __init__(self):
        super().__init__("bugs", order_by="date DESC, created_at DESC")

    def module(self, value: str):
        return self._add_where(f"module = '{value}'")

    def severity(self, value: str):
        return self._add_where(f"severity = '{value}'")

    def status(self, value: str):
        return self._add_where(f"status = '{value}'")

    def open_only(self):
        return self.status("open")

    def fixed(self):
        return self.status("fixed")

    def since(self, value: str):
        ts = _since_to_timestamp(value)
        return self._add_where(f"date >= '{ts[:10]}'")  # date is YYYY-MM-DD


class AuditQuery(_BaseQuery):
    """Query audit_entries table."""

    def __init__(self):
        super().__init__("audit_entries", order_by="id DESC")

    def event_type(self, value: str):
        return self._add_where(f"event_type = '{value}'")

    def run_id(self, value: str):
        return self._add_where(f"run_id = '{value}'")

    def org(self, value: str):
        return self._add_where(f"org_id = '{value}'")

    def workspace(self, value: str):
        return self._add_where(f"workspace_id = '{value}'")

    def since(self, value: str):
        ts = _since_to_timestamp(value)
        return self._add_where(f"timestamp >= '{ts}'")


class TaskQuery(_BaseQuery):
    """Query tasks table."""

    def __init__(self):
        super().__init__("tasks", order_by="created_at DESC")

    def status(self, value: str):
        return self._add_where(f"status = '{value}'")

    def agent(self, value: str):
        return self._add_where(f"agent = '{value}'")

    def module(self, value: str):
        return self._add_where(f"module = '{value}'")

    def queued(self):
        return self.status("queued")

    def running(self):
        return self.status("running")

    def failed(self):
        return self.status("failed")


class LineageQuery(_BaseQuery):
    """Query artifact_lineage table."""

    def __init__(self):
        super().__init__("artifact_lineage", order_by="timestamp ASC")

    def project(self, value: str):
        return self._add_where(f"project = '{value}'")

    def module(self, value: str):
        return self._add_where(f"module = '{value}'")

    def page(self, value: str):
        return self._add_where(f"page = '{value}'")

    def run_id(self, value: str):
        return self._add_where(f"run_id = '{value}'")

    def generated_by(self, value: str):
        return self._add_where(f"generated_by = '{value}'")


class SessionQuery(_BaseQuery):
    """Query chat_sessions table."""

    def __init__(self):
        super().__init__("chat_sessions", order_by="updated_at DESC")

    def title(self, value: str):
        return self._add_where(f"title LIKE '%{value}%'")

    def since(self, value: str):
        ts = _since_to_timestamp(value)
        return self._add_where(f"created_at >= '{ts}'")


# ── Aggregate queries ────────────────────────────────────────────────

def get_system_stats() -> dict:
    """Get overall system statistics."""
    rows = pg_query("""
        SELECT
            (SELECT COUNT(*) FROM runs) as total_runs,
            (SELECT COUNT(*) FROM runs WHERE status='completed') as completed_runs,
            (SELECT COUNT(*) FROM runs WHERE status='failed') as failed_runs,
            (SELECT COUNT(*) FROM run_events) as total_events,
            (SELECT COUNT(*) FROM bugs) as total_bugs,
            (SELECT COUNT(*) FROM bugs WHERE status='open') as open_bugs,
            (SELECT COUNT(*) FROM tasks) as total_tasks,
            (SELECT COUNT(*) FROM tasks WHERE status='queued') as queued_tasks,
            (SELECT COUNT(*) FROM audit_entries) as total_audit,
            (SELECT COUNT(*) FROM artifact_lineage) as total_lineage,
            (SELECT COUNT(*) FROM chat_sessions) as total_sessions
    """)
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
    where = f"WHERE r.status='failed' AND r.created_at >= '{since}'"
    if module:
        where += f" AND r.module = '{module}'"

    return pg_query(f"""
        SELECT r.module, r.agent, r.error_message, COUNT(*) as failure_count
        FROM runs r
        {where}
        GROUP BY r.module, r.agent, r.error_message
        ORDER BY failure_count DESC
        LIMIT 20
    """)
