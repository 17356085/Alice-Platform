"""Redis Pub/Sub — real-time cross-process event broadcasting.

P5 (2026-06-25): Enables real-time Kanban updates across FastAPI workers.
All WebSocket processes receive events simultaneously via Redis Pub/Sub.

Channels:
  kanban:update    — SOP phase completed / failed
  kanban:agent     — Agent started / completed
  execution:state  — Run state changes
  system:alert     — System notifications

Usage (publisher):
    from aitest.infra.redis_pubsub import publish
    publish("kanban:update", {"module": "equipment", "phase": "Automation", "status": "completed"})

Usage (subscriber — WebSocket handler):
    from aitest.infra.redis_pubsub import subscribe
    for event in subscribe("kanban:update", "kanban:agent"):
        await websocket.send_json(event)
"""
from __future__ import annotations

import json
import logging
import threading
from typing import Callable, Generator, Optional

logger = logging.getLogger("redis_pubsub")

_REDIS_AVAILABLE = False
try:
    import redis as _redis
    _REDIS_AVAILABLE = True
except ImportError:
    pass


def _get_redis() -> Optional[_redis.Redis]:
    if not _REDIS_AVAILABLE:
        return None
    try:
        from aitest.platform.config_registry import cfg
        r = _redis.Redis(
            host=cfg.redis_host, port=cfg.redis_port,
            socket_connect_timeout=cfg.redis_connect_timeout,
        )
        r.ping()
        return r
    except Exception:
        return None


def publish(channel: str, data: dict):
    """Publish an event to a Redis channel.

    Args:
        channel: "kanban:update", "kanban:agent", "execution:state", "system:alert"
        data: JSON-serializable dict
    """
    r = _get_redis()
    if not r:
        return
    try:
        msg = json.dumps(data, ensure_ascii=False, default=str)
        r.publish(f"tlo:{channel}", msg)
    except Exception:
        pass


def subscribe(*channels: str) -> Generator[dict, None, None]:
    """Subscribe to Redis channels. Yields parsed JSON events.

    Usage:
        for event in subscribe("kanban:update", "kanban:agent"):
            handle(event)
    """
    r = _get_redis()
    if not r:
        return

    pubsub = r.pubsub()
    try:
        prefixed = [f"tlo:{ch}" for ch in channels]
        pubsub.subscribe(*prefixed)
        for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    data = json.loads(message["data"])
                    data["_channel"] = message["channel"].decode().replace("tlo:", "")
                    yield data
                except json.JSONDecodeError:
                    pass
    finally:
        pubsub.close()


def subscribe_thread(*channels: str, callback: Callable[[dict], None]):
    """Subscribe in a background thread. Non-blocking.

    Usage:
        def on_kanban_update(event):
            broadcast_to_websockets(event)

        subscribe_thread("kanban:update", callback=on_kanban_update)
    """
    def _run():
        for event in subscribe(*channels):
            try:
                callback(event)
            except Exception:
                pass

    t = threading.Thread(target=_run, daemon=True, name="redis-pubsub")
    t.start()
    return t


# ── Kanban-specific helpers ───────────────────────────────────────────

def kanban_phase_completed(module: str, phase: str, agent: str = "",
                           duration_ms: float = 0):
    """Publish kanban phase completion event."""
    publish("kanban:update", {
        "type": "phase_completed",
        "module": module,
        "phase": phase,
        "agent": agent,
        "duration_ms": round(duration_ms, 1),
    })


def kanban_phase_failed(module: str, phase: str, error: str = ""):
    """Publish kanban phase failure event."""
    publish("kanban:update", {
        "type": "phase_failed",
        "module": module,
        "phase": phase,
        "error": error[:200],
    })


def kanban_agent_started(module: str, agent: str):
    """Publish agent started event."""
    publish("kanban:agent", {
        "type": "agent_started",
        "module": module,
        "agent": agent,
    })


def kanban_agent_completed(module: str, agent: str, tokens: int = 0):
    """Publish agent completed event."""
    publish("kanban:agent", {
        "type": "agent_completed",
        "module": module,
        "agent": agent,
        "tokens": tokens,
    })


def system_alert(message: str, severity: str = "info"):
    """Publish system alert."""
    publish("system:alert", {
        "type": "alert",
        "message": message,
        "severity": severity,
    })


# ── Stats ─────────────────────────────────────────────────────────────

def pubsub_stats() -> dict:
    """Get Pub/Sub statistics."""
    r = _get_redis()
    if not r:
        return {"backend": "none", "status": "redis_unavailable"}
    try:
        info = r.info("pubsub")
        return {
            "backend": "redis",
            "channels": info.get("pubsub_channels", 0),
            "patterns": info.get("pubsub_patterns", 0),
        }
    except Exception:
        return {"backend": "redis", "status": "error"}
