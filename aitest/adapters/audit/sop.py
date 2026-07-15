"""SOP Auditor — SOP compliance checking.

拆分为:
  - sop.py: SOPAuditor 核心 + audit (本文件)
  - sop_checks.py: 检查方法 mixin
"""

# [LAYER:Adapter/Audit] 从 aitest/audit_engine/sop_auditor.py 搬入
"""
SOP Auditor Agent — P1-2: SOP 合规检查 + 覆盖率分析 + 门禁验证。

七维检查:
  P-Check:   Phase Sequence 合规性 (阶段顺序、未知阶段、状态一致性)
  SKIP-Check: Skip Audit (跳过的 Phase 是否有原因记录)
  G-Check:   Gate Effectiveness (门禁通过率 vs 下游失败率)
  H-Check:   HITL Integrity (人工审批节点 skip 率)
  B-Check:   Bypass Detection (SOP Graph 外部直接调用 Agent)
  L-Check:   Loop Health (Bug fix 循环统计)
  X-Check:   Context Injection Completeness (上下文注入完整性)

数据源: trace_log.jsonl + checkpoints.sqlite + SOP_STATUS_*.json

与 State Auditor 的规则重叠 (P1 W05):
  State Auditor C-Check (Cross-Source) 与 SOP Auditor P-Check 都检查 phase 一致性，但角度不同:
    - State Auditor: 检查 SQLite vs JSON vs 文件系统 三方是否一致
    - SOP Auditor:   检查 phase 执行顺序是否符合 CANONICAL_PHASES
  State Auditor Q-Check (Quality Gate) 与 SOP Auditor G-Check 都涉及质量:
    - State Auditor: 产物内容质量 (最小行数、关键词匹配)
    - SOP Auditor:   门禁通过到下游的转化率 (质量数据而非内容质量)
  → 不合并，但共享 rule_id 前缀以便交叉引用。统一规则目录: governance/rules/

用法:
    from aitest.audit_engine.sop_auditor import SOPAuditor, run_sop_audit

    auditor = SOPAuditor()
    report = auditor.audit("equipment", days=7)
    logger.info(report["overall_compliance"])

CLI:
    aitest audit sop --module=<m> [--period=7d] [--json]
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from aitest.runtime.paths import get_workstudy
from aitest.adapters.event.interface import emit
from aitest.adapters.audit.ports import record_kpi


import logging

logger = logging.getLogger(__name__)

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = get_workstudy()
GOVERNANCE = WORKSTUDY / "governance"
TRACE_LOG = GOVERNANCE / ".traces" / "trace_log.jsonl"
CHECKPOINT_DB = GOVERNANCE / ".graph_state" / "checkpoints.sqlite"
ARTIFACTS_DIR = GOVERNANCE / "artifacts"
SOP_STATUS_DIR = ARTIFACTS_DIR / "sop-status"
AUDIT_DIR = ARTIFACTS_DIR / "audits"

# ── SOP 规范 ──────────────────────────────────────────────────────────
# 应与 aitest/graphs/state.py CANONICAL_PHASES 保持一致
CANONICAL_PHASES = [
    "Project Init",
    "Requirement",
    "Test Design",
    "Automation",
    "Execute & Debug",
    "Bug Analysis",
    "Data Sanitization",
    "Report",
    "Knowledge",
]

from aitest.adapters.audit.sop_checks import SOPCheckMixin, SOPViolation


class SOPAuditor(SOPCheckMixin):
    def __init__(self):
        self.violations: list[SOPViolation] = []
        self.module = ""
        self.events: list[dict] = []


    def audit(self, module: str, days: int = 7,
              checks: list[str] = None) -> dict:
        """
        对指定模块执行 SOP 合规审计。

        参数:
            module: 模块名
            days:   回溯天数
            checks: 指定检查维度，默认全部

        返回:
            {
                "module": "equipment",
                "audit_time": "...",
                "period": "7d",
                "overall_compliance": 0.85,
                "violations": [...],
                "checks": {...}
            }
        """
        self.violations = []
        self.module = module
        self.events = self._load_trace_events(days)

        if checks is None:
            checks = ["baseline_check", "p_check", "s_check", "g_check", "h_check", "b_check", "l_check", "x_check"]

        if "baseline_check" in checks:
            self._run_baseline_check()
        if "p_check" in checks:
            self._run_p_check()
        if "s_check" in checks:
            self._run_s_check()
        if "g_check" in checks:
            self._run_g_check()
        if "h_check" in checks:
            self._run_h_check()
        if "b_check" in checks:
            self._run_b_check()
        if "l_check" in checks:
            self._run_l_check()
        if "x_check" in checks:
            self._run_x_check()

        # 计算合规分
        total_checks = len(checks)
        checks_with_issues = len(set(v.check_type for v in self.violations))
        errors = [v for v in self.violations if v.severity == "error"]
        compliance = max(0.0, 1.0 - (checks_with_issues / max(total_checks, 1)))

        report = {
            "module": module,
            "audit_time": datetime.now().isoformat(),
            "period": f"{days}d",
            "overall_compliance": round(compliance, 3),
            "total_violations": len(self.violations),
            "error_count": len(errors),
            "warning_count": len(self.violations) - len(errors),
            "violations": [v.__dict__ for v in self.violations],
            "checks": {
                c: self._summarize_check(c) for c in checks
            },
        }

        self._write_report(report)

        # L4-MEASURED (2026-06-15): 记录 KPI 数据点
        try:
            record_kpi("sop", module, report)
        except Exception as e:
            from aitest.runtime.error_handling import log_error
            log_error("sop_auditor.kpi", "record", e, {"module": module})

        # P0-ACTIVATION (2026-06-15): 从 audit() 直接发射治理事件
        if report["total_violations"] > 0:
            try:
                emit("SOPViolation",
                     module=module,
                     run_id="auditor-direct",
                     violation_type="sop_audit",
                     detail=f"SOP审计发现 {report['total_violations']} 个违规")
            except Exception as e:
                from aitest.runtime.error_handling import log_error
                log_error("sop_auditor.emit", "SOPViolation", e, {"module": module})

        try:
            emit("AuditCompleted",
                 audit_type="sop",
                 module=module,
                 report_path=str(AUDIT_DIR / f"sop-audit-{module}-*.json"),
                 overall_status="warning" if report["total_violations"] > 0 else "ok")
        except Exception as e:
            from aitest.runtime.error_handling import log_error
            log_error("sop_auditor.emit", "AuditCompleted", e, {"module": module})

        return report

    # ══════════════════════════════════════════════════════════════════
    #  P-Check: Phase Sequence 合规
    # ══════════════════════════════════════════════════════════════════


    def _get_prerequisites(self, phase: str) -> list[str]:
        """返回 Phase 的前驱 Phase 列表。"""
        prereqs = {
            "Project Init": [],
            "Requirement": ["Project Init"],
            "Test Design": ["Requirement"],
            "Automation": ["Test Design"],
            "Execute & Debug": ["Automation"],
            "Bug Analysis": ["Execute & Debug"],
            "Data Sanitization": ["Execute & Debug"],
            "Report": ["Execute & Debug"],
            "Knowledge": [],
        }
        return prereqs.get(phase, [])

    # ══════════════════════════════════════════════════════════════════
    #  SKIP-Check: Skip Audit
    # ══════════════════════════════════════════════════════════════════


    def _load_trace_events(self, days: int) -> list[dict]:
        """加载最近 N 天的 trace 事件，按 module 过滤。"""
        if not TRACE_LOG.exists():
            return []

        cutoff = datetime.now() - timedelta(days=days)
        events = []

        try:
            with open(TRACE_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        ts = datetime.fromisoformat(
                            entry.get("timestamp", "2000-01-01T00:00:00")
                        )
                        if ts < cutoff:
                            continue
                        # 按 module 过滤（metadata 或 skill_id 中包含 module 信息）
                        meta = entry.get("metadata", {})
                        mod = meta.get("module", "") if isinstance(meta, dict) else ""
                        if self.module and mod and mod != self.module:
                            continue
                        events.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception:
            pass

        return events

    # ══════════════════════════════════════════════════════════════════
    #  Baseline Check: SOP_STATUS 完整性 + 质量
    # ══════════════════════════════════════════════════════════════════


    def _load_sop_status(self) -> dict | None:
        """加载 SOP_STATUS JSON。"""
        path = SOP_STATUS_DIR / f"SOP_STATUS_{self.module}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    # ══════════════════════════════════════════════════════════════════
    #  辅助
    # ══════════════════════════════════════════════════════════════════


    def _summarize_check(self, check_type: str) -> dict:
        """汇总某类检查的结果。"""
        related = [v for v in self.violations if v.check_type == check_type]
        return {
            "total": len(related),
            "errors": len([v for v in related if v.severity == "error"]),
            "warnings": len([v for v in related if v.severity == "warning"]),
            "infos": len([v for v in related if v.severity == "info"]),
            "ok": len(related) == 0,
        }


    def _write_report(self, report: dict):
        """持久化审计报告。"""
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = AUDIT_DIR / f"sop-audit-{self.module}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        try:
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            pass


# ══════════════════════════════════════════════════════════════════════════
#  CLI 入口
# ══════════════════════════════════════════════════════════════════════════

def run_sop_audit(module: str, days: int = 7, json_output: bool = False) -> dict:
    """
    P1-2: 运行 SOP Auditor。

    参数:
        module:  模块名
        days:    回溯天数
        json_output: 输出 JSON

    返回:
        审计报告 dict
    """
    auditor = SOPAuditor()
    report = auditor.audit(module, days=days)

    if json_output:
        logger.info(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    logger.info(f"\n{'='*60}")
    logger.info(f"  SOP Audit: {module}")
    logger.info(f"  Period: {days}d | Compliance: {report['overall_compliance']:.0%}")
    logger.error(f"  Violations: {report['total_violations']} (errors: {report['error_count']})")
    logger.info(f"{'='*60}\n")

    if not report["violations"]:
        logger.info("  ✅ 无 SOP 违规检测到\n")
        return report

    for v in report["violations"]:
        icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(v["severity"], "•")
        logger.info(f"  {icon} [{v['check_type']}] {v['detail']}")
        if v.get("suggestion"):
            logger.info(f"     → {v['suggestion']}")
        logger.info()

    logger.info(f"  Report saved to: {AUDIT_DIR}\n")
    return report


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logger.info("Usage: python sop_auditor.py <module> [--days=7] [--json]")
        logger.info("Modules: equipment, system, personnel, warehouse, tank, sales, lab, production, dcs, workflow")
        sys.exit(0)

    module_name = sys.argv[1]
    opts = sys.argv[2:]
    period = 7
    for opt in opts:
        if opt.startswith("--days="):
            period = int(opt.split("=")[1])
    run_sop_audit(module_name, days=period, json_output="--json" in opts)

def run_sop_audit(module: str, days: int = 7, json_output: bool = False) -> dict:
    """
    P1-2: 运行 SOP Auditor。

    参数:
        module:  模块名
        days:    回溯天数
        json_output: 输出 JSON

    返回:
        审计报告 dict
    """
    auditor = SOPAuditor()
    report = auditor.audit(module, days=days)

    if json_output:
        logger.info(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    logger.info(f"\n{'='*60}")
    logger.info(f"  SOP Audit: {module}")
    logger.info(f"  Period: {days}d | Compliance: {report['overall_compliance']:.0%}")
    logger.error(f"  Violations: {report['total_violations']} (errors: {report['error_count']})")
    logger.info(f"{'='*60}\n")

    if not report["violations"]:
        logger.info("  ✅ 无 SOP 违规检测到\n")
        return report

    for v in report["violations"]:
        icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(v["severity"], "•")
        logger.info(f"  {icon} [{v['check_type']}] {v['detail']}")
        if v.get("suggestion"):
            logger.info(f"     → {v['suggestion']}")
        logger.info()

    logger.info(f"  Report saved to: {AUDIT_DIR}\n")
    return report


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logger.info("Usage: python sop_auditor.py <module> [--days=7] [--json]")
        logger.info("Modules: equipment, system, personnel, warehouse, tank, sales, lab, production, dcs, workflow")
        sys.exit(0)

    module_name = sys.argv[1]
    opts = sys.argv[2:]
    period = 7
    for opt in opts:
        if opt.startswith("--days="):
            period = int(opt.split("=")[1])
    run_sop_audit(module_name, days=period, json_output="--json" in opts)
