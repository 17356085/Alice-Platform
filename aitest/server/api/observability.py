"""
Observability API — real-time resource stats for dashboards.

Endpoints:
  GET /api/observability/snapshot      — all stats in one call
  GET /api/observability/memory        — RSS, GC, heap
  GET /api/observability/threads       — thread count + states
  GET /api/observability/tasks         — asyncio task count + ages
  GET /api/observability/queue         — task queue depth + rate
  GET /api/observability/gc            — GC generation stats
  GET /api/observability/websocket     — WS connection count + rates
  GET /api/observability/sqlite        — DB sizes
"""

from __future__ import annotations
import asyncio
import gc
import os
import threading
import time
from datetime import datetime, timezone

from fastapi import APIRouter

obs_router = APIRouter(prefix="/api/v1/observability", tags=["observability"])

_SNAPSHOT_CACHE: dict = {}
_SNAPSHOT_CACHE_TIME = 0.0
_CACHE_TTL = 2.0  # cache snapshot for 2 seconds (prevents duplicate sampling)


def _cached_snapshot() -> dict:
    """Return cached snapshot if fresh, else sample."""
    global _SNAPSHOT_CACHE, _SNAPSHOT_CACHE_TIME
    now = time.time()
    if _SNAPSHOT_CACHE and (now - _SNAPSHOT_CACHE_TIME) < _CACHE_TTL:
        return _SNAPSHOT_CACHE
    _SNAPSHOT_CACHE = _sample_snapshot()
    _SNAPSHOT_CACHE_TIME = now
    return _SNAPSHOT_CACHE


def _sample_snapshot() -> dict:
    """Full resource snapshot."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "memory": _sample_memory(),
        "threads": _sample_threads(),
        "tasks": _sample_tasks(),
        "queue": _sample_queue(),
        "gc": _sample_gc(),
        "websocket": _sample_websocket(),
        "sqlite": _sample_sqlite(),
    }


# ═══════════════════════════════════════════════════════════════════════
#  Samplers
# ═══════════════════════════════════════════════════════════════════════

def _sample_memory() -> dict:
    try:
        import psutil
        p = psutil.Process()
        mem = p.memory_info()
        return {
            "rss_mb": round(mem.rss / (1024 * 1024), 2),
            "vms_mb": round(mem.vms / (1024 * 1024), 2),
            "pct": round(p.memory_percent(), 2),
        }
    except ImportError:
        return {"rss_mb": -1, "vms_mb": -1, "pct": -1}


def _sample_threads() -> dict:
    try:
        import psutil
        p = psutil.Process()
        threads = p.threads()
        return {
            "count": len(threads),
            "daemon_count": threading.active_count() - len([t for t in threading.enumerate() if not t.daemon]),
        }
    except ImportError:
        return {"count": threading.active_count()}


def _sample_tasks() -> dict:
    try:
        all_tasks = asyncio.all_tasks()
        now = time.monotonic()
        pending = 0
        done = 0
        ages = []
        for t in all_tasks:
            if t.done():
                done += 1
            else:
                pending += 1
                # Approximate age from task creation (Python 3.12 doesn't expose creation time directly)
                if hasattr(t, '_coroutine'):
                    ages.append(-1)  # can't easily get age without patching
        return {
            "total": len(all_tasks),
            "pending": pending,
            "done": done,
            "max_age_s": -1,
        }
    except RuntimeError:
        return {"total": -1, "pending": -1, "done": -1}


def _sample_queue() -> dict:
    try:
        from aitest.infra.task_queue import get_runner
        runner = get_runner()
        try:
            stats = runner.get_stats()
            return {
                "backend": stats.get("backend", "unknown"),
                "queued": stats.get("queued", 0),
                "running": stats.get("running", 0),
                "completed": stats.get("completed", 0),
                "failed": stats.get("failed", 0),
                "deferred": stats.get("deferred", 0),
            }
        except Exception:
            return {"backend": "unknown", "queued": 0}
    except Exception:
        return {"backend": "unavailable", "queued": 0}


def _sample_gc() -> dict:
    counts = gc.get_count()
    return {
        "gen0": counts[0],
        "gen1": counts[1],
        "gen2": counts[2],
        "thresholds": list(gc.get_threshold()),
        "total_objects": len(gc.get_objects()) if hasattr(gc, 'get_objects') else -1,
    }


def _sample_websocket() -> dict:
    result = {"total": 0, "endpoints": {}}
    try:
        from aitest.server.api.terminal import get_agent_terminal_ws
        tws = get_agent_terminal_ws()
        result["endpoints"]["agent-terminal"] = tws.active_connections
        result["total"] += tws.active_connections
    except Exception:
        result["endpoints"]["agent-terminal"] = 0
    try:
        from aitest.server.api.kanban import get_kanban_ws
        kws = get_kanban_ws()
        result["endpoints"]["kanban"] = kws.active_connections
        result["total"] += kws.active_connections
    except Exception:
        result["endpoints"]["kanban"] = 0
    return result


def _sample_sqlite() -> dict:
    from aitest.platform.paths import get_workstudy
    base = get_workstudy()
    dbs = {
        "runs": base / "governance" / ".data" / "runs.db",
        "audit": base / "governance" / ".data" / "audit.db",
        "checkpoints": base / "governance" / ".graph_state" / "checkpoints.sqlite",
    }
    result = {}
    for name, path in dbs.items():
        if path.exists():
            size_kb = round(path.stat().st_size / 1024, 1)
        else:
            size_kb = 0
        result[name] = {"size_kb": size_kb, "exists": path.exists()}
    return result


# ═══════════════════════════════════════════════════════════════════════
#  Routes
# ═══════════════════════════════════════════════════════════════════════

@obs_router.get("/snapshot")
async def get_snapshot():
    """Full resource snapshot — all stats in one call."""
    return _cached_snapshot()


@obs_router.get("/memory")
async def get_memory():
    return _sample_memory()


@obs_router.get("/threads")
async def get_threads():
    return _sample_threads()


@obs_router.get("/tasks")
async def get_tasks():
    return _sample_tasks()


@obs_router.get("/queue")
async def get_queue():
    return _sample_queue()


@obs_router.get("/gc")
async def get_gc():
    return _sample_gc()


@obs_router.get("/websocket")
async def get_websocket():
    return _sample_websocket()


@obs_router.get("/sqlite")
async def get_sqlite():
    return _sample_sqlite()
