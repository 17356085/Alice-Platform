"""Unified database — auto-selects backend based on environment.

Backends:
  - postgres: PostgreSQL via docker exec psql (default when Docker is running)
  - sqlite:   Zero-dependency local file (single-user mode)

Selection:
  1. AITEST_DB_BACKEND env var: "postgres" | "sqlite" | "auto" (default)
  2. Auto mode: try PostgreSQL first, fallback to SQLite

Usage (same interface regardless of backend):
    from aitest.infra.database import pg_exec, pg_query, init_db, get_backend

    pg_exec("INSERT INTO runs ...")
    rows = pg_query("SELECT * FROM runs LIMIT 5")
    print(get_backend())  # "postgres" or "sqlite"
"""

import os
import logging
import subprocess

logger = logging.getLogger("database")

_backend = None


def _detect_backend() -> str:
    """Detect which backend to use."""
    explicit = os.environ.get("AITEST_DB_BACKEND", "auto").lower()

    if explicit == "sqlite":
        return "sqlite"
    if explicit == "postgres":
        return "postgres"

    # Auto: try PostgreSQL first
    try:
        result = subprocess.run(
            ["docker", "exec", "aitest-pg", "pg_isready", "-U", "aitest"],
            capture_output=True,
            timeout=5,
        )
        if result.returncode == 0:
            return "postgres"
    except Exception:
        pass

    return "sqlite"


def get_backend() -> str:
    """Return active backend name."""
    global _backend
    if _backend is None:
        _backend = _detect_backend()
        logger.info("database_backend_selected", backend=_backend)
    return _backend


def _get_module():
    """Lazy-load the backend module."""
    backend = get_backend()
    if backend == "postgres":
        from aitest.infra import database_pg
        return database_pg
    else:
        from aitest.infra import database_sqlite
        return database_sqlite


def pg_exec(sql: str, **kwargs) -> str:
    """Execute SQL statement."""
    return _get_module().pg_exec(sql, **kwargs)


def pg_query(sql: str, **kwargs) -> list[dict]:
    """Execute SQL query, return list of dicts."""
    return _get_module().pg_query(sql, **kwargs)


def pg_exec_file(sql_file: str, **kwargs) -> str:
    """Execute SQL file."""
    return _get_module().pg_exec_file(sql_file, **kwargs)


def pg_table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    return _get_module().pg_table_exists(table_name)


def init_db():
    """Create all tables."""
    _get_module().init_db()
