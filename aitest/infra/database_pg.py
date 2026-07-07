"""PostgreSQL backend — native psycopg connection.

Replaces the old docker-exec-psql approach with direct TCP connection.
Same interface as database_sqlite.py: pg_exec(), pg_query(), init_db().

Usage:
    from aitest.infra.database import pg_exec, pg_query  # auto-selects backend
"""

import json
import logging
import os
import socket

logger = logging.getLogger("database.pg")

_conn_string = os.environ.get(
    "AITEST_DATABASE_URL",
    "postgresql://aitest:aitest@localhost:5432/aitest",
)


def _get_conn():
    """Create a new psycopg connection (autocommit, dict_row)."""
    import psycopg
    from psycopg.rows import dict_row
    return psycopg.connect(_conn_string, autocommit=True, row_factory=dict_row)


def pg_exec(sql: str, params: list | None = None, **kwargs) -> str:
    """Execute SQL statement. Returns row count info.

    Args:
        sql: SQL statement. May contain %s placeholders for parameterized queries.
        params: Optional parameter values for %s placeholders.
    """
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or [])
            return f"{cur.rowcount} rows affected"


def pg_query(sql: str, params: list | None = None, **kwargs) -> list[dict]:
    """Execute SQL query and return results as list of dicts.

    Args:
        sql: SQL query. May contain %s placeholders for parameterized queries.
        params: Optional parameter values for %s placeholders.
    """
    with _get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or [])
            return cur.fetchall()


def pg_exec_file(sql_file: str, **kwargs) -> str:
    """Execute SQL file."""
    with open(sql_file, encoding="utf-8") as f:
        sql = f.read()
    with _get_conn() as conn:
        conn.execute(sql)
    return "OK"


def pg_table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    rows = pg_query(
        "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname='public' AND tablename=%s)",
        [table_name],
    )
    return rows[0].get("exists", False) if rows else False


def init_db():
    """Create all tables from DDL file."""
    from pathlib import Path
    ddl_file = Path(__file__).parent.parent.parent / "create_tables.sql"
    if ddl_file.exists():
        pg_exec_file(str(ddl_file))
        logger.info("pg_database_initialized")
    else:
        logger.warning("create_tables.sql not found, skipping init_db")


def check_connection() -> bool:
    """Quick TCP probe to verify PG is reachable."""
    try:
        with socket.create_connection(("localhost", 5432), timeout=3):
            return True
    except OSError:
        return False
