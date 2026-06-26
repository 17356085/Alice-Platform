"""Governance audit + online monitoring + trace API endpoints.
Extracted from main.py (P0-2 split, 2026-06-25).

Routes:
  GET  /api/audit/state       — State Auditor
  GET  /api/audit/sop         — SOP Auditor
  GET  /api/audit/cost        — Cost Auditor
  GET  /api/audit/safety      — Safety Auditor
  GET  /api/audit/governance  — Aggregated audit summary
  GET  /api/online/analyze    — Online Monitor
  GET  /api/trace/{run_id}    — Trace replay
  GET  /api/trace/runs        — Recent runs
"""
from __future__ import annotations
from datetime import datetime

from fastapi import APIRouter

audit_router = APIRouter(prefix="/api", tags=["audit"])


@audit_router.get("/audit/state")
async def audit_state(module: str = "equipment", repair: bool = False):
    try:
        from aitest.audit_engine.state_auditor import StateAuditor
        return StateAuditor().audit(module, auto_repair=repair)
    except Exception as e:
        return {"error": str(e)[:300], "overall_status": "error", "drift_count": 0, "error_count": 1}


@audit_router.get("/audit/sop")
async def audit_sop(module: str = "equipment", days: int = 7):
    try:
        from aitest.audit_engine.sop_auditor import SOPAuditor
        return SOPAuditor().audit(module, days=days)
    except Exception as e:
        return {"error": str(e)[:300], "overall_compliance": 0, "total_violations": 0}


@audit_router.get("/audit/cost")
async def audit_cost(days: int = 7):
    try:
        from aitest.audit_engine.cost_auditor import CostAuditor
        return CostAuditor().audit(days=days)
    except Exception as e:
        return {"error": str(e)[:300], "total_cost": 0, "alert_count": 0}


@audit_router.get("/audit/safety")
async def audit_safety(module: str = "equipment", days: int = 7):
    try:
        from aitest.audit_engine.safety_auditor import SafetyAuditor
        return SafetyAuditor().audit(module, days=days)
    except Exception as e:
        return {"error": str(e)[:300], "overall_status": "error", "safety_score": 0}


@audit_router.get("/audit/governance")
async def audit_governance(module: str = "equipment", days: int = 7):
    result = {"module": module, "timestamp": datetime.now().isoformat()}
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


@audit_router.get("/online/analyze")
async def online_analyze(module: str = "system", days: int = 7):
    try:
        from aitest.audit_engine.online_monitor import OnlineMonitor
        return OnlineMonitor().analyze(module, days=days)
    except Exception as e:
        return {"error": str(e)[:300], "module": module}


@audit_router.get("/trace/{run_id}")
async def trace_replay(run_id: str):
    try:
        from aitest.audit_engine.online_monitor import get_run_trace_replay
        return get_run_trace_replay(run_id)
    except Exception as e:
        return {"error": str(e)[:300], "run_id": run_id, "steps": []}


@audit_router.get("/trace/runs")
async def trace_runs(limit: int = 20):
    try:
        from aitest.audit_engine.online_monitor import list_recent_runs
        return {"runs": list_recent_runs(limit=limit)}
    except Exception as e:
        return {"error": str(e)[:300], "runs": []}
