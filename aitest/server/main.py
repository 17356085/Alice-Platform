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


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Init session DB
    from aitest.server.session_store import init_db
    await init_db()
    print("[SessionStore] Database initialized")

    from aitest.infra.task_queue import get_runner, get_queue
    runner = get_runner()
    runner.start()
    queue = get_queue()
    pending = queue.count_by_status().get("queued", 0)
    print(f"[TaskRunner] Started. Pending: {pending}")

    # P1-ACTIVATION (2026-06-15): 生产环境激活 KnowledgeAgentSubscriber
    # Dead Path #5 修复 — 此前仅在 event_bus watch CLI 模式激活
    try:
        from aitest.governance.event_bus import KnowledgeAgentSubscriber
        _gov_subscriber = KnowledgeAgentSubscriber(provider="claude", auto_process=True)
        _gov_subscriber.activate()
        print(f"[Governance] KnowledgeAgentSubscriber activated — listening for governance events")
    except Exception as e:
        print(f"[Governance] Subscriber activation failed: {e}")

    # P2-ACTIVATION (2026-06-16): Dead Path — 审计未自动调度
    # 后台 asyncio Task 周期性运行 State/SOP/Cost 审计
    audit_interval = int(os.environ.get("AITEST_AUDIT_INTERVAL", "86400"))  # 默认 24h
    _audit_stop = asyncio.Event()

    async def _audit_scheduler():
        """后台审计调度器 — 周期性运行全量审计并发射治理事件。"""
        # 启动后等待 60s 再首次审计（让服务完全初始化）
        await asyncio.sleep(60)
        iteration = 0
        from aitest.governance.scheduled_audit import run_all_audits, discover_modules
        while not _audit_stop.is_set():
            iteration += 1
            started = asyncio.get_event_loop().time()
            print(f"[ScheduledAudit] #{iteration} starting — {datetime.now().strftime('%H:%M:%S')}")

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
                print(f"[ScheduledAudit] #{iteration} done — "
                      f"State: {state_drifts} drifts, "
                      f"SOP: {sop_violations} violations, "
                      f"Cost: ${cost_info.get('total_cost', 0):.4f} "
                      f"({asyncio.get_event_loop().time() - started:.1f}s)")

                # 审计后检查是否需要触发架构评审
                try:
                    from aitest.governance.review_trigger import check_and_enqueue, format_queue_summary
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


@app.get("/")
async def root():
    """API root — Vue 3 SPA is the frontend (see aitest/web/)."""
    return {
        "name": "TLO Platform",
        "version": "1.0.0",
        "frontend": "aitest/web/ (Vue 3 + shadcn-vue)",
        "docs": "/docs",
    }


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

    return {"status": overall, "components": components}


# ══════════════════════════════════════════════════════════════════════
#  P2-5: Governance Audit API
# ══════════════════════════════════════════════════════════════════════

@app.get("/api/audit/state")
async def audit_state(module: str = "equipment", repair: bool = False):
    """State Auditor — 状态审计 API。"""
    try:
        from aitest.governance.state_auditor import StateAuditor
        auditor = StateAuditor()
        report = auditor.audit(module, auto_repair=repair)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "overall_status": "error", "drift_count": 0, "error_count": 1}


@app.get("/api/audit/sop")
async def audit_sop(module: str = "equipment", days: int = 7):
    """SOP Auditor — SOP 合规审计 API。"""
    try:
        from aitest.governance.sop_auditor import SOPAuditor
        auditor = SOPAuditor()
        report = auditor.audit(module, days=days)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "overall_compliance": 0, "total_violations": 0}


@app.get("/api/audit/cost")
async def audit_cost(days: int = 7):
    """Cost Auditor — 成本审计 API。"""
    try:
        from aitest.governance.cost_auditor import CostAuditor
        auditor = CostAuditor()
        report = auditor.audit(days=days)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "total_cost": 0, "alert_count": 0}


@app.get("/api/audit/safety")
async def audit_safety(module: str = "equipment", days: int = 7):
    """Safety Auditor — 安全审计 API (P0)。"""
    try:
        from aitest.governance.safety_auditor import SafetyAuditor
        auditor = SafetyAuditor()
        report = auditor.audit(module, days=days)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "overall_status": "error", "safety_score": 0}


@app.get("/api/online/analyze")
async def online_analyze(module: str = "system", days: int = 7):
    """Online Monitor — 线上指标分析 API (P0)。"""
    try:
        from aitest.governance.online_monitor import OnlineMonitor
        monitor = OnlineMonitor()
        report = monitor.analyze(module, days=days)
        return report
    except Exception as e:
        return {"error": str(e)[:300], "module": module}


@app.get("/api/trace/{run_id}")
async def trace_replay(run_id: str):
    """Trace 回放 API — 获取指定运行的全部步骤。"""
    try:
        from aitest.governance.online_monitor import get_run_trace_replay
        return get_run_trace_replay(run_id)
    except Exception as e:
        return {"error": str(e)[:300], "run_id": run_id, "steps": []}


@app.get("/api/trace/runs")
async def trace_runs(limit: int = 20):
    """列出最近的运行记录。"""
    try:
        from aitest.governance.online_monitor import list_recent_runs
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
        from aitest.governance.state_auditor import StateAuditor
        result["state"] = StateAuditor().audit(module, auto_repair=False)
    except Exception as e:
        result["state"] = {"error": str(e)[:200]}
    try:
        from aitest.governance.sop_auditor import SOPAuditor
        result["sop"] = SOPAuditor().audit(module, days=days)
    except Exception as e:
        result["sop"] = {"error": str(e)[:200]}
    try:
        from aitest.governance.cost_auditor import CostAuditor
        result["cost"] = CostAuditor().audit(days=days)
    except Exception as e:
        result["cost"] = {"error": str(e)[:200]}
    try:
        from aitest.governance.safety_auditor import SafetyAuditor
        result["safety"] = SafetyAuditor().audit(module, days=days)
    except Exception as e:
        result["safety"] = {"error": str(e)[:200]}
    return result


# ══════════════════════════════════════════════════════════════════════════
#  L4 Measured: KPI API
# ══════════════════════════════════════════════════════════════════════════

@app.get("/api/sop-status")
async def sop_status_all():
    """返回全部模块 SOP 状态 — 用于治理仪表板模块矩阵。"""
    import json
    from pathlib import Path
    sop_dir = Path("governance/artifacts/sop-status")
    modules = {}
    for f in sorted(sop_dir.glob("SOP_STATUS_*.json")):
        mod = f.stem.replace("SOP_STATUS_", "")
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            modules[mod] = {
                "status": data.get("status", "?"),
                "phases": len(data.get("completed_phases", [])),
                "pages": len(data.get("pages_processed", [])),
                "failed": len(data.get("failed_phases", [])),
                "updated": data.get("updated_at", ""),
            }
        except Exception:
            modules[mod] = {"status": "error", "phases": 0, "pages": 0, "failed": 0, "updated": ""}
    return {"modules": modules, "total": len(modules)}


@app.get("/api/kpi/summary")
async def kpi_summary(days: int = 30):
    """KPI 总览 — 治理指标体系聚合。"""
    try:
        from aitest.governance.governance_kpi import KPICollector
        return KPICollector().get_summary(days=days)
    except Exception as e:
        return {"error": str(e)[:300]}


@app.get("/api/kpi/trends")
async def kpi_trends(audit_type: str = "state", days: int = 30):
    """KPI 趋势 — 指定审计类型的趋势分析。"""
    try:
        from aitest.governance.governance_kpi import KPICollector
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
        from aitest.governance.scheduled_audit import run_all_audits, discover_modules
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

    def run_sop_background():
        """Background thread: simulate SOP execution with phase broadcasts."""
        import time as _time

        for i, phase in enumerate(phases):
            progress = int((i + 1) / total * 100)

            # Broadcast phase start
            asyncio.run_coroutine_threadsafe(
                _kanban_ws.broadcast_sop_phase(
                    module=module, phase=phase, status="running",
                    progress=progress, message=f"Running {phase}..."
                ),
                asyncio.get_event_loop(),
            )
            _time.sleep(1.5)  # Simulate work (in production: actual SOP execution)

            # Update SOP_STATUS file
            new_status = "completed" if progress >= 100 else "in_progress"
            _update_module_phase(module, phase, new_status, progress)

        # Final broadcast
        asyncio.run_coroutine_threadsafe(
            _kanban_ws.broadcast_sop_phase(
                module=module, phase="Knowledge", status="completed",
                progress=100, message=f"SOP completed for {module}"
            ),
            asyncio.get_event_loop(),
        )

    thread = threading.Thread(target=run_sop_background, daemon=True)
    thread.start()

    return {
        "module": module,
        "status": "started",
        "total_phases": total,
        "phases": phases,
    }


def _update_module_phase(module: str, phase: str, status: str, progress: int):
    """后台更新 SOP_STATUS 文件。"""
    import json as _j
    sop_dir = Path(__file__).resolve().parent.parent.parent / "governance" / "artifacts" / "sop-status"
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


@app.get("/api/kanban/status")
async def kanban_status():
    """返回 Kanban WebSocket 连接状态。"""
    return {
        "active_connections": _kanban_ws.active_connections,
        "timestamp": datetime.now().isoformat(),
    }


def _update_module_stage(module: str, new_stage: str):
    """更新模块 SOP_STATUS 的阶段标记（卡片拖拽后持久化）。"""
    import json as _j
    sop_dir = Path(__file__).resolve().parent.parent.parent / "governance" / "artifacts" / "sop-status"
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
    uvicorn.run(app, host="0.0.0.0", port=8000)
