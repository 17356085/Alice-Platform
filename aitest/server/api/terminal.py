"""Agent Terminal WebSocket — real-time Agent execution log broadcast.
Extracted from main.py (P0-2 split, 2026-06-25).

Routes:
  WS /ws/agent-terminal — live ObservationBus event stream
"""
from __future__ import annotations
import json as _json
import time
import asyncio
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

terminal_router = APIRouter(tags=["terminal"])


class AgentTerminalWSManager:
    """WebSocket manager — broadcasts ObservationBus events to Agent Terminal clients.

    v2.5: Queue+Worker architecture. ObservationBus sync callback → asyncio.Queue
    (maxsize=500) → single broadcast Worker. Thread-safe via call_soon_threadsafe.
    """

    _QUEUE_MAXSIZE = 500
    _EWMA_ALPHA = 0.1

    def __init__(self):
        self._connections: list[WebSocket] = []
        self._subscribed = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._queue: asyncio.Queue | None = None
        self._worker_task: asyncio.Task | None = None
        self._enqueued_count: int = 0
        self._dropped_queue_full: int = 0
        self._dropped_conn_closed: int = 0
        self._queue_peak: int = 0
        self._worker_busy_ms: float = 0.0
        self._worker_total_ms: float = 0.0
        self._broadcast_count: int = 0
        self._broadcast_ewma_ms: float = 0.0

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)
        if self._loop is None:
            self._loop = asyncio.get_running_loop()
            self._queue = asyncio.Queue(maxsize=self._QUEUE_MAXSIZE)
            self._worker_task = asyncio.create_task(self._broadcast_worker())
        self._start_listening()

    def disconnect(self, ws: WebSocket):
        if ws in self._connections:
            self._connections.remove(ws)

    async def _broadcast_worker(self):
        t_worker_start = time.perf_counter()
        while True:
            try:
                payload = await self._queue.get()
                t0 = time.perf_counter()
                await self._send_all(payload)
                t_now = time.perf_counter()
                busy_ms = (t_now - t0) * 1000
                self._worker_busy_ms += busy_ms
                self._worker_total_ms += (t_now - t_worker_start) * 1000
                t_worker_start = t_now
                self._broadcast_count += 1
                if self._broadcast_ewma_ms == 0.0:
                    self._broadcast_ewma_ms = busy_ms
                else:
                    self._broadcast_ewma_ms = (
                        (1 - self._EWMA_ALPHA) * self._broadcast_ewma_ms
                        + self._EWMA_ALPHA * busy_ms
                    )
            except asyncio.CancelledError:
                break
            except Exception:
                pass

    async def _send_all(self, payload: dict):
        for ws in list(self._connections):
            try:
                await ws.send_text(_json.dumps(payload, ensure_ascii=False, default=str))
            except Exception:
                self._connections.remove(ws)
                self._dropped_conn_closed += 1

    def _start_listening(self):
        if self._subscribed:
            return
        self._subscribed = True
        loop = self._loop
        queue = self._queue

        def _on_event(event):
            payload = {
                "type": str(event.type.value) if hasattr(event.type, 'value') else str(event.type),
                "agent": getattr(event, 'agent_name', ''),
                "module": getattr(event, 'module', ''),
                "page": getattr(event, 'page', ''),
                "data": getattr(event, 'data', {}),
                "timestamp": datetime.now().isoformat(),
            }
            if loop is None or queue is None:
                return

            def _enqueue():
                if queue.full():
                    try:
                        queue.get_nowait()
                        self._dropped_queue_full += 1
                    except asyncio.QueueEmpty:
                        pass
                queue.put_nowait(payload)
                self._enqueued_count += 1
                qs = queue.qsize()
                if qs > self._queue_peak:
                    self._queue_peak = qs

            loop.call_soon_threadsafe(_enqueue)

        self._on_event_callback = _on_event
        self._subscribed_types = []
        try:
            from aitest.platform.observation_bus import get_bus, EventType
            bus = get_bus()
            for et in [
                "skill_start", "skill_complete", "skill_failed", "skill_retry",
                "agent_start", "agent_complete",
                "tool_call_start", "tool_call_complete", "tool_call_failed",
                "test_passed", "test_failed", "evidence_captured",
                "context_window_warn", "context_window_continue",
                "provider_fallback", "provider_retry",
            ]:
                try:
                    event_type = EventType(et)
                    bus.subscribe(event_type, _on_event)
                    self._subscribed_types.append(event_type)
                except Exception:
                    continue
        except Exception:
            pass

    def dispose(self) -> None:
        if self._worker_task and not self._worker_task.done():
            self._worker_task.cancel()
            self._worker_task = None
        if self._queue is not None:
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                except asyncio.QueueEmpty:
                    break
        if self._subscribed:
            try:
                from aitest.platform.observation_bus import get_bus
                bus = get_bus()
                if hasattr(self, '_on_event_callback') and self._on_event_callback:
                    for et in self._subscribed_types:
                        try:
                            bus.unsubscribe(et, self._on_event_callback)
                        except Exception:
                            pass
            except Exception:
                pass
            self._subscribed = False
        for ws in list(self._connections):
            try:
                ws.close()
            except Exception:
                pass
        self._connections.clear()

    @property
    def queue_size(self) -> int:
        if self._queue is None:
            return 0
        return self._queue.qsize()

    @property
    def active_connections(self) -> int:
        return len(self._connections)

    @property
    def worker_busy_pct(self) -> float:
        if self._worker_total_ms <= 0:
            return 0.0
        return round(self._worker_busy_ms / self._worker_total_ms * 100, 1)

    @property
    def stats(self) -> dict:
        return {
            "queue_size": self.queue_size, "queue_peak": self._queue_peak,
            "queue_max": self._QUEUE_MAXSIZE, "enqueued": self._enqueued_count,
            "dropped": {"queue_full": self._dropped_queue_full,
                        "connection_closed": self._dropped_conn_closed},
            "worker_busy_pct": self.worker_busy_pct,
            "broadcast_ewma_ms": round(self._broadcast_ewma_ms, 1),
            "broadcast_count": self._broadcast_count,
            "connections": self.active_connections,
        }


_agent_terminal_ws = AgentTerminalWSManager()


def get_agent_terminal_ws() -> AgentTerminalWSManager:
    return _agent_terminal_ws


# ── WebSocket endpoint ────────────────────────────────────────────────

@terminal_router.websocket("/ws/agent-terminal")
async def agent_terminal_websocket(ws: WebSocket):
    await _agent_terminal_ws.connect(ws)
    try:
        await ws.send_text(_json.dumps({
            "type": "connected", "connections": _agent_terminal_ws.active_connections,
            "timestamp": datetime.now().isoformat(),
        }))
        while True:
            data = await ws.receive_text()
            msg = _json.loads(data)
            if msg.get("action") == "ping":
                await ws.send_text(_json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        _agent_terminal_ws.disconnect(ws)
    except Exception:
        _agent_terminal_ws.disconnect(ws)
