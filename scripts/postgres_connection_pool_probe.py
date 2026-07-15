"""Validate a migrated PostgreSQL schema and SQLAlchemy pool with two sessions.

The URL is read from ``AITEST_DATABASE_URL``/``AITEST_SQLALCHEMY_URL`` and is
never printed.  Without either variable, the disposable local compose
database default is used.
"""

from __future__ import annotations

import json
import os
import uuid

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from aitest.infra.db import _pool_options


def _url() -> str:
    value = os.environ.get("AITEST_DATABASE_URL") or os.environ.get("AITEST_SQLALCHEMY_URL")
    value = value or "postgresql://aitest:aitest@127.0.0.1:5432/aitest"
    value = value.replace("+asyncpg", "+psycopg")
    if value.startswith("postgresql://"):
        value = value.replace("postgresql://", "postgresql+psycopg://", 1)
    return value


def main() -> None:
    engine = create_engine(_url(), future=True, **_pool_options(_url()))
    scope = f"pool-probe-{uuid.uuid4().hex[:12]}"
    notification_id = f"pool-probe-{uuid.uuid4().hex[:12]}"
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    try:
        with engine.connect() as connection:
            table_name = connection.execute(
                text("SELECT to_regclass('public.notification_read_state')")
            ).scalar_one_or_none()
        if table_name != "notification_read_state":
            raise RuntimeError("notification_read_state is missing; run migrations first")

        first = Session()
        second = Session()
        try:
            first.execute(
                text(
                    "INSERT INTO notification_read_state(scope, notification_id, read_at) "
                    "VALUES (:scope, :notification_id, CURRENT_TIMESTAMP) "
                    "ON CONFLICT (scope, notification_id) DO NOTHING"
                ),
                {"scope": scope, "notification_id": notification_id},
            )
            first.commit()
            visible = second.execute(
                text(
                    "SELECT notification_id FROM notification_read_state "
                    "WHERE scope = :scope AND notification_id = :notification_id"
                ),
                {"scope": scope, "notification_id": notification_id},
            ).scalar_one_or_none()
        finally:
            first.close()
            second.close()

        with engine.begin() as connection:
            connection.execute(
                text(
                    "DELETE FROM notification_read_state "
                    "WHERE scope = :scope AND notification_id = :notification_id"
                ),
                {"scope": scope, "notification_id": notification_id},
            )

        pool = engine.pool
        result = {
            "status": "validated" if visible == notification_id else "failed",
            "migration_table": table_name == "notification_read_state",
            "two_session_visibility": visible == notification_id,
            "pool_pre_ping": bool(getattr(pool, "_pre_ping", False)),
            "pool_size": pool.size() if hasattr(pool, "size") else None,
            "max_overflow": pool._max_overflow if hasattr(pool, "_max_overflow") else None,
            "checked_out_after_cleanup": pool.checkedout() if hasattr(pool, "checkedout") else None,
        }
        print(json.dumps(result, ensure_ascii=False))
        if result["status"] != "validated":
            raise SystemExit(1)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
