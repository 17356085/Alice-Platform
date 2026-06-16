"""
Scheduled Audit Runner — L4 Measured: 定时审计调度。

职责:
  1. 按配置的间隔周期性运行 State/SOP/Cost 审计
  2. 自动发射治理事件
  3. 自动记录 KPI 数据点
  4. 支持模块列表配置

用法:
    python -m aitest.scheduled_audit --interval=3600 --modules=equipment,tank
    python -m aitest.scheduled_audit --once  # 一次性运行全部模块

CLI:
    aitest audit scheduled [--interval=<s>] [--modules=<m1,m2>]
"""

import time
import sys
from pathlib import Path
from datetime import datetime

WORKSTUDY = Path(__file__).resolve().parent.parent
CONTEXT_MODULES = WORKSTUDY / "governance" / "context" / "projects" / "web-automation" / "modules"

# 默认审计间隔（秒）
DEFAULT_INTERVAL = 86400  # 24h
# 默认审计模块（自动发现）
DEFAULT_MODULES = [
    "equipment", "system", "personnel", "warehouse",
    "tank", "sales", "lab", "production", "workflow",
]


def discover_modules() -> list[str]:
    """从 context 目录自动发现模块列表。"""
    if not CONTEXT_MODULES.exists():
        return DEFAULT_MODULES
    return sorted([
        d.name for d in CONTEXT_MODULES.iterdir()
        if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_")
    ])


def run_all_audits(modules: list[str] = None) -> dict:
    """一次性运行全部审计（所有模块 + 全部审计类型）。"""
    if modules is None:
        modules = discover_modules()

    results = {
        "started_at": datetime.now().isoformat(),
        "state_audits": {},
        "sop_audits": {},
        "cost_audit": None,
    }

    # 1. State Auditor — 每个模块
    from aitest.state_auditor import StateAuditor
    state_auditor = StateAuditor()
    for mod in modules:
        try:
            report = state_auditor.audit(mod)
            results["state_audits"][mod] = {
                "status": report["overall_status"],
                "drift_count": report["drift_count"],
            }
        except Exception as e:
            results["state_audits"][mod] = {"status": "error", "error": str(e)[:200]}

    # 2. SOP Auditor — 每个模块
    from aitest.sop_auditor import SOPAuditor
    sop_auditor = SOPAuditor()
    for mod in modules:
        try:
            report = sop_auditor.audit(mod, days=7)
            results["sop_audits"][mod] = {
                "compliance": report["overall_compliance"],
                "violations": report["total_violations"],
            }
        except Exception as e:
            results["sop_audits"][mod] = {"compliance": 0, "error": str(e)[:200]}

    # 3. Cost Auditor — 全局一次
    from aitest.cost_auditor import CostAuditor
    try:
        cost_auditor = CostAuditor()
        cost_report = cost_auditor.audit(days=7)
        results["cost_audit"] = {
            "total_cost": cost_report["total_cost"],
            "alert_count": cost_report["alert_count"],
        }
    except Exception as e:
        results["cost_audit"] = {"error": str(e)[:200]}

    results["completed_at"] = datetime.now().isoformat()
    return results


def run_scheduled(interval: int = DEFAULT_INTERVAL, modules: list[str] = None):
    """以指定间隔周期性运行审计。"""
    if modules is None:
        modules = discover_modules()

    print(f"[ScheduledAudit] Started. Interval={interval}s, Modules={modules}")
    print(f"[ScheduledAudit] Press Ctrl+C to stop.\n")

    iteration = 0
    try:
        while True:
            iteration += 1
            started = time.time()
            print(f"[ScheduledAudit] #{iteration} — {datetime.now().strftime('%H:%M:%S')}")

            results = run_all_audits(modules)

            # 汇总输出
            state_drifts = sum(
                r.get("drift_count", 0)
                for r in results["state_audits"].values()
            )
            sop_violations = sum(
                r.get("violations", 0)
                for r in results["sop_audits"].values()
            )
            cost_alerts = (results.get("cost_audit") or {}).get("alert_count", 0)

            print(f"  State:  {state_drifts} drifts across {len(results['state_audits'])} modules")
            print(f"  SOP:    {sop_violations} violations across {len(results['sop_audits'])} modules")
            print(f"  Cost:   {cost_alerts} alerts, \${results.get('cost_audit', {}).get('total_cost', 0):.4f}")
            print(f"  Done in {time.time() - started:.1f}s\n")

            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n[ScheduledAudit] Stopped. {iteration} iterations completed.")


# ══════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Scheduled Audit Runner")
    p.add_argument("--interval", type=int, default=0,
                   help=f"Audit interval in seconds (default: one-shot)")
    p.add_argument("--once", action="store_true", help="Run once and exit")
    p.add_argument("--modules", type=str, default=None,
                   help="Comma-separated module list")
    p.add_argument("--json", action="store_true", help="JSON output (once mode)")

    args = p.parse_args()

    modules = args.modules.split(",") if args.modules else discover_modules()

    if args.once or args.interval == 0:
        results = run_all_audits(modules)
        if args.json:
            import json
            print(json.dumps(results, ensure_ascii=False, indent=2))
        else:
            print(f"\nModules audited: {len(modules)}")
            print(f"State drifts: {sum(r.get('drift_count', 0) for r in results['state_audits'].values())}")
            print(f"SOP violations: {sum(r.get('violations', 0) for r in results['sop_audits'].values())}")
            cost = results.get("cost_audit", {})
            print(f"Cost: \${cost.get('total_cost', 0):.4f}, {cost.get('alert_count', 0)} alerts")
    else:
        run_scheduled(interval=args.interval, modules=modules)
