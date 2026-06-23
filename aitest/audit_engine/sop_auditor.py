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
    print(report["overall_compliance"])

CLI:
    aitest audit sop --module=<m> [--period=7d] [--json]
"""

import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
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


@dataclass
class SOPViolation:
    """单条 SOP 违规记录。"""
    check_type: str          # "p_check" | "s_check" | "g_check" | "h_check" | "b_check" | "l_check"
    severity: str            # "error" | "warning" | "info"
    violation_type: str = ""
    detail: str = ""
    run_id: str = ""
    evidence: dict = field(default_factory=dict)
    suggestion: str = ""


class SOPAuditor:
    """
    SOP Auditor Agent — SOP 合规审计。

    用法:
        auditor = SOPAuditor()
        report = auditor.audit("equipment", days=7)
        for v in report["violations"]:
            print(f"[{v.severity}] {v.detail}")
    """

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
            from aitest.audit_engine.governance_kpi import KPICollector
            KPICollector().record_audit("sop", module, report)
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("sop_auditor.kpi", "record", e, {"module": module})

        # P0-ACTIVATION (2026-06-15): 从 audit() 直接发射治理事件
        if report["total_violations"] > 0:
            try:
                from aitest.audit_engine.event_bus import emit
                emit("SOPViolation",
                     module=module,
                     run_id="auditor-direct",
                     violation_type="sop_audit",
                     detail=f"SOP审计发现 {report['total_violations']} 个违规")
            except Exception as e:
                from aitest.infra.error_logger import log_error
                log_error("sop_auditor.emit", "SOPViolation", e, {"module": module})

        try:
            from aitest.audit_engine.event_bus import emit
            emit("AuditCompleted",
                 audit_type="sop",
                 module=module,
                 report_path=str(AUDIT_DIR / f"sop-audit-{module}-*.json"),
                 overall_status="warning" if report["total_violations"] > 0 else "ok")
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("sop_auditor.emit", "AuditCompleted", e, {"module": module})

        return report

    # ══════════════════════════════════════════════════════════════════
    #  P-Check: Phase Sequence 合规
    # ══════════════════════════════════════════════════════════════════

    def _run_p_check(self):
        """检查 Phase 执行顺序是否符合 CANONICAL_PHASES 前缀规则。

        P0-FIX (2026-06-15): 增加未知 Phase 检测 + status 一致性检查。
        """
        sop_status = self._load_sop_status()
        if sop_status is None:
            return

        completed = sop_status.get("completed_phases", [])
        if not completed:
            return

        # ── 未知 Phase 检测 ──
        canonical_set = set(CANONICAL_PHASES)
        unknown = [p for p in completed if p not in canonical_set]
        if unknown:
            self.violations.append(SOPViolation(
                check_type="p_check",
                severity="error",
                violation_type="unknown_phase",
                detail=f"completed_phases 包含未知 Phase: {unknown}。规范 Phase 列表: {CANONICAL_PHASES}",
                evidence={"unknown": unknown, "canonical": CANONICAL_PHASES},
                suggestion="检查 SOP_STATUS 是否使用了旧格式 Phase 名称，运行 migrate_sop_status.py 迁移",
            ))

        # ── Status 一致性: status="completed" 但 Phase 不完整 ──
        declared_status = sop_status.get("status", "")
        core_phases = [p for p in CANONICAL_PHASES if p != "Knowledge"]
        missing_core = [p for p in core_phases if p not in completed]
        if declared_status == "completed" and missing_core:
            self.violations.append(SOPViolation(
                check_type="p_check",
                severity="warning",
                violation_type="status_phase_mismatch",
                detail=f"SOP_STATUS 标记为 'completed' 但缺少核心 Phase: {missing_core}",
                evidence={"status": declared_status, "missing_phases": missing_core},
                suggestion="将缺失的 Phase 标记为跳过(含原因)，或继续运行未完成的 Phase",
            ))

        # 验证 completed 是 CANONICAL_PHASES 的前缀
        seen = set()
        for i, phase in enumerate(completed):
            seen.add(phase)
            # Knowledge 可以出现在任何位置
            if phase == "Knowledge":
                continue
            # 检查前驱 Phase 是否已完成
            prereqs = self._get_prerequisites(phase)
            for prereq in prereqs:
                if prereq not in seen:
                    self.violations.append(SOPViolation(
                        check_type="p_check",
                        severity="error",
                        violation_type="phase_order",
                        detail=f"Phase '{phase}' 已完成但前驱 '{prereq}' 未完成",
                        evidence={"completed": completed, "missing_prereq": prereq},
                        suggestion=f"Phase 顺序异常。先运行 {prereq} 再运行 {phase}。",
                    ))

        # 检查是否有 Phase 逆序（前面出现了后面的 Phase，然后前面 Phase 缺失）
        canonical_indices = {p: i for i, p in enumerate(CANONICAL_PHASES) if p != "Knowledge"}
        completed_indices = [
            canonical_indices.get(p, -1) for p in completed
            if p in canonical_indices
        ]
        for i in range(1, len(completed_indices)):
            # 允许 Knowledge 插入任何位置
            if completed_indices[i-1] < 0 or completed_indices[i] < 0:
                continue
            if completed_indices[i] < completed_indices[i-1]:
                self.violations.append(SOPViolation(
                    check_type="p_check",
                    severity="warning",
                    violation_type="phase_reversal",
                    detail=f"Phase 顺序异常: {completed[i-1]} → {completed[i]}",
                    evidence={"completed": completed},
                    suggestion="检查是否手动修改了 SOP_STATUS 或使用了非标准 skip 路径",
                ))
                break

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

    def _run_s_check(self):
        """检查跳过的 Phase 是否有明确的 skip_reason。"""
        sop_status = self._load_sop_status()
        if sop_status is None:
            return

        # 从 SOP_STATUS 检查 skipped_phases（如果有记录）
        skipped = sop_status.get("skipped_phases", [])
        if skipped:
            for skip_entry in skipped:
                if isinstance(skip_entry, dict):
                    if not skip_entry.get("reason"):
                        self.violations.append(SOPViolation(
                            check_type="s_check",
                            severity="warning",
                            violation_type="skip_no_reason",
                            detail=f"Phase '{skip_entry.get('phase', '?')}' 被跳过但无原因记录",
                            evidence=skip_entry,
                            suggestion="在 skip_phases 中为每个跳过的 Phase 添加 reason 字段",
                        ))
                elif isinstance(skip_entry, str):
                    self.violations.append(SOPViolation(
                        check_type="s_check",
                        severity="warning",
                        violation_type="skip_no_reason",
                        detail=f"Phase '{skip_entry}' 被跳过但无原因记录",
                        suggestion="在 skip_phases 中为每个跳过的 Phase 添加 reason 字段",
                    ))

        # 从 Trace 检查是否使用了 skip 模式
        for e in self.events:
            meta = e.get("metadata", {})
            if isinstance(meta, dict) and meta.get("mode") == "skip":
                if not meta.get("skip_reason"):
                    self.violations.append(SOPViolation(
                        check_type="s_check",
                        severity="info",
                        violation_type="skip_no_reason",
                        detail=f"Run {e.get('run_id', '?')} 使用了 skip 模式但无 skip_reason",
                        run_id=e.get("run_id", ""),
                        suggestion="skip 模式应在 metadata.skip_reason 中记录原因",
                    ))

    # ══════════════════════════════════════════════════════════════════
    #  G-Check: Gate Effectiveness
    # ══════════════════════════════════════════════════════════════════

    def _run_g_check(self):
        """检查门禁的通过率 vs 下游失败率，评估门禁有效性。"""
        # 统计 skill_execution 事件中各 skill 的成功/失败
        skill_stats: dict[str, dict] = {}
        for e in self.events:
            if e.get("event_type") != "skill_execution":
                continue
            sid = e.get("skill_id", "")
            if sid not in skill_stats:
                skill_stats[sid] = {"total": 0, "success": 0, "error": 0}
            skill_stats[sid]["total"] += 1
            if e.get("status") == "success":
                skill_stats[sid]["success"] += 1
            else:
                skill_stats[sid]["error"] += 1

        # 关键门禁: test-design → automation
        # test-design 的 skill 全部成功但 automation 的 skill 有失败 → gate 可能虚设
        td_total = sum(s["total"] for sid, s in skill_stats.items()
                       if sid.startswith("test-design/"))
        td_success = sum(s["success"] for sid, s in skill_stats.items()
                         if sid.startswith("test-design/"))
        auto_total = sum(s["total"] for sid, s in skill_stats.items()
                         if sid.startswith("automation/"))
        auto_error = sum(s["error"] for sid, s in skill_stats.items()
                         if sid.startswith("automation/"))

        if td_total > 0 and auto_total > 0:
            td_pass_rate = td_success / td_total
            auto_fail_rate = auto_error / auto_total
            if td_pass_rate > 0.9 and auto_fail_rate > 0.2:
                self.violations.append(SOPViolation(
                    check_type="g_check",
                    severity="warning",
                    violation_type="ineffective_gate",
                    detail=f"test-design gate 通过率 {td_pass_rate:.0%}，但 automation 失败率 {auto_fail_rate:.0%}。Gate 可能过于宽松。",
                    evidence={
                        "td_pass_rate": td_pass_rate,
                        "auto_fail_rate": auto_fail_rate,
                        "td_total": td_total,
                        "auto_total": auto_total,
                    },
                    suggestion="建议在 test-design→automation gate 中增加内容级检查（sop_validator content_check）",
                ))

        # 检查 automation→execution gate
        exec_total = sum(s["total"] for sid, s in skill_stats.items()
                         if sid.startswith("execution/"))
        exec_error = sum(s["error"] for sid, s in skill_stats.items()
                         if sid.startswith("execution/"))
        if auto_total > 0 and exec_total > 0:
            auto_pass_rate = (auto_total - auto_error) / auto_total
            exec_fail_rate = exec_error / exec_total
            if auto_pass_rate > 0.9 and exec_fail_rate > 0.2:
                self.violations.append(SOPViolation(
                    check_type="g_check",
                    severity="warning",
                    violation_type="ineffective_gate",
                    detail=f"automation gate 通过率 {auto_pass_rate:.0%}，但 execution 失败率 {exec_fail_rate:.0%}。",
                    evidence={
                        "auto_pass_rate": auto_pass_rate,
                        "exec_fail_rate": exec_fail_rate,
                    },
                    suggestion="检查代码一致性检查 (code-consistency-checker) 是否有效运行",
                ))

    # ══════════════════════════════════════════════════════════════════
    #  H-Check: HITL Integrity
    # ══════════════════════════════════════════════════════════════════

    def _run_h_check(self):
        """检查 HITL 审批节点是否被频繁跳过。

        P0-FIX (2026-06-15): 增加 fallback 逻辑。
        当 SOP_STATUS 缺少 hitl_stats 字段时，从 trace 事件推断 HITL 活动。
        """
        sop_status = self._load_sop_status()
        if sop_status is None:
            return

        hitl_stats = sop_status.get("hitl_stats", {})
        if hitl_stats:
            for node, stats in hitl_stats.items():
                if isinstance(stats, dict):
                    approve = stats.get("approve", 0)
                    reject = stats.get("reject", 0)
                    skip = stats.get("skip", 0)
                    total = approve + reject + skip
                    if total > 0 and skip / total > 0.8:
                        self.violations.append(SOPViolation(
                            check_type="h_check",
                            severity="warning",
                            violation_type="hitl_degraded",
                            detail=f"HITL 节点 '{node}' skip 率 {skip/total:.0%} ({skip}/{total})，审批流程可能退化",
                            evidence={"node": node, "approve": approve, "reject": reject, "skip": skip},
                            suggestion="检查该审批节点是否必要，或是否需要调整审批触发条件",
                        ))
        else:
            # Fallback: 从 trace 事件推断 HITL 审批活动
            # 查找 agent_decision 事件中的 approval/review 信号
            hitl_events = [
                e for e in self.events
                if e.get("event_type") in ("agent_decision", "milestone")
                and e.get("agent_name") in ("project-agent", "report-agent")
            ]
            if hitl_events:
                # 检查是否有审批相关关键词
                approval_keywords = ["approve", "审批", "通过", "确认", "批准"]
                skip_keywords = ["skip", "跳过", "auto", "自动通过"]
                approve_count = 0
                skip_count = 0
                for e in hitl_events:
                    content = json.dumps(e, ensure_ascii=False).lower() if hasattr(json, 'dumps') else str(e).lower()
                    if any(kw.lower() in content for kw in approval_keywords):
                        approve_count += 1
                    elif any(kw.lower() in content for kw in skip_keywords):
                        skip_count += 1

                total_hitl = approve_count + skip_count
                if total_hitl > 3 and skip_count / max(total_hitl, 1) > 0.8:
                    self.violations.append(SOPViolation(
                        check_type="h_check",
                        severity="warning",
                        violation_type="hitl_degraded_inferred",
                        detail=f"HITL 审批推断: skip 率 {skip_count/max(total_hitl,1):.0%} "
                               f"({skip_count}/{total_hitl}) — 从 trace agent_decision 事件推断",
                        evidence={"approve_signals": approve_count, "skip_signals": skip_count},
                        suggestion="HITL 审批活动不足。检查是否过度使用了自动模式。"
                                   "建议在 SOP_STATUS 中显式记录 hitl_stats 以获得精确检测。",
                    ))

    # ══════════════════════════════════════════════════════════════════
    #  B-Check: Bypass Detection
    # ══════════════════════════════════════════════════════════════════

    def _run_b_check(self):
        """检测在 SOP Graph 外部直接调用 AgentLoop 的情况。

        P0-FIX (2026-06-15): 从白名单模式改为黑名单模式。
        旧逻辑只标记 eval-/standalone-/direct- 前缀 → 漏掉大量空 run_id 直接调用。
        新逻辑: 非 sop- 前缀的 Agent 调用一律标记为潜在绕过。
        """
        # 收集所有 SOP 相关的 run_id
        sop_run_ids: set[str] = set()
        for e in self.events:
            rid = e.get("run_id", "")
            if rid.startswith("sop-"):
                sop_run_ids.add(rid)

        # SOP-phase agent 名称集合 (用于判断是否应走 SOP Graph)
        SOP_PHASE_AGENTS = {
            "project-agent", "requirement-agent", "test-design-agent",
            "automation-agent", "execution-agent", "bug-analysis-agent",
            "report-agent", "knowledge-agent",
        }

        # 收集非 SOP Graph 调用的 Agent 执行
        bypass_agents: dict[str, set[str]] = {}
        for e in self.events:
            rid = e.get("run_id", "")
            agent = e.get("agent_name", "")
            if not agent:
                continue
            # 跳过已知的 SOP run_id
            if rid in sop_run_ids:
                continue
            # 只关注 SOP-phase agent (非 SOP agent 如 knowledge-manager 不算绕过)
            if agent not in SOP_PHASE_AGENTS:
                continue
            # 任何非 sop- 前缀的 run_id (包括空字符串) 都是潜在绕过
            if agent not in bypass_agents:
                bypass_agents[agent] = set()
            bypass_agents[agent].add(rid if rid else "(empty run_id)")

        for agent, rids in sorted(bypass_agents.items()):
            if len(rids) > 0:
                self.violations.append(SOPViolation(
                    check_type="b_check",
                    severity="warning" if len(rids) >= 3 else "info",
                    violation_type="bypass",
                    detail=f"Agent '{agent}' 在 SOP Graph 外部执行了 {len(rids)} 次 "
                           f"(run_ids: {sorted(rids)[:5]}{'...' if len(rids) > 5 else ''})",
                    evidence={"agent": agent, "standalone_runs": sorted(rids)},
                    suggestion="尽量通过 SOP Graph 运行以确保状态同步。如确需独立运行，运行后应更新 SOP_STATUS。",
                ))

    # ══════════════════════════════════════════════════════════════════
    #  L-Check: Loop Health
    # ══════════════════════════════════════════════════════════════════

    def _run_l_check(self):
        """检查 Bug fix 循环的健康状况。"""
        # 统计 bug-analysis 相关的 trace 事件
        bug_cycles: list[int] = []
        current_run = ""
        current_cycle = 0

        for e in self.events:
            rid = e.get("run_id", "")
            sid = e.get("skill_id", "")

            if sid != "diagnosis/bug-analysis":
                continue

            if rid != current_run:
                if current_cycle > 0:
                    bug_cycles.append(current_cycle)
                current_run = rid
                current_cycle = 1
            else:
                current_cycle += 1

        if current_cycle > 0:
            bug_cycles.append(current_cycle)

        if not bug_cycles:
            return

        total_incidents = len(bug_cycles)
        avg_cycles = sum(bug_cycles) / total_incidents
        first_fix_success = sum(1 for c in bug_cycles if c == 1)
        exhausted = sum(1 for c in bug_cycles if c >= 3)

        exhausted_rate = exhausted / total_incidents if total_incidents > 0 else 0

        # 如果 3 次循环均失败率 > 30%
        if exhausted_rate > 0.3:
            self.violations.append(SOPViolation(
                check_type="l_check",
                severity="warning",
                violation_type="loop_exhaustion",
                detail=f"Bug fix 循环耗尽率 {exhausted_rate:.0%} ({exhausted}/{total_incidents})，"
                       f"平均循环 {avg_cycles:.1f} 次，首次修复率 {first_fix_success/total_incidents:.0%}",
                evidence={
                    "total_incidents": total_incidents,
                    "avg_cycles": round(avg_cycles, 1),
                    "first_fix_rate": round(first_fix_success / total_incidents, 2),
                    "exhausted_count": exhausted,
                },
                suggestion="建议升级 debug-agent 的修复策略或增加已知问题库覆盖",
            ))

        # 平均循环次数 > 2
        if avg_cycles > 2.0:
            self.violations.append(SOPViolation(
                check_type="l_check",
                severity="info",
                violation_type="loop_inefficiency",
                detail=f"Bug fix 平均需要 {avg_cycles:.1f} 次循环",
                evidence={"avg_cycles": round(avg_cycles, 1)},
                suggestion="考虑在首次修复失败后增加更详细的错误分析指导",
            ))

    # ══════════════════════════════════════════════════════════════════
    #  X-Check: Context Injection Completeness
    # ══════════════════════════════════════════════════════════════════

    # Skills that MUST have context injected (non-zero context_chars expected)
    CONTEXT_REQUIRED_SKILLS = {
        "test-design/page-analysis", "test-design/risk-modeling",
        "test-design/testcase-design", "automation/tech-analysis",
        "automation/auto-strategy", "automation/code-generation",
        "execution/test-executor", "bug-analysis/bug-analyzer",
    }

    def _run_x_check(self):
        """P1-FIX (2026-06-15): Context injection completeness check.

        检测 context injector 是否正常为需要上下文的 Skill 注入内容。
        从 trace 的 skill_execution metadata 中读取 context_chars。
        """
        # 统计每个需要上下文的 skill 的 context_chars 分布
        skill_context: dict[str, list[int]] = {}
        for e in self.events:
            if e.get("event_type") != "skill_execution":
                continue
            sid = e.get("skill_id", "")
            # 匹配 CONTEXT_REQUIRED_SKILLS (支持尾部匹配)
            matched = None
            for req in self.CONTEXT_REQUIRED_SKILLS:
                if sid == req or sid.endswith("/" + req.split("/")[-1]):
                    matched = req
                    break
            if not matched:
                continue

            meta = e.get("metadata", {})
            ctx_chars = meta.get("context_chars", 0) if isinstance(meta, dict) else 0
            skill_context.setdefault(matched, []).append(ctx_chars)

        for sid, ctx_list in skill_context.items():
            if not ctx_list:
                continue
            total = len(ctx_list)
            zero_count = sum(1 for c in ctx_list if c == 0)
            zero_rate = zero_count / total

            if zero_rate > 0.8 and total >= 3:
                self.violations.append(SOPViolation(
                    check_type="x_check",
                    severity="warning",
                    violation_type="context_missing",
                    detail=f"Skill '{sid}' 上下文注入缺失率 {zero_rate:.0%} "
                           f"({zero_count}/{total} 次 context_chars=0)",
                    evidence={"skill_id": sid, "zero_rate": zero_rate,
                              "total_runs": total, "zero_runs": zero_count},
                    suggestion="检查 ContextInjector 配置: SKILL_CONTEXT_MAP 是否包含该 Skill，"
                               "或 RAG collection 是否为空。",
                ))
            elif zero_rate > 0.3 and total >= 3:
                self.violations.append(SOPViolation(
                    check_type="x_check",
                    severity="info",
                    violation_type="context_partial",
                    detail=f"Skill '{sid}' 上下文注入不稳定: {zero_rate:.0%} 次为空 ({zero_count}/{total})",
                    evidence={"skill_id": sid, "zero_rate": zero_rate},
                    suggestion="检查 context_vars 是否正确传递 module/page 参数",
                ))

    # ══════════════════════════════════════════════════════════════════
    #  数据加载
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

    def _run_baseline_check(self):
        """P0-FIX (2026-06-17): 基于 SOP_STATUS JSON 的基线检查。

        解决 KPI 全模块 compliance=1.0 的问题 — 之前的 7 个 check 都依赖
        trace_log.jsonl，当 trace 没有模块级粒度时全部返回零违规。
        此检查直接从 SOP_STATUS JSON 读取模块完成状态。
        """
        sop_status = self._load_sop_status()

        # ── 无 SOP_STATUS 文件 ──
        if sop_status is None:
            self.violations.append(SOPViolation(
                check_type="baseline_check",
                severity="error",
                violation_type="no_sop_status",
                detail=f"模块 {self.module} 没有 SOP_STATUS JSON 文件 — 未纳入 SOP 追踪",
                suggestion="运行 SOP batch 或手动生成 SOP_STATUS_{self.module}.json",
            ))
            return

        # ── Pending 状态 ──
        status = sop_status.get("status", "")
        if status == "pending":
            reset_reason = sop_status.get("reset_reason", "未指定原因")
            self.violations.append(SOPViolation(
                check_type="baseline_check",
                severity="error",
                violation_type="module_pending",
                detail=f"模块 {self.module} 状态为 pending — 未完成 SOP。原因: {reset_reason}",
                suggestion="运行 SOP batch 或恢复 pre-reset 状态",
            ))
            return

        # ── Partial 状态 ──
        if status == "partial":
            incomplete = sop_status.get("incomplete_phases", [])
            self.violations.append(SOPViolation(
                check_type="baseline_check",
                severity="warning",
                violation_type="module_partial",
                detail=f"模块 {self.module} 状态为 partial — 缺失 Phase: {incomplete}",
                evidence={"incomplete_phases": incomplete},
                suggestion=f"补齐 {len(incomplete)} 个 Phase 后重新标记为 completed",
            ))

        # ── 质量检查: TECH_ANALYSIS 覆盖率 ──
        pages = len(sop_status.get("pages_processed", []))
        artifacts = sop_status.get("artifact_count", 0)
        if pages > 0:
            # 从 sub_pages 统计 TECH_ANALYSIS
            sub_pages = sop_status.get("sub_pages", {})
            if sub_pages:
                tech_count = sum(1 for p in sub_pages.values()
                               if isinstance(p, dict) and p.get("has_tech_analysis"))
                auto_count = sum(1 for p in sub_pages.values()
                               if isinstance(p, dict) and p.get("has_auto_strategy"))

                if tech_count < pages * 0.5 and status == "completed":
                    self.violations.append(SOPViolation(
                        check_type="baseline_check",
                        severity="warning",
                        violation_type="thin_coverage_tech",
                        detail=f"模块 {self.module}: TECH_ANALYSIS 仅覆盖 {tech_count}/{pages} 页面 (<50%)",
                        evidence={"tech_coverage": f"{tech_count}/{pages}"},
                        suggestion="为未覆盖页面生成 TECH_ANALYSIS.md",
                    ))

                if auto_count < pages * 0.3 and status == "completed":
                    self.violations.append(SOPViolation(
                        check_type="baseline_check",
                        severity="warning",
                        violation_type="thin_coverage_auto",
                        detail=f"模块 {self.module}: AUTO_STRATEGY 仅覆盖 {auto_count}/{pages} 页面 (<30%)",
                        evidence={"auto_coverage": f"{auto_count}/{pages}"},
                        suggestion="为未覆盖页面生成 AUTO_STRATEGY.md",
                    ))

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
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    print(f"\n{'='*60}")
    print(f"  SOP Audit: {module}")
    print(f"  Period: {days}d | Compliance: {report['overall_compliance']:.0%}")
    print(f"  Violations: {report['total_violations']} (errors: {report['error_count']})")
    print(f"{'='*60}\n")

    if not report["violations"]:
        print("  ✅ 无 SOP 违规检测到\n")
        return report

    for v in report["violations"]:
        icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(v["severity"], "•")
        print(f"  {icon} [{v['check_type']}] {v['detail']}")
        if v.get("suggestion"):
            print(f"     → {v['suggestion']}")
        print()

    print(f"  Report saved to: {AUDIT_DIR}\n")
    return report


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sop_auditor.py <module> [--days=7] [--json]")
        print("Modules: equipment, system, personnel, warehouse, tank, sales, lab, production, dcs, workflow")
        sys.exit(0)

    module_name = sys.argv[1]
    opts = sys.argv[2:]
    period = 7
    for opt in opts:
        if opt.startswith("--days="):
            period = int(opt.split("=")[1])
    run_sop_audit(module_name, days=period, json_output="--json" in opts)
