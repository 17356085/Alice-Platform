"""AI Test Platform — FastAPI 服务入口。

启动: python -m aitest.server.main
       uvicorn aitest.server.main:app --reload --port 8000
       aitest server start --reload

启动后访问 http://localhost:8000/docs 查看交互式 API 文档。
"""
import sys
import os
import asyncio
from datetime import datetime

# Windows: 用 SelectorEventLoop 替代 ProactorEventLoop，避免 SSE 断开时报
# "Exception in callback _ProactorBasePipeTransport._call_connection_lost(None)"
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from aitest.server.api.agents import agents_router
from aitest.server.api.webhooks import webhooks_router
from aitest.server.api.workflows import workflows_router
from aitest.server.api.bugs import bugs_router
from aitest.server.api.chat import chat_router
from aitest.server.api.sessions_api import router as sessions_router
from aitest.server.api.onboarding import onboarding_router
from aitest.server.api.integrations import integrations_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from aitest.infra.logging import get_logger
    log = get_logger("server")

    # Init session DB
    from aitest.server.session_store import init_db
    await init_db()
    log.info("session_db_initialized")

    from aitest.infra.task_queue import get_runner, get_queue
    runner = get_runner()
    runner.start()
    queue = get_queue()
    pending = queue.count_by_status().get("queued", 0)
    log.info("task_runner_started", pending=pending)

    # P1-ACTIVATION (2026-06-15): 生产环境激活 KnowledgeAgentSubscriber
    try:
        from aitest.audit_engine.event_bus import KnowledgeAgentSubscriber
        _gov_subscriber = KnowledgeAgentSubscriber(provider="claude", auto_process=True)
        _gov_subscriber.activate()
        log.info("governance_subscriber_activated")
    except Exception as e:
        log.error("governance_subscriber_failed", error=str(e))

    # P2-ACTIVATION (2026-06-16): Dead Path — 审计未自动调度
    # 后台 asyncio Task 周期性运行 State/SOP/Cost 审计
    from aitest.config import config
    audit_interval = config.audit_interval
    _audit_stop = asyncio.Event()

    async def _audit_scheduler():
        """后台审计调度器 — 周期性运行全量审计并发射治理事件。"""
        # 启动后等待 60s 再首次审计（让服务完全初始化）
        await asyncio.sleep(60)
        iteration = 0
        from aitest.audit_engine.scheduled_audit import run_all_audits, discover_modules
        while not _audit_stop.is_set():
            iteration += 1
            started = asyncio.get_event_loop().time()
            log.info("scheduled_audit_start", iteration=iteration)

            try:
                # 在线程池中运行审计（审计器包含阻塞 I/O）
                modules = discover_modules()
                results = await asyncio.to_thread(run_all_audits, modules)

                state_drifts = sum(
                    r.get("drift_count", 0)
                    for r in results["state_audits"].values()
                )
                sop_violations = sum(
                    r.get("violations", 0)
                    for r in results["sop_audits"].values()
                )
                cost_info = results.get("cost_audit", {})
                duration = asyncio.get_event_loop().time() - started
                log.info("scheduled_audit_done", iteration=iteration,
                         state_drifts=state_drifts, sop_violations=sop_violations,
                         cost=round(cost_info.get('total_cost', 0), 4),
                         duration_s=round(duration, 1))

                # 审计后检查是否需要触发架构评审
                try:
                    from aitest.audit_engine.review_trigger import check_and_enqueue, format_queue_summary
                    tasks = check_and_enqueue()
                    if tasks:
                        summary = format_queue_summary()
                        print(f"[ReviewTrigger] {len(tasks)} review(s) enqueued:")
                        for t in tasks:
                            print(f"  - {t.urgency.upper()}: {t.mode} ({t.reason})")
                except Exception as re:
                    print(f"[ReviewTrigger] check failed: {re}")

            except Exception as e:
                print(f"[ScheduledAudit] #{iteration} error: {e}")

            # 等待下一次审计（支持提前取消）
            try:
                await asyncio.wait_for(_audit_stop.wait(), timeout=audit_interval)
            except asyncio.TimeoutError:
                pass  # 正常超时，继续下一次审计

        print(f"[ScheduledAudit] Stopped. {iteration} iterations completed.")

    _audit_task = asyncio.create_task(_audit_scheduler())
    print(f"[Governance] Audit scheduler started — interval={audit_interval}s")

    yield

    # ── Shutdown ──
    _audit_stop.set()
    _audit_task.cancel()
    try:
        await _audit_task
    except asyncio.CancelledError:
        pass
    print("[Governance] Audit scheduler stopped.")
    runner.stop()
    print("[TaskRunner] Stopped.")


app = FastAPI(
    title="AITest Platform",
    description="AI 自动化测试平台 API — Agent 触发 · Workflow 管理 · Bug 历史 · Chat Agent",
    version="0.4.0",
    lifespan=lifespan,
)

# CORS — 允许浏览器直接访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Rate Limiting Middleware ──────────────────────────────────────────
# Simple sliding-window per-IP rate limiter for REST API.
# MCP tools have their own rate limiting in mcp/rate_limit.py.

_rate_state: dict[str, list[float]] = {}
_rate_lock = __import__('threading').Lock()
_RATE_WINDOW = 60       # seconds
_RATE_MAX_REQUESTS = 60  # per window per IP
_RATE_EXEMPT_PATHS = {"/health", "/docs", "/openapi.json", "/"}


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple IP-based sliding window rate limiter for REST endpoints."""
    path = request.url.path

    if path not in _RATE_EXEMPT_PATHS and not path.startswith("/static"):
        client_ip = request.client.host if request.client else "unknown"
        now = __import__('time').time()
        window_start = now - _RATE_WINDOW

        with _rate_lock:
            timestamps = _rate_state.get(client_ip, [])
            timestamps = [t for t in timestamps if t > window_start]
            if len(timestamps) >= _RATE_MAX_REQUESTS:
                from fastapi.responses import JSONResponse
                return JSONResponse(
                    status_code=429,
                    content={"detail": f"Rate limit exceeded ({_RATE_MAX_REQUESTS}/{_RATE_WINDOW}s). Retry later."},
                )
            timestamps.append(now)
            _rate_state[client_ip] = timestamps

    return await call_next(request)


# ── Auth Middleware ───────────────────────────────────────────────────
# Disabled by default (no AITEST_API_KEY set). Set the env var to enable.

from fastapi.middleware.base import BaseHTTPMiddleware
from aitest.server.auth import auth_middleware
app.add_middleware(BaseHTTPMiddleware, dispatch=auth_middleware)


@app.get("/")
async def root():
    """API root — Vue 3 SPA is the frontend (see aitest/web/)."""
    return {
        "name": "TLO Platform",
        "version": "1.0.0",
        "frontend": "aitest/web/ (Vue 3 + shadcn-vue)",
        "docs": "/docs",
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics — operational counters, gauges, histograms."""
    from aitest.infra.metrics import get_metrics_response
    body, status, headers = get_metrics_response()
    from fastapi.responses import Response
    return Response(content=body, status_code=status, headers=headers)


@app.get("/health")
async def health():
    """P2-5: 平台健康检查 — 各组件状态汇总。"""
    from aitest.infra.task_queue import get_queue
    from aitest.infra.error_logger import get_summary as error_summary

    components = {}
    overall = "healthy"

    # ── Task Queue ──
    try:
        queue = get_queue()
        components["task_queue"] = {"status": "ok", "stats": queue.count_by_status()}
    except Exception as e:
        components["task_queue"] = {"status": "error", "error": str(e)[:100]}
        overall = "degraded"

    # ── RAG / ChromaDB ──
    try:
        from aitest.knowledge.rag_engine import get_chroma_client
        client = get_chroma_client()
        colls = client.list_collections()
        components["rag"] = {
            "status": "connected",
            "collections": len(colls),
            "total_docs": sum(c.count() for c in colls),
            "names": [c.name for c in colls],
        }
    except Exception as e:
        components["rag"] = {"status": "disconnected", "error": str(e)[:100]}
        overall = "degraded"

    # ── Known Issues Sync (P2-1) ──
    try:
        from aitest.knowledge.rag_engine import _known_issues_mtime, KNOWN_ISSUES
        yaml_mtime = KNOWN_ISSUES.stat().st_mtime if KNOWN_ISSUES.exists() else 0
        components["known_issues"] = {
            "status": "synced" if _known_issues_mtime >= yaml_mtime else "stale",
            "yaml_mtime": yaml_mtime,
            "index_mtime": _known_issues_mtime,
        }
    except Exception as e:
        components["known_issues"] = {"status": "error", "error": str(e)[:100]}

    # ── Error Log (P0-2) ──
    try:
        summary = error_summary(days=1)
        components["error_log"] = {
            "status": "ok",
            "recent_24h": summary["total"],
            "by_severity": summary.get("by_severity", {}),
        }
    except Exception as e:
        components["error_log"] = {"status": "error", "error": str(e)[:100]}

    # ── Checkpoint DB ──
    try:
        from aitest.graphs.checkpoint import DB_PATH, list_runs
        db_exists = DB_PATH.exists()
        runs = list_runs(limit=5) if db_exists else []
        components["checkpoint_db"] = {
            "status": "connected" if db_exists else "empty",
            "path": str(DB_PATH),
            "recent_runs": len(runs),
        }
    except Exception as e:
        components["checkpoint_db"] = {"status": "error", "error": str(e)[:100]}

    # ── LLM Provider ──
    try:
        from aitest.config import config
        provider = config.resolve_llm_provider()
        components["llm"] = {"status": "ok", "resolved_provider": provider}

        # Circuit breaker metrics
        from aitest.llm.circuit_breaker import get_all_metrics
        cb_metrics = get_all_metrics()
        if cb_metrics:
            open_breakers = [m for m in cb_metrics if m["state"] == "open"]
            components["llm"]["circuit_breakers"] = {
                "total": len(cb_metrics),
                "open": len(open_breakers),
                "details": {m["name"]: m["state"] for m in cb_metrics},
            }
    except Exception as e:
        components["llm"] = {"status": "error", "error": str(e)[:100]}
        if overall == "healthy":
            overall = "degraded"

    # ── Session DB ──
    try:
        from aitest.server.session_store import engine
        components["session_db"] = {"status": "connected"}
    except Exception as e:
        components["session_db"] = {"status": "error", "error": str(e)[:100]}

    # ── Tenants (multi-project) ──
    try:
        from aitest.platform.tenant import get_tenant_manager
        tm = get_tenant_manager()
        tenants = tm.list_tenants()
        components["tenants"] = {
            "status": "ok",
            "count": len(tenants),
            "ids": tenants,
        }
    except Exception as e:
        components["tenants"] = {"status": "error", "error": str(e)[:100]}

    # ── Worker Pool (★ M3) ──
    try:
        from aitest.infra.worker_pool import get_worker_pool
        pool = get_worker_pool()
        stats = pool.stats()
        components["worker_pool"] = {
            "status": "ok",
            "max_workers": stats.max_workers,
            "active": stats.active_tasks,
            "queued": stats.queued_tasks,
            "completed": stats.completed_tasks,
            "failed": stats.failed_tasks,
            "per_tenant": stats.per_tenant,
        }
    except Exception as e:
        components["worker_pool"] = {"status": "error", "error": str(e)[:100]}

    return {"status": overall, "components": components}


# ══════════════════════════════════════════════════════════════════════
#  P2-5: Governance Audit API
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/audit/state")
async def audit_state(module: str = "equipment", repair: bool = False):
    """State Auditor — 状态审计 API。"""
    try:
        from aitest.audit_engine.state_auditor import StateAuditor
        auditor = StateAuditor()
        report = auditor.audit(module, auto_repair=repair)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "overall_status": "error", "drift_count": 0, "error_count": 1}


@app.get("/api/audit/sop")
async def audit_sop(module: str = "equipment", days: int = 7):
    """SOP Auditor — SOP 合规审计 API。"""
    try:
        from aitest.audit_engine.sop_auditor import SOPAuditor
        auditor = SOPAuditor()
        report = auditor.audit(module, days=days)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "overall_compliance": 0, "total_violations": 0}


@app.get("/api/audit/cost")
async def audit_cost(days: int = 7):
    """Cost Auditor — 成本审计 API。"""
    try:
        from aitest.audit_engine.cost_auditor import CostAuditor
        auditor = CostAuditor()
        report = auditor.audit(days=days)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "total_cost": 0, "alert_count": 0}


@app.get("/api/audit/safety")
async def audit_safety(module: str = "equipment", days: int = 7):
    """Safety Auditor — 安全审计 API (P0)。"""
    try:
        from aitest.audit_engine.safety_auditor import SafetyAuditor
        auditor = SafetyAuditor()
        report = auditor.audit(module, days=days)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "overall_status": "error", "safety_score": 0}


@app.get("/api/online/analyze")
async def online_analyze(module: str = "system", days: int = 7):
    """Online Monitor — 线上指标分析 API (P0)。"""
    try:
        from aitest.audit_engine.online_monitor import OnlineMonitor
        monitor = OnlineMonitor()
        report = monitor.analyze(module, days=days)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "module": module}


@app.get("/api/trace/{run_id}")
async def trace_replay(run_id: str):
    """Trace 回放 API — 获取指定运行的全部步骤。"""
    try:
        from aitest.audit_engine.online_monitor import get_run_trace_replay
        return get_run_trace_replay(run_id)
    except Exception as e:
        return {"error": str(e)[:300], "run_id": run_id, "steps": []}


@app.get("/api/trace/runs")
async def trace_runs(limit: int = 20):
    """列出最近的运行记录。"""
    try:
        from aitest.audit_engine.online_monitor import list_recent_runs
        return {"runs": list_recent_runs(limit=limit)}
    except Exception as e:
        return {"error": str(e)[:300], "runs": []}


@app.get("/api/audit/governance")
async def audit_governance(module: str = "equipment", days: int = 7):
    """Governance 聚合 API — 一次返回所有审计摘要。"""
    result = {
        "module": module,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }
    try:
        from aitest.audit_engine.state_auditor import StateAuditor
        result["state"] = StateAuditor().audit(module, auto_repair=False)
    except Exception as e:
        result["state"] = {"error": str(e)[:200]}
    try:
        from aitest.audit_engine.sop_auditor import SOPAuditor
        result["sop"] = SOPAuditor().audit(module, days=days)
    except Exception as e:
        result["sop"] = {"error": str(e)[:200]}
    try:
        from aitest.audit_engine.cost_auditor import CostAuditor
        result["cost"] = CostAuditor().audit(days=days)
    except Exception as e:
        result["cost"] = {"error": str(e)[:200]}
    try:
        from aitest.audit_engine.safety_auditor import SafetyAuditor
        result["safety"] = SafetyAuditor().audit(module, days=days)
    except Exception as e:
        result["safety"] = {"error": str(e)[:200]}
    return result


# ══════════════════════════════════════════════════════════════════════════
#  L4 Measured: KPI API
# ══════════════════════════════════════════════════════════════════════════

@app.get("/api/sop-status")
async def sop_status_all(project: str = ""):
    """返回全部模块 SOP 状态 — 用于 Kanban 看板。

    Query params:
        project: override active project (used after onboarding)
    """
    import json
    from pathlib import Path
    from collections import OrderedDict

    # SOP 9 phases — one-to-one with agent-definitions.yaml orchestrator
    # (Preflight + Quality Gate excluded — gates, not agent phases)
    SOP_PHASES = [
        "Project Init", "Requirement", "Test Design",
        "Automation", "Execute & Debug", "Bug Analysis",
        "Data Sanitization", "Report", "Knowledge",
    ]

    # Read from .tlo/runtime/sop-status/ first, then per-project dir, then legacy flat
    from aitest.platform.context import get_active_project_id
    from aitest.platform.paths import get_test_project_root
    project_id = project.strip() or get_active_project_id()
    base = Path(__file__).resolve().parent.parent.parent

    # Search paths in priority order (ADR-001)
    search_dirs = []

    # 1. .tlo/runtime/sop-status/ (if project has .tlo/)
    root = get_test_project_root(project_id)
    if root:
        tlo_runtime = root / ".tlo" / "runtime" / "sop-status"
        if tlo_runtime.exists():
            search_dirs.append(tlo_runtime)

    # 2. Per-project sop-status directory
    per_project = base / "governance" / "artifacts" / "sop-status" / project_id
    per_project.mkdir(parents=True, exist_ok=True)
    search_dirs.append(per_project)

    # 3. Legacy flat directory (for backward compatibility)
    legacy_flat = base / "governance" / "artifacts" / "sop-status"
    if legacy_flat.exists():
        search_dirs.append(legacy_flat)

    modules = OrderedDict()
    seen = set()
    for sop_dir in search_dirs:
        for f in sorted(sop_dir.glob("SOP_STATUS_*.json")):
            mod = f.stem.replace("SOP_STATUS_", "")
            if mod in seen:
                continue
            seen.add(mod)
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                modules[mod] = {"status": "error", "stage": "init", "phase_status": {}, "phases_done": 0, "phases_total": len(SOP_PHASES), "pages": 0, "pages_list": [], "artifacts": 0, "failed": 0, "run_id": "", "updated": "", "note": ""}
                continue
            completed = data.get("completed_phases", [])
            pages = data.get("pages_processed", [])
            phase_status = {p: (p in completed) for p in SOP_PHASES}
            phases_done = len(completed)
            if phases_done >= len(SOP_PHASES):
                stage = "complete"
            else:
                status = data.get("status", "?")
                if status == "completed" or status == "completed_with_issues":
                    stage = "analysis" if status == "completed_with_issues" else "complete"
                elif status == "ready":
                    stage = "automation"
                elif status == "in_progress":
                    stage = "execution"
                else:
                    stage = "init"
            modules[mod] = {
                "status": data.get("status", "?"),
                "stage": stage,
                "phase_status": phase_status,
                "phases_done": phases_done,
                "phases_total": len(SOP_PHASES),
                "pages": len(pages),
                "pages_list": pages,
                "artifacts": data.get("artifact_count", 0),
                "failed": len(data.get("failed_phases", [])),
                "run_id": data.get("run_id", ""),
                "updated": data.get("updated_at", ""),
                "note": (data.get("note", "") or "")[:80],
            }
    return {"modules": modules, "total": len(modules), "sop_phases": SOP_PHASES}


@app.get("/api/kpi/summary")
async def kpi_summary(days: int = 30):
    """KPI 总览 — 治理指标体系聚合。"""
    try:
        from aitest.audit_engine.governance_kpi import KPICollector
        return KPICollector().get_summary(days=days)
    except Exception as e:
        return {"error": str(e)[:300]}


@app.get("/api/kpi/trends")
async def kpi_trends(audit_type: str = "state", days: int = 30):
    """KPI 趋势 — 指定审计类型的趋势分析。"""
    try:
        from aitest.audit_engine.governance_kpi import KPICollector
        collector = KPICollector()
        trends = collector.get_trends(audit_type, days=days)
        return {
            "audit_type": audit_type,
            "period": f"{days}d",
            "trends": [t.__dict__ if hasattr(t, '__dict__') else t for t in trends],
        }
    except Exception as e:
        return {"error": str(e)[:300]}


@app.post("/api/kpi/audit-all")
async def kpi_audit_all(modules: str = None):
    """L4: 一次性审计全部模块（定时调度入口）。"""
    try:
        from aitest.audit_engine.scheduled_audit import run_all_audits, discover_modules
        mod_list = modules.split(",") if modules else discover_modules()
        return run_all_audits(mod_list)
    except Exception as e:
        return {"error": str(e)[:300]}


@app.get("/api/kpi/operational")
async def operational_metrics():
    """★ v1.1: 8 runtime KPIs — agent latency, token cost, workflow, plugin, memory, recovery, phase, capability.

    Returns the current operational metrics snapshot used for data-driven platform evolution.
    """
    try:
        from aitest.platform.operational_metrics import get_collector
        return get_collector().snapshot()
    except Exception as e:
        return {"error": str(e)[:300]}


@app.get("/api/timeline/{project_id}")
async def timeline(project_id: str, limit: int = 50):
    """★ v1.1: Agent 活动时间线 — 调试 Agent 的第一入口。

    Returns recent timeline events: phase transitions, artifacts, errors, retries, memory hits.
    """
    events = []
    try:
        # Operational metrics → timeline entries
        mc = get_collector()
        snap = mc.snapshot()

        # Agent runs
        for agent, data in snap.get("agent_latency_p95", {}).items():
            if data.get("total", 0) > 0:
                events.append({
                    "ts": snap["ts"],
                    "type": "agent_summary",
                    "agent": agent,
                    "message": f"{agent} — {data['total']} runs, p95={data['p95']}s, avg={data['avg']}s",
                })

        # Workflow status
        for mod, data in snap.get("workflow", {}).items():
            events.append({
                "ts": snap["ts"],
                "type": "workflow_status",
                "agent": "workflow",
                "module": mod,
                "message": f"{mod}: {data['success']}/{data['total']} ({round(data['rate']*100)}%)",
                "success": data["rate"] >= 0.9,
            })

        # Recent trace events from JSONL
        try:
            from pathlib import Path
            trace_file = Path(__file__).resolve().parent.parent.parent / "governance" / ".traces" / "trace_log.jsonl"
            if trace_file.exists():
                import json
                lines = []
                with open(trace_file, "r", encoding="utf-8") as f:
                    for line in f:
                        lines.append(line.strip())
                for line in lines[-limit:]:
                    try:
                        te = json.loads(line)
                        events.append({
                            "ts": te.get("timestamp", ""),
                            "type": te.get("event_type", "trace"),
                            "agent": te.get("agent_name", ""),
                            "message": f"{te.get('event_type', '')} — {te.get('provider', '')} {te.get('model', '')} — {te.get('latency_ms', 0)}ms",
                            "tokens": te.get("token_input", 0) + te.get("token_output", 0),
                        })
                    except Exception:
                        pass
        except Exception:
            pass

    except Exception as e:
        events.append({"ts": "", "type": "error", "message": str(e)[:200]})

    return {"project": project_id, "events": events[:limit], "total": len(events)}


@app.get("/api/artifacts/{project_id}")
async def artifacts(project_id: str, module: str = "", page: str = ""):
    """★ v1.1: Artifact 列表 — 项目/模块/页面的 SOP 产物。

    Returns known artifacts with existence status.
    """
    items = []
    try:
        from aitest.platform.paths import get_project_dir

        project_dir = get_project_dir(project_id)
        modules_dir = project_dir / "modules"
        if modules_dir.exists():
            for mod_dir in sorted(modules_dir.iterdir()):
                if not mod_dir.is_dir(): continue
                mod_name = mod_dir.name
                if module and mod_name != module: continue

                # Module-level artifacts
                for doc in ["MODULE_CONTEXT.md", "REQUIREMENT_ANALYSIS.md", "PROJECT_CONTEXT.md"]:
                    path = mod_dir / doc
                    items.append({
                        "name": doc,
                        "path": f"{mod_name}/{doc}",
                        "module": mod_name,
                        "exists": path.exists(),
                        "size": path.stat().st_size if path.exists() else 0,
                    })

                # Page-level artifacts
                pages_dir = mod_dir / "pages"
                if pages_dir.exists():
                    for page_dir in sorted(pages_dir.iterdir()):
                        if not page_dir.is_dir(): continue
                        pname = page_dir.name
                        if page and pname != page: continue
                        for doc in ["PAGE_CONTEXT.md", "RISK_MODEL.md", "TEST_CASES.md",
                                     "TECH_ANALYSIS.md", "AUTO_STRATEGY.md"]:
                            path = page_dir / doc
                            items.append({
                                "name": doc,
                                "path": f"{mod_name}/pages/{pname}/{doc}",
                                "module": mod_name,
                                "page": pname,
                                "exists": path.exists(),
                                "size": path.stat().st_size if path.exists() else 0,
                            })
    except Exception as e:
        items.append({"name": "error", "path": "", "exists": False, "error": str(e)[:100]})

    return {"project": project_id, "artifacts": items, "total": len(items)}


@app.get("/api/kpi/trends/operational")
async def operational_trends(days: int = 7):
    """★ v1.3: 运营指标历史趋势 — 用于前端折线图。

    Reads operational_metrics.jsonl and returns time-series data
    for the 8 KPIs over the last N days.
    """
    from pathlib import Path
    import json

    metrics_file = (
        Path(__file__).resolve().parent.parent.parent
        / "governance" / "kpi" / "timeseries" / "operational_metrics.jsonl"
    )
    if not metrics_file.exists():
        return {"points": [], "message": "No operational metrics data yet"}

    cutoff = None
    if days > 0:
        from datetime import datetime, timedelta, timezone
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

    points = []
    try:
        with open(metrics_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                    ts = entry.get("ts", "")
                    if cutoff and ts:
                        try:
                            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            if dt < cutoff:
                                continue
                        except Exception:
                            pass

                    # Extract key metrics for trending
                    total_tokens = sum(
                        v.get("input", 0) + v.get("output", 0)
                        for v in entry.get("token_cost", {}).values()
                        if isinstance(v, dict)
                    )
                    workflow_rates = [
                        v.get("rate", 0)
                        for v in entry.get("workflow", {}).values()
                        if isinstance(v, dict)
                    ]
                    avg_rate = sum(workflow_rates) / len(workflow_rates) if workflow_rates else 0

                    points.append({
                        "ts": ts[:19] if ts else "",
                        "total_tokens": total_tokens,
                        "workflow_rate": round(avg_rate, 3),
                        "uptime_s": entry.get("uptime_s", 0),
                    })
                except Exception:
                    pass
    except Exception:
        pass

    return {
        "points": points[-200:],  # last 200 data points max
        "total": len(points),
        "days": days,
    }


@app.get("/api/kpi/product")
async def product_kpi():
    """★ v1.4: Product KPI Dashboard — 衡量平台是否比上周更好。

    Returns weekly-aggregated product KPIs:
      - projects, runs, success_rate, avg_duration, cost_per_run, error_rate
      - This week vs last week comparison
      - Phase distribution (which phases take most time)
    """
    from pathlib import Path
    import json
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    def aggregate_since(cutoff):
        stats = {
            "runs": 0, "success": 0, "failed": 0,
            "total_tokens": 0, "total_cost": 0.0,
            "total_duration_s": 0.0, "p95_latency": 0.0,
            "agent_runs": {},
            "phase_times": {},
        }
        metrics_file = (
            Path(__file__).resolve().parent.parent.parent
            / "governance" / "kpi" / "timeseries" / "operational_metrics.jsonl"
        )
        if not metrics_file.exists():
            return stats

        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        entry = json.loads(line)
                        ts = entry.get("ts", "")
                        if ts:
                            try:
                                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                if dt < cutoff: continue
                            except: pass

                        # Agent latency
                        for agent, data in entry.get("agent_latency_p95", {}).items():
                            if isinstance(data, dict):
                                stats["agent_runs"][agent] = stats["agent_runs"].get(agent, 0) + data.get("total", 0)
                                stats["total_duration_s"] += data.get("avg", 0) * data.get("total", 0)

                        # Token cost
                        for agent, data in entry.get("token_cost", {}).items():
                            if isinstance(data, dict):
                                stats["total_tokens"] += data.get("input", 0) + data.get("output", 0)
                                stats["total_cost"] += data.get("cost_est", 0.0)

                        # Workflow
                        for mod, data in entry.get("workflow", {}).items():
                            if isinstance(data, dict):
                                stats["runs"] += data.get("total", 0)
                                stats["success"] += data.get("success", 0)
                                stats["failed"] += data.get("failed", 0)

                        # Phase distribution
                        for key, data in entry.get("phase_distribution", {}).items():
                            if isinstance(data, dict):
                                stats["phase_times"][key] = stats["phase_times"].get(key, 0) + data.get("avg", 0)
                    except: pass
        except: pass
        return stats

    this_week = aggregate_since(week_ago)
    last_week = aggregate_since(two_weeks_ago)

    total_runs = this_week["runs"]
    success_rate = this_week["success"] / total_runs if total_runs > 0 else 0
    prev_rate = last_week["success"] / last_week["runs"] if last_week["runs"] > 0 else 0

    return {
        "period": "7d",
        "this_week": {
            "runs": total_runs,
            "success": this_week["success"],
            "failed": this_week["failed"],
            "success_rate": round(success_rate, 3),
            "total_tokens": this_week["total_tokens"],
            "total_cost": round(this_week["total_cost"], 4),
            "avg_duration_s": round(this_week["total_duration_s"] / total_runs, 1) if total_runs > 0 else 0,
            "agents_used": len(this_week["agent_runs"]),
            "phase_hotspots": dict(sorted(
                this_week["phase_times"].items(), key=lambda x: -x[1]
            )[:5]),
        },
        "vs_last_week": {
            "success_rate_delta": round(success_rate - prev_rate, 3),
            "runs_delta": total_runs - last_week["runs"],
            "cost_delta": round(this_week["total_cost"] - last_week["total_cost"], 4),
            "trend": "up" if success_rate >= prev_rate else "down",
        },
        "updated": now.isoformat(),
    }


@app.get("/api/timeline/replay/{run_id}")
async def timeline_replay(run_id: str):
    """★ v1.4: Timeline Replay — 完整 Run 回放 (context/prompt/output/artifacts)."""
    import json
    from pathlib import Path

    events = []
    trace_file = (
        Path(__file__).resolve().parent.parent.parent
        / "governance" / ".traces" / "trace_log.jsonl"
    )
    if trace_file.exists():
        with open(trace_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line: continue
                try:
                    te = json.loads(line)
                    if te.get("run_id") == run_id:
                        events.append({
                            "ts": te.get("timestamp", ""),
                            "type": te.get("event_type", ""),
                            "agent": te.get("agent_name", ""),
                            "provider": te.get("provider", ""),
                            "model": te.get("model", ""),
                            "latency_ms": te.get("latency_ms", 0),
                            "tokens_in": te.get("token_input", 0),
                            "tokens_out": te.get("token_output", 0),
                            "status": te.get("status", ""),
                        })
                except Exception:
                    pass

    events.sort(key=lambda e: e["ts"])
    return {
        "run_id": run_id,
        "events": events,
        "total_events": len(events),
        "total_tokens": sum(e["tokens_in"] + e["tokens_out"] for e in events),
        "agents": list(set(e["agent"] for e in events if e["agent"])),
        "started": events[0]["ts"] if events else "",
        "ended": events[-1]["ts"] if events else "",
    }


app.include_router(agents_router)
app.include_router(webhooks_router)
app.include_router(workflows_router)
app.include_router(bugs_router)
app.include_router(chat_router)
app.include_router(sessions_router)
app.include_router(onboarding_router)
app.include_router(integrations_router)

# 静态文件 + Chat UI
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")




# ══════════════════════════════════════════════════════════════════════════
#  🆕 TLO Kanban WebSocket — 实时推送生命周期状态变更
# ══════════════════════════════════════════════════════════════════════════

import json as _json
from fastapi import WebSocket, WebSocketDisconnect


class KanbanWSManager:
    """WebSocket 连接管理器 — 广播生命周期状态变更到所有已连接的 Kanban 客户端。"""

    def __init__(self):
        self._connections: list[WebSocket] = []

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)

    def disconnect(self, ws: WebSocket):
        if ws in self._connections:
            self._connections.remove(ws)

    async def broadcast(self, event: dict):
        """向所有连接的 Kanban 客户端广播事件。"""
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

    async def broadcast_sop_phase(self, module: str, phase: str, status: str = "running", progress: int = 0, message: str = ""):
        """广播 SOP 阶段变更到所有 Kanban 客户端。可从任意上下文调用。"""
        await self.broadcast({
            "type": "phase_change",
            "module": module,
            "phase": phase,
            "status": status,
            "progress": progress,  # 0-100
            "message": message,
            "timestamp": datetime.now().isoformat(),
        })


_kanban_ws = KanbanWSManager()


@app.post("/api/sop/start")
async def sop_start(request: Request):
    """
    启动模块 SOP 执行（异步后台线程）。
    执行过程中通过 WebSocket 广播 phase_change 事件到 Kanban。
    """
    import threading

    body = await request.json() if await request.body() else {}
    module = body.get("module", "")
    pages = body.get("pages", [])
    mode = body.get("mode", "full")
    provider = body.get("provider", "claude")

    if not module:
        return {"error": "module is required"}

    # Emit initial phase
    phases = ["Requirement", "Test Strategy", "Test Design", "Automation", "Environment", "Execution", "Bug Analysis", "Report", "Knowledge"]
    total = len(phases)

    loop = asyncio.get_event_loop()  # capture main loop BEFORE thread starts

    def run_sop_background():
        """Background thread: simulate SOP execution with phase broadcasts."""
        import time as _time

        for i, phase in enumerate(phases):
            progress = int((i + 1) / total * 100)

            asyncio.run_coroutine_threadsafe(
                _kanban_ws.broadcast_sop_phase(
                    module=module, phase=phase, status="running",
                    progress=progress, message=f"Running {phase}..."
                ),
                loop,
            )
            _time.sleep(1.5)

            # Update SOP_STATUS file
            new_status = "completed" if progress >= 100 else "in_progress"
            _update_module_phase(module, phase, new_status, progress)

        # Final broadcast
        asyncio.run_coroutine_threadsafe(
            _kanban_ws.broadcast_sop_phase(
                module=module, phase="Knowledge", status="completed",
                progress=100, message=f"SOP completed for {module}"
            ),
            loop,
        )

    thread = threading.Thread(target=run_sop_background, daemon=True)
    thread.start()

    return {
        "module": module,
        "status": "started",
        "total_phases": total,
        "phases": phases,
    }


def _get_sop_status_dir() -> Path:
    """Resolve per-project SOP_STATUS directory, creating if needed."""
    from aitest.platform.context import get_active_project_id
    base = Path(__file__).resolve().parent.parent.parent
    d = base / "governance" / "artifacts" / "sop-status" / get_active_project_id()
    d.mkdir(parents=True, exist_ok=True)
    return d


def _update_module_phase(module: str, phase: str, status: str, progress: int):
    """后台更新 SOP_STATUS 文件——写入 per-project 目录。"""
    import json as _j
    sop_dir = _get_sop_status_dir()
    status_file = sop_dir / f"SOP_STATUS_{module}.json"
    if status_file.exists():
        try:
            data = _j.loads(status_file.read_text(encoding="utf-8"))
            if phase not in data.get("completed_phases", []):
                data.setdefault("completed_phases", []).append(phase)
            data["status"] = status
            data["progress"] = progress
            data["updated_at"] = datetime.now().isoformat()
            status_file.write_text(_j.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass


@app.websocket("/ws/kanban")
async def kanban_websocket(ws: WebSocket):
    """Kanban 实时更新 WebSocket — 客户端连接后接收生命周期事件推送。"""
    await _kanban_ws.connect(ws)
    try:
        # 发送初始连接确认
        await ws.send_text(_json.dumps({
            "type": "connected",
            "connections": _kanban_ws.active_connections,
            "timestamp": datetime.now().isoformat(),
        }))
        # 保持连接，等待客户端消息
        while True:
            data = await ws.receive_text()
            msg = _json.loads(data)
            action = msg.get("action", "")
            if action == "ping":
                await ws.send_text(_json.dumps({"type": "pong"}))
            elif action == "card_move":
                # 客户端拖拽卡片到新列 → 广播给所有客户端
                await _kanban_ws.broadcast({
                    "type": "card_moved",
                    "module": msg.get("module", ""),
                    "from_stage": msg.get("from_stage", ""),
                    "to_stage": msg.get("to_stage", ""),
                    "timestamp": datetime.now().isoformat(),
                })
                # 更新 SOP_STATUS (写入新状态)
                _update_module_stage(msg.get("module", ""), msg.get("to_stage", ""))
    except WebSocketDisconnect:
        _kanban_ws.disconnect(ws)
    except Exception:
        _kanban_ws.disconnect(ws)


# ══════════════════════════════════════════════════════════════════════════
#  🆕 Agent Terminal WebSocket — 实时推送Agent执行日志
# ══════════════════════════════════════════════════════════════════════════

class AgentTerminalWSManager:
    """WebSocket连接管理器 — 广播ObservationBus事件到Agent终端客户端。"""

    def __init__(self):
        self._connections: list[WebSocket] = []
        self._subscribed = False

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self._connections.append(ws)
        self._start_listening()

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

    def _start_listening(self):
        """订阅ObservationBus，将事件转发到所有WebSocket客户端。"""
        if self._subscribed:
            return
        self._subscribed = True

        def _on_event(event):
            """同步回调：将ObservationEvent转为字典并广播。"""
            payload = {
                "type": str(event.type.value) if hasattr(event.type, 'value') else str(event.type),
                "agent": getattr(event, 'agent_name', ''),
                "module": getattr(event, 'module', ''),
                "page": getattr(event, 'page', ''),
                "data": getattr(event, 'data', {}),
                "timestamp": datetime.now().isoformat(),
            }
            # Schedule async broadcast from sync callback
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self.broadcast(payload))
            except Exception:
                pass

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
                    bus.subscribe(EventType(et), _on_event)
                except Exception:
                    continue
        except Exception:
            pass  # ObservationBus unavailable — agent terminal works in degraded mode


_agent_terminal_ws = AgentTerminalWSManager()


@app.websocket("/ws/agent-terminal")
async def agent_terminal_websocket(ws: WebSocket):
    """Agent终端实时日志 WebSocket。"""
    await _agent_terminal_ws.connect(ws)
    try:
        await ws.send_text(_json.dumps({
            "type": "connected",
            "connections": len(_agent_terminal_ws._connections),
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


@app.get("/api/kanban/status")
async def kanban_status():
    """返回 Kanban WebSocket 连接状态。"""
    return {
        "active_connections": _kanban_ws.active_connections,
        "timestamp": datetime.now().isoformat(),
    }


def _update_module_stage(module: str, new_stage: str):
    """更新模块 SOP_STATUS 的阶段标记（卡片拖拽后持久化）——写入 per-project 目录。"""
    import json as _j
    sop_dir = _get_sop_status_dir()
    status_file = sop_dir / f"SOP_STATUS_{module}.json"
    if not status_file.exists():
        return
    try:
        data = _j.loads(status_file.read_text(encoding="utf-8"))
        stage_map = {
            "pending": "pending",
            "planning": "ready",
            "executing": "in_progress",
            "analyzing": "completed_with_issues",
            "completed": "completed",
        }
        new_status = stage_map.get(new_stage, data.get("status", "completed"))
        data["status"] = new_status
        data["kanban_stage"] = new_stage
        data["kanban_updated_at"] = datetime.now().isoformat()
        status_file.write_text(_j.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass  # 非阻塞


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="::", port=8000)
