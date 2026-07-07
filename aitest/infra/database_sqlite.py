"""SQLite backend — zero-dependency local database for single-user mode.

Same interface as database_pg.py: pg_exec(), pg_query(), init_db().

Usage:
    from aitest.infra.database import pg_exec, pg_query  # auto-selects backend
"""

import json
import sqlite3
import threading
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger("database.sqlite")

_DB_PATH: Optional[Path] = None
_lock = threading.Lock()


def _get_db_path() -> Path:
    global _DB_PATH
    if _DB_PATH is None:
        from aitest.infra.paths import get_workstudy
        _DB_PATH = get_workstudy() / "governance" / ".data" / "aitest.db"
        _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    return _DB_PATH


def _get_conn() -> sqlite3.Connection:
    db_path = _get_db_path()
    new_db = not db_path.exists()
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    if new_db:
        ddl_file = Path(__file__).parent.parent.parent / "create_tables_sqlite.sql"
        if ddl_file.exists():
            conn.executescript(ddl_file.read_text(encoding="utf-8"))
            conn.commit()
    return conn


def pg_exec(sql: str, params: list | None = None, **kwargs) -> str:
    """Execute SQL statement. Returns row count info.

    Args:
        sql: SQL statement. May contain ? placeholders for parameterized queries.
        params: Optional parameter values for ? placeholders.
    """
    with _lock:
        conn = _get_conn()
        try:
            cursor = conn.execute(sql, params or [])
            conn.commit()
            return f"{cursor.rowcount} rows affected"
        finally:
            conn.close()


def pg_query(sql: str, params: list | None = None, **kwargs) -> list[dict]:
    """Execute SQL query and return results as list of dicts.

    Args:
        sql: SQL query. May contain ? placeholders for parameterized queries.
        params: Optional parameter values for ? placeholders.
    """
    with _lock:
        conn = _get_conn()
        try:
            cursor = conn.execute(sql, params or [])
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()


def pg_exec_file(sql_file: str, **kwargs) -> str:
    """Execute SQL file."""
    with open(sql_file, encoding="utf-8") as f:
        sql = f.read()
    with _lock:
        conn = _get_conn()
        try:
            conn.executescript(sql)
            conn.commit()
            return "OK"
        finally:
            conn.close()


def pg_table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    rows = pg_query(
        f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'"
    )
    return len(rows) > 0


def init_db():
    """Create all tables from DDL file."""
    from pathlib import Path
    ddl_file = Path(__file__).parent.parent.parent / "create_tables_sqlite.sql"
    if ddl_file.exists():
        pg_exec_file(str(ddl_file))
        logger.info("sqlite_database_initialized", path=str(_get_db_path()))
    else:
        logger.warning("create_tables_sqlite.sql not found, skipping init_db")
