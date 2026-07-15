"""Compatibility DB-API session for resource stores that use SQL directly.

Newer resource stores use SQLAlchemy, while MCP Server persistence predates
that layer and expects a small ``execute/commit`` session.  Keeping this
adapter local avoids introducing another persistence abstraction.

Moved: 2026-07-14 from platform.db to infra.db_session (Step 1.1b - eliminate mcp → platform dependency)
"""

from __future__ import annotations

from pathlib import Path

from aitest.infra import database


def get_session():
    """Return a DB-API connection for the configured platform backend."""
    backend = database.get_backend()
    if backend == "sqlite":
        from aitest.infra.database_sqlite import _get_conn
        connection = _get_conn()
        _ensure_sqlite_mcp_schema(connection)
        return connection

    from aitest.infra.database_pg import _get_conn
    return _get_conn()


def _ensure_sqlite_mcp_schema(connection) -> None:
    """Apply the idempotent MCP migration for local SQLite sessions."""
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='mcp_servers'"
    ).fetchone()
    if exists:
        return
    migration = Path(__file__).resolve().parents[2] / "migrations" / "017_mcp_servers_sqlite.sql"
    connection.executescript(migration.read_text(encoding="utf-8"))
    connection.commit()
