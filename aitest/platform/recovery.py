"""Local SQLite backup/restore primitives for disaster-recovery drills."""

from __future__ import annotations

import sqlite3
from pathlib import Path


def backup_sqlite(source: str | Path, destination: str | Path) -> Path:
    source_path = Path(source).resolve()
    destination_path = Path(destination).resolve()
    if source_path == destination_path:
        raise ValueError("Backup destination must differ from source")
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(str(source_path)) as source_conn, sqlite3.connect(str(destination_path)) as destination_conn:
        source_conn.backup(destination_conn)
    return destination_path


def verify_sqlite(path: str | Path) -> dict:
    db_path = Path(path).resolve()
    with sqlite3.connect(str(db_path)) as conn:
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()
    return {"path": str(db_path), "integrity": integrity, "tables": [row[0] for row in tables], "ok": integrity == "ok"}
