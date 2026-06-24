"""Execution API — v2.2 Platform Runtime Foundation.

Endpoints:
  POST   /api/workspaces/:ws_id/executions  — Start execution (creates ExecutionRequest → Run)
  GET    /api/executions/:request_id         — Get ExecutionRequest status
  GET    /api/runs/:run_id                   — Get Run details
  GET    /api/runs                           — List Runs (filterable by workspace_id, org_id, status)
  POST   /api/executions/:request_id/cancel  — Cancel pending execution
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional

execution_router = APIRouter(prefix="/api", tags=["Execution v2.2"])


class StartExecutionRequest(BaseModel):
    module: str
    pages: list[str] = []
    agent: str = "automation-agent"
    mode: str = "full"
    provider: str = "claude"
    priority: int = 0


# ── POST /api/workspaces/:ws_id/executions ──────────────────────────

@execution_router.post("/workspaces/{ws_id}/executions")
async def start_execution(ws_id: str, req: StartExecutionRequest, request: Request):
    """Start a new execution. Creates ExecutionRequest → dispatches → Run.

    Returns ExecutionResult with request_id, run_id, status, summary.
    """
    from aitest.platform.execution_service import ExecutionService
    from aitest.platform.workspace import ExecutionContext

    # Resolve identity from auth middleware or header fallback
    user_id = getattr(request.state, "user_id", None) or request.headers.get("X-User-Id", "anonymous")
    org_id = getattr(request.state, "org_id", None) or request.headers.get("X-Org-Id", "")

    ctx = ExecutionContext(
        workspace_id=ws_id,
        user_id=user_id,
        scopes=getattr(request.state, "scopes", ["read", "execute"]),
        org_id=org_id,
    )

    try:
        svc = ExecutionService()
        result = svc.execute(
            ctx=ctx,
            module=req.module,
            pages=req.pages,
            agent=req.agent,
            mode=req.mode,
            provider=req.provider,
            priority=req.priority,
        )
        return {
            "request_id": result.request_id,
            "run_id": result.run_id,
            "status": result.status,
            "total_tokens": result.total_tokens,
            "total_cost": result.total_cost,
            "agent_runs": result.agent_runs,
            "artifacts": result.artifacts,
            "error_message": result.error_message,
            "duration_ms": result.duration_ms,
        }
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


# ── GET /api/executions/:request_id ─────────────────────────────────

@execution_router.get("/executions/{request_id}")
async def get_execution(request_id: str):
    """Get ExecutionRequest status. v2.2: looks up Run by request_id."""
    from aitest.platform.run_store import get_run_store

    store = get_run_store()
    runs = store.list_runs(limit=500)
    run = next((r for r in runs if r.request_id == request_id), None)

    if run is None:
        raise HTTPException(404, f"Execution '{request_id}' not found")

    events = store.list_events(run_id=run.run_id, limit=50)

    # Find all runs for this request (one request → many runs on retry)
    all_runs = [r for r in store.list_runs(limit=500) if r.request_id == request_id]

    return {
        "request_id": request_id,
        "run_ids": [r.run_id for r in all_runs],
        "latest_run": run.to_dict(),
        "attempts": len(all_runs),
        "events": [e.to_dict() for e in events],
    }


# ── GET /api/runs/:run_id ───────────────────────────────────────────

@execution_router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get Run details with events."""
    from aitest.platform.run_store import get_run_store

    store = get_run_store()
    run = store.load_run(run_id)

    if run is None:
        raise HTTPException(404, f"Run '{run_id}' not found")

    events = store.list_events(run_id=run_id, limit=100)

    return {
        "run": run.to_dict(),
        "events": [e.to_dict() for e in events],
    }


# ── GET /api/runs ───────────────────────────────────────────────────

@execution_router.get("/runs")
async def list_runs(
    workspace_id: str = "",
    org_id: str = "",
    status: str = "",
    limit: int = 50,
    offset: int = 0,
):
    """List Runs. Filterable by workspace_id, org_id, status."""
    from aitest.platform.run_store import get_run_store

    store = get_run_store()
    runs = store.list_runs(
        workspace_id=workspace_id,
        org_id=org_id,
        status=status,
        limit=min(limit, 200),
        offset=offset,
    )
    total = store.count_runs(workspace_id=workspace_id, org_id=org_id)

    return {
        "runs": [r.to_dict() for r in runs],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ── POST /api/executions/:request_id/cancel ─────────────────────────

@execution_router.post("/executions/{request_id}/cancel")
async def cancel_execution(request_id: str):
    """Cancel a pending/queued execution."""
    from aitest.platform.execution_service import ExecutionService

    svc = ExecutionService()
    cancelled = svc.cancel(request_id)

    if not cancelled:
        raise HTTPException(404, f"Execution '{request_id}' not found or already terminal")

    return {"request_id": request_id, "status": "cancelled"}
