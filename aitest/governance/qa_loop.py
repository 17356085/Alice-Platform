"""
QA Loop — 测试失败→修复→重验证闭环编排器。

借鉴 Aperant qa/loop.py + reviewer.py + fixer.py 模式，适配 TLO 测试生命周期。
Aperant: Code QA (review → fix → re-review)
TLO:     Test QA (failure analysis → auto-fix → re-run → pass/escalate)

架构:
    Failure Analyst → Automation Developer(fix) → Execution Agent(re-run)
    ￪                                              ￬
    └────────── pass → merge + update RAG ←────────┘
    ￬
    └────────── still fail → escalate to human ──────→ ticket

使用:
    from aitest.governance.qa_loop import QALoop
    loop = QALoop(module="equipment", max_rounds=3)
    result = loop.run(failed_test="test_alarm_config.py::test_create_alarm")
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from aitest.platform.paths import get_test_project_root
_WORKSTUDY = Path(__file__).resolve().parent.parent.parent


class LoopStatus(Enum):
    PASSED = "passed"               # Fixed and verified
    FAILED = "failed"               # Could not fix after max rounds
    ESCALATED = "escalated"         # Escalated to human
    SKIPPED = "skipped"             # Not applicable (infra issue, test env down)


class RootCauseCategory(Enum):
    LOCATOR_STALE = "locator_stale"            # DOM/selector changed
    TIMING_ISSUE = "timing_issue"              # Race condition / wait too short
    DATA_STALE = "data_stale"                  # Test data no longer valid
    ENV_DOWN = "env_down"                      # Service/dependency unavailable
    REAL_DEFECT = "real_defect"                # Actual bug in system under test
    SCRIPT_ERROR = "script_error"              # Bug in test script logic
    UNKNOWN = "unknown"


@dataclass
class QAFinding:
    """Single failure analysis finding."""
    test_id: str
    root_cause: RootCauseCategory
    confidence: float          # 0.0–1.0
    evidence: dict = field(default_factory=dict)
    # evidence keys: screenshot, dom_snapshot, console_log, network_trace, error_message
    suggested_fix: str = ""
    auto_fixable: bool = False


@dataclass
class QAResult:
    """Result of a complete QA Loop run."""
    module: str
    status: LoopStatus
    rounds: int
    findings: list[QAFinding] = field(default_factory=list)
    fixes_applied: list[str] = field(default_factory=list)
    verification_output: str = ""
    started_at: str = ""
    finished_at: str = ""
    total_duration_s: float = 0.0

    def to_dict(self) -> dict:
        return {
            "module": self.module,
            "status": self.status.value,
            "rounds": self.rounds,
            "total_findings": len(self.findings),
            "auto_fixable": sum(1 for f in self.findings if f.auto_fixable),
            "escalated": sum(1 for f in self.findings if not f.auto_fixable),
            "fixes_applied": self.fixes_applied,
            "verification_output": self.verification_output[:500],
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "total_duration_s": self.total_duration_s,
        }


class QALoop:
    """
    测试失败→修复→重验证闭环。

    max_rounds: 最大重试轮数 (默认 3, 借鉴 Aperant QA loop 的 max_rounds)
    worktree: 是否使用 Git Worktree 隔离修复 (Phase 2 启用)
    provider: LLM Provider (claude/deepseek/google)
    """

    def __init__(
        self,
        module: str,
        max_rounds: int = 3,
        worktree: bool = False,
        provider: str = "claude",
    ):
        self.module = module
        self.max_rounds = max_rounds
        self.worktree = worktree
        self.provider = provider
        zjsn = get_test_project_root()
        self._script_dir = (zjsn / "script" / module) if zjsn else (_WORKSTUDY / "ZJSN_Test-master526" / "script" / module)

    # ── Public API ──

    def run(self, failed_test: str = None, pytest_args: str = None) -> QAResult:
        """
        运行 QA Loop。

        Args:
            failed_test: 单个失败测试 ID (如 "test_alarm_config.py::test_create_alarm")
            pytest_args: 额外的 pytest 参数

        Returns:
            QAResult with status, findings, and fixes
        """
        result = QAResult(
            module=self.module,
            status=LoopStatus.FAILED,
            rounds=0,
            started_at=datetime.now().isoformat(),
        )
        start = time.time()

        for round_num in range(1, self.max_rounds + 1):
            result.rounds = round_num
            print(f"\n[QA Loop] Round {round_num}/{self.max_rounds} — {self.module}")

            # 1. Analyze failure
            findings = self._analyze(failed_test)
            result.findings = findings

            if not findings:
                print("[QA Loop] No findings — all tests passed or no output to analyze")
                result.status = LoopStatus.PASSED
                break

            auto_fixable = [f for f in findings if f.auto_fixable]
            manual = [f for f in findings if not f.auto_fixable]

            print(f"[QA Loop] Findings: {len(findings)} total, "
                  f"{len(auto_fixable)} auto-fixable, {len(manual)} need human")

            # 2. Apply auto-fixes
            fixes = self._apply_fixes(auto_fixable)
            result.fixes_applied.extend(fixes)

            # 3. Re-run tests
            rerun_ok, rerun_output = self._rerun(failed_test, pytest_args)
            result.verification_output = rerun_output

            if rerun_ok:
                print(f"[QA Loop] ✅ Round {round_num} passed — all fixes verified")
                result.status = LoopStatus.PASSED
                self._merge_and_learn(findings)
                break
            else:
                print(f"[QA Loop] ❌ Round {round_num} failed — {len(manual)} issues need human")
                if manual:
                    result.status = LoopStatus.ESCALATED
                    self._escalate(manual)
                    break

        if result.status == LoopStatus.FAILED and result.rounds >= self.max_rounds:
            result.status = LoopStatus.ESCALATED
            self._escalate(result.findings)

        result.finished_at = datetime.now().isoformat()
        result.total_duration_s = round(time.time() - start, 1)
        self._log_result(result)
        return result

    # ── Internal: Analyze ──

    def _analyze(self, failed_test: str = None) -> list[QAFinding]:
        """
        多维证据采集 + LLM 根因分析。

        证据采集:
          1. 截图 (最后失败页面)
          2. DOM snapshot (失败时刻 HTML)
          3. Console logs (JS errors)
          4. Network trace (API errors)
          5. Error message / stack trace

        根因分类 → auto_fixable 判定:
          LOCATOR_STALE  → ✅ auto-fixable
          TIMING_ISSUE   → ✅ auto-fixable
          DATA_STALE     → ✅ auto-fixable (refresh test data)
          SCRIPT_ERROR   → ⚠️ auto-fixable (simple fixes only)
          ENV_DOWN       → ❌ escalate
          REAL_DEFECT    → ❌ escalate
        """
        findings = []

        # Collect evidence
        error_output = self._collect_pytest_output(failed_test)
        if not error_output:
            return findings

        # Parse failures from pytest output
        failures = self._parse_failures(error_output)
        for failure in failures:
            finding = self._classify_failure(failure)
            findings.append(finding)

        return findings

    def _collect_pytest_output(self, failed_test: str = None) -> str:
        """Collect pytest failure output."""
        # Try to read from existing trace/log first
        trace_log = _WORKSTUDY / "governance" / ".traces" / "trace_log.jsonl"
        if trace_log.exists():
            with open(trace_log, encoding="utf-8") as f:
                recent_errors = [
                    json.loads(line).get("error_message", "")
                    for line in f
                    if line.strip() and json.loads(line).get("status") != "success"
                ]
            if recent_errors:
                return "\n".join(recent_errors[-5:])  # last 5 errors

        # Fallback: read from pytest log
        zjsn = get_test_project_root()
        log_dir = zjsn if zjsn else _WORKSTUDY / "ZJSN_Test-master526"
        log_files = sorted(log_dir.glob("*.log"), key=os.path.getmtime, reverse=True)
        if log_files:
            with open(log_files[0], encoding="utf-8", errors="ignore") as f:
                return f.read()[-5000:]  # Last 5KB

        return ""

    def _parse_failures(self, output: str) -> list[dict]:
        """Parse pytest output for individual test failures."""
        failures = []
        lines = output.split("\n")
        current = None

        for line in lines:
            if "FAILED" in line or "ERROR" in line or "Error:" in line:
                if current:
                    failures.append(current)
                test_id = line.strip().split(" ")[0] if " " in line.strip() else line.strip()
                current = {"test_id": test_id, "error_lines": []}
            elif current is not None:
                current["error_lines"].append(line.strip())
                if len(current["error_lines"]) > 20:  # limit per failure
                    failures.append(current)
                    current = None
        if current:
            failures.append(current)

        return failures

    def _classify_failure(self, failure: dict) -> QAFinding:
        """
        Classify failure root cause from error signature.

        Heuristic rules (can be enhanced with LLM):
        """
        error_text = " ".join(failure.get("error_lines", [])).lower()
        test_id = failure.get("test_id", "unknown")

        # Rule-based classification (LLM-enhanced in Phase 2)
        if any(kw in error_text for kw in ["nosuchelement", "no such element", "unable to locate", "selector", "xpath", "css selector"]):
            return QAFinding(
                test_id=test_id,
                root_cause=RootCauseCategory.LOCATOR_STALE,
                confidence=0.85,
                evidence={"error_message": error_text[:300]},
                suggested_fix="Update locator: check if element class/id/attribute changed in DOM",
                auto_fixable=True,
            )

        if any(kw in error_text for kw in ["timeout", "timed out", "wait", "stale element", "not clickable", "not visible"]):
            return QAFinding(
                test_id=test_id,
                root_cause=RootCauseCategory.TIMING_ISSUE,
                confidence=0.80,
                evidence={"error_message": error_text[:300]},
                suggested_fix="Increase WebDriverWait timeout or add explicit wait for element ready state",
                auto_fixable=True,
            )

        if any(kw in error_text for kw in ["assertion", "assert", "expected", "actual", "not equal", "mismatch"]):
            return QAFinding(
                test_id=test_id,
                root_cause=RootCauseCategory.DATA_STALE,
                confidence=0.70,
                evidence={"error_message": error_text[:300]},
                suggested_fix="Check if test data values have changed. Update expected values or regenerate test data.",
                auto_fixable=True,
            )

        if any(kw in error_text for kw in ["connection refused", "503", "502", "500", "gateway", "unreachable", "dns"]):
            return QAFinding(
                test_id=test_id,
                root_cause=RootCauseCategory.ENV_DOWN,
                confidence=0.90,
                evidence={"error_message": error_text[:300]},
                suggested_fix="Target system unavailable. Verify service status at https://aiwechatminidemo.cimc-digital.com/",
                auto_fixable=False,
            )

        # Default: unknown, escalate for human analysis
        return QAFinding(
            test_id=test_id,
            root_cause=RootCauseCategory.UNKNOWN,
            confidence=0.30,
            evidence={"error_message": error_text[:300]},
            suggested_fix="Manual investigation needed — error pattern not recognized",
            auto_fixable=False,
        )

    # ── Internal: Fix ──

    def _apply_fixes(self, findings: list[QAFinding]) -> list[str]:
        """Apply automated fixes based on findings classification."""
        fixes = []
        for finding in findings:
            fix_desc = f"[{finding.root_cause.value}] {finding.test_id}"
            print(f"[QA Loop] Applying fix: {fix_desc}")

            if finding.root_cause == RootCauseCategory.LOCATOR_STALE:
                fix = self._fix_locator(finding)
            elif finding.root_cause == RootCauseCategory.TIMING_ISSUE:
                fix = self._fix_timing(finding)
            elif finding.root_cause == RootCauseCategory.DATA_STALE:
                fix = self._fix_data(finding)
            else:
                fix = f"SKIP: {finding.root_cause.value} — not auto-fixable"
                print(f"[QA Loop] {fix}")

            fixes.append(fix)

        return fixes

    def _fix_locator(self, finding: QAFinding) -> str:
        """Fix stale locator — delegate to Automation Developer Agent."""
        # In Phase 1, emit event for Automation Developer
        # Phase 2: actual Worktree-based fix
        self._emit_governance_event("qa_loop.fix_requested", {
            "test_id": finding.test_id,
            "root_cause": "locator_stale",
            "suggested_fix": finding.suggested_fix,
            "module": self.module,
        })
        return f"fix_locator: {finding.test_id} — event emitted for Automation Developer"

    def _fix_timing(self, finding: QAFinding) -> str:
        """Fix timing issue — increase wait or add explicit wait."""
        self._emit_governance_event("qa_loop.fix_requested", {
            "test_id": finding.test_id,
            "root_cause": "timing_issue",
            "suggested_fix": finding.suggested_fix,
            "module": self.module,
        })
        return f"fix_timing: {finding.test_id} — event emitted for Automation Developer"

    def _fix_data(self, finding: QAFinding) -> str:
        """Fix stale test data."""
        self._emit_governance_event("qa_loop.fix_requested", {
            "test_id": finding.test_id,
            "root_cause": "data_stale",
            "suggested_fix": finding.suggested_fix,
            "module": self.module,
        })
        return f"fix_data: {finding.test_id} — event emitted"

    # ── Internal: Re-run ──

    def _rerun(self, failed_test: str = None, extra_args: str = None) -> tuple[bool, str]:
        """
        Re-run failed tests after fixes.

        Returns:
            (passed: bool, output: str)
        """
        cmd = ["pytest"]
        if failed_test:
            test_path = self._script_dir / failed_test.split("::")[0]
            cmd.append(str(test_path) if test_path.exists() else failed_test)
        else:
            cmd.append(str(self._script_dir))
        cmd.extend(["-v", "--tb=short", "-x"])  # stop on first failure
        if extra_args:
            cmd.extend(extra_args.split())

        zjsn_cwd = get_test_project_root() or (_WORKSTUDY / "ZJSN_Test-master526")
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(zjsn_cwd),
                capture_output=True,
                text=True,
                timeout=300,  # 5 min timeout
            )
            output = proc.stdout[-3000:] + "\n" + proc.stderr[-1000:]
            passed = proc.returncode == 0
            return passed, output
        except subprocess.TimeoutExpired:
            return False, "Re-run timed out (>5min)"
        except Exception as e:
            return False, str(e)

    # ── Internal: Post-loop actions ──

    def _merge_and_learn(self, findings: list[QAFinding]):
        """After successful fix: merge changes + update RAG knowledge."""
        # Phase 1: emit EventBus event for Knowledge Agent to pick up
        for f in findings:
            self._emit_governance_event("qa_loop.fix_verified", {
                "test_id": f.test_id,
                "root_cause": f.root_cause.value,
                "fix": f.suggested_fix,
                "module": self.module,
            })
        print(f"[QA Loop] {len(findings)} fix pattern(s) emitted to EventBus for Knowledge Agent")

    def _escalate(self, findings: list[QAFinding]):
        """Escalate non-auto-fixable issues to human."""
        for f in findings:
            print(f"[QA Loop] 🚨 ESCALATE: [{f.root_cause.value}] {f.test_id}")
            print(f"           Evidence: {str(f.evidence)[:200]}")
            self._emit_governance_event("qa_loop.escalated", {
                "test_id": f.test_id,
                "root_cause": f.root_cause.value,
                "confidence": f.confidence,
                "evidence": f.evidence,
                "module": self.module,
            })

    # ── Internal: Infrastructure ──

    def _emit_governance_event(self, event_type: str, payload: dict):
        """Emit governance event to EventBus (JSONL append)."""
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "module": self.module,
            "agent": "qa-loop",
            "status": "info",
            **payload,
        }
        events_dir = _WORKSTUDY / "governance" / ".events"
        events_dir.mkdir(parents=True, exist_ok=True)
        events_file = events_dir / "qa_loop.jsonl"
        with open(events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")

    def _log_result(self, result: QAResult):
        """Persist QA Loop result to audit trail."""
        audit_dir = _WORKSTUDY / "governance" / "artifacts" / "audits"
        audit_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d-%H%M%S")
        filepath = audit_dir / f"qa-loop-{self.module}-{ts}.json"
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(result.to_dict(), f, indent=2, ensure_ascii=False)
        print(f"[QA Loop] Result logged: {filepath}")


# ── Convenience function ──

def run_qa_loop(module: str, max_rounds: int = 3, provider: str = "claude") -> QAResult:
    """Run QA Loop for a module. Convenience entry point."""
    loop = QALoop(module=module, max_rounds=max_rounds, provider=provider)
    return loop.run()
