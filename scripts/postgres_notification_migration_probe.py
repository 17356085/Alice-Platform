"""Validate the notification read-state migration against PostgreSQL.

The DDL is executed in a transaction and rolled back.  A newly created table
therefore leaves no persistent change; an existing table is only inspected.
Set ``AITEST_DATABASE_URL`` or ``AITEST_SQLALCHEMY_URL`` to target a staging
database.  The local compose defaults are used only when neither is set.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import psycopg


def _url() -> str:
    value = os.environ.get("AITEST_DATABASE_URL") or os.environ.get("AITEST_SQLALCHEMY_URL")
    if value:
        return value.replace("+asyncpg", "+psycopg")
    return "postgresql://aitest:aitest@127.0.0.1:5432/aitest"


def main() -> None:
    migration = Path(__file__).resolve().parents[1].joinpath(
        "migrations", "add_notification_read_state.sql"
    ).read_text(encoding="utf-8")

    with psycopg.connect(_url()) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT current_schema(), current_setting('server_version')")
            schema, version = cursor.fetchone()
            cursor.execute(
                "SELECT EXISTS (SELECT 1 FROM information_schema.tables "
                "WHERE table_schema = current_schema() AND table_name = 'notification_read_state')"
            )
            existed_before = bool(cursor.fetchone()[0])
            cursor.execute(migration)
            cursor.execute(
                "SELECT column_name, data_type, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_schema = current_schema() AND table_name = 'notification_read_state' "
                "ORDER BY ordinal_position"
            )
            columns = [dict(zip(("name", "type", "nullable"), row)) for row in cursor.fetchall()]
            cursor.execute(
                "SELECT constraint_type, constraint_name "
                "FROM information_schema.table_constraints "
                "WHERE table_schema = current_schema() AND table_name = 'notification_read_state' "
                "ORDER BY constraint_type, constraint_name"
            )
            constraints = [dict(zip(("type", "name"), row)) for row in cursor.fetchall()]
        connection.rollback()

    print(json.dumps({
        "status": "validated",
        "schema": schema,
        "server_version": version,
        "existed_before": existed_before,
        "rolled_back": True,
        "columns": columns,
        "constraints": constraints,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
