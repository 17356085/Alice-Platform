"""Tests for audit_engine/sop_optimizer.py — SOPOptimizer, OptimizationSuggestion.

Tests: 规则检查逻辑、建议生成、报告格式化。
Mock OnlineMonitor.analyze() 避免文件系统依赖。
"""
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from aitest.audit_engine.sop_optimizer import (
    SOPOptimizer,
    OptimizationSuggestion,
    OPTIONAL_NODES,
    CORE_NODES,
    analyze_sop_health,
)


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


def _make_monitor_report(
    total_runs: int = 10,
    anomalies: list = None,
    trends: dict = None,
    metrics: dict = None,
) -> dict:
    """构造 OnlineMonitor.analyze() 的返回值。"""
    return {
        "module": "equipment",
        "period_days": 7,
        "total_runs": total_runs,
        "metrics": metrics or {},
        "anomalies": anomalies or [],
        "trends": trends or {},
    }


def _make_anomaly(
    attr: str = "tool_failure_rate",
    current: float = 0.6,
    baseline: float = 0.2,
    direction: str = "up",
    severity: str = "error",
) -> dict:
    """构造异常条目。"""
    return {
        "type": f"{attr}_spike",
        "metric": attr,
        "current": current,
        "baseline": baseline,
        "change_pct": round((current - baseline) / max(baseline, 0.001) * 100, 1),
        "direction": direction,
        "severity": severity,
        "suggestion": "Check dependencies",
    }


# ══════════════════════════════════════════════════════════════════════════
#  OptimizationSuggestion
# ══════════════════════════════════════════════════════════════════════════


class TestOptimizationSuggestion:
    def test_defaults(self):
        s = OptimizationSuggestion(
            timestamp="2026-07-03T00:00:00",
            module="equipment",
            node="execution_agent",
            suggestion_type="human_review",
            severity="high",
            trigger_metric="tool_failure_rate",
            trigger_value=0.6,
            baseline_value=0.2,
            suggestion="Check services",
        )
        assert s.auto_applicable is False
        assert s.evidence == {}

    def test_asdict(self):
        s = OptimizationSuggestion(
            timestamp="t", module="m", node="n",
            suggestion_type="skip_optional", severity="low",
            trigger_metric="x", trigger_value=1.0, baseline_value=0.5,
            suggestion="test",
        )
        d = asdict(s)
        assert "node" in d
        assert "suggestion" in d


# ══════════════════════════════════════════════════════════════════════════
#  SOPOptimizer.analyze — with mocked OnlineMonitor
# ══════════════════════════════════════════════════════════════════════════


class TestAnalyze:
    def _make_optimizer(self):
        return SOPOptimizer(save_suggestions=False)

    @patch("aitest.audit_engine.sop_optimizer.OnlineMonitor")
    def test_no_data_returns_empty(self, MockMonitor):
        MockMonitor.return_value.analyze.return_value = _make_monitor_report(total_runs=0)
        optimizer = self._make_optimizer()
        result = optimizer.analyze("equipment", days=7)
        assert result == []

    @patch("aitest.audit_engine.sop_optimizer.OnlineMonitor")
    def test_no_anomalies_returns_empty(self, MockMonitor):
        MockMonitor.return_value.analyze.return_value = _make_monitor_report()
        optimizer = self._make_optimizer()
        result = optimizer.analyze("equipment", days=7)
        assert result == []

    @patch("aitest.audit_engine.sop_optimizer.OnlineMonitor")
    def test_failure_rate_triggers_optional_skip(self, MockMonitor):
        anomaly = _make_anomaly("tool_failure_rate", current=0.6, baseline=0.2)
        MockMonitor.return_value.analyze.return_value = _make_monitor_report(anomalies=[anomaly])
        optimizer = self._make_optimizer()
        result = optimizer.analyze("equipment")

        # Should have suggestions for optional nodes
        optional_suggestions = [s for s in result if s.suggestion_type == "skip_optional"]
        assert len(optional_suggestions) == len(OPTIONAL_NODES)
        assert all(s.auto_applicable for s in optional_suggestions)

    @patch("aitest.audit_engine.sop_optimizer.OnlineMonitor")
    def test_failure_rate_triggers_human_review(self, MockMonitor):
        anomaly = _make_anomaly("tool_failure_rate", current=0.6, baseline=0.2)
        MockMonitor.return_value.analyze.return_value = _make_monitor_report(anomalies=[anomaly])
        optimizer = self._make_optimizer()
        result = optimizer.analyze("equipment")

        # Should have suggestions for core nodes
        review_suggestions = [s for s in result if s.suggestion_type == "human_review"
                              and s.trigger_metric == "tool_failure_rate"]
        assert len(review_suggestions) == len(CORE_NODES)
        assert all(not s.auto_applicable for s in review_suggestions)

    @patch("aitest.audit_engine.sop_optimizer.OnlineMonitor")
    def test_step_increase_triggers_check_prompt(self, MockMonitor):
        anomaly = _make_anomaly("avg_steps_per_run", current=20.0, baseline=8.0)
        MockMonitor.return_value.analyze.return_value = _make_monitor_report(anomalies=[anomaly])
        optimizer = self._make_optimizer()
        result = optimizer.analyze("equipment")

        prompt_suggestions = [s for s in result if s.suggestion_type == "check_prompt"]
        assert len(prompt_suggestions) == 1
        assert prompt_suggestions[0].node == "all"

    @patch("aitest.audit_engine.sop_optimizer.OnlineMonitor")
    def test_completion_drop_triggers_downgrade(self, MockMonitor):
        anomaly = _make_anomaly("task_completion_rate", current=0.3, baseline=0.8)
        MockMonitor.return_value.analyze.return_value = _make_monitor_report(anomalies=[anomaly])
        optimizer = self._make_optimizer()
        result = optimizer.analyze("equipment")

        downgrade = [s for s in result if s.suggestion_type == "downgrade_pipeline"]
        assert len(downgrade) == 1
        assert downgrade[0].severity == "high"

    @patch("aitest.audit_engine.sop_optimizer.OnlineMonitor")
    def test_timeout_rate_triggers_review(self, MockMonitor):
        anomaly = _make_anomaly("timeout_rate", current=0.25, baseline=0.05)
        MockMonitor.return_value.analyze.return_value = _make_monitor_report(anomalies=[anomaly])
        optimizer = self._make_optimizer()
        result = optimizer.analyze("equipment")

        timeout_suggestions = [s for s in result if s.trigger_metric == "timeout_rate"]
        assert len(timeout_suggestions) == 1

    @patch("aitest.audit_engine.sop_optimizer.OnlineMonitor")
    def test_multiple_anomalies(self, MockMonitor):
        anomalies = [
            _make_anomaly("tool_failure_rate", current=0.6, baseline=0.2),
            _make_anomaly("avg_steps_per_run", current=20.0, baseline=8.0),
        ]
        MockMonitor.return_value.analyze.return_value = _make_monitor_report(anomalies=anomalies)
        optimizer = self._make_optimizer()
        result = optimizer.analyze("equipment")

        # Should have suggestions from both rules
        types = {s.suggestion_type for s in result}
        assert "skip_optional" in types
        assert "check_prompt" in types


# ══════════════════════════════════════════════════════════════════════════
#  analyze_multi_module
# ══════════════════════════════════════════════════════════════════════════


class TestAnalyzeMultiModule:
    @patch("aitest.audit_engine.sop_optimizer.OnlineMonitor")
    def test_multi_module(self, MockMonitor):
        MockMonitor.return_value.analyze.return_value = _make_monitor_report(total_runs=0)
        optimizer = SOPOptimizer(save_suggestions=False)
        result = optimizer.analyze_multi_module(["equipment", "personnel"], days=7)
        assert "equipment" in result
        assert "personnel" in result


# ══════════════════════════════════════════════════════════════════════════
#  format_report
# ══════════════════════════════════════════════════════════════════════════


class TestFormatReport:
    def test_empty_suggestions(self):
        report = SOPOptimizer.format_report([])
        assert "无优化建议" in report

    def test_with_suggestions(self):
        suggestions = [
            OptimizationSuggestion(
                timestamp="t", module="m", node="execution_agent",
                suggestion_type="human_review", severity="high",
                trigger_metric="tool_failure_rate", trigger_value=0.6,
                baseline_value=0.2, suggestion="Check services",
            ),
            OptimizationSuggestion(
                timestamp="t", module="m", node="knowledge_agent",
                suggestion_type="skip_optional", severity="medium",
                trigger_metric="tool_failure_rate", trigger_value=0.6,
                baseline_value=0.2, suggestion="Skip for now",
                auto_applicable=True,
            ),
        ]
        report = SOPOptimizer.format_report(suggestions)
        assert "🔴 高优先级" in report
        assert "🟡 中优先级" in report
        assert "execution_agent" in report
        assert "knowledge_agent" in report


# ══════════════════════════════════════════════════════════════════════════
#  analyze_sop_health (convenience function)
# ══════════════════════════════════════════════════════════════════════════


class TestAnalyzeSopHealth:
    @patch("aitest.audit_engine.sop_optimizer.OnlineMonitor")
    def test_returns_dict(self, MockMonitor):
        MockMonitor.return_value.analyze.return_value = _make_monitor_report(
            anomalies=[_make_anomaly("tool_failure_rate", current=0.6, baseline=0.2)]
        )
        result = analyze_sop_health("equipment", days=7)
        assert isinstance(result, dict)
        assert result["module"] == "equipment"
        assert "suggestion_count" in result
        assert "high_severity" in result

    @patch("aitest.audit_engine.sop_optimizer.OnlineMonitor")
    def test_no_data(self, MockMonitor):
        MockMonitor.return_value.analyze.return_value = _make_monitor_report(total_runs=0)
        result = analyze_sop_health("equipment")
        assert result["suggestion_count"] == 0
