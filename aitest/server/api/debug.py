"""Debug endpoints — memory observatory, ownership, threads, chat queues.
Extracted from main.py (P0-2 split, 2026-06-25).

Routes:
  GET  /api/debug/memory              — full leak report
  GET  /api/debug/memory/snapshot     — lifecycle snapshot
  GET  /api/debug/memory/diff         — growth attribution
  GET  /api/debug/memory/retain/{id}  — retain chain
  GET  /api/debug/memory/gc-top       — top GC objects
  GET  /api/debug/memory/threads      — thread enumeration
  GET  /api/debug/memory/chat-queues  — chat session queue diagnostics
  GET  /api/debug/ownership/scan      — ownership violation scan
  GET  /api/debug/ownership/tasks     — tracked asyncio tasks
  GET  /api/debug/ownership/stores    — OwnedDict store sizes
  POST /api/debug/ownership/enforce   — force ownership enforcement
  POST /api/debug/memory/control      — memory control plane
"""
from __future__ import annotations
import sys
import time
import traceback as _traceback

from fastapi import APIRouter, Request

debug_router = APIRouter(prefix="/api/debug", tags=["debug"])


# ── Memory Observatory (v2.7) ──────────────────────────────────────────

@debug_router.get("/memory")
async def debug_memory_report():
    try:
        from aitest.platform.lifecycle import get_registry, LeakAnalyzer
        return LeakAnalyzer(get_registry()).find_top_leaks(top_n=30)
    except Exception as e:
        return {"error": str(e)[:300]}


@debug_router.get("/memory/snapshot")
async def debug_memory_snapshot():
    try:
        from aitest.platform.lifecycle import get_registry
        return get_registry().snapshot()
    except Exception as e:
        return {"error": str(e)[:300]}


@debug_router.get("/memory/diff")
async def debug_memory_diff():
    try:
        from aitest.platform.lifecycle import get_registry, LeakAnalyzer
        return LeakAnalyzer(get_registry()).growth_attribution()
    except Exception as e:
        return {"error": str(e)[:300]}


@debug_router.get("/memory/retain/{lifecycle_id:path}")
async def debug_retain_chain(lifecycle_id: str):
    try:
        from aitest.platform.lifecycle import get_registry, LeakAnalyzer
        return LeakAnalyzer(get_registry()).find_retain_chain(lifecycle_id)
    except Exception as e:
        return {"error": str(e)[:300]}


@debug_router.get("/memory/gc-top")
async def debug_gc_top(limit: int = 20):
    try:
        from aitest.platform.lifecycle import LeakAnalyzer
        return {
            "top_objects": LeakAnalyzer.top_gc_objects(limit=limit),
            "note": "Shallow sizes only (sys.getsizeof).",
        }
    except Exception as e:
        return {"error": str(e)[:300]}


# ── Thread + Queue observability (RCA 2026-06-24) ─────────────────────

@debug_router.get("/memory/threads")
async def debug_threads():
    import threading
    frames = sys._current_frames()
    threads = []
    for t in threading.enumerate():
        frame = frames.get(t.ident)
        stack = []
        if frame:
            try:
                stack = _traceback.format_stack(frame)
            except Exception:
                stack = []
        threads.append({
            "name": t.name, "ident": t.ident, "daemon": t.daemon,
            "alive": t.is_alive(),
            "stack_top": [s.strip() for s in stack[-3:]] if stack else [],
        })
    chat_threads = [t for t in threads if "chat-" in t["name"]]
    return {
        "total": len(threads),
        "daemon_count": sum(1 for t in threads if t["daemon"]),
        "chat_thread_count": len(chat_threads),
        "chat_threads": chat_threads,
        "all_threads": threads,
    }


@debug_router.get("/memory/chat-queues")
async def debug_chat_queues():
    from aitest.server.api.chat import sessions
    result = []
    for sid, s in list(sessions.items()):
        qsize = s.agent_queue.qsize() if s.agent_queue else 0
        thread_alive = s.agent_thread.is_alive() if s.agent_thread else False
        cancel_set = s._cancel_event.is_set() if hasattr(s, '_cancel_event') else False
        result.append({
            "session_id": sid, "queue_size": qsize,
            "queue_maxsize": getattr(s, '_QUEUE_MAXSIZE', 0),
            "thread_alive": thread_alive, "cancel_signalled": cancel_set,
            "messages_count": len(s.messages),
            "age_s": round(time.time() - s.created_at, 1) if s.created_at else 0,
        })
    result.sort(key=lambda x: -x["age_s"])
    warnings = []
    for r in result:
        if r["thread_alive"] and r["queue_size"] == 0 and r["age_s"] > 120:
            warnings.append(f"{r['session_id']}: thread alive {r['age_s']:.0f}s but queue empty")
        if not r["thread_alive"] and r["queue_size"] > 0:
            warnings.append(f"{r['session_id']}: thread dead but queue has {r['queue_size']} items")
    return {
        "sessions": result, "total": len(result),
        "total_queue_items": sum(r["queue_size"] for r in result),
        "alive_threads": sum(1 for r in result if r["thread_alive"]),
        "warnings": warnings,
    }


# ── Ownership Enforcement (v2.9) ──────────────────────────────────────

@debug_router.get("/ownership/scan")
async def debug_ownership_scan():
    try:
        from aitest.platform.ownership import get_ownership_checker
        return get_ownership_checker().scan(max_objects=50)
    except Exception as e:
        return {"error": str(e)[:300]}


@debug_router.get("/ownership/tasks")
async def debug_ownership_tasks():
    try:
        from aitest.platform.ownership import get_task_guard
        return {"stats": get_task_guard().stats}
    except Exception as e:
        return {"error": str(e)[:300]}


@debug_router.get("/ownership/stores")
async def debug_ownership_stores():
    stores = {}
    try:
        from aitest.server.api.chat import sessions as _cs
        stores["chat-sessions"] = len(_cs)
    except Exception:
        pass
    try:
        from aitest.onboarding.project_onboarding_agent import _sessions as _os
        stores["onboarding-sessions"] = len(_os)
    except Exception:
        pass
    try:
        from aitest.server.api.onboarding import _active_agents as _oa
        stores["onboarding-agents"] = len(_oa)
    except Exception:
        pass
    return {"stores": stores, "total": sum(stores.values())}


@debug_router.post("/ownership/enforce")
async def debug_ownership_enforce(request: Request):
    try:
        from aitest.platform.ownership import get_ownership_checker
        from aitest.platform.lifecycle import get_registry
        checker = get_ownership_checker()
        scan = checker.scan(max_objects=100)
        violations = scan.get("violations", [])
        disposed = 0
        for v in violations:
            try:
                if get_registry().dispose(v["lifecycle_id"]):
                    disposed += 1
            except Exception:
                pass
        return {"violations_found": len(violations), "disposed": disposed,
                "remaining": len(violations) - disposed}
    except Exception as e:
        return {"error": str(e)[:300]}


# ── Memory Control Plane (v2.8) ───────────────────────────────────────

@debug_router.post("/memory/control")
async def debug_memory_control(request: Request):
    try:
        body = {}
        try:
            if await request.body():
                body = await request.json()
        except Exception:
            pass

        action = body.get("action", "check")
        from aitest.platform.lifecycle import get_memory_guard, get_registry
        guard = get_memory_guard()

        if "soft_limit_mb" in body:
            guard.soft_limit_mb = float(body["soft_limit_mb"])
        if "hard_limit_mb" in body:
            guard.hard_limit_mb = float(body["hard_limit_mb"])

        if action == "check":
            result = guard.check()
        elif action == "cascade":
            registry = get_registry()
            largest = guard._dispose_largest(limit=10)
            oldest = guard._dispose_oldest(limit=10)
            swept = registry.sweep()
            collected = __import__('gc').collect()
            result = {
                "action": "cascade", "largest_disposed": largest,
                "oldest_disposed": oldest, "swept": swept,
                "gc_collected": collected, "remaining_alive": len(registry),
            }
        elif action == "gc":
            collected = __import__('gc').collect()
            result = {"action": "gc", "collected": collected}
        else:
            return {"error": f"Unknown action: {action}. Use check, cascade, or gc."}

        result["soft_limit_mb"] = guard.soft_limit_mb
        result["hard_limit_mb"] = guard.hard_limit_mb
        result["guard_stats"] = {
            "check_count": guard._check_count, "cascade_count": guard._cascade_count,
            "total_disposed_by_guard": guard._total_disposed_by_guard,
        }
        return result
    except Exception as e:
        return {"error": str(e)[:300]}
