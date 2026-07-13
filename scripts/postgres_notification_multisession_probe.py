"""Verify notification read markers are visible across PostgreSQL sessions.

This probe is deliberately scoped to a uniquely named temporary test table and
always drops it in ``finally``.  It uses two independent ``psql`` processes so
it also works with a local compose database whose TCP password differs from
the checked-in development default.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import uuid


CONTAINER = os.environ.get("AITEST_POSTGRES_CONTAINER", "aitest-pg")
DB_USER = os.environ.get("AITEST_POSTGRES_USER", "aitest")
DB_NAME = os.environ.get("AITEST_POSTGRES_DB", "aitest")


def _psql(sql: str) -> str:
    completed = subprocess.run(
        [
            "docker", "exec", CONTAINER, "psql",
            "-v", "ON_ERROR_STOP=1", "-U", DB_USER, "-d", DB_NAME,
            "-X", "-Atc", sql,
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def main() -> None:
    requested_table = os.environ.get("AITEST_POSTGRES_TABLE", "").strip()
    if requested_table and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", requested_table):
        raise SystemExit("AITEST_POSTGRES_TABLE must be a simple PostgreSQL table name")
    table = requested_table or f"notification_read_state_probe_{uuid.uuid4().hex[:12]}"
    created_by_probe = not requested_table
    qualified = f'public."{table}"'
    create = (
        f"CREATE TABLE {qualified} ("
        "scope VARCHAR(200) NOT NULL, "
        "notification_id VARCHAR(256) NOT NULL, "
        "read_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP, "
        f"PRIMARY KEY (scope, notification_id));"
    )
    marker = f"probe:{uuid.uuid4().hex}"
    try:
        if created_by_probe:
            _psql(create)
        _psql(
            f"INSERT INTO {qualified} (scope, notification_id) "
            f"VALUES ('multisession', '{marker}');"
        )
        visible = _psql(
            f"SELECT count(*) FROM {qualified} "
            f"WHERE scope = 'multisession' AND notification_id = '{marker}';"
        )
        assert visible == "1", f"second session did not observe marker: {visible!r}"
        print(json.dumps({
            "status": "validated",
            "container": CONTAINER,
            "sessions": 2,
            "visible_from_second_session": True,
            "temporary_table": created_by_probe,
            "cleaned_up": True,
        }, ensure_ascii=False))
    finally:
        if created_by_probe:
            _psql(f"DROP TABLE IF EXISTS {qualified};")
        else:
            _psql(
                f"DELETE FROM {qualified} "
                f"WHERE scope = 'multisession' AND notification_id = '{marker}';"
            )


if __name__ == "__main__":
    main()
