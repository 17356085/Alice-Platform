"""One-shot migration: copy data from 4 SQLite DBs into PostgreSQL.

Usage:
    docker compose up -d postgres
    python -m aitest.infra.migrate_sqlite_to_pg

Steps:
    1. Start PostgreSQL (docker compose up -d postgres)
    2. Run Alembic migration (alembic upgrade head)
    3. Run this script
    4. Verify row counts
    5. Old .db files renamed to .bak
"""

import json
import sqlite3
import asyncio
import shutil
from pathlib import Path
from datetime import datetime, timezone

from aitest.platform.paths import get_workstudy

WORKSTUDY = get_workstudy()
DATA_DIR = WORKSTUDY / "governance" / ".data"


def _connect_sqlite(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def _parse_dt(s: str) -> datetime:
    """Parse ISO datetime string, fallback to now."""
    if not s:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(s)
    except (ValueError, TypeError):
        return datetime.now(timezone.utc)


def _parse_dt_float(f: float) -> datetime:
    """Parse Unix timestamp float."""
    if not f:
        return datetime.now(timezone.utc)
    return datetime.fromtimestamp(f, tz=timezone.utc)


async def migrate_runs(db_path: Path) -> dict:
    """Migrate runs.db → runs + run_events + execution_requests."""
    from aitest.infra.database import async_session
    from aitest.infra.models import RunModel, RunEventModel, ExecutionRequestModel

    conn = _connect_sqlite(db_path)
    counts = {"runs": 0, "events": 0, "requests": 0}

    async with async_session() as db:
        # Runs
        for row in conn.execute("SELECT * FROM runs").fetchall():
            r = dict(row)
            model = RunModel(
                run_id=r["run_id"],
                request_id=r["request_id"],
                workspace_id=r["workspace_id"],
                org_id=r.get("org_id", ""),
                triggered_by=r.get("triggered_by", ""),
                capability=r.get("capability", "browser"),
                agent=r.get("agent", ""),
                module=r.get("module", ""),
                pages=json.loads(r.get("pages", "[]")),
                mode=r.get("mode", "full"),
                status=r.get("status", "running"),
                created_at=_parse_dt(r.get("created_at", "")),
                completed_at=_parse_dt(r["completed_at"]) if r.get("completed_at") else None,
                total_tokens=r.get("total_tokens", 0),
                total_cost=r.get("total_cost", 0.0),
                agent_runs=r.get("agent_runs", 0),
                artifacts=json.loads(r.get("artifacts", "[]")),
                error_message=r.get("error_message", ""),
            )
            await db.merge(model)
            counts["runs"] += 1

        # Run Events
        for row in conn.execute("SELECT * FROM run_events").fetchall():
            r = dict(row)
            model = RunEventModel(
                event_id=r["event_id"],
                event_type=r["event_type"],
                run_id=r.get("run_id", ""),
                request_id=r.get("request_id", ""),
                timestamp=_parse_dt(r.get("timestamp", "")),
                data=json.loads(r.get("data", "{}")),
                correlation_id=r.get("run_id") or None,
            )
            await db.merge(model)
            counts["events"] += 1

        # Execution Requests
        for row in conn.execute("SELECT * FROM execution_requests").fetchall():
            r = dict(row)
            model = ExecutionRequestModel(
                request_id=r["request_id"],
                workspace_id=r["workspace_id"],
                org_id=r.get("org_id", ""),
                triggered_by=r.get("triggered_by", ""),
                trigger_type=r.get("trigger_type", "manual"),
                module=r.get("module", ""),
                pages=json.loads(r.get("pages", "[]")),
                mode=r.get("mode", "full"),
                provider=r.get("provider", "claude"),
                priority=r.get("priority", 0),
                status=r.get("status", "created"),
                run_ids=json.loads(r.get("run_ids", "[]")),
                created_at=_parse_dt(r.get("created_at", "")),
                started_at=_parse_dt(r["started_at"]) if r.get("started_at") else None,
                completed_at=_parse_dt(r["completed_at"]) if r.get("completed_at") else None,
                retry_count=r.get("retry_count", 0),
                max_retries=r.get("max_retries", 0),
            )
            await db.merge(model)
            counts["requests"] += 1

        await db.commit()

    conn.close()
    return counts


async def migrate_tasks(db_path: Path) -> int:
    """Migrate tasks.db → tasks."""
    from aitest.infra.database import async_session
    from aitest.infra.models import TaskModel

    conn = _connect_sqlite(db_path)
    count = 0

    async with async_session() as db:
        for row in conn.execute("SELECT * FROM tasks").fetchall():
            r = dict(row)
            model = TaskModel(
                id=r["id"],
                agent=r.get("agent", ""),
                module=r.get("module", ""),
                page=r.get("page", ""),
                provider=r.get("provider", "claude"),
                status=r.get("status", "queued"),
                result_json=r.get("result_json", ""),
                error_msg=r.get("error_msg", ""),
                retry_count=r.get("retry_count", 0),
                max_retries=r.get("max_retries", 3),
                retry_at=r.get("retry_at", 0.0),
                created_at=r.get("created_at"),
                started_at=r.get("started_at"),
                completed_at=r.get("completed_at"),
            )
            await db.merge(model)
            count += 1

        await db.commit()

    conn.close()
    return count


async def migrate_audit(db_path: Path) -> int:
    """Migrate audit.db → audit_entries."""
    from aitest.infra.database import async_session
    from aitest.infra.models import AuditEntryModel

    conn = _connect_sqlite(db_path)
    count = 0

    async with async_session() as db:
        for row in conn.execute("SELECT * FROM audit_entries").fetchall():
            r = dict(row)
            model = AuditEntryModel(
                event_id=r.get("event_id", ""),
                event_type=r.get("event_type", ""),
                run_id=r.get("run_id", ""),
                request_id=r.get("request_id", ""),
                org_id=r.get("org_id", ""),
                workspace_id=r.get("workspace_id", ""),
                user_id=r.get("user_id", ""),
                timestamp=_parse_dt(r.get("timestamp", "")),
                data_json=json.loads(r.get("data_json", "{}")),
            )
            db.add(model)
            count += 1

        await db.commit()

    conn.close()
    return count


async def migrate_bugs(db_path: Path) -> int:
    """Migrate bugs.db → bugs."""
    from aitest.infra.database import async_session
    from aitest.infra.models import BugModel

    conn = _connect_sqlite(db_path)
    count = 0

    async with async_session() as db:
        for row in conn.execute("SELECT * FROM bugs").fetchall():
            r = dict(row)
            model = BugModel(
                id=r["id"],
                date=r.get("date", ""),
                module=r.get("module", ""),
                page=r.get("page", ""),
                test_name=r.get("test_name", ""),
                error_type=r.get("error_type", ""),
                error_message=r.get("error_message", ""),
                root_cause=r.get("root_cause", ""),
                severity=r.get("severity", "medium"),
                status=r.get("status", "open"),
                matched_issue=r.get("matched_issue", ""),
                fix_description=r.get("fix_description", ""),
                fix_files=r.get("fix_files", ""),
                regression_risk=r.get("regression_risk", "low"),
                tags=r.get("tags", ""),
                created_at=r.get("created_at", 0.0),
                updated_at=r.get("updated_at", 0.0),
            )
            await db.merge(model)
            count += 1

        await db.commit()

    conn.close()
    return count


async def main():
    """Run full migration."""
    from aitest.infra.database import init_db

    print("=" * 60)
    print("AITest SQLite → PostgreSQL Migration")
    print("=" * 60)

    # Step 1: Create tables
    print("\n[1/5] Creating PostgreSQL tables...")
    await init_db()
    print("  ✅ Tables created")

    # Step 2: Migrate runs.db
    runs_db = DATA_DIR / "runs.db"
    if runs_db.exists():
        print(f"\n[2/5] Migrating {runs_db.name}...")
        counts = await migrate_runs(runs_db)
        print(f"  ✅ {counts['runs']} runs, {counts['events']} events, {counts['requests']} requests")
    else:
        print("\n[2/5] runs.db not found — skipping")

    # Step 3: Migrate tasks.db
    tasks_db = WORKSTUDY / "aitest" / "tasks.db"
    if tasks_db.exists():
        print(f"\n[3/5] Migrating {tasks_db.name}...")
        count = await migrate_tasks(tasks_db)
        print(f"  ✅ {count} tasks")
    else:
        print("\n[3/5] tasks.db not found — skipping")

    # Step 4: Migrate audit.db
    audit_db = DATA_DIR / "audit.db"
    if audit_db.exists():
        print(f"\n[4/5] Migrating {audit_db.name}...")
        count = await migrate_audit(audit_db)
        print(f"  ✅ {count} audit entries")
    else:
        print("\n[4/5] audit.db not found — skipping")

    # Step 5: Migrate bugs.db
    bugs_db = DATA_DIR / "bugs.db"
    if bugs_db.exists():
        print(f"\n[5/5] Migrating {bugs_db.name}...")
        count = await migrate_bugs(bugs_db)
        print(f"  ✅ {count} bugs")
    else:
        print("\n[5/5] bugs.db not found — skipping")

    # Backup old files
    print("\n[backup] Renaming old .db files to .bak...")
    for db_file in [runs_db, tasks_db, audit_db, bugs_db]:
        if db_file.exists():
            bak = db_file.with_suffix(".db.bak")
            shutil.copy2(str(db_file), str(bak))
            print(f"  📦 {db_file.name} → {bak.name}")

    print("\n" + "=" * 60)
    print("Migration complete!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
