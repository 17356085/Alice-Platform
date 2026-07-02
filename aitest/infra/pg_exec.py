"""PostgreSQL executor — uses docker exec psql as transport.

Workaround for Windows Docker Desktop networking issue where Python async
drivers (asyncpg, psycopg2, psycopg3) cannot authenticate to Docker PG
despite pg_hba.conf having trust authentication.

Usage:
    from aitest.infra.pg_exec import pg_exec, pg_query

    # Execute DDL/DML
    pg_exec("CREATE TABLE test (id SERIAL PRIMARY KEY)")

    # Query and get results
    rows = pg_query("SELECT * FROM runs LIMIT 5")
"""

import json
import subprocess
from typing import Any


def pg_exec(sql: str, database: str = "aitest", user: str = "aitest") -> str:
    """Execute SQL via docker exec psql. Returns stdout."""
    result = subprocess.run(
        ["docker", "exec", "aitest-pg", "psql", "-U", user, "-d", database, "-c", sql],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(f"psql error: {result.stderr}")
    return result.stdout


def pg_query(sql: str, database: str = "aitest", user: str = "aitest") -> list[dict]:
    """Execute SQL query and return results as list of dicts."""
    # Use JSON output format
    json_sql = f"SELECT json_agg(t) FROM ({sql}) t"
    output = pg_exec(json_sql, database, user)

    # Parse the JSON output (skip header/separator lines)
    lines = [l.strip() for l in output.strip().split("\n") if l.strip()]
    for line in lines:
        if line.startswith("[") or line.startswith("{"):
            result = json.loads(line)
            return result if result else []
    return []


def pg_exec_file(sql_file: str, database: str = "aitest", user: str = "aitest") -> str:
    """Execute SQL file via docker exec psql."""
    result = subprocess.run(
        ["docker", "exec", "-i", "aitest-pg", "psql", "-U", user, "-d", database],
        input=open(sql_file, encoding="utf-8").read(),
        capture_output=True,
        text=True,
        timeout=60,
    )
    if result.returncode != 0:
        raise RuntimeError(f"psql error: {result.stderr}")
    return result.stdout


def pg_table_exists(table_name: str) -> bool:
    """Check if a table exists in the database."""
    result = pg_query(
        f"SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname='public' AND tablename='{table_name}')"
    )
    return result[0].get("exists", False) if result else False
