"""PostgreSQL backend — via docker exec psql.

Same interface as database_sqlite.py: pg_exec(), pg_query(), init_db().

Note: This uses docker exec psql because asyncpg/psycopg2 can't connect
to Docker PG on Windows. When deploying on Linux/Mac, replace subprocess
calls with native async SQLAlchemy:

    from sqlalchemy.ext.asyncio import create_async_engine
    engine = create_async_engine(DATABASE_URL)
    async with engine.connect() as conn:
        result = await conn.execute(text(sql))
"""

import os
import json
import logging
import subprocess

logger = logging.getLogger("database.pg")

DATABASE_URL = os.environ.get(
    "AITEST_DATABASE_URL",
    "postgresql+asyncpg://aitest:aitest@localhost:5432/aitest",
)


def pg_exec(sql: str, database: str = "aitest", user: str = "aitest") -> str:
    """Execute SQL via docker exec psql. Returns stdout."""
    result = subprocess.run(
        ["docker", "exec", "aitest-pg", "psql", "-U", user, "-d", database, "-c", sql],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"psql error: {result.stderr.strip()}")
    return result.stdout


def pg_query(sql: str, database: str = "aitest", user: str = "aitest") -> list[dict]:
    """Execute SQL query and return results as list of dicts."""
    json_sql = f"SELECT COALESCE(json_agg(t), '[]'::json) FROM ({sql}) t"
    result = subprocess.run(
        ["docker", "exec", "aitest-pg", "psql", "-t", "-A", "-U", user, "-d", database, "-c", json_sql],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"psql error: {result.stderr.strip()}")

    raw = (result.stdout or "").strip()
    raw = raw.replace("+\n", "").replace("\n", "")
    if "(" in raw and "rows)" in raw:
        raw = raw[:raw.rfind("(")].strip()

    if raw.startswith("["):
        return json.loads(raw)
    return []


def pg_exec_file(sql_file: str, database: str = "aitest", user: str = "aitest") -> str:
    """Execute SQL file via docker exec psql."""
    result = subprocess.run(
        ["docker", "exec", "-i", "aitest-pg", "psql", "-U", user, "-d", database],
        input=open(sql_file, encoding="utf-8").read(),
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"psql error: {result.stderr.strip()}")
    return result.stdout


def pg_table_exists(table_name: str) -> bool:
    """Check if a table exists."""
    result = pg_query(
        f"SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname='public' AND tablename='{table_name}')"
    )
    return result[0].get("exists", False) if result else False


def init_db():
    """Create all tables from DDL file."""
    from pathlib import Path
    ddl_file = Path(__file__).parent.parent.parent / "create_tables.sql"
    if ddl_file.exists():
        pg_exec_file(str(ddl_file))
        logger.info("pg_database_initialized")
    else:
        logger.warning("create_tables.sql not found, skipping init_db")
