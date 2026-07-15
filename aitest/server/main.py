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
import os
import threading
import logging
from contextlib import asynccontextmanager
from pathlib import Path

# Windows: SelectorEventLoop avoids SSE disconnect errors on older Python
# versions. Python 3.14 deprecates the policy API, so keep the platform
# default there and let uvicorn manage the event loop.
if sys.platform == "win32" and sys.version_info < (3, 14):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from aitest.platform.plugin import get_plugin_manager

logger = logging.getLogger(__name__)


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

    # Wire infra/metrics → llm/circuit_breaker (break circular import)
    from aitest.infra.metrics import register_cb_metrics_provider
    from alice_engine.runtime.core.circuit_breaker import get_all_metrics
    register_cb_metrics_provider(get_all_metrics)

    # Task runner (P4: auto-detect Redis or SQLite)
    from aitest.infra.queue_factory import get_queue, get_backend
    queue = get_queue()
    backend = get_backend()
    runner = None
    if backend == "sqlite":
        from aitest.infra.task_queue import get_runner
        runner = get_runner()
        # Inject agent executor (break infra → agents cycle)
        def _agent_executor(task):
            from alice_engine.core.executor import run_agent
            return run_agent(
                agent_name=task["agent"], provider=task.get("provider", "claude"),
                module=task["module"], page=task.get("page", ""),
                mode=task.get("mode", "full"), verbose=False,
            )
        runner._executor = _agent_executor
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
    try:
        from aitest.audit_engine.event_bus import set_review_runner
        from alice_engine.workflow.review_graph import run_review
        set_review_runner(run_review)
    except (ImportError, ModuleNotFoundError):
        log.info("review_graph_not_available", msg="skipping review_graph wiring")

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
        ("report-consumer", activated.get("report-consumer")),
        ("agent-terminal-ws", agent_terminal_ws),
        ("kanban-ws", kanban_ws),
    ]:
        if obj is not None:
            lifecycle_registry.register(_ObjectRef(lid, "main:lifespan", obj))

    # Background loops
    audit_stop = asyncio.Event()
    rq_recovery_stop = asyncio.Event()
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

    rq_recovery_task = None
    if backend == "redis" and hasattr(queue, "recover_stale_tasks"):
        from aitest.server.core.rq_recovery import rq_recovery_loop

        rq_recovery_task = task_guard.create_task(
            rq_recovery_loop(
                queue,
                rq_recovery_stop,
                interval_seconds=float(os.environ.get("AITEST_RQ_RECOVERY_INTERVAL", "60")),
                stale_after_seconds=float(os.environ.get("AITEST_RQ_STALE_AFTER", "3600")),
                log=log,
            ),
            owner="main:lifespan", lifecycle_id="rq-stale-recovery",
        )

    # ★ v2.6: Crash recovery — detect in-flight runs from previous session
    try:
        from aitest.platform.run_store import get_run_store
        rs = get_run_store()
        orphaned = rs.recover_crashed_runs()
        if orphaned:
            log.warning("crash_recovery", orphaned_runs=orphaned)
        recovered_requests = rs.recover_stale_requests()
        if recovered_requests:
            log.warning("stale_request_recovery", recovered_requests=recovered_requests)
        if backend == "redis" and hasattr(queue, "recover_stale_tasks"):
            queue.recover_stale_tasks(
                stale_after_seconds=float(os.environ.get("AITEST_RQ_STALE_AFTER", "3600"))
            )
        else:
            from aitest.infra.task_queue import get_queue
            get_queue().recover_stale_tasks()
    except Exception as e:
        log.warning("crash_recovery_failed", error=str(e))

    # v3.1 / Phase 8: explicit composition-root wiring for shared services
    from aitest.server.core.composition import install_shared_services
    install_shared_services(app.state, log)

    # v5.4: embedded execution worker for backward compatibility
    worker = None
    if os.environ.get("AITEST_EXECUTION_WORKER_DISABLED", "").lower() not in {"1", "true", "yes"}:
        from aitest.platform.execution_worker import get_execution_worker

        worker = get_execution_worker(service=app.state.execution_service)
        worker.start()
        app.state.execution_worker = worker
        log.info("execution_worker_started", worker_id=worker.worker_id)

    log.info("server_started", audit_interval_s=config.audit_interval)

    yield  # ── Server running ──

    # Shutdown
    log.info("server_shutdown_start")
    audit_stop.set()
    rq_recovery_stop.set()
    cancelled = task_guard.cancel_all()
    log.info("task_guard_cancel_all", cancelled=cancelled)

    # Dispose session stores (best-effort — log but don't block shutdown)
    try:
        from aitest.server.api.chat import sessions as _chat_sessions
        _chat_sessions.dispose_all()
    except Exception as e:
        log.warning("chat_sessions_dispose_failed", error=str(e))
    try:
        from aitest.onboarding.project_onboarding_agent import _sessions as _onb_sessions
        _onb_sessions.dispose_all()
    except Exception as e:
        log.warning("onboarding_sessions_dispose_failed", error=str(e))
    try:
        from aitest.server.api.onboarding import _active_agents as _onb_agents
        _onb_agents.dispose_all()
    except Exception as e:
        log.warning("onboarding_agents_dispose_failed", error=str(e))

    # Deactivate subscribers (stop hooks, consumers, dispatchers)
    from aitest.server.core.subscribers import deactivate_subscribers
    stopped = await deactivate_subscribers(activated, log)
    log.info("subscribers_deactivated", count=stopped)

    count = lifecycle_registry.dispose_all()
    log.info("lifecycle_dispose_all_complete", count=count)
    if runner is not None:
        runner.stop()
    if worker is not None:
        worker.stop()
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
_RATE_MAX_REQUESTS = int(os.getenv("AITEST_RATE_MAX_REQUESTS", "60"))
_RATE_EXEMPT_PATHS = {
    "/health", "/ready", "/docs", "/openapi.json", "/",
    # The response is sampled and cached internally; dashboard polling should
    # not consume the general API request budget.
    "/api/v1/observability/snapshot",
}


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


@app.middleware("http")
async def control_audit_middleware(request: Request, call_next):
    """Audit state-changing API requests with resolved identity context."""
    response = await call_next(request)
    if request.method in {"POST", "PUT", "PATCH", "DELETE"} and request.url.path.startswith("/api/"):
        try:
            from aitest.platform.audit_log import get_audit_logger
            get_audit_logger().record_action(
                action=f"http.{request.method.lower()}",
                actor=getattr(request.state, "user_id", "anonymous"),
                org_id=getattr(request.state, "org_id", "") or request.headers.get("X-Org-Id", ""),
                resource_type="http",
                resource_id=request.url.path,
                request_id=getattr(request.state, "request_id", ""),
                outcome="success" if response.status_code < 400 else "error",
                metadata={"status_code": response.status_code},
            )
        except Exception:
            pass
    return response


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
async def health(request: Request):
    from aitest.server.core.health import get_health_response
    return await get_health_response(app_state=request.app.state)


@app.get("/ready")
async def ready():
    from aitest.platform.deployment_preflight import run_deployment_preflight
    from fastapi.responses import JSONResponse
    result = run_deployment_preflight()
    return JSONResponse(result.to_dict(), status_code=200 if result.status != "blocked" else 503)


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
from aitest.server.api.insights import insights_router
from aitest.server.api.runs import runs_router  # P7-2: 统一执行入口
from aitest.server.api.quality import quality_router  # P5-1: Quality Loop
from aitest.server.api.workflows_v1 import workflows_v1_router  # P8-1: Workflow 资源化
from aitest.server.api.providers_v1 import providers_router  # P6-1: ModelProvider 资源化
from aitest.server.api.secrets_v1 import secrets_router  # P6-5: Secret Manager
from aitest.server.api.environments_v1 import environments_router  # P6-4: Environment 资源化
from aitest.server.api.workers_v1 import workers_router  # P3-5: Worker Lease/Heartbeat
from aitest.server.api.billing_v1 import billing_router  # P3-6: Billing REST API
from aitest.server.api.human_gates import human_gates_router
from aitest.server.api.registry_v1 import registry_router
from aitest.server.api.mcp_servers_v1 import mcp_servers_router
from aitest.server.api.notifications_v1 import notifications_router
from aitest.server.api.modules_v1 import modules_router

app.include_router(runs_router)  # P7-2: 新端点优先注册
app.include_router(quality_router)  # P5-1: Quality Loop
app.include_router(workflows_v1_router)  # P8-1: Workflow 资源化
app.include_router(providers_router)  # P6-1: ModelProvider 资源化
app.include_router(secrets_router)  # P6-5: Secret Manager
app.include_router(environments_router)  # P6-4: Environment 资源化
app.include_router(workers_router)  # P3-5: Worker Lease/Heartbeat
app.include_router(billing_router)  # P3-6: Billing REST API
app.include_router(human_gates_router)
app.include_router(registry_router)
app.include_router(mcp_servers_router)
app.include_router(notifications_router)
app.include_router(modules_router)
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
app.include_router(insights_router)

# P6-3: 动态注册 Plugin API 路由
def _register_plugin_routes(target_app: FastAPI | None = None):
    """从 PluginManager 动态注册 Plugin 提供的 API 路由。

    Plugin API 路由类需要实现 create_router() 方法 → APIRouter。
    """
    target_app = target_app or app
    try:
        pm = get_plugin_manager()
        pm.load_all()

        for prefix, router_class in pm.get_api_routes():
            try:
                # 实例化 Router 类并调用 create_router() 方法
                router_instance = router_class()
                if hasattr(router_instance, "create_router"):
                    router = router_instance.create_router()
                    target_app.include_router(router, prefix=prefix)
                    logger.info(f"[Plugin] API route registered: {prefix}")
                else:
                    logger.warning(
                        f"[Plugin] API route class '{router_class.__name__}' "
                        f"missing create_router() method, skipped"
                    )
            except Exception as e:
                logger.error(
                    f"[Plugin] API route registration failed for {prefix}: {e}"
                )

    except Exception as e:
        # Plugin 加载失败不应中断服务启动
        logger.warning(f"[Plugin] API route discovery failed: {e}")


_register_plugin_routes()

# Static files
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

# SPA frontend (Tauri desktop shell loads from this)
_DIST_DIR = Path(__file__).resolve().parents[1] / "web" / "dist"
if _DIST_DIR.is_dir():
    from fastapi.responses import FileResponse

    app.mount("/assets", StaticFiles(directory=str(_DIST_DIR / "assets")), name="assets")

    # SPA fallback: serve index.html for all non-API routes
    @app.get("/{full_path:path}")
    async def spa_fallback(full_path: str):
        # Don't serve index.html for API routes
        if full_path.startswith("api/") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            raise HTTPException(status_code=404, detail="Not found")
        # Try to serve static file first
        file_path = _DIST_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        # Fallback to index.html for SPA routing
        return FileResponse(str(_DIST_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    host = os.environ.get("AITEST_SERVER_HOST", "0.0.0.0")
    try:
        port = int(os.environ.get("AITEST_SERVER_PORT", "8000"))
    except ValueError as exc:
        raise SystemExit("AITEST_SERVER_PORT must be an integer") from exc
    uvicorn.run(app, host=host, port=port)
