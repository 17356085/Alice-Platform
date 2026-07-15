"""Production deployment preflight checks and readiness contract."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from aitest.platform.paths import get_workstudy


@dataclass
class DeploymentPreflight:
    status: str = "ready"
    checks: dict[str, dict] = field(default_factory=dict)

    def add(self, name: str, ok: bool, detail: str, *, blocking: bool = True) -> None:
        self.checks[name] = {"status": "ok" if ok else ("error" if blocking else "warning"), "detail": detail}
        if not ok and blocking:
            self.status = "blocked"

    def to_dict(self) -> dict:
        return {"status": self.status, "checks": self.checks}


def _check_postgres_ready() -> tuple[bool, str]:
    """Verify connectivity and that the formal migration step ran."""
    from aitest.infra import database_pg

    with database_pg._get_conn() as connection:
        connection.execute("SELECT 1")
        row = connection.execute(
            "SELECT 1 FROM aitest_schema_migrations LIMIT 1"
        ).fetchone()
    if row is None:
        return False, "PostgreSQL is reachable but formal migrations are not recorded"
    return True, "PostgreSQL connection and migration ledger are ready"


def run_deployment_preflight(*, production: bool | None = None) -> DeploymentPreflight:
    production = production if production is not None else os.environ.get("AITEST_PRODUCTION", "0").lower() in {"1", "true", "yes"}
    result = DeploymentPreflight()

    from aitest.infra import database
    backend = database.get_backend()
    result.add("database_backend", backend == "postgres" if production else backend in {"sqlite", "postgres"}, f"selected={backend}")
    database_url = os.environ.get("AITEST_DATABASE_URL", "")
    result.add("database_url", bool(database_url) if production else True, "PostgreSQL URL configured" if database_url else "AITEST_DATABASE_URL is missing", blocking=production)

    if production and backend == "postgres" and database_url:
        try:
            ready, detail = _check_postgres_ready()
            result.add("database_connection", ready, detail, blocking=True)
        except Exception as exc:
            result.add("database_connection", False, f"PostgreSQL readiness failed: {exc}", blocking=True)

    api_key = os.environ.get("AITEST_API_KEY", "")
    result.add("api_auth", bool(api_key), "AITEST_API_KEY configured" if api_key else "AITEST_API_KEY is missing", blocking=production)

    worker_auth = os.environ.get("AITEST_WORKER_AUTH_REQUIRED", "0").lower() in {"1", "true", "yes"}
    worker_secret = bool(os.environ.get("AITEST_WORKER_AUTH_SECRET", ""))
    result.add("worker_auth", not worker_auth or worker_secret, "Worker auth secret configured" if worker_secret else "Worker auth is required but secret is missing", blocking=worker_auth)

    redis_url = os.environ.get("REDIS_URL", "")
    result.add("redis", bool(redis_url) if production else True, "Redis URL configured" if redis_url else "REDIS_URL is missing", blocking=production)

    mtls_required = os.environ.get("AITEST_WORKER_MTLS_REQUIRED", "0").lower() in {"1", "true", "yes"}
    try:
        from aitest.platform.worker_mtls import load_worker_tls_config
        load_worker_tls_config(required=mtls_required)
        result.add("worker_mtls", True, "Worker mTLS configured" if mtls_required else "Worker mTLS optional or disabled", blocking=mtls_required)
    except ValueError as exc:
        result.add("worker_mtls", False, str(exc), blocking=mtls_required)

    data_dir = Path(get_workstudy()) / "governance" / ".data"
    try:
        data_dir.mkdir(parents=True, exist_ok=True)
        probe = data_dir / ".readiness-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        result.add("data_directory", True, str(data_dir))
    except OSError as exc:
        result.add("data_directory", False, str(exc))
    return result
