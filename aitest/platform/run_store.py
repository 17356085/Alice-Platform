"""RunStore — PostgreSQL persistence for Run and RunEvent records. v3.0

Uses docker exec psql as transport (Windows workaround).
Method signatures unchanged — callers unaffected.

Usage:
    from aitest.platform.run_store import RunStore
    store = RunStore()
    store.save_run(run)
    store.save_event(event)
"""

import json
import logging
from datetime import datetime, timezone
from typing import Optional

from .run import Run
from .run_event import RunEvent
from .execution_request import ExecutionRequest
from aitest.infra.database import pg_exec, pg_query

logger = logging.getLogger("run_store")


def _escape(val) -> str:
    if val is None:
        return "NULL"
    return "'" + str(val).replace("'", "''") + "'"


def _escape_json(val) -> str:
    if val is None:
        return "'{}'"
    return "'" + json.dumps(val, ensure_ascii=False).replace("'", "''") + "'"


def _row_to_run(r: dict) -> Run:
    return Run(
        run_id=r["run_id"], request_id=r["request_id"],
        workspace_id=r["workspace_id"], org_id=r.get("org_id", ""),
        triggered_by=r.get("triggered_by", ""), capability=r.get("capability", "browser"),
        agent=r.get("agent", ""), module=r.get("module", ""),
        pages=r.get("pages", []), mode=r.get("mode", "full"),
        status=r.get("status", "running"),
        created_at=r.get("created_at", ""), completed_at=r.get("completed_at", "") or "",
        total_tokens=r.get("total_tokens", 0), total_cost=r.get("total_cost", 0.0),
        agent_runs=r.get("agent_runs", 0), artifacts=r.get("artifacts", []),
        error_message=r.get("error_message", ""),
    )


def _row_to_event(r: dict) -> RunEvent:
    return RunEvent(
        event_id=r["event_id"], event_type=r["event_type"],
        run_id=r.get("run_id", ""), request_id=r.get("request_id", ""),
        timestamp=r.get("timestamp", ""), data=r.get("data", {}),
    )


def _row_to_request(r: dict) -> ExecutionRequest:
    return ExecutionRequest(
        request_id=r["request_id"], workspace_id=r["workspace_id"],
        org_id=r.get("org_id", ""), triggered_by=r.get("triggered_by", ""),
        trigger_type=r.get("trigger_type", "manual"), module=r.get("module", ""),
        pages=r.get("pages", []), mode=r.get("mode", "full"),
        provider=r.get("provider", "claude"), priority=r.get("priority", 0),
        status=r.get("status", "created"), run_ids=r.get("run_ids", []),
        created_at=r.get("created_at", ""), started_at=r.get("started_at"),
        completed_at=r.get("completed_at"),
        retry_count=r.get("retry_count", 0), max_retries=r.get("max_retries", 0),
    )


class RunStore:
    def save_request(self, request: ExecutionRequest):
        pg_exec(f"""INSERT INTO execution_requests
            (request_id, workspace_id, org_id, triggered_by, trigger_type, module, pages, mode, provider, priority, status, run_ids, created_at, started_at, completed_at, retry_count, max_retries)
            VALUES ({_escape(request.request_id)}, {_escape(request.workspace_id)}, {_escape(request.org_id)}, {_escape(request.triggered_by)}, {_escape(request.trigger_type)}, {_escape(request.module)}, {_escape_json(request.pages)}, {_escape(request.mode)}, {_escape(request.provider or 'claude')}, {request.priority}, {_escape(request.status)}, {_escape_json(request.run_ids)}, {_escape(request.created_at)}, {_escape(request.started_at)}, {_escape(request.completed_at)}, {request.retry_count}, {request.max_retries})
            ON CONFLICT (request_id) DO UPDATE SET status=EXCLUDED.status, run_ids=EXCLUDED.run_ids, started_at=EXCLUDED.started_at, completed_at=EXCLUDED.completed_at""")

    def load_request(self, request_id: str) -> Optional[ExecutionRequest]:
        rows = pg_query(f"SELECT * FROM execution_requests WHERE request_id={_escape(request_id)}")
        return _row_to_request(rows[0]) if rows else None

    def save_run(self, run: Run):
        pg_exec(f"""INSERT INTO runs
            (run_id, request_id, workspace_id, org_id, triggered_by, capability, agent, module, pages, mode, status, created_at, completed_at, total_tokens, total_cost, agent_runs, artifacts, error_message)
            VALUES ({_escape(run.run_id)}, {_escape(run.request_id)}, {_escape(run.workspace_id)}, {_escape(run.org_id)}, {_escape(run.triggered_by)}, {_escape(run.capability)}, {_escape(run.agent)}, {_escape(run.module)}, {_escape_json(run.pages)}, {_escape(run.mode)}, {_escape(run.status)}, {_escape(run.created_at)}, {_escape(run.completed_at)}, {run.total_tokens}, {run.total_cost}, {run.agent_runs}, {_escape_json(run.artifacts)}, {_escape(run.error_message)})
            ON CONFLICT (run_id) DO UPDATE SET status=EXCLUDED.status, completed_at=EXCLUDED.completed_at, total_tokens=EXCLUDED.total_tokens, total_cost=EXCLUDED.total_cost, agent_runs=EXCLUDED.agent_runs, artifacts=EXCLUDED.artifacts, error_message=EXCLUDED.error_message""")

    def load_run(self, run_id: str) -> Optional[Run]:
        rows = pg_query(f"SELECT * FROM runs WHERE run_id={_escape(run_id)}")
        return _row_to_run(rows[0]) if rows else None

    def list_runs(self, workspace_id: str = "", org_id: str = "", status: str = "", request_id: str = "", limit: int = 50, offset: int = 0) -> list[Run]:
        where = ["1=1"]
        if workspace_id: where.append(f"workspace_id={_escape(workspace_id)}")
        if org_id: where.append(f"org_id={_escape(org_id)}")
        if status: where.append(f"status={_escape(status)}")
        if request_id: where.append(f"request_id={_escape(request_id)}")
        rows = pg_query(f"SELECT * FROM runs WHERE {' AND '.join(where)} ORDER BY created_at DESC LIMIT {limit} OFFSET {offset}")
        return [_row_to_run(r) for r in rows]

    def count_runs(self, workspace_id: str = "", org_id: str = "") -> int:
        where = ["1=1"]
        if workspace_id: where.append(f"workspace_id={_escape(workspace_id)}")
        if org_id: where.append(f"org_id={_escape(org_id)}")
        rows = pg_query(f"SELECT COUNT(*) as cnt FROM runs WHERE {' AND '.join(where)}")
        return rows[0]["cnt"] if rows else 0

    def save_event(self, event: RunEvent):
        pg_exec(f"""INSERT INTO run_events (event_id, event_type, run_id, request_id, timestamp, data, correlation_id)
            VALUES ({_escape(event.event_id)}, {_escape(event.event_type)}, {_escape(event.run_id)}, {_escape(event.request_id)}, {_escape(event.timestamp)}, {_escape_json(event.data)}, {_escape(event.run_id or '')})
            ON CONFLICT (event_id) DO NOTHING""")

    def list_events(self, run_id: str = "", event_type: str = "", limit: int = 100) -> list[RunEvent]:
        where = ["1=1"]
        if run_id: where.append(f"run_id={_escape(run_id)}")
        if event_type: where.append(f"event_type={_escape(event_type)}")
        rows = pg_query(f"SELECT * FROM run_events WHERE {' AND '.join(where)} ORDER BY timestamp ASC LIMIT {limit}")
        return [_row_to_event(r) for r in rows]

    def cleanup_old_runs(self, max_age_days: int = 30) -> int:
        rows = pg_query(f"SELECT run_id FROM runs WHERE status IN ('completed','failed','cancelled','timed_out') AND completed_at < NOW() - INTERVAL '{max_age_days} days'")
        for r in rows:
            pg_exec(f"DELETE FROM run_events WHERE run_id={_escape(r['run_id'])}")
            pg_exec(f"DELETE FROM runs WHERE run_id={_escape(r['run_id'])}")
        return len(rows)

    def recover_crashed_runs(self) -> int:
        pg_exec("UPDATE runs SET status='failed', error_message='Server crash — run interrupted', completed_at=NOW() WHERE status='running'")
        rows = pg_query("SELECT COUNT(*) as cnt FROM runs WHERE status='failed' AND error_message='Server crash — run interrupted'")
        return rows[0]["cnt"] if rows else 0

    def get_stats(self) -> dict:
        rows = pg_query("SELECT (SELECT COUNT(*) FROM runs) as run_count, (SELECT COUNT(*) FROM run_events) as event_count, (SELECT COUNT(*) FROM execution_requests) as request_count")
        return {"backend": "postgresql", **rows[0]} if rows else {"backend": "postgresql"}


_store: RunStore | None = None
def get_run_store() -> RunStore:
    global _store
    if _store is None: _store = RunStore()
    return _store
