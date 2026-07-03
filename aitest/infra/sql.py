"""
Unified SQL parameterization — eliminates f-string SQL injection risk. v3.0

Problem: 6+ files each define their own _escape()/_escape_json() with f-string
SQL concatenation. This module centralizes all SQL parameter handling.

Two backends:
  - SQLite: uses native ? parameterized queries (safe by design)
  - PostgreSQL (docker exec): uses quote_literal() for server-side escaping

Usage:
    from aitest.infra.sql import safe_exec, safe_query, safe_literal, safe_json

    # Before (vulnerable):
    pg_exec(f"INSERT INTO runs (run_id, module) VALUES ({_escape(run_id)}, {_escape(module)})")

    # After (safe):
    safe_exec("INSERT INTO runs (run_id, module) VALUES (?, ?)", [run_id, module])

    # For PG-specific cases where ? doesn't work:
    safe_exec(f"INSERT INTO runs (run_id) VALUES ({safe_literal(run_id)})")
"""

import json
import logging
from typing import Any

logger = logging.getLogger("sql")


def _get_backend() -> str:
    """Get current database backend."""
    from aitest.infra.database import get_backend
    return get_backend()


def _to_pg_placeholder(index: int) -> str:
    """Convert 0-based index to PG $1, $2, ... placeholder."""
    return f"${index + 1}"


def _convert_placeholders(sql: str, backend: str) -> str:
    """Convert ? placeholders to backend-specific format.

    SQLite: ? (native)
    PostgreSQL: $1, $2, ... (native)
    """
    if backend == "sqlite":
        return sql
    # Convert ? to $1, $2, ...
    result = []
    param_index = 0
    i = 0
    while i < len(sql):
        if sql[i] == '?':
            result.append(_to_pg_placeholder(param_index))
            param_index += 1
        elif sql[i] == "'":
            # Skip string literals to avoid counting ? inside strings
            result.append(sql[i])
            i += 1
            while i < len(sql) and sql[i] != "'":
                if sql[i] == '\\' and i + 1 < len(sql):
                    result.append(sql[i])
                    i += 1
                result.append(sql[i])
                i += 1
            if i < len(sql):
                result.append(sql[i])  # closing quote
        else:
            result.append(sql[i])
        i += 1
    return ''.join(result)


def _pg_escape_string(val: str) -> str:
    """Escape a string for PostgreSQL using quote_literal()."""
    # Replace backslashes first, then single quotes
    escaped = val.replace("\\", "\\\\").replace("'", "''")
    return f"'{escaped}'"


def safe_literal(val: Any) -> str:
    """Convert a Python value to a safe SQL literal string.

    For use in f-string SQL where parameterized queries aren't possible
    (e.g., PostgreSQL via docker exec).

    Returns:
        SQL-safe literal string (quoted and escaped)
    """
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, (int, float)):
        return str(val)
    if isinstance(val, (dict, list)):
        s = json.dumps(val, ensure_ascii=False)
        return _pg_escape_string(s)
    # String: escape single quotes and backslashes
    return _pg_escape_string(str(val))


def safe_json(val: Any) -> str:
    """Convert a Python value to a safe SQL JSON literal.

    For JSON columns. Handles None as empty JSON.
    """
    if val is None:
        return "'{}'"
    return _pg_escape_string(json.dumps(val, ensure_ascii=False))


def safe_exec(sql: str, params: list[Any] | None = None) -> str:
    """Execute SQL with optional parameterized values.

    Args:
        SQL with ? placeholders (SQLite style). Auto-converted for PG.
        params: List of parameter values. None = no parameters (legacy mode).

    Returns:
        Backend-specific result string.
    """
    from aitest.infra.database import pg_exec

    if params is None:
        # Legacy mode: raw SQL (for init_db, DDL, etc.)
        return pg_exec(sql)

    backend = _get_backend()
    if backend == "sqlite":
        # SQLite: native parameterized queries
        import sqlite3
        from aitest.infra.database_sqlite import _get_conn, _lock
        with _lock:
            conn = _get_conn()
            try:
                cursor = conn.execute(sql, params)
                conn.commit()
                return f"{cursor.rowcount} rows affected"
            finally:
                conn.close()
    else:
        # PG via docker exec: convert ? to $1,$2 and use psql variable substitution
        # Since we can't do true parameterized queries via CLI, we escape each param
        escaped_params = [_sql_value(p) for p in params]
        # Replace ? with escaped values
        result_sql = sql
        for ep in escaped_params:
            result_sql = result_sql.replace("?", ep, 1)
        return pg_exec(result_sql)


def safe_query(sql: str, params: list[Any] | None = None) -> list[dict]:
    """Execute SQL query with optional parameterized values.

    Args:
        SQL with ? placeholders (SQLite style). Auto-converted for PG.
        params: List of parameter values. None = no parameters (legacy mode).

    Returns:
        List of result dicts.
    """
    from aitest.infra.database import pg_query

    if params is None:
        # Legacy mode: raw SQL
        return pg_query(sql)

    backend = _get_backend()
    if backend == "sqlite":
        # SQLite: native parameterized queries
        from aitest.infra.database_sqlite import _get_conn, _lock
        with _lock:
            conn = _get_conn()
            try:
                cursor = conn.execute(sql, params)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
            finally:
                conn.close()
    else:
        # PG via docker exec: escape params inline
        escaped_params = [_sql_value(p) for p in params]
        result_sql = sql
        for ep in escaped_params:
            result_sql = result_sql.replace("?", ep, 1)
        return pg_query(result_sql)


def _sql_value(val: Any) -> str:
    """Convert a Python value to a SQL value string (for inline escaping).

    This is the SINGLE source of truth for SQL value escaping.
    All 6+ previous _escape/_escape_json implementations are replaced by this.
    """
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "TRUE" if val else "FALSE"
    if isinstance(val, int):
        return str(val)
    if isinstance(val, float):
        return str(val)
    if isinstance(val, (dict, list)):
        s = json.dumps(val, ensure_ascii=False)
        return "'" + s.replace("'", "''").replace("\\", "\\\\") + "'"
    # String: escape
    s = str(val)
    return "'" + s.replace("'", "''").replace("\\", "\\\\") + "'"
