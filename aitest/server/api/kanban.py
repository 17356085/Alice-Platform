"""Kanban WebSocket + SOP execution API.
Extracted from main.py (P0-2 split, 2026-06-25).

Routes:
  WS   /ws/kanban           — real-time lifecycle events
  POST /api/sop/start        — start SOP execution
  GET  /api/kanban/status    — WebSocket connection count
"""
from __future__ import annotations
import json as _json
import threading
import asyncio
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Request
from aitest.platform.paths import get_workstudy

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

    async def broadcast_sop_phase(self, module: str, phase: str, status: str = "running",
                                   progress: int = 0, message: str = ""):
        await self.broadcast({
            "type": "phase_change", "module": module, "phase": phase,
            "status": status, "progress": progress, "message": message,
            "timestamp": datetime.now().isoformat(),
        })


_kanban_ws = KanbanWSManager()


def get_kanban_ws() -> KanbanWSManager:
    return _kanban_ws


# ── Helpers ───────────────────────────────────────────────────────────

def _get_sop_status_dir() -> Path:
    from aitest.platform.context import get_active_project_id
    base = get_workstudy()
    d = base / "governance" / "artifacts" / "sop-status" / get_active_project_id()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _update_module_phase(module: str, phase: str, status: str, progress: int):
    sop_dir = _get_sop_status_dir()
    status_file = sop_dir / f"SOP_STATUS_{module}.json"
    if status_file.exists():
        try:
            data = _json.loads(status_file.read_text(encoding="utf-8"))
            if phase not in data.get("completed_phases", []):
                data.setdefault("completed_phases", []).append(phase)
            data["status"] = status
            data["progress"] = progress
            data["updated_at"] = datetime.now().isoformat()
            status_file.write_text(_json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass


def _update_module_stage(module: str, new_stage: str):
    sop_dir = _get_sop_status_dir()
    status_file = sop_dir / f"SOP_STATUS_{module}.json"
    if not status_file.exists():
        return
    try:
        data = _json.loads(status_file.read_text(encoding="utf-8"))
        stage_map = {"pending": "pending", "planning": "ready", "executing": "in_progress",
                     "analyzing": "completed_with_issues", "completed": "completed"}
        data["status"] = stage_map.get(new_stage, data.get("status", "completed"))
        data["kanban_stage"] = new_stage
        data["kanban_updated_at"] = datetime.now().isoformat()
        status_file.write_text(_json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


# ── Endpoints ─────────────────────────────────────────────────────────

@kanban_router.post("/api/sop/start")
async def sop_start(request: Request):
    body = await request.json() if await request.body() else {}
    module = body.get("module", "")
    pages = body.get("pages", [])
    mode = body.get("mode", "full")
    provider = body.get("provider", "claude")

    if not module:
        return {"error": "module is required"}

    phases = ["Requirement", "Test Strategy", "Test Design", "Automation",
              "Environment", "Execution", "Bug Analysis", "Report", "Knowledge"]
    total = len(phases)
    loop = asyncio.get_event_loop()

    def run_sop_background():
        import time as _time
        for i, phase in enumerate(phases):
            progress = int((i + 1) / total * 100)
            asyncio.run_coroutine_threadsafe(
                _kanban_ws.broadcast_sop_phase(
                    module=module, phase=phase, status="running",
                    progress=progress, message=f"Running {phase}..."),
                loop,
            )
            _time.sleep(1.5)
            new_status = "completed" if progress >= 100 else "in_progress"
            _update_module_phase(module, phase, new_status, progress)
        asyncio.run_coroutine_threadsafe(
            _kanban_ws.broadcast_sop_phase(
                module=module, phase="Knowledge", status="completed",
                progress=100, message=f"SOP completed for {module}"),
            loop,
        )

    thread = threading.Thread(target=run_sop_background, daemon=True)
    thread.start()
    return {"module": module, "status": "started", "total_phases": total, "phases": phases}


@kanban_router.websocket("/ws/kanban")
async def kanban_websocket(ws: WebSocket):
    await _kanban_ws.connect(ws)
    try:
        await ws.send_text(_json.dumps({
            "type": "connected", "connections": _kanban_ws.active_connections,
            "timestamp": datetime.now().isoformat(),
        }))
        while True:
            data = await ws.receive_text()
            msg = _json.loads(data)
            action = msg.get("action", "")
            if action == "ping":
                await ws.send_text(_json.dumps({"type": "pong"}))
            elif action == "card_move":
                await _kanban_ws.broadcast({
                    "type": "card_moved", "module": msg.get("module", ""),
                    "from_stage": msg.get("from_stage", ""), "to_stage": msg.get("to_stage", ""),
                    "timestamp": datetime.now().isoformat(),
                })
                _update_module_stage(msg.get("module", ""), msg.get("to_stage", ""))
    except WebSocketDisconnect:
        _kanban_ws.disconnect(ws)
    except Exception:
        _kanban_ws.disconnect(ws)


@kanban_router.get("/api/kanban/status")
async def kanban_status():
    return {"active_connections": _kanban_ws.active_connections, "timestamp": datetime.now().isoformat()}
