"""AI Test Platform — FastAPI service entry point.

Start: python -m aitest.server.main
      uvicorn aitest.server.main:app --reload --port 8000
      aitest server start --reload
"""
from __future__ import annotations
import sys
import asyncio
import time
import uuid
import threading
from contextlib import asynccontextmanager
from pathlib import Path

# Windows: SelectorEventLoop avoids SSE disconnect errors on ProactorEventLoop
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles


# ══════════════════════════════════════════════════════════════════════════
#  Lifespan — delegates to server/core/ modules
# ══════════════════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    from aitest.infra.logging import get_logger
    log = get_logger("server")

    # Init DB
    from aitest.server.session_store import init_db
    await init_db()
    log.info("session_db_initialized")

    # Task runner (P4: auto-detect Redis or SQLite)
    from aitest.infra.queue_factory import get_queue, get_backend
    queue = get_queue()
    backend = get_backend()
    if backend == "sqlite":
        from aitest.infra.task_queue import get_runner
        runner = get_runner()
        runner.start()
        log.info("task_runner_started", backend="sqlite",
                 pending=queue.count_by_status().get("pending", 0))
    else:
        log.info("task_queue_ready", backend="redis",
                 pending=queue.count_by_status().get("pending", 0))
        worker_flag = " --worker-class rq.SimpleWorker" if sys.platform == "win32" else ""
        log.info("rq_worker_hint",
                 cmd=f"rq worker aitest-tasks --url redis://localhost:6379/0{worker_flag}")

    # Wire event_bus → review_graph (break circular import, P0 2026-06-27)
    from aitest.audit_engine.event_bus import set_review_runner
    from aitest.graphs.review_graph import run_review
    set_review_runner(run_review)

    # Activate platform subscribers (v2.3-v2.5)
    from aitest.server.core.subscribers import activate_subscribers
    activated = await activate_subscribers(log)

    # Lifecycle + ownership infrastructure (v2.9)
    from aitest.platform.lifecycle import get_registry, get_memory_guard, _ObjectRef
    lifecycle_registry = get_registry()
    memory_guard = get_memory_guard()
    from aitest.platform.ownership import get_ownership_checker, get_task_guard
    task_guard = get_task_guard()
    ownership_checker = get_ownership_checker()

    # Agent terminal WS — register for lifecycle tracking
    from aitest.server.api.terminal import get_agent_terminal_ws
    agent_terminal_ws = get_agent_terminal_ws()
    from aitest.server.api.kanban import get_kanban_ws
    kanban_ws = get_kanban_ws()
    for lid, obj in [
        ("audit-logger", activated.get("audit-logger")),
        ("webhook-dispatcher", activated.get("webhook-dispatcher")),
        ("metrics-consumer", activated.get("metrics-consumer")),
        ("billing-hook", activated.get("billing-hook")),
        ("quota-usage", activated.get("quota-usage")),
        ("agent-terminal-ws", agent_terminal_ws),
        ("kanban-ws", kanban_ws),
    ]:
        if obj is not None:
            lifecycle_registry.register(_ObjectRef(lid, "main:lifespan", obj))

    # Background loops
    audit_stop = asyncio.Event()
    from aitest.config import config

    from aitest.server.core.audit_scheduler import audit_scheduler_loop
    audit_task = task_guard.create_task(
        audit_scheduler_loop(log, config.audit_interval, audit_stop),
        owner="main:lifespan", lifecycle_id="audit-scheduler",
    )

    from aitest.server.core.sweep import lifecycle_sweep_loop, rate_state_cleanup_loop
    sweep_task = task_guard.create_task(
        lifecycle_sweep_loop(log, lifecycle_registry, memory_guard, ownership_checker, task_guard),
        owner="main:lifespan", lifecycle_id="sweep-loop", ttl_s=0,
    )
    rate_cleanup_task = task_guard.create_task(
        rate_state_cleanup_loop(_rate_state, _rate_lock, _RATE_WINDOW),
        owner="main:lifespan", lifecycle_id="rate-cleanup",
    )

    # ★ v2.6: Crash recovery — detect in-flight runs from previous session
    try:
        from aitest.platform.run_store import get_run_store
        rs = get_run_store()
        orphaned = rs.recover_crashed_runs()
        if orphaned:
            log.warning("crash_recovery", orphaned_runs=orphaned)
        from aitest.infra.task_queue import get_queue
        tq = get_queue()
        tq.recover_stale_tasks()
    except Exception:
        pass

    log.info("server_started", audit_interval_s=config.audit_interval)

    yield  # ── Server running ──

    # Shutdown
    log.info("server_shutdown_start")
    audit_stop.set()
    cancelled = task_guard.cancel_all()
    log.info("task_guard_cancel_all", cancelled=cancelled)

    # Dispose session stores
    try:
        from aitest.server.api.chat import sessions as _chat_sessions
        _chat_sessions.dispose_all()
    except Exception:
        pass
    try:
        from aitest.onboarding.project_onboarding_agent import _sessions as _onb_sessions
        _onb_sessions.dispose_all()
    except Exception:
        pass
    try:
        from aitest.server.api.onboarding import _active_agents as _onb_agents
        _onb_agents.dispose_all()
    except Exception:
        pass

    count = lifecycle_registry.dispose_all()
    log.info("lifecycle_dispose_all_complete", count=count)
    runner.stop()
    log.info("server_shutdown_complete")


# ══════════════════════════════════════════════════════════════════════════
#  App
# ══════════════════════════════════════════════════════════════════════════

app = FastAPI(
    title="AITest Platform",
    description="AI automated testing platform API — v2.5 Architecture Freeze",
    version="2.5.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)


# ── P3-1: Request ID Middleware — every request gets X-Request-Id ─────

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-Id", str(uuid.uuid4())[:12])
    request.state.request_id = req_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = req_id
    return response


# ── Rate Limiting Middleware ────────────────────────────────────────────

_rate_state: dict[str, list[float]] = {}
_rate_lock = threading.Lock()
_RATE_WINDOW = 60
_RATE_MAX_REQUESTS = 60
_RATE_EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/"}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    path = request.url.path
    if path not in _RATE_EXEMPT_PATHS and not path.startswith("/static"):
        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - _RATE_WINDOW
        with _rate_lock:
            timestamps = _rate_state.get(client_ip, [])
            timestamps = [t for t in timestamps if t > window_start]
            if not timestamps:
                _rate_state.pop(client_ip, None)
            if len(timestamps) >= _RATE_MAX_REQUESTS:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": f"Rate limit exceeded ({_RATE_MAX_REQUESTS}/{_RATE_WINDOW}s).",
                            "request_id": getattr(request.state, "request_id", ""),
                        }
                    },
                )
            timestamps.append(now)
            _rate_state[client_ip] = timestamps
    return await call_next(request)


# ── Auth Middleware ──────────────────────────────────────────────────────

from starlette.middleware.base import BaseHTTPMiddleware
from aitest.server.auth import auth_middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)


# ── P3-1: Unified error handler — consistent error responses ──────────

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.responses import JSONResponse


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail,
                "request_id": getattr(request.state, "request_id", ""),
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": str(exc.errors()),
                "request_id": getattr(request.state, "request_id", ""),
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    from aitest.infra.logging import get_logger
    _log = get_logger("server")
    req_id = getattr(request.state, "request_id", "")
    _log.error("unhandled_exception", request_id=req_id, error=str(exc)[:200])
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error",
                "request_id": req_id,
            }
        },
    )


# ══════════════════════════════════════════════════════════════════════════
#  Core Endpoints
# ══════════════════════════════════════════════════════════════════════════

@app.get("/api/info")
async def api_info():
    return {"name": "TLO Platform", "version": "2.5.0", "frontend": "aitest/web/ (React 18)", "docs": "/docs"}


@app.get("/metrics")
async def metrics():
    from aitest.infra.metrics import get_metrics_response
    from fastapi.responses import Response
    body, status, headers = get_metrics_response()
    return Response(content=body, status_code=status, headers=headers)


@app.get("/health")
async def health():
    from aitest.server.core.health import get_health_response
    return await get_health_response()


# ══════════════════════════════════════════════════════════════════════════
#  Router Mounting
# ══════════════════════════════════════════════════════════════════════════

from aitest.server.api.agents import agents_router
from aitest.server.api.webhooks import webhooks_router
from aitest.server.api.workflows import workflows_router
from aitest.server.api.bugs import bugs_router
from aitest.server.api.chat import chat_router
from aitest.server.api.sessions_api import router as sessions_router
from aitest.server.api.onboarding import onboarding_router
from aitest.server.api.integrations import integrations_router
from aitest.server.api.platform import platform_router
from aitest.server.api.workspace import workspace_router
from aitest.server.api.execution import execution_router
from aitest.server.api.debug import debug_router
from aitest.server.api.audit import audit_router
from aitest.server.api.kpi import kpi_router
from aitest.server.api.kanban import kanban_router
from aitest.server.api.terminal import terminal_router
from aitest.server.api.observability import obs_router

app.include_router(platform_router)
app.include_router(workspace_router)
app.include_router(execution_router)
app.include_router(agents_router)
app.include_router(webhooks_router)
app.include_router(workflows_router)
app.include_router(bugs_router)
app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(onboarding_router)
app.include_router(integrations_router)
app.include_router(debug_router)
app.include_router(audit_router)
app.include_router(kpi_router)
app.include_router(kanban_router)
app.include_router(terminal_router)
app.include_router(obs_router)

# Static files
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# SPA frontend (Tauri desktop shell loads from this)
_DIST_DIR = Path(__file__).resolve().parents[1] / "web" / "dist"
if _DIST_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=str(_DIST_DIR / "assets")), name="assets")
    # SPA fallback: index.html for unmatched routes
    app.mount("/", StaticFiles(directory=str(_DIST_DIR), html=True), name="spa")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
