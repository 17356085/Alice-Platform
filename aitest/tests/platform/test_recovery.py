"""SQLite backup and integrity verification tests."""

import sqlite3

from aitest.platform.recovery import backup_sqlite, verify_sqlite


def test_sqlite_backup_can_be_verified(tmp_path):
    source = tmp_path / "source.db"
    backup = tmp_path / "backup" / "copy.db"
    with sqlite3.connect(source) as conn:
        conn.execute("CREATE TABLE runs (id TEXT PRIMARY KEY)")
        conn.execute("INSERT INTO runs VALUES ('run-1')")
    backup_sqlite(source, backup)
    result = verify_sqlite(backup)
    assert result["ok"] is True
    assert "runs" in result["tables"]
