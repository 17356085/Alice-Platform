"""AI Test Platform — FastAPI 服务入口。

启动: python -m aitest.server.main
       uvicorn aitest.server.main:app --reload --port 8000
       aitest server start --reload

启动后访问 http://localhost:8000/docs 查看交互式 API 文档。
"""
import sys
import asyncio

# Windows: 用 SelectorEventLoop 替代 ProactorEventLoop，避免 SSE 断开时报
# "Exception in callback _ProactorBasePipeTransport._call_connection_lost(None)"
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from aitest.server.api.agents import agents_router
from aitest.server.api.webhooks import webhooks_router
from aitest.server.api.workflows import workflows_router
from aitest.server.api.bugs import bugs_router
from aitest.server.api.chat import chat_router
from aitest.server.api.sessions_api import router as sessions_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init session DB
    from aitest.server.session_store import init_db
    await init_db()
    print("[SessionStore] Database initialized")

    from aitest.task_queue import get_runner, get_queue
    runner = get_runner()
    runner.start()
    queue = get_queue()
    pending = queue.count_by_status().get("queued", 0)
    print(f"[TaskRunner] Started. Pending: {pending}")

    # P1-ACTIVATION (2026-06-15): 生产环境激活 KnowledgeAgentSubscriber
    # Dead Path #5 修复 — 此前仅在 event_bus watch CLI 模式激活
    try:
        from aitest.event_bus import KnowledgeAgentSubscriber
        _gov_subscriber = KnowledgeAgentSubscriber(provider="claude", auto_process=True)
        _gov_subscriber.activate()
        print(f"[Governance] KnowledgeAgentSubscriber activated — listening for governance events")
    except Exception as e:
        print(f"[Governance] Subscriber activation failed: {e}")

    yield

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


@app.get("/")
async def root():
    return {
        "name": "AITest Platform",
        "version": "0.4.0",
        "docs": "/docs",
        "chat": "/chat",
        "modules": {
            "chat":      ["POST /api/chat/sessions", "POST /api/chat/sessions/{id}/messages", "GET /api/chat/sessions/{id}/stream/{mid}"],
            "agents":    ["POST /api/agent/run", "GET /api/agent/task/{id}", "GET /api/agent/queue", "GET /api/agent/status/{module}", "GET /api/agent/list"],
            "workflows": ["POST /api/workflow/run", "GET /api/workflow/status/{run_id}", "GET /api/workflow/list", "GET /api/workflow/runs"],
            "bugs":      ["GET /api/bugs/list", "POST /api/bugs/add", "GET /api/bugs/trends"],
            "webhooks":  ["POST /api/webhook/jenkins"],
        },
    }


@app.get("/health")
async def health():
    """P2-5: 平台健康检查 — 各组件状态汇总。"""
    from aitest.task_queue import get_queue
    from aitest.error_logger import get_summary as error_summary

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
        from aitest.rag_engine import get_chroma_client
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
        from aitest.rag_engine import _known_issues_mtime, KNOWN_ISSUES
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

    return {"status": overall, "components": components}


# ══════════════════════════════════════════════════════════════════════
#  P2-5: Governance Audit API
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/audit/state")
async def audit_state(module: str = "equipment", repair: bool = False):
    """State Auditor — 状态审计 API。"""
    try:
        from aitest.state_auditor import StateAuditor
        auditor = StateAuditor()
        report = auditor.audit(module, auto_repair=repair)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "overall_status": "error", "drift_count": 0, "error_count": 1}


@app.get("/api/audit/sop")
async def audit_sop(module: str = "equipment", days: int = 7):
    """SOP Auditor — SOP 合规审计 API。"""
    try:
        from aitest.sop_auditor import SOPAuditor
        auditor = SOPAuditor()
        report = auditor.audit(module, days=days)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "overall_compliance": 0, "total_violations": 0}


@app.get("/api/audit/cost")
async def audit_cost(days: int = 7):
    """Cost Auditor — 成本审计 API。"""
    try:
        from aitest.cost_auditor import CostAuditor
        auditor = CostAuditor()
        report = auditor.audit(days=days)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "total_cost": 0, "alert_count": 0}


@app.get("/api/audit/governance")
async def audit_governance(module: str = "equipment", days: int = 7):
    """Governance 聚合 API — 一次返回所有审计摘要。"""
    result = {
        "module": module,
        "timestamp": __import__("datetime").datetime.now().isoformat(),
    }
    try:
        from aitest.state_auditor import StateAuditor
        result["state"] = StateAuditor().audit(module, auto_repair=False)
    except Exception as e:
        result["state"] = {"error": str(e)[:200]}
    try:
        from aitest.sop_auditor import SOPAuditor
        result["sop"] = SOPAuditor().audit(module, days=days)
    except Exception as e:
        result["sop"] = {"error": str(e)[:200]}
    try:
        from aitest.cost_auditor import CostAuditor
        result["cost"] = CostAuditor().audit(days=days)
    except Exception as e:
        result["cost"] = {"error": str(e)[:200]}
    return result


# ══════════════════════════════════════════════════════════════════════════
#  L4 Measured: KPI API
# ══════════════════════════════════════════════════════════════════════════

@app.get("/api/kpi/summary")
async def kpi_summary(days: int = 30):
    """KPI 总览 — 治理指标体系聚合。"""
    try:
        from aitest.governance_kpi import KPICollector
        return KPICollector().get_summary(days=days)
    except Exception as e:
        return {"error": str(e)[:300]}


@app.get("/api/kpi/trends")
async def kpi_trends(audit_type: str = "state", days: int = 30):
    """KPI 趋势 — 指定审计类型的趋势分析。"""
    try:
        from aitest.governance_kpi import KPICollector
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
        from aitest.scheduled_audit import run_all_audits, discover_modules
        mod_list = modules.split(",") if modules else discover_modules()
        return run_all_audits(mod_list)
    except Exception as e:
        return {"error": str(e)[:300]}


app.include_router(agents_router)
app.include_router(webhooks_router)
app.include_router(workflows_router)
app.include_router(bugs_router)
app.include_router(chat_router)
app.include_router(sessions_router)

# 静态文件 + Chat UI
_STATIC_DIR = Path(__file__).resolve().parent / "static"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


@app.get("/chat")
async def chat_ui():
    """Chat 聊天界面。"""
    chat_html = _STATIC_DIR / "chat.html"
    if chat_html.exists():
        from fastapi.responses import HTMLResponse
        return HTMLResponse(chat_html.read_text(encoding="utf-8"))
    return {"message": f"chat.html not found at {_STATIC_DIR}. Run: aitest server start"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
