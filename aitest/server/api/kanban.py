"""Kanban WebSocket + SOP execution API. v3.1

v3.1: 删除伪执行，kanban 从 run_events 表读取真实 phase 进度。

Routes:
  WS   /ws/kanban           — real-time lifecycle events
  POST /api/sop/start        — start SOP execution (via ExecutionService)
  GET  /api/kanban/status    — WebSocket connection count
  GET  /api/kanban/phases/:module — query phase progress from run_events
"""
from __future__ import annotations
import json as _json
import asyncio
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from aitest.server.core.dependencies import get_execution_service

kanban_router = APIRouter(tags=["kanban"])


# ── Kanban WS Manager ─────────────────────────────────────────────────

class KanbanWSManager:
    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self._connections:
            self._connections.remove(ws)

    async def broadcast(self, event: dict):
        stale = []
        for ws in self._connections:
            try:
                await ws.send_text(_json.dumps(event, ensure_ascii=False, default=str))
            except Exception:
                stale.append(ws)
        for ws in stale:
            self.disconnect(ws)

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    async def dispose(self):
        """Close all connections and clear list. Called on server shutdown."""
        for ws in list(self._connections):
            try:
                await ws.close()
            except Exception:
                pass
        self._connections.clear()


_kanban_ws = KanbanWSManager()


def get_kanban_ws() -> KanbanWSManager:
    return _kanban_ws


# ── Phase progress query (from run_events) ────────────────────────────

def get_module_phase_progress(module: str) -> dict:
    """Query phase progress for a module from run_events table.

    Returns: {
        "module": str,
        "phases": [{"name": str, "status": str, "started_at": str, "completed_at": str}],
        "overall_status": str,
        "progress": int (0-100),
    }
    """
    from aitest.platform.run_store import get_run_store
    from aitest.platform.run_event import EventType

    store = get_run_store()
    # Find most recent run for this module
    runs = store.list_runs(limit=10)
    module_runs = [r for r in runs if r.module == module]
    if not module_runs:
        return {"module": module, "phases": [], "overall_status": "not_started", "progress": 0}

    latest_run = module_runs[0]
    events = store.list_events(run_id=latest_run.run_id, limit=500)

    # Build phase map from events
    phase_map: dict[str, dict] = {}
    for e in events:
        if e.event_type not in (EventType.PHASE_STARTED, EventType.PHASE_COMPLETED):
            continue
        name = e.data.get("phase", "unknown")
        if name not in phase_map:
            phase_map[name] = {"name": name, "status": "pending", "started_at": None, "completed_at": None}
        if e.event_type == EventType.PHASE_STARTED:
            phase_map[name]["status"] = "running"
            phase_map[name]["started_at"] = e.timestamp
        elif e.event_type == EventType.PHASE_COMPLETED:
            phase_map[name]["status"] = "completed"
            phase_map[name]["completed_at"] = e.timestamp

    phases = list(phase_map.values())
    completed = sum(1 for p in phases if p["status"] == "completed")
    total = len(phases) if phases else 1
    progress = int(completed / total * 100)

    overall = "completed" if latest_run.is_terminal and latest_run.status == "completed" else \
              "failed" if latest_run.is_terminal else "running"

    return {
        "module": module,
        "run_id": latest_run.run_id,
        "status": latest_run.status,
        "phases": phases,
        "overall_status": overall,
        "progress": progress,
    }


# ── Endpoints ─────────────────────────────────────────────────────────

@kanban_router.post("/api/sop/start")
async def sop_start(request: Request):
    """Start SOP execution via ExecutionService (real execution, not fake)."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    module = body.get("module", "")
    pages = body.get("pages", [])
    mode = body.get("mode", "full")
    provider = body.get("provider", "claude")

    if not module:
        return {"error": "module is required"}

    # v3.1: Use real ExecutionService instead of fake sleep-based execution
    from aitest.platform.workspace import ExecutionContext

    user_id = getattr(request.state, "user_id", None) or request.headers.get("X-User-Id", "anonymous")
    org_id = getattr(request.state, "org_id", None) or request.headers.get("X-Org-Id", "")

    ctx = ExecutionContext(
        workspace_id="default",
        user_id=user_id,
        scopes=["read", "execute"],
        org_id=org_id,
    )

    svc = get_execution_service(request)

    # Execute in background (non-blocking)
    async def _run():
        try:
            await asyncio.to_thread(
                svc.execute, ctx=ctx, module=module, pages=pages,
                agent="automation-agent", mode=mode, provider=provider,
            )
        except Exception:
            pass

    asyncio.create_task(_run())

    return {"module": module, "status": "started", "message": "SOP execution started via ExecutionService"}


@kanban_router.get("/api/kanban/phases/{module}")
async def get_phases(module: str):
    """Query phase progress for a module from run_events table."""
    return get_module_phase_progress(module)


# ── Idle timeout ──────────────────────────────────────────────────────
from aitest.platform.config_registry import cfg as _cfg
_WS_IDLE_TIMEOUT = _cfg.ws_idle_timeout_s


@kanban_router.websocket("/ws/kanban")
async def kanban_websocket(ws: WebSocket):
    await _kanban_ws.connect(ws)
    try:
        await ws.send_text(_json.dumps({
            "type": "connected", "connections": _kanban_ws.active_connections,
            "timestamp": datetime.now().isoformat(),
        }))
        while True:
            data = await asyncio.wait_for(ws.receive_text(), timeout=_WS_IDLE_TIMEOUT)
            msg = _json.loads(data)
            action = msg.get("action", "")
            # v3.1: action types from ws-events.ts WS_ACTIONS
            if action == "ping":  # WS_ACTIONS.PING
                await ws.send_text(_json.dumps({"type": "pong"}))  # WS_EVENTS.PONG
            elif action == "card_move":  # WS_ACTIONS.CARD_MOVE
                await _kanban_ws.broadcast({
                    "type": "card_moved",  # WS_EVENTS.CARD_MOVED
                    "module": msg.get("module", ""),
                    "from_stage": msg.get("from_stage", ""),
                    "to_stage": msg.get("to_stage", ""),
                    "timestamp": datetime.now().isoformat(),
                })
    except (WebSocketDisconnect, asyncio.TimeoutError):
        _kanban_ws.disconnect(ws)
    except Exception:
        _kanban_ws.disconnect(ws)


@kanban_router.get("/api/kanban/status")
async def kanban_status():
    return {"active_connections": _kanban_ws.active_connections, "timestamp": datetime.now().isoformat()}
