"""KPI + SOP status + Timeline + Artifacts endpoints.
Extracted from main.py (P0-2 split, 2026-06-25).

Routes:
  GET  /api/sop-status              — Kanban module status
  GET  /api/kpi/summary             — KPI overview
  GET  /api/kpi/trends              — KPI trends
  POST /api/kpi/audit-all           — Trigger full audit
  GET  /api/kpi/operational         — 8 runtime KPIs
  GET  /api/kpi/trends/operational  — Operational trends
  GET  /api/kpi/product             — Product KPI (this week vs last)
  GET  /api/kpi/optimization-insights — Auto-detected optimizations
  GET  /api/timeline/{project_id}   — Agent activity timeline
  GET  /api/timeline/replay/{run_id} — Full run replay
  GET  /api/artifacts/{project_id}  — Artifact listing
  GET  /api/artifacts/lineage/{project_id} — Artifact lineage DAG
"""
from __future__ import annotations
import json
from pathlib import Path
from collections import OrderedDict

from aitest.platform.paths import get_workstudy
from fastapi import APIRouter

kpi_router = APIRouter(prefix="/api", tags=["kpi"])

SOP_PHASES = [
    "Project Init", "Requirement", "Test Design",
    "Automation", "Execute & Debug", "Bug Analysis",
    "Data Sanitization", "Report", "Knowledge",
]


# ── SOP Status ────────────────────────────────────────────────────────

@kpi_router.get("/sop-status")
async def sop_status_all(project: str = ""):
    from aitest.platform.context import get_active_project_id
    from aitest.platform.paths import get_test_project_root

    project_id = project.strip() or get_active_project_id()
    base = get_workstudy()
    search_dirs: list[Path] = []

    root = get_test_project_root(project_id)
    if root:
        tlo_runtime = root / ".tlo" / "runtime" / "sop-status"
        if tlo_runtime.exists():
            search_dirs.append(tlo_runtime)

    per_project = base / "governance" / "artifacts" / "sop-status" / project_id
    per_project.mkdir(parents=True, exist_ok=True)
    search_dirs.append(per_project)

    legacy_flat = base / "governance" / "artifacts" / "sop-status"
    if legacy_flat.exists():
        search_dirs.append(legacy_flat)

    modules = OrderedDict()
    seen: set[str] = set()
    for sop_dir in search_dirs:
        for f in sorted(sop_dir.glob("SOP_STATUS_*.json")):
            mod = f.stem.replace("SOP_STATUS_", "")
            if mod in seen:
                continue
            seen.add(mod)
            try:
                data = json.loads(f.read_text(encoding="utf-8"))
            except Exception:
                modules[mod] = {"status": "error", "stage": "init", "phase_status": {},
                                "phases_done": 0, "phases_total": len(SOP_PHASES),
                                "pages": 0, "pages_list": [], "artifacts": 0, "failed": 0,
                                "run_id": "", "updated": "", "note": ""}
                continue
            completed = data.get("completed_phases", [])
            pages = data.get("pages_processed", [])
            phase_status = {p: (p in completed) for p in SOP_PHASES}
            phases_done = len(completed)
            if phases_done >= len(SOP_PHASES):
                stage = "complete"
            else:
                status = data.get("status", "?")
                if status in ("completed", "completed_with_issues"):
                    stage = "analysis" if status == "completed_with_issues" else "complete"
                elif status == "ready":
                    stage = "automation"
                elif status == "in_progress":
                    stage = "execution"
                else:
                    stage = "init"
            modules[mod] = {
                "status": data.get("status", "?"), "stage": stage,
                "phase_status": phase_status, "phases_done": phases_done,
                "phases_total": len(SOP_PHASES), "pages": len(pages),
                "pages_list": pages, "artifacts": data.get("artifact_count", 0),
                "failed": len(data.get("failed_phases", [])),
                "run_id": data.get("run_id", ""), "updated": data.get("updated_at", ""),
                "note": (data.get("note", "") or "")[:80],
            }
    return {"modules": modules, "total": len(modules), "sop_phases": SOP_PHASES}


# ── KPI ───────────────────────────────────────────────────────────────

@kpi_router.get("/kpi/summary")
async def kpi_summary(days: int = 30):
    try:
        from aitest.audit_engine.governance_kpi import KPICollector
        return KPICollector().get_summary(days=days)
    except Exception as e:
        return {"error": str(e)[:300]}


@kpi_router.get("/kpi/trends")
async def kpi_trends(audit_type: str = "state", days: int = 30):
    try:
        from aitest.audit_engine.governance_kpi import KPICollector
        trends = KPICollector().get_trends(audit_type, days=days)
        return {"audit_type": audit_type, "period": f"{days}d",
                "trends": [t.__dict__ if hasattr(t, '__dict__') else t for t in trends]}
    except Exception as e:
        return {"error": str(e)[:300]}


@kpi_router.post("/kpi/audit-all")
async def kpi_audit_all(modules: str = None):
    try:
        from aitest.audit_engine.scheduled_audit import run_all_audits, discover_modules
        mod_list = modules.split(",") if modules else discover_modules()
        return run_all_audits(mod_list)
    except Exception as e:
        return {"error": str(e)[:300]}


@kpi_router.get("/kpi/operational")
async def operational_metrics():
    try:
        from aitest.platform.operational_metrics import get_collector
        return get_collector().snapshot()
    except Exception as e:
        return {"error": str(e)[:300]}


@kpi_router.get("/kpi/trends/operational")
async def operational_trends(days: int = 7):
    from datetime import datetime, timedelta, timezone

    metrics_file = (
        get_workstudy()
        / "governance" / "kpi" / "timeseries" / "operational_metrics.jsonl"
    )
    if not metrics_file.exists():
        return {"points": [], "message": "No operational metrics data yet"}

    cutoff = None
    if days > 0:
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
                    total_tokens = sum(
                        v.get("input", 0) + v.get("output", 0)
                        for v in entry.get("token_cost", {}).values()
                        if isinstance(v, dict)
                    )
                    workflow_rates = [
                        v.get("rate", 0) for v in entry.get("workflow", {}).values()
                        if isinstance(v, dict)
                    ]
                    avg_rate = sum(workflow_rates) / len(workflow_rates) if workflow_rates else 0
                    points.append({
                        "ts": ts[:19] if ts else "", "total_tokens": total_tokens,
                        "workflow_rate": round(avg_rate, 3),
                        "uptime_s": entry.get("uptime_s", 0),
                    })
                except Exception:
                    pass
    except Exception:
        pass
    return {"points": points[-200:], "total": len(points), "days": days}


@kpi_router.get("/kpi/product")
async def product_kpi():
    from datetime import datetime, timedelta, timezone

    now = datetime.now(timezone.utc)
    week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)

    def aggregate_since(cutoff):
        stats = {"runs": 0, "success": 0, "failed": 0, "total_tokens": 0,
                 "total_cost": 0.0, "total_duration_s": 0.0, "agent_runs": {}, "phase_times": {}}
        metrics_file = (
            get_workstudy()
            / "governance" / "kpi" / "timeseries" / "operational_metrics.jsonl"
        )
        if not metrics_file.exists():
            return stats
        try:
            with open(metrics_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        ts = entry.get("ts", "")
                        if ts:
                            try:
                                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                                if dt < cutoff:
                                    continue
                            except Exception:
                                pass
                        for agent, data in entry.get("agent_latency_p95", {}).items():
                            if isinstance(data, dict):
                                stats["agent_runs"][agent] = stats["agent_runs"].get(agent, 0) + data.get("total", 0)
                                stats["total_duration_s"] += data.get("avg", 0) * data.get("total", 0)
                        for agent, data in entry.get("token_cost", {}).items():
                            if isinstance(data, dict):
                                stats["total_tokens"] += data.get("input", 0) + data.get("output", 0)
                                stats["total_cost"] += data.get("cost_est", 0.0)
                        for mod, data in entry.get("workflow", {}).items():
                            if isinstance(data, dict):
                                stats["runs"] += data.get("total", 0)
                                stats["success"] += data.get("success", 0)
                                stats["failed"] += data.get("failed", 0)
                        for key, data in entry.get("phase_distribution", {}).items():
                            if isinstance(data, dict):
                                stats["phase_times"][key] = stats["phase_times"].get(key, 0) + data.get("avg", 0)
                    except Exception:
                        pass
        except Exception:
            pass
        return stats

    this_week = aggregate_since(week_ago)
    last_week = aggregate_since(two_weeks_ago)
    total_runs = this_week["runs"]
    success_rate = this_week["success"] / total_runs if total_runs > 0 else 0
    prev_rate = last_week["success"] / last_week["runs"] if last_week["runs"] > 0 else 0

    return {
        "period": "7d",
        "this_week": {
            "runs": total_runs, "success": this_week["success"],
            "failed": this_week["failed"], "success_rate": round(success_rate, 3),
            "total_tokens": this_week["total_tokens"],
            "total_cost": round(this_week["total_cost"], 4),
            "avg_duration_s": round(this_week["total_duration_s"] / total_runs, 1) if total_runs > 0 else 0,
            "agents_used": len(this_week["agent_runs"]),
            "phase_hotspots": dict(sorted(this_week["phase_times"].items(), key=lambda x: -x[1])[:5]),
        },
        "vs_last_week": {
            "success_rate_delta": round(success_rate - prev_rate, 3),
            "runs_delta": total_runs - last_week["runs"],
            "cost_delta": round(this_week["total_cost"] - last_week["total_cost"], 4),
            "trend": "up" if success_rate >= prev_rate else "down",
        },
        "updated": now.isoformat(),
    }


@kpi_router.get("/kpi/optimization-insights")
async def optimization_insights():
    try:
        from aitest.platform.operational_metrics import get_collector
        snap = get_collector().snapshot()
        insights = []
        for agent, data in snap.get("agent_latency_p95", {}).items():
            if isinstance(data, dict) and data.get("p95", 0) > 30:
                insights.append({"type": "slow_agent", "severity": "warning", "agent": agent,
                                 "metric": f"p95={data['p95']}s",
                                 "suggestion": f"Consider lowering model tier for {agent} or adding caching"})
        for agent, data in snap.get("token_cost", {}).items():
            if isinstance(data, dict) and data.get("cost_est", 0) > 0.50:
                insights.append({"type": "high_cost", "severity": "info", "agent": agent,
                                 "metric": f"${data['cost_est']:.4f}",
                                 "suggestion": f"Consider switching {agent} to econ tier for non-critical runs"})
        for mod, data in snap.get("workflow", {}).items():
            if isinstance(data, dict) and data.get("rate", 1) < 0.8 and data.get("total", 0) > 3:
                insights.append({"type": "low_success_rate", "severity": "warning", "module": mod,
                                 "metric": f"{round(data['rate']*100)}% ({data['success']}/{data['total']})",
                                 "suggestion": f"Review {mod} failures in Timeline. Check locator stability."})
        try:
            from aitest.infra.cache_layer import cache
            for ctype, cs in cache.stats().items():
                if cs["saved_tokens"] > 0:
                    insights.append({"type": "cache_savings", "severity": "info", "cache": ctype,
                                     "metric": f"{cs['saved_tokens']} tokens saved, {cs['hit_rate']*100:.0f}% hit rate",
                                     "suggestion": f"Cache '{ctype}' active: {cs['size']}/{cs['max_size']} entries"})
        except Exception:
            pass
        if not insights:
            insights.append({"type": "no_data", "severity": "info",
                             "message": "Not enough operational data yet. Run more SOPs to get optimization insights."})
        return {"insights": insights, "total": len(insights), "ts": snap.get("ts", "")}
    except Exception as e:
        return {"error": str(e)[:300]}


# ── Timeline ──────────────────────────────────────────────────────────

@kpi_router.get("/timeline/{project_id}")
async def timeline(project_id: str, limit: int = 50):
    events = []
    try:
        from aitest.platform.operational_metrics import get_collector
        snap = get_collector().snapshot()
        for agent, data in snap.get("agent_latency_p95", {}).items():
            if data.get("total", 0) > 0:
                events.append({"ts": snap["ts"], "type": "agent_summary", "agent": agent,
                               "message": f"{agent} — {data['total']} runs, p95={data['p95']}s, avg={data['avg']}s"})
        for mod, data in snap.get("workflow", {}).items():
            events.append({"ts": snap["ts"], "type": "workflow_status", "agent": "workflow",
                           "module": mod, "message": f"{mod}: {data['success']}/{data['total']} ({round(data['rate']*100)}%)",
                           "success": data["rate"] >= 0.9})
        trace_file = get_workstudy() / "governance" / ".traces" / "trace_log.jsonl"
        if trace_file.exists():
            lines = []
            with open(trace_file, "r", encoding="utf-8") as f:
                for line in f:
                    lines.append(line.strip())
            for line in lines[-limit:]:
                try:
                    te = json.loads(line)
                    events.append({"ts": te.get("timestamp", ""), "type": te.get("event_type", "trace"),
                                   "agent": te.get("agent_name", ""),
                                   "message": f"{te.get('event_type', '')} — {te.get('provider', '')} {te.get('model', '')} — {te.get('latency_ms', 0)}ms",
                                   "tokens": te.get("token_input", 0) + te.get("token_output", 0)})
                except Exception:
                    pass
    except Exception as e:
        events.append({"ts": "", "type": "error", "message": str(e)[:200]})
    return {"project": project_id, "events": events[:limit], "total": len(events)}


@kpi_router.get("/timeline/replay/{run_id}")
async def timeline_replay(run_id: str):
    events = []
    trace_file = get_workstudy() / "governance" / ".traces" / "trace_log.jsonl"
    if trace_file.exists():
        with open(trace_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    te = json.loads(line)
                    if te.get("run_id") == run_id:
                        events.append({"ts": te.get("timestamp", ""), "type": te.get("event_type", ""),
                                       "agent": te.get("agent_name", ""), "provider": te.get("provider", ""),
                                       "model": te.get("model", ""), "latency_ms": te.get("latency_ms", 0),
                                       "tokens_in": te.get("token_input", 0), "tokens_out": te.get("token_output", 0),
                                       "status": te.get("status", "")})
                except Exception:
                    pass
    events.sort(key=lambda e: e["ts"])
    return {"run_id": run_id, "events": events, "total_events": len(events),
            "total_tokens": sum(e["tokens_in"] + e["tokens_out"] for e in events),
            "agents": list(set(e["agent"] for e in events if e["agent"])),
            "started": events[0]["ts"] if events else "", "ended": events[-1]["ts"] if events else ""}


# ── Artifacts ─────────────────────────────────────────────────────────

@kpi_router.get("/artifacts/{project_id}")
async def artifacts(project_id: str, module: str = "", page: str = ""):
    items = []
    try:
        from aitest.platform.paths import get_project_dir
        project_dir = get_project_dir(project_id)
        modules_dir = project_dir / "modules"
        if modules_dir.exists():
            for mod_dir in sorted(modules_dir.iterdir()):
                if not mod_dir.is_dir():
                    continue
                mod_name = mod_dir.name
                if module and mod_name != module:
                    continue
                for doc in ["MODULE_CONTEXT.md", "REQUIREMENT_ANALYSIS.md", "PROJECT_CONTEXT.md"]:
                    path = mod_dir / doc
                    items.append({"name": doc, "path": f"{mod_name}/{doc}", "module": mod_name,
                                  "exists": path.exists(), "size": path.stat().st_size if path.exists() else 0})
                pages_dir = mod_dir / "pages"
                if pages_dir.exists():
                    for page_dir in sorted(pages_dir.iterdir()):
                        if not page_dir.is_dir():
                            continue
                        pname = page_dir.name
                        if page and pname != page:
                            continue
                        for doc in ["PAGE_CONTEXT.md", "RISK_MODEL.md", "TEST_CASES.md",
                                     "TECH_ANALYSIS.md", "AUTO_STRATEGY.md"]:
                            path = page_dir / doc
                            items.append({"name": doc, "path": f"{mod_name}/pages/{pname}/{doc}",
                                          "module": mod_name, "page": pname,
                                          "exists": path.exists(),
                                          "size": path.stat().st_size if path.exists() else 0})
    except Exception as e:
        items.append({"name": "error", "path": "", "exists": False, "error": str(e)[:100]})
    return {"project": project_id, "artifacts": items, "total": len(items)}


@kpi_router.get("/artifacts/lineage/{project_id}")
async def artifact_lineage(project_id: str, module: str = "", page: str = ""):
    try:
        from aitest.platform.artifact_lineage import get_lineage
        return get_lineage(project_id, module or "equipment", page or "")
    except Exception as e:
        return {"error": str(e)[:300]}
