"""
StateAuditor — 治理状态审计器 (S/C/Q/T Check).

从 1224 行拆分为:
  - state.py: StateAuditor 核心 + audit + repairs (本文件)
  - state_checks.py: 检查方法 mixin
"""

import json
import logging
import time
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from aitest.adapters.audit.state_checks import StateCheckMixin

logger = logging.getLogger(__name__)


class DriftRecord:
    """单条漂移记录。"""
    check_type: str          # "s_check" | "c_check" | "orphan"
    severity: str            # "error" | "warning" | "info"
    phase: str = ""
    description: str = ""
    expected: str = ""
    actual: str = ""
    suggestion: str = ""




class StateAuditor(StateCheckMixin):
    """
    State Auditor Agent — 状态漂移检测。

    用法:
        auditor = StateAuditor()
        report = auditor.audit("equipment")
        if report["overall_status"] != "ok":
            for drift in report["drifts"]:
                logger.info(f"[{drift.severity}] {drift.description}")
    """

    def __init__(self):
        self.drifts: list[DriftRecord] = []
        self.module = ""
        self.pages: list[str] = []


    def audit(self, module: str, auto_repair: bool = False,
              checks: list[str] = None) -> dict:
        """
        对指定模块执行完整状态审计。

        参数:
            module: 模块名
            auto_repair: 是否尝试自动修复可修复的漂移
            checks: 指定检查类型列表，默认全部 (s_check, orphan, c_check, q_check, t_check)

        返回:
            {
                "module": "equipment",
                "audit_time": "2026-06-15T10:30:00",
                "overall_status": "ok" | "warning" | "error",
                "drifts": [...],
                "repairs_attempted": [...],
                "checks": {...}
            }
        """
        self.drifts = []
        self.module = module
        self.pages = self._discover_pages()

        if checks is None:
            checks = ["s_check", "orphan", "c_check", "q_check", "t_check", "r_check", "o_check", "bsc_check"]

        # S-Check: State-to-Artifact
        if "s_check" in checks:
            self._run_s_check()

        # R-Check: Reverse State-to-Artifact (artifact 存在但 state 未记录)
        if "r_check" in checks:
            self._run_r_check()

        # O-Check: Output-State Consistency (Agent 输出内容有效性)
        if "o_check" in checks:
            self._run_o_check()

        # A-Check: Artifact orphan detection
        if "orphan" in checks:
            self._run_orphan_check()

        # C-Check: Cross-source consistency
        if "c_check" in checks:
            self._run_c_check()

        # P1-1: Q-Check — 产物质量门禁
        if "q_check" in checks:
            self._run_q_check()

        # P1-1: T-Check — Phase 时间线合理性
        if "t_check" in checks:
            self._run_t_check()

        # P2-5: BSC-Check — 业务场景覆盖质量门禁
        if "bsc_check" in checks:
            self._run_bsc_check()

        repairs = []
        if auto_repair:
            repairs = self._attempt_repairs()

        # 判定整体状态
        errors = [d for d in self.drifts if d.severity == "error"]
        warnings = [d for d in self.drifts if d.severity == "warning"]

        if errors:
            overall = "error"
        elif warnings:
            overall = "warning"
        else:
            overall = "ok"

        report = {
            "module": module,
            "audit_time": datetime.now().isoformat(),
            "overall_status": overall,
            "drift_count": len(self.drifts),
            "error_count": len(errors),
            "warning_count": len(warnings),
            "drifts": [d.__dict__ for d in self.drifts],
            "repairs_attempted": repairs,
            "checks": {
                "s_check": self._summarize_check("s_check"),
                "r_check": self._summarize_check("r_check"),
                "o_check": self._summarize_check("o_check"),
                "orphan_check": self._summarize_check("orphan"),
                "c_check": self._summarize_check("c_check"),
                "q_check": self._summarize_check("q_check"),
                "t_check": self._summarize_check("t_check"),
            },
        }

        # 持久化审计报告
        self._write_report(report)

        # P0-ACTIVATION (2026-06-15): 从 audit() 直接发射治理事件
        # 修复 Dead Path #2 — 此前 emit 仅在 sop_graph.exit_node 中，
        # CLI/API 审计路径发现漂移但不发射事件。
        if report["drift_count"] > 0:
            try:
                emit("StateDrift",
                     module=module,
                     run_id="auditor-direct",
                     drift_count=report["drift_count"],
                     error_count=report["error_count"],
                     warning_count=report["warning_count"],
                     overall_status=report["overall_status"])
            except Exception as e:
                from aitest.runtime.error_handling import log_error
                log_error("state_auditor.emit", "StateDrift", e, {"module": module})

        # L4-MEASURED (2026-06-15): 记录 KPI 数据点
        try:
            from aitest.audit_engine.governance_kpi import KPICollector
            KPICollector().record_audit("state", module, report)
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("state_auditor.kpi", "record", e, {"module": module})

        # Dead Path #3: AuditCompleted 事件之前不存在
        try:
            emit("AuditCompleted",
                 audit_type="state",
                 module=module,
                 report_path=str(AUDIT_DIR / f"state-audit-{module}-*.json"),
                 overall_status=report["overall_status"])
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("state_auditor.emit", "AuditCompleted", e, {"module": module})

        return report

    # ── 页面发现 ─────────────────────────────────────────────────────


    def _discover_pages(self) -> list[str]:
        """发现模块下的所有页面目录。"""
        pages_dir = get_module_dir(self.module) / "pages"
        if not pages_dir.exists():
            return []
        return sorted([p.name for p in pages_dir.iterdir() if p.is_dir()])


    def _module_dir(self) -> Path:
        return get_module_dir(self.module)

    # ── S-Check: State-to-Artifact ────────────────────────────────────


    def _attempt_repairs(self) -> list[dict]:
        """
        P1-1: 尝试自动修复可修复的漂移。

        修复能力:
          1. C-Check: JSON 缺少 checkpoint 中的 phase → 重新导出 JSON
          2. S-Check: 产物缺失但同名文件在其他位置存在 → 报告不可自动修复
          3. Q-Check: 空文件 → 标记为待修复（不可自动修复，需 Agent 重跑）
        """
        repairs = []

        # 修复1: C-Check — JSON 缺少 checkpoint 中的 phase → 重新导出 JSON
        c_drifts = [d for d in self.drifts if d.check_type == "c_check" and d.severity == "error"]
        if c_drifts:
            cp_phases = self._load_checkpoint_phases()
            if cp_phases:
                try:
                    import json as _json
                    status_path = SOP_STATUS_DIR / f"SOP_STATUS_{self.module}.json"
                    existing = self._load_sop_status() or {}
                    existing["completed_phases"] = cp_phases
                    existing["_auto_repaired_at"] = datetime.now().isoformat()
                    existing["_repair_note"] = "从 SQLite checkpoint 自动恢复"
                    status_path.parent.mkdir(parents=True, exist_ok=True)
                    status_path.write_text(
                        _json.dumps(existing, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                    repairs.append({
                        "type": "c_check_repair",
                        "action": f"从 checkpoint 恢复了 {len(cp_phases)} 个 Phase 到 SOP_STATUS",
                        "phases": cp_phases,
                    })
                    # 清除已修复的 drifts
                    self.drifts = [d for d in self.drifts if d.check_type != "c_check" or d.severity != "error"]
                except Exception as e:
                    repairs.append({
                        "type": "c_check_repair_failed",
                        "error": str(e)[:200],
                    })

        # 修复2: Q-Check — 空文件标记（不能自动填内容，但可以标记）
        q_drifts = [d for d in self.drifts if d.check_type == "q_check" and d.severity == "warning"]
        if q_drifts:
            repairs.append({
                "type": "q_check_note",
                "action": f"检测到 {len(q_drifts)} 个文件质量不足",
                "note": "质量不足的文件需要 Agent 重新生成，无法自动修复。建议运行对应 Phase Agent。",
                "affected_files": [d.description.split(":")[0] if ":" in d.description else d.description for d in q_drifts],
            })

        # 修复3: S-Check orphan — 自动归档非标准产物
        orphan_drifts = [d for d in self.drifts if d.check_type == "orphan"]
        if orphan_drifts:
            archive_dir = ARTIFACTS_DIR / "archive"
            archive_dir.mkdir(parents=True, exist_ok=True)
            archived = 0
            for d in orphan_drifts:
                orphan_path = Path(d.actual) if d.actual else None
                if orphan_path and orphan_path.exists():
                    try:
                        dest = archive_dir / orphan_path.name
                        if dest.exists():
                            dest = archive_dir / f"{orphan_path.stem}_{int(time.time())}{orphan_path.suffix}"
                        orphan_path.rename(dest)
                        archived += 1
                    except OSError:
                        pass
            if archived > 0:
                repairs.append({
                    "type": "orphan_archive",
                    "action": f"归档了 {archived} 个孤儿文件到 {archive_dir}",
                })
                # 清除已修复的orphan drifts
                self.drifts = [d for d in self.drifts if d.check_type != "orphan"]

        return repairs


    def _write_report(self, report: dict):
        """将审计报告持久化到 governance/artifacts/audits/。"""
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = AUDIT_DIR / f"state-audit-{self.module}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
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


def run_state_audit(module: str, auto_repair: bool = False, json_output: bool = False) -> dict:
    """
    P0-2: 运行 State Auditor。

    参数:
        module:      模块名
        auto_repair: 是否尝试自动修复
        json_output: 是否输出 JSON 而非人类可读文本

    返回:
        审计报告 dict
    """
    auditor = StateAuditor()
    report = auditor.audit(module, auto_repair=auto_repair)

    if json_output:
        logger.info(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    # 人类可读输出
    logger.info(f"\n{'='*60}")
    logger.info(f"  State Audit: {module}")
    logger.info(f"  Time: {report['audit_time']}")
    logger.info(f"  Status: {report['overall_status'].upper()}")
    logger.info(f"{'='*60}\n")

    if not report["drifts"]:
        logger.info("  ✅ 无状态漂移检测到\n")
        return report

    for d in report["drifts"]:
        icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(d["severity"], "•")
        logger.info(f"  {icon} [{d['severity'].upper()}] [{d.get('check_type', '')}] {d['description']}")
        if d.get("phase"):
            logger.info(f"     Phase: {d['phase']}")
        if d.get("suggestion"):
            logger.info(f"     → {d['suggestion']}")
        logger.info()

    logger.error(f"  Drifts: {report['drift_count']} (errors: {report['error_count']}, warnings: {report['warning_count']})")

    if report.get("repairs_attempted"):
        logger.info(f"\n  🔧 Repairs: {len(report['repairs_attempted'])}")
        for r in report["repairs_attempted"]:
            logger.info(f"     {r.get('action', r)}")

    audit_report_path = AUDIT_DIR / f"state-audit-{module}-*.json"
    logger.info(f"\n  Report saved to: {AUDIT_DIR}")
    logger.info()

    return report


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        logger.info("Usage: python state_auditor.py <module> [--repair] [--json]")
        logger.info("Modules: equipment, system, personnel, warehouse, tank, sales, lab, production, dcs, workflow")
        sys.exit(0)

    module_name = sys.argv[1]
    opts = set(sys.argv[2:])
    run_state_audit(
        module_name,
        auto_repair="--repair" in opts,
        json_output="--json" in opts,
    )
