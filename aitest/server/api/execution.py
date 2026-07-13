"""Execution API — v2.2 Platform Runtime Foundation.

Endpoints:
  POST   /api/workspaces/:ws_id/executions  — Start execution (creates ExecutionRequest → Run)
  GET    /api/executions/:request_id         — Get ExecutionRequest status
  GET    /api/runs/:run_id                   — Get Run details
  GET    /api/runs                           — List Runs (filterable by workspace_id, org_id, status)
  POST   /api/executions/:request_id/cancel  — Cancel pending execution
"""
import asyncio
import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional

from aitest.server.core.dependencies import (
    get_execution_service,
    get_from_app_state as _shared_get_from_app_state,
)

execution_router = APIRouter(prefix="/api", tags=["Execution v2.2"])


def _get_from_state(request: Request, attr: str, factory):
    """Compatibility wrapper around shared server dependency resolution."""
    return _shared_get_from_app_state(request, attr, factory)


def _require_request_workspace_access(request: Request, *, org_id: str, workspace_id: str, required_scope: str):
    from aitest.platform.ownership import resolve_request_identity, require_workspace_access

    user_id, request_org_id, scopes = resolve_request_identity(request)
    if request_org_id and request_org_id != org_id:
        raise PermissionError(f"Request org '{request_org_id}' cannot access org '{org_id}'")
    require_workspace_access(
        org_id=org_id,
        workspace_id=workspace_id,
        user_id=user_id,
        required_scope=required_scope,
        request_scopes=scopes,
    )
    return user_id, scopes


def _require_request_run_access(request: Request, run, *, required_scope: str):
    from aitest.platform.ownership import resolve_request_identity, require_run_access

    user_id, request_org_id, scopes = resolve_request_identity(request)
    # SQLite/local mode intentionally runs without auth.  Historical runs can
    # outlive the in-memory workspace registry, so do not turn a read of the
    # local user's own data into a 500 merely because that registry was rebuilt.
    # Authenticated or explicitly scoped requests still take the full RBAC path.
    from aitest.server.auth import _rbac_required
    if not _rbac_required() and not request_org_id and not scopes:
        return user_id, scopes
    run_org_id = getattr(run, "org_id", "")
    if request_org_id and run_org_id and request_org_id != run_org_id:
        raise PermissionError(f"Request org '{request_org_id}' cannot access org '{run_org_id}'")
    require_run_access(
        run=run,
        user_id=user_id,
        required_scope=required_scope,
        request_scopes=scopes,
    )
    return user_id, scopes


def _resolve_request_org(request: Request, org_id: str = ""):
    from aitest.platform.ownership import resolve_request_identity

    user_id, request_org_id, scopes = resolve_request_identity(request)
    effective_org_id = org_id or request_org_id
    if request_org_id and effective_org_id and request_org_id != effective_org_id:
        raise PermissionError(f"Request org '{request_org_id}' cannot access org '{effective_org_id}'")
    return user_id, effective_org_id, scopes


def _require_request_scope(request: Request, required_scope: str):
    from aitest.platform.ownership import resolve_request_identity

    _, _, scopes = resolve_request_identity(request)
    if required_scope not in scopes and "admin" not in scopes:
        raise PermissionError(f"Request lacks scope '{required_scope}'")
    return scopes


def _require_request_workspace_by_id(request: Request, *, workspace_id: str, required_scope: str):
    from aitest.platform.workspace import get_ws_manager

    wm = get_ws_manager()
    ws = wm.get(workspace_id)
    if ws is None:
        raise ValueError(f"Workspace '{workspace_id}' not found")
    _require_request_workspace_access(
        request,
        org_id=getattr(ws, "org_id", ""),
        workspace_id=workspace_id,
        required_scope=required_scope,
    )
    return ws


def _filter_accessible_runs(request: Request, runs: list, *, required_scope: str = "read") -> list:
    allowed = []
    for run in runs:
        try:
            _require_request_run_access(request, run, required_scope=required_scope)
        except PermissionError:
            continue
        allowed.append(run)
    return allowed


class StartExecutionRequest(BaseModel):
    module: str
    pages: list[str] = []
    agent: str = "automation-agent"
    mode: str = "full"
    provider: str = "claude"
    priority: int = 0
    idempotency_key: str = ""
    max_retries: int = 3
    async_mode: bool = False


# ── POST /api/workspaces/:ws_id/executions ──────────────────────────

@execution_router.post("/workspaces/{ws_id}/executions", deprecated=True)
async def start_execution(ws_id: str, req: StartExecutionRequest, request: Request):
    """Start a new execution. Creates ExecutionRequest → dispatches → Run.

    ⚠️ **DEPRECATED**: Use `POST /api/v1/runs` instead. This endpoint will be removed in 6 months.

    Migration guide:
    - Replace `/api/workspaces/{ws_id}/executions` with `/api/v1/runs`
    - Map request body: `agent` → `target.id`, `module`/`pages` → `params.*`, `provider` → `runtime.provider`

    Returns ExecutionResult with request_id, run_id, status, summary.
    """
    from aitest.platform.workspace import ExecutionContext

    # Resolve identity from auth middleware or header fallback
    user_id = getattr(request.state, "user_id", None) or request.headers.get("X-User-Id", "anonymous")
    org_id = getattr(request.state, "org_id", None) or request.headers.get("X-Org-Id", "")
    idem_key = req.idempotency_key or request.headers.get("Idempotency-Key", "")

    ctx = ExecutionContext(
        workspace_id=ws_id,
        user_id=user_id,
        scopes=getattr(request.state, "scopes", ["read", "execute"]),
        org_id=org_id,
        entrypoint="server.execution",
        metadata={
            "idempotency_key": idem_key,
            "max_retries": req.max_retries,
        },
    )

    try:
        _require_request_workspace_access(
            request,
            org_id=org_id,
            workspace_id=ws_id,
            required_scope="execute",
        )
        # v3.0: Use shared ExecutionService from app.state (DI)
        svc = get_execution_service(request)
        if req.async_mode:
            result = svc.submit_async(
                ctx=ctx,
                module=req.module,
                pages=req.pages,
                agent=req.agent,
                mode=req.mode,
                provider=req.provider,
                priority=req.priority,
                idempotency_key=idem_key,
                max_retries=req.max_retries,
            )
        else:
            result = await asyncio.to_thread(
                svc.execute,
                ctx=ctx,
                module=req.module,
                pages=req.pages,
                agent=req.agent,
                mode=req.mode,
                provider=req.provider,
                priority=req.priority,
                idempotency_key=idem_key,
                max_retries=req.max_retries,
            )
        return result.to_dict()
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))


# ── GET /api/executions/:request_id ─────────────────────────────────

@execution_router.get("/executions/{request_id}")
async def get_execution(request_id: str, request: Request):
    """Get ExecutionRequest status with all related Runs."""
    from aitest.platform.run_store import get_run_store
    store = _get_from_state(request, "run_store", get_run_store)

    # v2.4.1: load ExecutionRequest directly (was O(n) scan)
    req = store.load_request(request_id)
    if req is None:
        raise HTTPException(404, f"Execution '{request_id}' not found")

    # Load all linked runs
    runs = []
    for run_id in req.run_ids:
        r = store.load_run(run_id)
        if r:
            runs.append(r)

    latest = runs[-1] if runs else None
    if latest is not None:
        try:
            _require_request_run_access(request, latest, required_scope="read")
        except PermissionError as e:
            raise HTTPException(403, str(e))
    events = store.list_events(run_id=latest.run_id, limit=50) if latest else []

    return {
        "request_id": request_id,
        "status": req.status,
        "run_ids": req.run_ids,
        "attempts": len(runs),
        "runs": [r.to_dict() for r in runs],
        "latest_run": latest.to_dict() if latest else None,
        "events": [e.to_dict() for e in events],
        "created_at": req.created_at,
        "completed_at": req.completed_at,
    }


# ── GET /api/runs/:run_id ───────────────────────────────────────────

@execution_router.get("/runs/{run_id}")
async def get_run(run_id: str, request: Request):
    """Get Run details with events."""
    from aitest.platform.run_store import get_run_store
    store = _get_from_state(request, "run_store", get_run_store)
    run = store.load_run(run_id)

    if run is None:
        raise HTTPException(404, f"Run '{run_id}' not found")
    try:
        _require_request_run_access(request, run, required_scope="read")
    except PermissionError as e:
        raise HTTPException(403, str(e))

    events = store.list_events(run_id=run_id, limit=100)

    return {
        "run": run.to_dict(),
        "events": [e.to_dict() for e in events],
    }


# ── GET /api/runs ───────────────────────────────────────────────────

@execution_router.get("/runs")
async def list_runs(
    request: Request,
    workspace_id: str = "",
    org_id: str = "",
    status: str = "",
    limit: int = 50,
    offset: int = 0,
):
    """List Runs. Filterable by workspace_id, org_id, status."""
    from aitest.platform.run_store import get_run_store
    store = _get_from_state(request, "run_store", get_run_store)
    if workspace_id and org_id:
        try:
            _require_request_workspace_access(
                request,
                org_id=org_id,
                workspace_id=workspace_id,
                required_scope="read",
            )
        except PermissionError as e:
            raise HTTPException(403, str(e))
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
async def cancel_execution(request_id: str, request: Request):
    """Cancel a pending/queued execution."""
    from aitest.platform.run_store import get_run_store
    store = _get_from_state(request, "run_store", get_run_store)
    runs = store.list_runs(request_id=request_id, limit=1)
    run = runs[0] if runs else None
    if run is None:
        raise HTTPException(404, f"Execution '{request_id}' not found or already terminal")
    try:
        _require_request_run_access(request, run, required_scope="execute")
    except PermissionError as e:
        raise HTTPException(403, str(e))
    svc = get_execution_service(request)
    cancelled = await asyncio.to_thread(svc.cancel, request_id)

    if not cancelled:
        raise HTTPException(404, f"Execution '{request_id}' not found or already terminal")

    return {"request_id": request_id, "status": "cancelled"}


# ── POST /api/executions/:run_id/timeout ─────────────────────────────

@execution_router.post("/runs/{run_id}/timeout")
async def timeout_run(run_id: str, request: Request):
    """Force-timeout a running execution. Sets abort + marks DB."""
    from aitest.platform.run_store import get_run_store
    rs = _get_from_state(request, "run_store", get_run_store)
    run = rs.load_run(run_id)
    if run is None:
        raise HTTPException(404, f"Run '{run_id}' not found or already terminal")
    try:
        _require_request_run_access(request, run, required_scope="execute")
    except PermissionError as e:
        raise HTTPException(403, str(e))
    svc = get_execution_service(request)
    ok = await asyncio.to_thread(svc.timeout_run, run_id)

    if not ok:
        raise HTTPException(404, f"Run '{run_id}' not found or already terminal")

    return {"run_id": run_id, "status": "timed_out"}


# ── POST /api/executions/:request_id/resume ──────────────────────────

@execution_router.post("/executions/{request_id}/resume")
async def resume_execution(request_id: str, request: Request):
    """Resume a paused or interrupted execution from its last checkpoint."""
    from aitest.platform.run_store import get_run_store
    try:
        # Resolve request_id → run_id (indexed query, no O(n) scan)
        rs = _get_from_state(request, "run_store", get_run_store)
        runs = rs.list_runs(request_id=request_id, limit=1)
        run = runs[0] if runs else None

        if run is None:
            raise HTTPException(status_code=404, detail=f"Execution '{request_id}' not found")
        if run.is_frozen:
            raise HTTPException(status_code=409, detail=f"Execution '{request_id}' already terminal ({run.status})")
        try:
            _require_request_run_access(request, run, required_scope="execute")
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

        svc = get_execution_service(request)
        result = await asyncio.to_thread(svc.resume, run.run_id)
        if result is None:
            raise HTTPException(status_code=400, detail=f"Cannot resume execution '{request_id}'")

        return {
            "request_id": request_id,
            "run_id": result.run_id,
            "status": result.status,
            "total_tokens": result.total_tokens,
            "total_cost": result.total_cost,
            "duration_ms": result.duration_ms,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resume failed: {str(e)[:200]}")


# ── GET /api/runs/:run_id/debug ──────────────────────────────────────

@execution_router.get("/runs/{run_id}/debug")
async def get_run_debug(run_id: str, request: Request):
    """Debug panel for a Run — LLM calls, tool calls, skill invocations."""
    from aitest.platform.run_store import get_run_store
    rs = _get_from_state(request, "run_store", get_run_store)
    run = rs.load_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    try:
        _require_request_run_access(request, run, required_scope="read")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    events = rs.list_events(run_id)

    # Classify events into categories
    timeline = []
    llm_calls = []
    tool_calls = []
    state_changes = []

    for e in events:
        entry = {
            "event_id": e.event_id,
            "event_type": e.event_type,
            "timestamp": e.timestamp,
            "data": e.data if isinstance(e.data, dict) else {},
        }
        timeline.append(entry)

        if "llm" in e.event_type.lower() or "agent" in e.event_type.lower():
            llm_calls.append(entry)
        if "tool" in e.event_type.lower() or "browser" in e.event_type.lower():
            tool_calls.append(entry)
        if "state" in e.event_type.lower() or "phase" in e.event_type.lower():
            state_changes.append(entry)

    return {
        "run_id": run.run_id,
        "request_id": run.request_id,
        "status": run.status,
        "agent": run.agent,
        "module": run.module,
        "pages": run.pages,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
        "total_tokens": run.total_tokens,
        "total_cost": run.total_cost,
        "error_message": run.error_message,
        "debug": {
            "total_events": len(events),
            "llm_calls": len(llm_calls),
            "tool_calls": len(tool_calls),
            "state_changes": len(state_changes),
            "timeline": timeline,
            "llm_calls_detail": llm_calls[:50],
            "tool_calls_detail": tool_calls[:50],
        },
    }


# ── GET /api/runs/:run_id/inspector ──────────────────────────────────

@execution_router.get("/runs/{run_id}/inspector")
async def get_run_inspector(run_id: str, request: Request):
    """Run Inspector — comprehensive execution detail for full-page view."""
    from aitest.platform.run_store import get_run_store
    from aitest.platform.timeline import build_timeline, timeline_summary
    from aitest.platform.run_event import EventType, EventDataKey as K

    rs = _get_from_state(request, "run_store", get_run_store)
    run = rs.load_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    try:
        _require_request_run_access(request, run, required_scope="read")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    events = rs.list_events(run_id, limit=500)

    # ── Header ──
    started = run.created_at
    ended = run.completed_at or started
    duration_ms = 0
    try:
        from datetime import datetime
        s = datetime.fromisoformat(started)
        e = datetime.fromisoformat(ended)
        duration_ms = int((e - s).total_seconds() * 1000)
    except Exception:
        pass

    header = {
        "run_id": run.run_id,
        "request_id": run.request_id,
        "workspace_id": run.workspace_id,
        "org_id": run.org_id,
        "triggered_by": run.triggered_by,
        "capability": run.capability,
        "agent": run.agent,
        "module": run.module,
        "pages": run.pages,
        "mode": run.mode,
        "status": run.status,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
        "duration_ms": duration_ms,
        "total_tokens": run.total_tokens,
        "total_cost": run.total_cost,
        "agent_runs": run.agent_runs,
        "artifacts_count": len(run.artifacts),
        "error_message": run.error_message,
    }

    # ── Timeline (from existing module) ──
    timeline = build_timeline(run_id)

    # ── Phase breakdown ──
    phases = []
    phase_events = [e for e in events if e.event_type in (
        EventType.PHASE_STARTED, EventType.PHASE_COMPLETED
    )]
    # Group phase events by phase name
    phase_map: dict[str, dict] = {}
    for e in phase_events:
        name = e.data.get(K.PHASE, "unknown") if isinstance(e.data, dict) else "unknown"
        if name not in phase_map:
            phase_map[name] = {"name": name, "started_at": None, "completed_at": None, "status": "unknown"}
        if e.event_type == EventType.PHASE_STARTED:
            phase_map[name]["started_at"] = e.timestamp
        elif e.event_type == EventType.PHASE_COMPLETED:
            phase_map[name]["completed_at"] = e.timestamp

    for name, p in phase_map.items():
        dur = 0
        if p["started_at"] and p["completed_at"]:
            try:
                from datetime import datetime
                dur = int((datetime.fromisoformat(p["completed_at"]) - datetime.fromisoformat(p["started_at"])).total_seconds() * 1000)
            except Exception:
                pass
        p["duration_ms"] = dur
        p["status"] = "completed" if p["completed_at"] else ("running" if p["started_at"] else "pending")
        phases.append(p)
    phases.sort(key=lambda p: p.get("started_at") or "")

    # ── Agent calls (LLM interactions) ──
    agent_calls = []
    llm_events = [e for e in events if "llm" in e.event_type.lower() or "agent" in e.event_type.lower()]
    for e in llm_events:
        d = e.data if isinstance(e.data, dict) else {}
        agent_calls.append({
            "event_id": e.event_id,
            "event_type": e.event_type,
            "timestamp": e.timestamp,
            "agent": d.get("agent", ""),
            "prompt": d.get("prompt", "")[:2000] if d.get("prompt") else "",
            "response": d.get("response", "")[:2000] if d.get("response") else "",
            "tokens": d.get("tokens", 0),
            "cost": d.get("cost", 0),
            "tool_calls": d.get("tool_calls", []) if isinstance(d.get("tool_calls"), list) else [],
        })

    # ── Artifacts ──
    artifact_events = [e for e in events if e.event_type == EventType.ARTIFACT_CREATED]
    artifacts = []
    for e in artifact_events:
        d = e.data if isinstance(e.data, dict) else {}
        artifact_path = d.get("path") or d.get(K.ARTIFACT_PATH, "")
        artifacts.append({
            "event_id": e.event_id,
            "timestamp": e.timestamp,
            "path": artifact_path,
            "download_url": f"/api/runs/{run_id}/artifacts/{e.event_id}/download",
            "type": d.get("type") or d.get(K.ARTIFACT_TYPE, "unknown"),
            "size": d.get("size", 0),
            "mime_type": d.get("mime_type", ""),
            "source_phase": d.get("phase", ""),
        })

    # ── Logs (all events as structured log) ──
    logs = []
    for e in events:
        d = e.data if isinstance(e.data, dict) else {}
        level = "error" if "fail" in e.event_type.lower() or "error" in e.event_type.lower() else \
                "warn" if "cancel" in e.event_type.lower() or "timeout" in e.event_type.lower() else \
                "info"
        logs.append({
            "timestamp": e.timestamp,
            "level": level,
            "event_type": e.event_type,
            "message": d.get("message", "") or d.get("error", "") or e.event_type,
        })

    # ── Execution tree (phase → step → action) ──
    execution_tree = _build_execution_tree(events, phases)

    return {
        "header": header,
        "timeline": timeline,
        "phases": phases,
        "agent_calls": agent_calls,
        "artifacts": artifacts,
        "logs": logs,
        "execution_tree": execution_tree,
        "summary": timeline_summary(run_id),
    }


def _resolve_run_artifact_file(raw_path: object) -> Path | None:
    """Resolve an event artifact without allowing arbitrary filesystem reads."""
    if not isinstance(raw_path, str) or not raw_path.strip():
        return None
    from aitest.platform.paths import get_workstudy

    root = Path(get_workstudy()).resolve()
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = root / candidate
    try:
        resolved = candidate.resolve()
        resolved.relative_to(root)
    except (OSError, ValueError):
        return None
    return resolved if resolved.is_file() else None


@execution_router.get("/runs/{run_id}/artifacts/{event_id}/download")
async def download_run_artifact(run_id: str, event_id: str, request: Request):
    """Download an artifact referenced by a Run Inspector artifact event."""
    from aitest.platform.run_store import get_run_store
    from aitest.platform.run_event import EventType, EventDataKey as K

    rs = _get_from_state(request, "run_store", get_run_store)
    run = rs.load_run(run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    try:
        _require_request_run_access(request, run, required_scope="read")
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))

    event = next((item for item in rs.list_events(run_id, limit=500)
                  if item.event_id == event_id and item.event_type == EventType.ARTIFACT_CREATED), None)
    if event is None:
        raise HTTPException(status_code=404, detail="Artifact event not found")
    data = event.data if isinstance(event.data, dict) else {}
    path = _resolve_run_artifact_file(data.get("path") or data.get(K.ARTIFACT_PATH))
    if path is None:
        raise HTTPException(status_code=404, detail="Artifact file not found")
    media_type = data.get("mime_type") or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type, filename=path.name)


def _build_execution_tree(events: list, phases: list[dict]) -> list[dict]:
    """Build nested execution tree: Phase → Step → Action."""
    from aitest.platform.run_event import EventType, EventDataKey as K

    tree = []
    current_phase: dict | None = None

    for e in events:
        if e.event_type == EventType.PHASE_STARTED:
            name = e.data.get(K.PHASE, "unknown") if isinstance(e.data, dict) else "unknown"
            current_phase = {
                "type": "phase",
                "name": name,
                "timestamp": e.timestamp,
                "status": "running",
                "children": [],
            }
            tree.append(current_phase)
        elif e.event_type == EventType.PHASE_COMPLETED and current_phase:
            current_phase["status"] = "completed"
            current_phase = None
        elif e.event_type == EventType.ARTIFACT_CREATED and current_phase:
            d = e.data if isinstance(e.data, dict) else {}
            current_phase["children"].append({
                "type": "artifact",
                "name": d.get("path") or d.get(K.ARTIFACT_PATH, "unknown"),
                "timestamp": e.timestamp,
                "status": "created",
            })
        elif e.event_type == EventType.RUN_FAILED:
            if current_phase:
                current_phase["status"] = "failed"
            if tree:
                tree[-1]["status"] = "failed"

    return tree


# ══════════════════════════════════════════════════════════════════════════
#  v2.3 Platform Observability — Timeline, History, Audit
# ══════════════════════════════════════════════════════════════════════════

# ── GET /api/runs/:run_id/timeline ─────────────────────────────────

@execution_router.get("/runs/{run_id}/timeline")
async def get_timeline(run_id: str, request: Request):
    """Time-ordered timeline of all events for a Run."""
    from aitest.platform.timeline import build_timeline
    from aitest.platform.run_store import get_run_store

    store = _get_from_state(request, "run_store", get_run_store)
    run = store.load_run(run_id)
    if run is None:
        raise HTTPException(404, f"Run '{run_id}' not found")
    try:
        _require_request_run_access(request, run, required_scope="read")
    except PermissionError as e:
        raise HTTPException(403, str(e))

    entries = build_timeline(run_id)
    if not entries:
        raise HTTPException(404, f"Run '{run_id}' not found")

    return {
        "run_id": run_id,
        "entries": entries,
        "total": len(entries),
    }


# ── GET /api/history ────────────────────────────────────────────────

@execution_router.get("/history")
async def execution_history(
    request: Request,
    workspace_id: str = "",
    org_id: str = "",
    status: str = "",
    module: str = "",
    agent: str = "",
    limit: int = 50,
    offset: int = 0,
):
    """Enriched execution history with summary per run."""
    from aitest.platform.run_store import get_run_store
    from aitest.platform.timeline import timeline_summary

    store = _get_from_state(request, "run_store", get_run_store)
    runs = store.list_runs(
        workspace_id=workspace_id,
        org_id=org_id,
        status=status,
        limit=min(limit, 200),
        offset=offset,
    )
    total = store.count_runs(workspace_id=workspace_id, org_id=org_id)

    # Filter by module/agent in-memory (simple, good enough for current scale)
    if module:
        runs = [r for r in runs if r.module == module]
    if agent:
        runs = [r for r in runs if r.agent == agent]
    if workspace_id:
        try:
            if org_id:
                _require_request_workspace_access(
                    request,
                    org_id=org_id,
                    workspace_id=workspace_id,
                    required_scope="read",
                )
            else:
                _require_request_workspace_by_id(
                    request,
                    workspace_id=workspace_id,
                    required_scope="read",
                )
        except PermissionError as e:
            raise HTTPException(403, str(e))
        except ValueError as e:
            raise HTTPException(404, str(e))

    runs = _filter_accessible_runs(request, runs, required_scope="read")

    items = [timeline_summary(r.run_id) for r in runs]

    return {
        "history": items,
        "total": len(items),
        "limit": limit,
        "offset": offset,
    }


# ── GET /api/audit ──────────────────────────────────────────────────

@execution_router.get("/audit")
async def query_audit(
    request: Request,
    org_id: str = "",
    workspace_id: str = "",
    event_type: str = "",
    run_id: str = "",
    limit: int = 50,
    offset: int = 0,
    since: str = "",
    until: str = "",
):
    """Query operational audit log. Append-only, filterable."""
    from aitest.platform.audit_log import get_audit_logger
    from aitest.platform.run_store import get_run_store

    if run_id:
        store = _get_from_state(request, "run_store", get_run_store)
        run = store.load_run(run_id)
        if run is None:
            raise HTTPException(404, f"Run '{run_id}' not found")
        try:
            _require_request_run_access(request, run, required_scope="read")
        except PermissionError as e:
            raise HTTPException(403, str(e))
        org_id = org_id or getattr(run, "org_id", "")
        workspace_id = workspace_id or getattr(run, "workspace_id", "")
    elif workspace_id:
        try:
            ws = _require_request_workspace_by_id(
                request,
                workspace_id=workspace_id,
                required_scope="read",
            )
        except PermissionError as e:
            raise HTTPException(403, str(e))
        except ValueError as e:
            raise HTTPException(404, str(e))
        org_id = org_id or getattr(ws, "org_id", "")
    else:
        try:
            _, org_id, _ = _resolve_request_org(request, org_id)
        except PermissionError as e:
            raise HTTPException(403, str(e))
        if not org_id:
            raise HTTPException(403, "Organization context required for audit query")

    logger = _get_from_state(request, "audit_logger", get_audit_logger)
    entries = logger.query(
        org_id=org_id,
        workspace_id=workspace_id,
        event_type=event_type,
        run_id=run_id,
        limit=limit,
        offset=offset,
        since=since,
        until=until,
    )
    total = logger.count(
        org_id=org_id,
        workspace_id=workspace_id,
        event_type=event_type,
    )

    return {
        "entries": entries,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ── GET /api/audit/stats ────────────────────────────────────────────

@execution_router.get("/audit/stats")
async def audit_stats(request: Request, org_id: str = ""):
    """Audit log statistics: event type breakdown, recent activity."""
    from aitest.platform.audit_log import get_audit_logger
    try:
        _, effective_org_id, _ = _resolve_request_org(request, org_id)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    if not effective_org_id:
        raise HTTPException(403, "Organization context required for audit stats")
    logger = _get_from_state(request, "audit_logger", get_audit_logger)
    return logger.stats(org_id=effective_org_id)


# ── GET /api/runs/:run_id/report ──────────────────────────────────────

@execution_router.get("/runs/{run_id}/report")
async def get_run_report(run_id: str, request: Request):
    """AI-generated execution summary for a Run. Returns None if not yet generated."""
    from aitest.platform.hooks.report_consumer import get_report_consumer
    from aitest.platform.run_store import get_run_store

    store = _get_from_state(request, "run_store", get_run_store)
    run = store.load_run(run_id)
    if run is None:
        raise HTTPException(404, f"Run '{run_id}' not found")
    try:
        _require_request_run_access(request, run, required_scope="read")
    except PermissionError as e:
        raise HTTPException(403, str(e))
    rc = _get_from_state(request, "report_consumer", get_report_consumer)
    report = rc.get_report(run_id)
    if report is None:
        return {"run_id": run_id, "report": None, "message": "Report not yet generated. Reports are auto-generated on run completion."}
    return {"run_id": run_id, "report": report}


# ── GET /api/reports ───────────────────────────────────────────────────

@execution_router.get("/reports")
async def list_reports(request: Request, limit: int = 50):
    """List all generated AI reports."""
    from aitest.platform.hooks.report_consumer import get_report_consumer
    from aitest.platform.run_store import get_run_store

    rc = _get_from_state(request, "report_consumer", get_report_consumer)
    reports = rc.list_reports(limit=min(limit, 100))
    store = _get_from_state(request, "run_store", get_run_store)
    visible = []
    for report in reports:
        run_id = report.get("run_id", "")
        run = store.load_run(run_id) if run_id else None
        if run is None:
            continue
        try:
            _require_request_run_access(request, run, required_scope="read")
        except PermissionError:
            continue
        visible.append(report)
    return {"reports": visible, "total": len(visible)}


# ══════════════════════════════════════════════════════════════════════════
#  v2.4 Platform Governance — Webhooks, Metrics, Billing, Quota
# ══════════════════════════════════════════════════════════════════════════

# ── Webhook CRUD ────────────────────────────────────────────────────

class RegisterWebhookRequest(BaseModel):
    url: str
    events: list[str]
    secret: str = ""


@execution_router.post("/workspaces/{ws_id}/webhooks")
async def register_webhook(ws_id: str, req: RegisterWebhookRequest, request: Request):
    """Register a webhook endpoint for a workspace."""
    from aitest.platform.hooks.webhook import get_webhook_registry
    try:
        _require_request_workspace_by_id(request, workspace_id=ws_id, required_scope="write")
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
    registry = _get_from_state(request, "webhook_registry", get_webhook_registry)
    wh = registry.register(
        workspace_id=ws_id,
        url=req.url,
        events=req.events,
        secret=req.secret,
    )
    return {"webhook": wh.__dict__}


@execution_router.get("/workspaces/{ws_id}/webhooks")
async def list_webhooks(ws_id: str, request: Request):
    """List webhooks for a workspace."""
    from aitest.platform.hooks.webhook import get_webhook_registry
    try:
        _require_request_workspace_by_id(request, workspace_id=ws_id, required_scope="read")
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
    registry = _get_from_state(request, "webhook_registry", get_webhook_registry)
    hooks = registry.list(workspace_id=ws_id)
    return {"webhooks": [h.__dict__ for h in hooks]}


@execution_router.delete("/workspaces/{ws_id}/webhooks/{webhook_id}")
async def delete_webhook(ws_id: str, webhook_id: str, request: Request):
    """Delete a webhook registration."""
    from aitest.platform.hooks.webhook import get_webhook_registry
    registry = _get_from_state(request, "webhook_registry", get_webhook_registry)
    try:
        _require_request_workspace_by_id(request, workspace_id=ws_id, required_scope="write")
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
    deleted = registry.delete(webhook_id)
    if not deleted:
        raise HTTPException(404, f"Webhook '{webhook_id}' not found")
    return {"status": "deleted"}


# ── Metrics ──────────────────────────────────────────────────────────

@execution_router.get("/metrics/snapshot")
async def metrics_snapshot(request: Request):
    """Current platform metrics: runs, cost, by module, by agent."""
    from aitest.platform.hooks.metrics_consumer import get_metrics_consumer
    try:
        _require_request_scope(request, "admin")
    except PermissionError as e:
        raise HTTPException(403, str(e))
    mc = _get_from_state(request, "metrics_consumer", get_metrics_consumer)
    return mc.snapshot()


# ── Billing ──────────────────────────────────────────────────────────

@execution_router.get("/billing/records")
async def billing_records(request: Request, org_id: str = "", limit: int = 50):
    """Billing hook records. No balance — hook only."""
    from aitest.platform.hooks.billing_hook import get_billing_hook
    try:
        _, effective_org_id, _ = _resolve_request_org(request, org_id)
    except PermissionError as e:
        raise HTTPException(403, str(e))
    if not effective_org_id:
        raise HTTPException(403, "Organization context required for billing records")
    hook = _get_from_state(request, "billing_hook", get_billing_hook)
    records = hook.query(org_id=effective_org_id, limit=limit)
    return {"records": records, "total": len(records)}


# ── Quota Usage ──────────────────────────────────────────────────────

@execution_router.get("/workspaces/{ws_id}/usage")
async def workspace_usage(ws_id: str, request: Request):
    """Resource usage for a workspace. Stats only, no enforcement."""
    from aitest.platform.hooks.quota_usage import get_quota_usage
    try:
        _require_request_workspace_by_id(request, workspace_id=ws_id, required_scope="read")
    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(404, str(e))
    qu = _get_from_state(request, "quota_usage", get_quota_usage)
    return qu.get_usage(ws_id)


@execution_router.get("/usage")
async def all_usage(request: Request):
    """Resource usage for all workspaces."""
    from aitest.platform.hooks.quota_usage import get_quota_usage
    try:
        _require_request_scope(request, "admin")
    except PermissionError as e:
        raise HTTPException(403, str(e))
    qu = _get_from_state(request, "quota_usage", get_quota_usage)
    usage = []
    for item in qu.snapshot():
        ws_id = item.get("workspace_id", "")
        if not ws_id:
            continue
        try:
            _require_request_workspace_by_id(request, workspace_id=ws_id, required_scope="read")
        except (PermissionError, ValueError):
            continue
        usage.append(item)
    return {"usage": usage}


@execution_router.get("/metrics/trends")
async def metrics_trends(request: Request, days: int = 7, module: str = ""):
    """Historical metrics trends from PG metrics_daily table."""
    from aitest.platform.hooks.metrics_consumer import get_metrics_consumer
    try:
        _require_request_scope(request, "admin")
    except PermissionError as e:
        raise HTTPException(403, str(e))
    mc = _get_from_state(request, "metrics_consumer", get_metrics_consumer)
    trends = mc.query_trends(days=min(days, 90), module=module)
    visible = []
    for row in trends:
        ws_id = row.get("workspace_id", "")
        if not ws_id:
            continue
        try:
            _require_request_workspace_by_id(request, workspace_id=ws_id, required_scope="read")
        except (PermissionError, ValueError):
            continue
        visible.append(row)
    return {"trends": visible, "days": days, "module": module or "all"}
