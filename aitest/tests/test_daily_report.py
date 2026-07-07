"""Tests for audit_engine/daily_report.py — DailyReport, DailyReportData.

Tests: 数据收集、汇总计算、Markdown 渲染、模块发现。
Mock 所有子系统避免文件系统/ChromaDB 依赖。
"""
import json
import pytest
from unittest.mock import patch, MagicMock

from aitest.audit_engine.daily_report import (
    DailyReport,
    DailyReportData,
    generate_daily_report,
)


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


def _mock_online_report(runs=10, anomalies=None):
    return {
        "module": "equipment",
        "period_days": 7,
        "total_runs": runs,
        "metrics": {
            "task_completion_rate": 0.85,
            "tool_failure_rate": 0.1,
            "timeout_rate": 0.05,
        },
        "anomalies": anomalies or [],
        "trends": {},
    }


def _mock_cost_audit(alerts=None):
    return {
        "period_days": 7,
        "alerts": alerts or [],
        "total_cost": 1.23,
    }


# ══════════════════════════════════════════════════════════════════════════
#  DailyReportData
# ══════════════════════════════════════════════════════════════════════════


class TestDailyReportData:
    def test_defaults(self):
        data = DailyReportData(date="2026-07-03", modules=["equipment"], period_days=7)
        assert data.date == "2026-07-03"
        assert data.online_monitor == {}
        assert data.summary == {}


# ══════════════════════════════════════════════════════════════════════════
#  DailyReport.generate — mocked subsystems
# ══════════════════════════════════════════════════════════════════════════


class TestGenerate:
    def _make_report(self):
        return DailyReport(save_report=False)

    @patch("aitest.audit_engine.daily_report.SOPOptimizer")
    @patch("aitest.audit_engine.daily_report.CostAuditor")
    @patch("aitest.audit_engine.daily_report.FailureAttributor")
    @patch("aitest.audit_engine.daily_report.OnlineMonitor")
    def test_generate_markdown(self, MockOM, MockFA, MockCA, MockSO):
        MockOM.return_value.analyze.return_value = _mock_online_report()
        MockFA.return_value.analyze_trends.return_value = {}
        MockCA.return_value.audit.return_value = _mock_cost_audit()
        MockSO.return_value.analyze.return_value = []

        report = self._make_report()
        content = report.generate(modules=["equipment"], days=7, format="markdown")

        assert "每日测试自动化报告" in content
        assert "equipment" in content
        assert "总览" in content

    @patch("aitest.audit_engine.daily_report.SOPOptimizer")
    @patch("aitest.audit_engine.daily_report.CostAuditor")
    @patch("aitest.audit_engine.daily_report.FailureAttributor")
    @patch("aitest.audit_engine.daily_report.OnlineMonitor")
    def test_generate_json(self, MockOM, MockFA, MockCA, MockSO):
        MockOM.return_value.analyze.return_value = _mock_online_report()
        MockFA.return_value.analyze_trends.return_value = {}
        MockCA.return_value.audit.return_value = _mock_cost_audit()
        MockSO.return_value.analyze.return_value = []

        report = self._make_report()
        content = report.generate(modules=["equipment"], days=7, format="json")

        data = json.loads(content)
        assert data["date"] is not None
        assert "summary" in data

    @patch("aitest.audit_engine.daily_report.SOPOptimizer")
    @patch("aitest.audit_engine.daily_report.CostAuditor")
    @patch("aitest.audit_engine.daily_report.FailureAttributor")
    @patch("aitest.audit_engine.daily_report.OnlineMonitor")
    def test_multiple_modules(self, MockOM, MockFA, MockCA, MockSO):
        MockOM.return_value.analyze.return_value = _mock_online_report()
        MockFA.return_value.analyze_trends.return_value = {}
        MockCA.return_value.audit.return_value = _mock_cost_audit()
        MockSO.return_value.analyze.return_value = []

        report = self._make_report()
        content = report.generate(modules=["equipment", "personnel"], format="markdown")

        assert "equipment" in content
        assert "personnel" in content


# ══════════════════════════════════════════════════════════════════════════
#  _build_summary
# ══════════════════════════════════════════════════════════════════════════


class TestBuildSummary:
    def _make_report(self):
        return DailyReport(save_report=False)

    def test_summary_healthy(self):
        report = self._make_report()
        data = DailyReportData(
            date="2026-07-03", modules=["m"], period_days=7,
            online_monitor={"m": _mock_online_report(runs=10)},
            sop_suggestions={"m": {"count": 0, "high": 0, "auto_applicable": 0}},
        )
        summary = report._build_summary(data)
        assert summary["total_runs"] == 10
        assert summary["total_anomalies"] == 0
        assert summary["health_score"] == 100
        assert summary["health_level"] == "healthy"

    def test_summary_warning(self):
        report = self._make_report()
        anomalies = [{"type": "x_spike"}] * 5
        data = DailyReportData(
            date="2026-07-03", modules=["m"], period_days=7,
            online_monitor={"m": _mock_online_report(anomalies=anomalies)},
            sop_suggestions={"m": {"count": 2, "high": 1, "auto_applicable": 0}},
        )
        summary = report._build_summary(data)
        assert summary["total_anomalies"] == 5
        assert summary["high_suggestions"] == 1
        assert summary["health_level"] == "warning"

    def test_summary_critical(self):
        report = self._make_report()
        anomalies = [{"type": "x_spike"}] * 15
        data = DailyReportData(
            date="2026-07-03", modules=["m"], period_days=7,
            online_monitor={"m": _mock_online_report(anomalies=anomalies)},
            sop_suggestions={"m": {"count": 10, "high": 5, "auto_applicable": 0}},
        )
        summary = report._build_summary(data)
        assert summary["health_level"] == "critical"


# ══════════════════════════════════════════════════════════════════════════
#  子系统异常降级
# ══════════════════════════════════════════════════════════════════════════


class TestGracefulDegradation:
    def _make_report(self):
        return DailyReport(save_report=False)

    @patch("aitest.audit_engine.daily_report.SOPOptimizer")
    @patch("aitest.audit_engine.daily_report.CostAuditor")
    @patch("aitest.audit_engine.daily_report.FailureAttributor")
    @patch("aitest.audit_engine.daily_report.OnlineMonitor")
    def test_online_monitor_error(self, MockOM, MockFA, MockCA, MockSO):
        MockOM.return_value.analyze.side_effect = Exception("ChromaDB down")
        MockFA.return_value.analyze_trends.return_value = {}
        MockCA.return_value.audit.return_value = {}
        MockSO.return_value.analyze.return_value = []

        report = self._make_report()
        content = report.generate(modules=["equipment"], format="markdown")
        # Should still produce a report
        assert "每日测试自动化报告" in content

    @patch("aitest.audit_engine.daily_report.SOPOptimizer")
    @patch("aitest.audit_engine.daily_report.CostAuditor")
    @patch("aitest.audit_engine.daily_report.FailureAttributor")
    @patch("aitest.audit_engine.daily_report.OnlineMonitor")
    def test_all_subsystems_error(self, MockOM, MockFA, MockCA, MockSO):
        MockOM.return_value.analyze.side_effect = Exception("e1")
        MockFA.return_value.analyze_trends.side_effect = Exception("e2")
        MockCA.return_value.audit.side_effect = Exception("e3")
        MockSO.return_value.analyze.side_effect = Exception("e4")

        report = self._make_report()
        content = report.generate(modules=["equipment"], format="markdown")
        assert "每日测试自动化报告" in content


# ══════════════════════════════════════════════════════════════════════════
#  generate_daily_report (convenience function)
# ══════════════════════════════════════════════════════════════════════════


class TestGenerateDailyReport:
    @patch("aitest.audit_engine.daily_report.SOPOptimizer")
    @patch("aitest.audit_engine.daily_report.CostAuditor")
    @patch("aitest.audit_engine.daily_report.FailureAttributor")
    @patch("aitest.audit_engine.daily_report.OnlineMonitor")
    def test_returns_summary(self, MockOM, MockFA, MockCA, MockSO):
        MockOM.return_value.analyze.return_value = _mock_online_report()
        MockFA.return_value.analyze_trends.return_value = {}
        MockCA.return_value.audit.return_value = _mock_cost_audit()
        MockSO.return_value.analyze.return_value = []

        result = generate_daily_report(modules=["equipment"], save=False)
        assert isinstance(result, dict)
        assert "health_score" in result
