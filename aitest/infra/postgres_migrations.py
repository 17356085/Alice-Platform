"""Idempotent PostgreSQL bootstrap/migration runner for production deploys.

The project historically had SQLite-only SQL files and an Alembic skeleton
without revisions.  Production must therefore run one explicit, repeatable
step before the API or RQ workers start.  ORM metadata creates the shared
resource tables; the PostgreSQL-only SQL files cover tables that do not have
ORM models yet.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.pool import NullPool


POSTGRES_MIGRATIONS = (
    "017_mcp_servers.sql",
    "add_workers_table_postgres.sql",
    "add_notification_read_state.sql",
)


def normalize_database_url(value: str) -> str:
    """Return a synchronous psycopg SQLAlchemy URL without exposing it."""
    value = value.strip().replace("+asyncpg", "+psycopg")
    if value.startswith("postgresql://"):
        value = value.replace("postgresql://", "postgresql+psycopg://", 1)
    if not value.startswith("postgresql+"):
        raise ValueError("PostgreSQL URL must use a postgresql scheme")
    return value


def _migration_checksum(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def apply_postgres_migrations(
    database_url: str | None = None,
    migrations_dir: str | Path | None = None,
) -> dict[str, Any]:
    """Create ORM tables and apply all tracked PostgreSQL SQL migrations."""
    raw_url = database_url or os.environ.get("AITEST_DATABASE_URL", "")
    if not raw_url:
        raise RuntimeError("AITEST_DATABASE_URL is required for PostgreSQL migrations")
    url = normalize_database_url(raw_url)
    root = Path(migrations_dir) if migrations_dir else Path(__file__).resolve().parents[2] / "migrations"

    engine = create_engine(url, future=True, poolclass=NullPool)
    applied: list[str] = []
    try:
        with engine.begin() as connection:
            connection.execute(text(
                "CREATE TABLE IF NOT EXISTS aitest_schema_migrations ("
                "version VARCHAR(128) PRIMARY KEY, "
                "checksum VARCHAR(64) NOT NULL, "
                "applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP"
                ")"
            ))

        # Importing models registers every SQLAlchemy table on Base.metadata.
        # This is deliberately separate from the versioned raw SQL below so
        # future revisions can add ALTER statements without hiding drift.
        # Base lives in the database facade; importing the models package
        # separately registers every ORM model on that metadata collection.
        from aitest.infra.db import Base
        import aitest.infra.models  # noqa: F401

        Base.metadata.create_all(engine)

        with engine.begin() as connection:
            for filename in POSTGRES_MIGRATIONS:
                path = root / filename
                if not path.is_file():
                    raise FileNotFoundError(f"PostgreSQL migration missing: {path}")
                content = path.read_text(encoding="utf-8")
                checksum = _migration_checksum(content)
                existing = connection.execute(
                    text("SELECT checksum FROM aitest_schema_migrations WHERE version = :version"),
                    {"version": filename},
                ).scalar_one_or_none()
                if existing is not None:
                    if existing != checksum:
                        raise RuntimeError(f"Migration checksum changed: {filename}")
                    continue
                connection.exec_driver_sql(content)
                connection.execute(
                    text(
                        "INSERT INTO aitest_schema_migrations(version, checksum) "
                        "VALUES (:version, :checksum)"
                    ),
                    {"version": filename, "checksum": checksum},
                )
                applied.append(filename)

        return {
            "status": "validated",
            "applied": applied,
            "tracked": list(POSTGRES_MIGRATIONS),
            "orm_tables": sorted(Base.metadata.tables),
        }
    finally:
        engine.dispose()


def main() -> None:
    result = apply_postgres_migrations()
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
