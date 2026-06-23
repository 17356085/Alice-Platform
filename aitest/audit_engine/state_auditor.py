"""
State Auditor Agent — P0-2: 状态一致性检查 + 漂移检测。

职责:
  1. S-Check:  State-to-Artifact — SOP 状态声称完成的 Phase 产物是否真实存在
  2. R-Check:  Reverse Artifact-to-State — 产物存在但 State 未记录 (反向漂移)
  3. O-Check:  Output-State Consistency — Agent 输出内容有效性
  4. C-Check:  Cross-Source — checkpoint vs SOP_STATUS JSON vs 文件系统三方一致性
  5. Q-Check:  Quality Gate — 产物内容质量门禁
  6. T-Check:  Timeline — 时间线合理性
  7. Orphan Check — 非标准产物文件检测

与 SOP Auditor 的规则重叠 (P1 W05):
  C-Check (Cross-Source) 与 SOP Auditor P-Check 都验证 phase 状态:
    - State Auditor: 比较 SQLite/JSON/文件系统的时间戳和内容
    - SOP Auditor:   检查 phase 执行顺序是否符合 CANONICAL_PHASES
  Q-Check (Quality Gate) 与 SOP Auditor G-Check 都涉及质量度量:
    - State Auditor: 文件级 (行数、关键词、占位符检测)
    - SOP Auditor:   流程级 (通过率、失败率、转化率)
  → 互补关系，不合并。共享 governance/rules/ 统一规则目录。

注意: SOP Auditor 使用的 "S-Check" = Skip Audit (跳过的 Phase 是否有原因记录)，
     与本文件的 "S-Check" = State-to-Artifact 完全不同。两者不重叠。

用法:
    from aitest.audit_engine.state_auditor import StateAuditor, run_state_audit

    auditor = StateAuditor()
    report = auditor.audit("equipment")
    print(report["overall_status"], report["drifts"])

CLI:
    aitest audit state --module=<m>
    aitest audit state --module=<m> --json
"""

import json
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from datetime import datetime

from aitest.graphs.state import get_module_dir, get_page_dir

# ── 路径配置 ──────────────────────────────────────────────────────────
from aitest.platform.paths import get_workstudy, get_context_modules, get_governance_dir
WORKSTUDY = get_workstudy()
GOVERNANCE = get_governance_dir()
CONTEXT_MODULES = get_context_modules()
ARTIFACTS_DIR = GOVERNANCE / "artifacts"
SOP_STATUS_DIR = ARTIFACTS_DIR / "sop-status"
CHECKPOINT_DB = GOVERNANCE / ".graph_state" / "checkpoints.sqlite"
AUDIT_DIR = ARTIFACTS_DIR / "audits"

# ── Phase → 预期产物映射 ─────────────────────────────────────────────
# 每个 Phase 完成后应存在的文件（相对于 module_dir）
PHASE_EXPECTED_ARTIFACTS = {
    "Project Init": {
        "module_level": ["PROJECT_CONTEXT.md"],
        "per_page": [],
    },
    "Requirement": {
        "module_level": ["MODULE_CONTEXT.md"],
        "per_page": [],
    },
    "Test Design": {
        "module_level": [],
        "per_page": ["PAGE_CONTEXT.md", "RISK_MODEL.md", "BUSINESS_SCENARIOS.md", "TEST_DESIGN.md", "TEST_CASES.md"],
    },
    "Automation": {
        "module_level": [],
        "per_page": [
            "TECH_ANALYSIS.md", "AUTO_STRATEGY.md",
            "PAGE_ELEMENT_POSITION.md", "PAGE_INTERFACE.yaml",
        ],
    },
    "Execute & Debug": {
        "module_level": [],
        "per_page": [],
        # allure-results 目录由 Gate checker 检查
        # 本阶段主要产出为测试执行结果 (allure-results/*.json)，
        # 治理文档层面无强制产物
    },
    "Bug Analysis": {
        "module_level": [],
        "per_page": ["BUG_ANALYSIS.md"],
    },
    "Data Sanitization": {
        "module_level": ["DATA_QUALITY.md"],
        "per_page": [],
    },
    "Report": {
        "module_level": ["TEST_SUMMARY.md"],
        "per_page": [],
    },
    "Knowledge": {
        "module_level": [],
        "per_page": [],
        # Knowledge 阶段产出沉淀到 governance/artifacts/ 和 known-issues/,
        # 不在模块目录下，由 Knowledge Agent 独立管理
    },
}


@dataclass
class DriftRecord:
    """单条漂移记录。"""
    check_type: str          # "s_check" | "c_check" | "orphan"
    severity: str            # "error" | "warning" | "info"
    phase: str = ""
    description: str = ""
    expected: str = ""
    actual: str = ""
    suggestion: str = ""


class StateAuditor:
    """
    State Auditor Agent — 状态漂移检测。

    用法:
        auditor = StateAuditor()
        report = auditor.audit("equipment")
        if report["overall_status"] != "ok":
            for drift in report["drifts"]:
                print(f"[{drift.severity}] {drift.description}")
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
                from aitest.audit_engine.event_bus import emit
                emit("StateDrift",
                     module=module,
                     run_id="auditor-direct",
                     drift_count=report["drift_count"],
                     error_count=report["error_count"],
                     warning_count=report["warning_count"],
                     overall_status=report["overall_status"])
            except Exception as e:
                from aitest.infra.error_logger import log_error
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
            from aitest.audit_engine.event_bus import emit
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

    def _run_s_check(self):
        """检查 SOP_STATUS 中已完成的 Phase 是否有对应的产物。"""
        sop_status = self._load_sop_status()
        if sop_status is None:
            self.drifts.append(DriftRecord(
                check_type="s_check",
                severity="error",
                description=f"SOP_STATUS_{self.module}.json 不存在或无法解析",
                suggestion="运行一次完整的 SOP 以生成 SOP_STATUS",
            ))
            return

        completed_phases = sop_status.get("completed_phases", [])
        for phase in completed_phases:
            expected = PHASE_EXPECTED_ARTIFACTS.get(phase)
            if expected is None:
                continue

            mod_dir = self._module_dir()

            # 检查模块级产物
            for artifact in expected.get("module_level", []):
                path = mod_dir / artifact
                if not path.exists():
                    self.drifts.append(DriftRecord(
                        check_type="s_check",
                        severity="error",
                        phase=phase,
                        description=f"Phase '{phase}' 已完成，但模块级产物缺失: {artifact}",
                        expected=str(path),
                        actual="文件不存在",
                        suggestion=f"建议重新运行 {phase} 相关 Agent",
                    ))
                elif path.stat().st_size == 0:
                    self.drifts.append(DriftRecord(
                        check_type="s_check",
                        severity="warning",
                        phase=phase,
                        description=f"Phase '{phase}' 的产物为空: {artifact}",
                        expected=str(path),
                        actual="文件为空 (0 bytes)",
                        suggestion="检查 Agent 输出是否被截断",
                    ))

            # 检查页面级产物
            for page in self.pages:
                page_dir = get_page_dir(self.module, page)
                for artifact in expected.get("per_page", []):
                    path = page_dir / artifact
                    if not path.exists():
                        self.drifts.append(DriftRecord(
                            check_type="s_check",
                            severity="warning",
                            phase=phase,
                            description=f"Phase '{phase}' 已完成，但页面 '{page}' 缺失: {artifact}",
                            expected=str(path),
                            actual="文件不存在",
                            suggestion=f"建议对该页面重新运行 {phase} 相关 Agent",
                        ))

    # ── A-Check: Orphan Artifact Detection ────────────────────────────

    def _run_r_check(self):
        """P1-FIX (2026-06-15): Reverse State-to-Artifact 检查。

        检测方向: Artifact → State。
        如果预期产物文件存在，但 SOP_STATUS 中对应 Phase 未标记为完成，
        说明产物可能由外部创建，或状态未同步更新。
        """
        sop_status = self._load_sop_status()
        completed_phases = set(sop_status.get("completed_phases", [])) if sop_status else set()
        mod_dir = self._module_dir()

        for phase, expected in PHASE_EXPECTED_ARTIFACTS.items():
            if phase in completed_phases:
                continue  # Phase 已完成，跳过（正向 S-Check 已覆盖）

            # 检查模块级产物
            for artifact in expected.get("module_level", []):
                path = mod_dir / artifact
                if path.exists() and path.stat().st_size > 0:
                    self.drifts.append(DriftRecord(
                        check_type="r_check",
                        severity="warning",
                        phase=phase,
                        description=f"产物 '{artifact}' 存在但 Phase '{phase}' 未在 completed_phases 中",
                        expected=f"Phase '{phase}' 在 completed_phases 中",
                        actual=f"Phase '{phase}' 不在 completed_phases 中，但 {artifact} 已存在",
                        suggestion=f"更新 SOP_STATUS 将 '{phase}' 加入 completed_phases，或确认产物是否由外部创建",
                    ))

            # 检查页面级产物
            for page in self.pages:
                page_dir = get_page_dir(self.module, page)
                for artifact in expected.get("per_page", []):
                    path = page_dir / artifact
                    if path.exists() and path.stat().st_size > 0:
                        self.drifts.append(DriftRecord(
                            check_type="r_check",
                            severity="warning",
                            phase=phase,
                            description=f"产物 '{artifact}' 在页面 '{page}' 存在但 Phase '{phase}' 未完成",
                            expected=f"Phase '{phase}' 在 completed_phases 中",
                            actual=f"Phase '{phase}' 不在 completed_phases 中",
                            suggestion=f"更新 SOP_STATUS 将 '{phase}' 加入 completed_phases，或确认产物是否由外部创建",
                        ))

    # ── A-Check: Orphan Artifact Detection ────────────────────────────


    # P1-FIX (2026-06-15): O-Check - Agent output consistency

    PLACEHOLDER_PATTERNS = [
        (r"(?i)(?:TODO|TBD|FIXME|HACK)|(?<!\w)(XXX)(?!\w)", "placeholder"),
        (r"(?i)(to be (determined|defined|decided|filled|written))", "TBD"),
        (r"(?i)(待补充|待完善|待填写|暂缺|暂无)", "CN-placeholder"),
    ]
    DUPLICATE_LINE_RATIO_THRESHOLD = 0.4

    def _run_o_check(self):
        """Agent output consistency: detect placeholder/garbage content."""
        import re
        sop_status = self._load_sop_status()
        completed_phases = set(sop_status.get("completed_phases", [])) if sop_status else set()
        mod_dir = self._module_dir()

        for phase in completed_phases:
            expected = PHASE_EXPECTED_ARTIFACTS.get(phase, {})
            if not expected:
                continue
            for artifact in expected.get("module_level", []):
                path = mod_dir / artifact
                if path.exists() and path.stat().st_size > 0:
                    self._check_output_consistency(path, artifact, phase)
            for page in self.pages:
                page_dir = get_page_dir(self.module, page)
                for artifact in expected.get("per_page", []):
                    path = page_dir / artifact
                    if path.exists() and path.stat().st_size > 0:
                        self._check_output_consistency(path, artifact, phase)

    def _check_output_consistency(self, path, artifact_name, phase):
        import re
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return
        if not text.strip():
            return
        lines = [l for l in text.split("\n") if l.strip()]
        if not lines:
            return
        issues = []

        placeholder_lines = 0
        for line in lines:
            for pattern, _ in self.PLACEHOLDER_PATTERNS:
                if re.search(pattern, line):
                    placeholder_lines += 1
                    break
        pr = placeholder_lines / len(lines) if lines else 0
        if pr > 0.3:
            issues.append(f"placeholder ratio {pr:.0%} > 30%")

        if len(lines) >= 5:
            lc = {}
            for l in lines:
                n = l.strip().lower()
                lc[n] = lc.get(n, 0) + 1
            mr = max(lc.values())
            rr = mr / len(lines)
            if rr > self.DUPLICATE_LINE_RATIO_THRESHOLD:
                mc = max(lc, key=lc.get)
                issues.append(f"duplicate line {mr}/{len(lines)}: {mc[:80]}")

        auto_a = {"TECH_ANALYSIS.md", "AUTO_STRATEGY.md", "PAGE_ELEMENT_POSITION.md"}
        td_a = {"TEST_DESIGN.md", "TEST_CASES.md", "RISK_MODEL.md", "PAGE_CONTEXT.md"}
        if artifact_name in auto_a:
            if not any(t in text.lower() for t in ["定位", "xpath", "css", "selector", "等待", "元素", "el-", "组件"]):
                issues.append("automation artifact lacks tech terms")
        if artifact_name in td_a:
            if not any(t in text.lower() for t in ["用例", "测试", "场景", "预期", "步骤", "前置"]):
                issues.append("test-design artifact lacks test terms")

        if issues:
            self.drifts.append(DriftRecord(
                check_type="o_check",
                severity="warning",
                phase=phase,
                description=f"{artifact_name} output suspect: {'; '.join(issues)}",
                expected="valid non-placeholder phase-matching output",
                actual=f"lines={len(lines)}, pl_ratio={pr:.0%}",
                suggestion=f"Re-run {phase} Agent",
            ))


    def _run_orphan_check(self):
        """检测孤儿文件 — 存在但不在任何 Phase 预期列表中的产物。"""
        mod_dir = self._module_dir()
        known_artifacts = set()

        # 收集所有已知产物文件名
        for expected in PHASE_EXPECTED_ARTIFACTS.values():
            for name in expected.get("module_level", []):
                known_artifacts.add(name)
            for name in expected.get("per_page", []):
                known_artifacts.add(name)

        # 扫描模块根目录的非标准文件
        if mod_dir.exists():
            for fpath in mod_dir.iterdir():
                if fpath.is_file() and fpath.suffix in (".md", ".yaml", ".json"):
                    if fpath.name not in known_artifacts and not fpath.name.startswith("MODULE_") and not fpath.name.startswith("PROJECT_"):
                        self.drifts.append(DriftRecord(
                            check_type="orphan",
                            severity="info",
                            description=f"发现非标准产物文件: {fpath.name}",
                            expected="标准产物 (PAGE_CONTEXT, RISK_MODEL, TEST_DESIGN, TEST_CASES, TECH_ANALYSIS, AUTO_STRATEGY)",
                            actual=str(fpath),
                            suggestion="确认文件用途后归档到 governance/artifacts/archive/ 或删除",
                        ))

    # ── C-Check: Cross-Source Consistency ─────────────────────────────

    def _run_c_check(self):
        """检查 checkpoint (SQLite) 与 SOP_STATUS JSON 的一致性。

        P1-FIX (2026-06-15): checkpoint 缺失时输出诊断信息。
        """
        sop_status = self._load_sop_status()

        # 诊断: checkpoint DB 是否存在
        if not CHECKPOINT_DB.exists():
            self.drifts.append(DriftRecord(
                check_type="c_check",
                severity="info",
                description="SQLite checkpoint 数据库不存在 — 无法执行跨源一致性检查",
                expected=f"checkpoint DB at {CHECKPOINT_DB}",
                actual="文件不存在",
                suggestion="运行一次完整的 SOP Graph (非 dry-run) 以生成 checkpoint",
            ))
            return

        checkpoint_phases = self._load_checkpoint_phases()

        # 诊断: checkpoint 表为空 (SOP_STATUS 存在但无 checkpoint 记录)
        if sop_status and not checkpoint_phases:
            self.drifts.append(DriftRecord(
                check_type="c_check",
                severity="warning",
                description="SOP_STATUS JSON 存在但 SQLite checkpoint 无数据 — 可能是 dry-run 或 checkpoint 写入失败",
                expected="checkpoint 中包含 completed_phases",
                actual="checkpoint 为空",
                suggestion="运行一次完整的 SOP Graph (确保 checkpointer 正确编译) 以生成 checkpoint",
            ))
            return

        if sop_status and checkpoint_phases:
            json_phases = set(sop_status.get("completed_phases", []))
            cp_phases = set(checkpoint_phases)

            only_in_json = json_phases - cp_phases
            only_in_cp = cp_phases - json_phases

            if only_in_json:
                self.drifts.append(DriftRecord(
                    check_type="c_check",
                    severity="warning",
                    description=f"SOP_STATUS JSON 中有但 checkpoint 中无: {only_in_json}",
                    expected="JSON 和 checkpoint 一致",
                    actual=f"JSON: {sorted(json_phases)}, SQLite: {sorted(cp_phases)}",
                    suggestion="以 SQLite checkpoint 为准，重新导出 SOP_STATUS JSON",
                ))

            if only_in_cp:
                self.drifts.append(DriftRecord(
                    check_type="c_check",
                    severity="error",
                    description=f"Checkpoint 中有但 SOP_STATUS JSON 中无: {only_in_cp}",
                    expected="JSON 和 checkpoint 一致",
                    actual=f"JSON: {sorted(json_phases)}, SQLite: {sorted(cp_phases)}",
                    suggestion="从 SQLite checkpoint 恢复并重新生成 SOP_STATUS JSON。JSON 快照可能未正常写入。",
                ))

    # ── P1-1: Q-Check 内容质量标记 ───────────────────────────────────
    QUALITY_MARKERS = {
        "PAGE_CONTEXT.md": {
            "min_lines": 20,
            "markers": ["元素", "定位", "交互", "页面"],
            "marker_min_match": 2,
        },
        "RISK_MODEL.md": {
            "min_lines": 15,
            "markers": ["风险", "等级", "缓解", "概率"],
            "marker_min_match": 2,
        },
        "BUSINESS_SCENARIOS.md": {
            "min_lines": 20,
            "markers": ["业务目标", "角色", "流程", "业务规则", "数据流", "置信度"],
            "marker_min_match": 3,
        },
        "TEST_DESIGN.md": {
            "min_lines": 15,
            "markers": ["用例", "场景", "覆盖", "策略"],
            "marker_min_match": 2,
        },
        "TEST_CASES.md": {
            "min_lines": 15,
            "markers": ["用例", "预期", "步骤", "前置"],
            "marker_min_match": 2,
        },
        "TECH_ANALYSIS.md": {
            "min_lines": 10,
            "markers": ["定位器", "优先级", "等待", "元素"],
            "marker_min_match": 2,
        },
        "AUTO_STRATEGY.md": {
            "min_lines": 10,
            "markers": ["覆盖", "自动化", "策略", "优先级"],
            "marker_min_match": 2,
        },
        "PAGE_ELEMENT_POSITION.md": {
            "min_lines": 10,
            "markers": ["定位器", "元素", "xpath", "css"],
            "marker_min_match": 2,
        },
        "PAGE_INTERFACE.yaml": {
            "min_lines": 5,
            "markers": [],  # YAML 结构由 schema 保证，不检查关键词
            "marker_min_match": 0,
        },
        "BUG_ANALYSIS.md": {
            "min_lines": 10,
            "markers": ["根因", "修复", "bug", "错误"],
            "marker_min_match": 2,
        },
        "DATA_QUALITY.md": {
            "min_lines": 10,
            "markers": ["数据", "清洗", "脱敏", "质量"],
            "marker_min_match": 2,
        },
        "TEST_SUMMARY.md": {
            "min_lines": 15,
            "markers": ["测试", "覆盖", "通过", "失败"],
            "marker_min_match": 2,
        },
        "PROJECT_CONTEXT.md": {
            "min_lines": 10,
            "markers": ["项目", "模块", "技术栈", "环境"],
            "marker_min_match": 2,
        },
        "MODULE_CONTEXT.md": {
            "min_lines": 10,
            "markers": ["模块", "页面", "路由", "功能"],
            "marker_min_match": 2,
        },
    }

    # ── 数据加载 ──────────────────────────────────────────────────────

    def _load_sop_status(self) -> dict | None:
        """加载 SOP_STATUS JSON。"""
        path = SOP_STATUS_DIR / f"SOP_STATUS_{self.module}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    def _load_checkpoint_phases(self) -> list[str]:
        """从 SQLite checkpoint 加载该模块最近一次运行的 completed_phases。

        P0-FIX (2026-06-15): LangGraph SqliteSaver 使用 msgpack 序列化，
        此前用 json.loads() 解析始终失败，导致 C-Check 永远返回空。
        """
        if not CHECKPOINT_DB.exists():
            return []

        try:
            import sqlite3
            import msgpack
            conn = sqlite3.connect(str(CHECKPOINT_DB))
            cursor = conn.cursor()
            # 查找最新的 checkpoint（按 checkpoint_id 降序）
            # P0-FIX: 按模块匹配 checkpoint (thread_id = sop-{module}-{ts})
            thread_prefix = f"sop-{self.module}-"
            cursor.execute(
                "SELECT thread_id, checkpoint FROM checkpoints "
                "WHERE thread_id LIKE ? "
                "ORDER BY checkpoint_id DESC LIMIT 10",
                (f"{thread_prefix}%",)
            )
            rows = cursor.fetchall()
            # 如果没找到模块特定的，回退到全局最新
            if not rows:
                cursor.execute(
                    "SELECT thread_id, checkpoint FROM checkpoints "
                    "ORDER BY checkpoint_id DESC LIMIT 10"
                )
                rows = cursor.fetchall()
            conn.close()

            for (tid, blob) in rows:
                try:
                    data = msgpack.unpackb(blob, raw=False)
                    channels = data.get("channel_values", data)
                    phases = channels.get("completed_phases", [])
                    if phases:
                        return list(phases)
                except (ValueError, TypeError, KeyError):
                    continue
        except Exception:
            pass

        return []

    # ── P1-1: Q-Check ────────────────────────────────────────────────

    def _run_q_check(self):
        """P1-1: 产物质量门禁检查 — 文件内容是否满足最低质量标准。"""
        sop_status = self._load_sop_status()
        completed_phases = sop_status.get("completed_phases", []) if sop_status else []
        mod_dir = self._module_dir()

        # 检查模块级产物质量 (覆盖所有有 module_level 产物的 Phase)
        phases_with_module_artifacts = [
            "Project Init", "Requirement", "Data Sanitization", "Report"
        ]
        for phase in phases_with_module_artifacts:
            if phase not in completed_phases:
                continue
            expected = PHASE_EXPECTED_ARTIFACTS.get(phase, {})
            for artifact in expected.get("module_level", []):
                path = mod_dir / artifact
                if path.exists():
                    self._check_file_quality(path, artifact)

        # 检查页面级产物质量 (覆盖所有有 per_page 产物的 Phase)
        test_phases = ["Test Design", "Automation", "Bug Analysis"]
        for phase in test_phases:
            if phase not in completed_phases:
                continue
            expected = PHASE_EXPECTED_ARTIFACTS.get(phase, {})
            for page in self.pages:
                page_dir = get_page_dir(self.module, page)
                for artifact in expected.get("per_page", []):
                    path = page_dir / artifact
                    if path.exists():
                        self._check_file_quality(path, artifact)

    def _check_file_quality(self, path: Path, artifact_name: str):
        """检查单个产物的内容质量。"""
        qm = self.QUALITY_MARKERS.get(artifact_name)
        if qm is None:
            return

        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            return

        lines = text.count("\n") + 1
        issues = []

        if lines < qm["min_lines"]:
            issues.append(f"行数 {lines} < 最低要求 {qm['min_lines']}")

        matched = sum(1 for m in qm["markers"] if m.lower() in text.lower())
        if matched < qm["marker_min_match"]:
            issues.append(
                f"关键标记匹配 {matched}/{len(qm['markers'])} < 最低 {qm['marker_min_match']} "
                f"(缺失: {[m for m in qm['markers'] if m.lower() not in text.lower()]})"
            )

        if issues:
            self.drifts.append(DriftRecord(
                check_type="q_check",
                severity="warning",
                description=f"{artifact_name} 内容质量不足: {'; '.join(issues)}",
                expected=f"行数≥{qm['min_lines']}, 标记匹配≥{qm['marker_min_match']}/{qm['markers']}",
                actual=f"行数={lines}, 标记匹配={matched}/{len(qm['markers'])}",
                suggestion=f"建议重新运行相关 Agent 生成 {artifact_name}",
            ))

    # ── P1-1: T-Check ────────────────────────────────────────────────

    def _run_t_check(self):
        """P1-1: Phase 时间线合理性检查。"""
        sop_status = self._load_sop_status()
        if sop_status is None:
            return

        # 检查 updated_at 时间戳
        updated_at = sop_status.get("updated_at", "")
        if updated_at:
            try:
                ts = datetime.fromisoformat(updated_at)
                now = datetime.now()
                if ts > now:
                    self.drifts.append(DriftRecord(
                        check_type="t_check",
                        severity="warning",
                        description=f"SOP_STATUS 更新时间在未来: {updated_at}",
                        expected=f"≤ {now.isoformat()}",
                        actual=updated_at,
                        suggestion="检查系统时钟或 SOP_STATUS 写入逻辑",
                    ))
            except (ValueError, TypeError):
                self.drifts.append(DriftRecord(
                    check_type="t_check",
                    severity="info",
                    description=f"SOP_STATUS updated_at 无法解析: {updated_at}",
                    suggestion="检查 ISO 8601 格式",
                ))

        # 检查 agent_summary 中各 Agent 的执行时间
        agent_summary = sop_status.get("agent_summary", {})
        if agent_summary:
            # 如果多个 Agent 有 completed_skills=0 状态，检查对应 Phase 是否应该有产物
            stuck_agents = [
                name for name, a in agent_summary.items()
                if a.get("skills_completed", 0) == 0 and a.get("success") is False
            ]
            if stuck_agents:
                self.drifts.append(DriftRecord(
                    check_type="t_check",
                    severity="info",
                    description=f"以下 Agent 未能完成任何 Skill: {stuck_agents}",
                    suggestion="检查是否在早期 Phase 遇到阻塞，建议 resume 或重跑",
                ))

        # 检查 Phase 间隔 (如果 completed_phases 按顺序有对应的时间戳)
        per_page_results = sop_status.get("per_page_results", [])
        if per_page_results:
            for pr in per_page_results:
                if pr.get("status") == "failed":
                    self.drifts.append(DriftRecord(
                        check_type="t_check",
                        severity="info",
                        description=f"页面 '{pr.get('page_slug', '?')}' 处理失败",
                        suggestion="检查该页面的 Agent 执行日志，考虑重跑该页面",
                    ))

    # ── P2-5: BSC-Check — 业务场景覆盖质量门禁 ───────────────────────

    # 业务覆盖评分维度及权重
    BSC_DIMENSIONS = {
        "business_goal_coverage": {"weight": 0.25, "label": "业务目标覆盖"},
        "role_coverage":          {"weight": 0.15, "label": "角色覆盖"},
        "workflow_coverage":      {"weight": 0.20, "label": "工作流覆盖"},
        "rule_coverage":          {"weight": 0.15, "label": "业务规则覆盖"},
        "data_flow_coverage":     {"weight": 0.10, "label": "数据流覆盖"},
        "automation_readiness":   {"weight": 0.10, "label": "自动化就绪度"},
        "maintainability":        {"weight": 0.05, "label": "可维护性"},
    }

    BSC_PASS_THRESHOLD = 60       # 最低通过分
    BSC_WARN_THRESHOLD = 70       # P0 模块警告阈值

    def _run_bsc_check(self):
        """P2-5: 业务场景覆盖质量门禁 — 结构性检查 + 业务覆盖度评分。

        对 Test Design phase 完成的每个页面，检查:
        1. BUSINESS_SCENARIOS.md 是否存在且内容有效
        2. TEST_DESIGN.md 是否包含业务场景维度（第 9 维）
        3. TEST_CASES.md 是否包含 BS-XXX-NNN 场景 ID 映射
        4. 基于确定性规则计算 Business Coverage Score (0-100)

        评分 < BSC_PASS_THRESHOLD → 发射 BusinessCoverageInsufficient 事件
        跨页面流程覆盖=0 且模块≥2页 → 发射 WorkflowCoverageInsufficient 事件
        """
        mod_dir = self._module_dir()
        sop_status = self._load_sop_status()
        completed_phases = sop_status.get("completed_phases", []) if sop_status else []

        if "Test Design" not in completed_phases:
            return

        for page in self.pages:
            page_dir = get_page_dir(self.module, page)
            score = self._compute_bsc_score(page_dir, page)
            cross_page_ok = self._check_cross_page_coverage(page_dir, page)

            if score < self.BSC_PASS_THRESHOLD:
                self.drifts.append(DriftRecord(
                    check_type="bsc_check",
                    severity="error",
                    phase="Test Design",
                    description=(
                        f"页面 '{page}' 业务场景覆盖评分 {score} < {self.BSC_PASS_THRESHOLD}。"
                        f"测试用例可能仅覆盖 UI 操作，缺失业务场景验证。"
                    ),
                    expected=f"Business Coverage Score ≥ {self.BSC_PASS_THRESHOLD}",
                    actual=f"score={score}",
                    suggestion=(
                        "建议: (1) 确保 risk-modeling 产出了 BUSINESS_SCENARIOS.md; "
                        "(2) 重新运行 testcase-design 确保维度 9 (业务场景验证) 已覆盖; "
                        "(3) 检查 TEST_CASES.md 中是否有 BS-XXX-NNN 场景 ID 映射"
                    ),
                ))
                # 发射 BusinessCoverageInsufficient 事件
                try:
                    from aitest.audit_engine.event_bus import emit
                    emit("BusinessCoverageInsufficient",
                         module=self.module,
                         page=page,
                         score=score,
                         threshold=self.BSC_PASS_THRESHOLD,
                         dimensions_detail=f"各维度得分见 audit report")
                except Exception:
                    pass

            if not cross_page_ok and len(self.pages) >= 2:
                self.drifts.append(DriftRecord(
                    check_type="bsc_check",
                    severity="warning",
                    phase="Test Design",
                    description=(
                        f"模块 '{self.module}' 有 {len(self.pages)} 个页面，"
                        f"但页面 '{page}' 的 BUSINESS_SCENARIOS.md 中未检测到跨页面流程覆盖"
                    ),
                    expected="≥1 条跨页面业务流程场景",
                    actual="cross_page_scenarios=0",
                    suggestion="检查 BUSINESS_SCENARIOS.md 的 '3. 业务流程' 是否覆盖了跨页面场景",
                ))
                try:
                    from aitest.audit_engine.event_bus import emit
                    emit("WorkflowCoverageInsufficient",
                         module=self.module,
                         page_count=len(self.pages),
                         cross_page_scenarios=0)
                except Exception:
                    pass

    def _compute_bsc_score(self, page_dir: Path, page_slug: str) -> int:
        """计算单个页面的 Business Coverage Score (0-100)。

        基于确定性规则（零 LLM token 消耗）:
        - 产物存在性 (30%)
        - 业务维度覆盖 (50%)
        - 用例质量标记 (20%)
        """
        score = 0
        max_score = 100

        # ── 第 1 层: 产物存在性 (30 分) ──
        bs_path = page_dir / "BUSINESS_SCENARIOS.md"
        td_path = page_dir / "TEST_DESIGN.md"
        tc_path = page_dir / "TEST_CASES.md"

        if bs_path.exists():
            score += 10
            try:
                bs_content = bs_path.read_text(encoding="utf-8")
            except OSError as e:
                logger.warning("_compute_bsc_score: cannot read %s: %s", bs_path, e)
                bs_content = ""
        else:
            bs_content = ""
            score -= 5  # 缺失 BUSINESS_SCENARIOS 罚分

        if td_path.exists():
            score += 10
            try:
                td_content = td_path.read_text(encoding="utf-8")
            except OSError:
                td_content = ""
        else:
            td_content = ""
            score -= 5

        if tc_path.exists():
            score += 10
            try:
                tc_content = tc_path.read_text(encoding="utf-8")
            except OSError:
                tc_content = ""
        else:
            tc_content = ""
            score -= 5

        # ── 第 2 层: 业务维度覆盖 (50 分) ──
        # 检查 BUSINESS_SCENARIOS.md 中的 6 个业务维度
        bs_dimensions = {
            "业务目标": ["业务目标", "Business Goal", "核心业务目标"],
            "角色": ["角色", "Role", "角色与旅程"],
            "流程": ["流程", "Workflow", "业务流程", "Happy Path", "Alternative Path"],
            "业务规则": ["业务规则", "Business Rule", "状态流转", "触发规则", "计算规则"],
            "数据流": ["数据流", "Data Flow", "数据来源", "数据消费"],
            "风险映射": ["风险", "场景映射", "Risk-to-Scenario", "关联风险"],
        }

        for dim_name, keywords in bs_dimensions.items():
            if any(kw.lower() in bs_content.lower() for kw in keywords):
                score += 8  # ~50/6 ≈ 8.3
            else:
                # 检查 TEST_DESIGN 中是否有该维度的覆盖
                if any(kw.lower() in td_content.lower() for kw in keywords):
                    score += 4  # 部分覆盖

        # 检查 TEST_DESIGN 是否包含第 9 维 (业务场景验证)
        business_scenario_markers = [
            "业务场景验证", "业务场景", "端到端业务流程", "角色协作",
            "BS-", "跨页面", "数据流完整性", "状态机验证",
        ]
        bs_dim9_hits = sum(1 for m in business_scenario_markers if m.lower() in td_content.lower())
        if bs_dim9_hits >= 3:
            score += 8
        elif bs_dim9_hits >= 1:
            score += 4

        # ── 第 3 层: 用例质量标记 (20 分) ──
        # BS-XXX-NNN 场景 ID 映射
        if tc_content:
            import re
            bs_id_count = len(re.findall(r'BS-\w+-\d{3}', tc_content))
            if bs_id_count >= 5:
                score += 10
            elif bs_id_count >= 1:
                score += 5

            # P0 业务场景覆盖
            if "P0" in tc_content or "阻塞" in tc_content:
                score += 5

            # 具体测试数据（非占位符）
            placeholder_patterns = ["输入XXX", "输入用户名", "输入密码", "输入数据", "输入值"]
            if not any(p in tc_content for p in placeholder_patterns):
                score += 5

        return max(0, min(100, score))

    def _check_cross_page_coverage(self, page_dir: Path, page_slug: str) -> bool:
        """检查 BUSINESS_SCENARIOS.md 是否包含跨页面流程覆盖。"""
        bs_path = page_dir / "BUSINESS_SCENARIOS.md"
        if not bs_path.exists():
            return False
        try:
            content = bs_path.read_text(encoding="utf-8")
        except OSError:
            return False

        cross_page_markers = [
            "跨页面", "cross-page", "跨模块", "cross-module",
            "page-a", "page-b", "→", "流转到", "进入.*页面",
        ]
        import re
        return any(re.search(m, content, re.IGNORECASE) for m in cross_page_markers)

    # ── 辅助 ──────────────────────────────────────────────────────────

    def _summarize_check(self, check_type: str) -> dict:
        """汇总某类检查的结果。"""
        related = [d for d in self.drifts if d.check_type == check_type]
        errors = [d for d in related if d.severity == "error"]
        warnings = [d for d in related if d.severity == "warning"]
        return {
            "total": len(related),
            "errors": len(errors),
            "warnings": len(warnings),
            "ok": len(related) == 0,
        }

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
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    # 人类可读输出
    print(f"\n{'='*60}")
    print(f"  State Audit: {module}")
    print(f"  Time: {report['audit_time']}")
    print(f"  Status: {report['overall_status'].upper()}")
    print(f"{'='*60}\n")

    if not report["drifts"]:
        print("  ✅ 无状态漂移检测到\n")
        return report

    for d in report["drifts"]:
        icon = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}.get(d["severity"], "•")
        print(f"  {icon} [{d['severity'].upper()}] [{d.get('check_type', '')}] {d['description']}")
        if d.get("phase"):
            print(f"     Phase: {d['phase']}")
        if d.get("suggestion"):
            print(f"     → {d['suggestion']}")
        print()

    print(f"  Drifts: {report['drift_count']} (errors: {report['error_count']}, warnings: {report['warning_count']})")

    if report.get("repairs_attempted"):
        print(f"\n  🔧 Repairs: {len(report['repairs_attempted'])}")
        for r in report["repairs_attempted"]:
            print(f"     {r.get('action', r)}")

    audit_report_path = AUDIT_DIR / f"state-audit-{module}-*.json"
    print(f"\n  Report saved to: {AUDIT_DIR}")
    print()

    return report


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python state_auditor.py <module> [--repair] [--json]")
        print("Modules: equipment, system, personnel, warehouse, tank, sales, lab, production, dcs, workflow")
        sys.exit(0)

    module_name = sys.argv[1]
    opts = set(sys.argv[2:])
    run_state_audit(
        module_name,
        auto_repair="--repair" in opts,
        json_output="--json" in opts,
    )
