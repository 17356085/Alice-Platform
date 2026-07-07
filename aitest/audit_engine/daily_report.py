"""Daily Report — P3: 离线批量分析报告。

复用现有审计组件生成每日汇总报告，提供管理层 visibility:
  - OnlineMonitor: 线上指标 + 异常
  - FailureAttributor: 失败归因分布
  - CostAuditor: 成本趋势 + 告警
  - GovernanceKPI: KPI 趋势
  - SOPOptimizer: SOP 优化建议

报告输出:
  - Markdown 格式，适合人工阅读
  - JSON 格式，适合程序消费

用法:
    from aitest.audit_engine.daily_report import DailyReport

    report = DailyReport()
    md = report.generate(modules=["equipment", "personnel"])
    # → Markdown 报告

CLI:
    python -m aitest.audit_engine.daily_report --modules=equipment,personnel --days=7
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

from aitest.platform.paths import get_workstudy
from aitest.audit_engine.online_monitor import OnlineMonitor
from aitest.audit_engine.failure_attributor import FailureAttributor
from aitest.audit_engine.cost_auditor import CostAuditor
from aitest.audit_engine.sop_optimizer import SOPOptimizer

_log = logging.getLogger(__name__)

WORKSTUDY = get_workstudy()
GOVERNANCE = WORKSTUDY / "governance"
REPORTS_DIR = GOVERNANCE / "artifacts" / "daily_reports"


@dataclass
class DailyReportData:
    """每日报告数据结构。"""
    date: str
    modules: list[str]
    period_days: int
    # 各子系统数据
    online_monitor: dict = field(default_factory=dict)
    failure_trends: dict = field(default_factory=dict)
    cost_audit: dict = field(default_factory=dict)
    sop_suggestions: dict = field(default_factory=dict)
    # 汇总
    summary: dict = field(default_factory=dict)


class DailyReport:
    """每日汇总报告生成器。

    聚合多个审计子系统的数据，生成统一的管理层报告。
    """

    def __init__(self, save_report: bool = True):
        self.save_report = save_report

    def generate(
        self,
        modules: list[str] = None,
        days: int = 7,
        format: str = "markdown",
    ) -> str:
        """生成每日汇总报告。

        Args:
            modules: 模块列表（None 则分析所有有数据的模块）
            days: 分析天数
            format: 输出格式 ("markdown" | "json")

        Returns:
            报告内容（Markdown 或 JSON 字符串）
        """
        if modules is None:
            modules = self._discover_modules()

        data = self._collect_data(modules, days)

        if format == "json":
            content = json.dumps(asdict(data), ensure_ascii=False, indent=2)
        else:
            content = self._render_markdown(data)

        if self.save_report:
            self._save(content, format)

        return content

    def _collect_data(self, modules: list[str], days: int) -> DailyReportData:
        """从各子系统收集数据。"""
        data = DailyReportData(
            date=datetime.now().strftime("%Y-%m-%d"),
            modules=modules,
            period_days=days,
        )

        # 1. OnlineMonitor
        data.online_monitor = self._collect_online_monitor(modules, days)

        # 2. FailureAttributor
        data.failure_trends = self._collect_failure_trends(modules, days)

        # 3. CostAuditor
        data.cost_audit = self._collect_cost_audit(days)

        # 4. SOPOptimizer
        data.sop_suggestions = self._collect_sop_suggestions(modules, days)

        # 5. 汇总
        data.summary = self._build_summary(data)

        return data

    # ── Subsystem Collectors ──────────────────────────────────────

    def _collect_online_monitor(self, modules: list[str], days: int) -> dict:
        """收集 OnlineMonitor 数据。"""
        try:
            monitor = OnlineMonitor()
            results = {}
            for module in modules:
                results[module] = monitor.analyze(module, days=days)
            return results
        except Exception as e:
            _log.warning(f"[DailyReport] OnlineMonitor collection failed: {e}")
            return {"error": str(e)}

    def _collect_failure_trends(self, modules: list[str], days: int) -> dict:
        """收集 FailureAttributor 趋势数据。"""
        try:
            attributor = FailureAttributor()
            results = {}
            for module in modules:
                results[module] = attributor.analyze_trends(module, days=days)
            return results
        except Exception as e:
            _log.warning(f"[DailyReport] FailureAttributor collection failed: {e}")
            return {"error": str(e)}

    def _collect_cost_audit(self, days: int) -> dict:
        """收集 CostAuditor 数据。"""
        try:
            auditor = CostAuditor()
            return auditor.audit(days=days)
        except Exception as e:
            _log.warning(f"[DailyReport] CostAuditor collection failed: {e}")
            return {"error": str(e)}

    def _collect_sop_suggestions(self, modules: list[str], days: int) -> dict:
        """收集 SOPOptimizer 建议。"""
        try:
            optimizer = SOPOptimizer(save_suggestions=False)
            results = {}
            for module in modules:
                suggestions = optimizer.analyze(module, days=days)
                results[module] = {
                    "count": len(suggestions),
                    "high": len([s for s in suggestions if s.severity == "high"]),
                    "auto_applicable": len([s for s in suggestions if s.auto_applicable]),
                }
            return results
        except Exception as e:
            _log.warning(f"[DailyReport] SOPOptimizer collection failed: {e}")
            return {"error": str(e)}

    # ── Summary ───────────────────────────────────────────────────

    def _build_summary(self, data: DailyReportData) -> dict:
        """构建汇总信息。"""
        total_runs = 0
        total_anomalies = 0
        total_suggestions = 0
        high_suggestions = 0

        # 从 OnlineMonitor 汇总
        for module, report in data.online_monitor.items():
            if isinstance(report, dict) and "error" not in report:
                total_runs += report.get("total_runs", 0)
                total_anomalies += len(report.get("anomalies", []))

        # 从 SOPOptimizer 汇总
        for module, info in data.sop_suggestions.items():
            if isinstance(info, dict) and "error" not in info:
                total_suggestions += info.get("count", 0)
                high_suggestions += info.get("high", 0)

        # 健康度评分 (简单算法: 100 - 异常数*5 - 高优先级建议*10)
        health_score = max(0, 100 - total_anomalies * 5 - high_suggestions * 10)

        return {
            "total_runs": total_runs,
            "total_anomalies": total_anomalies,
            "total_suggestions": total_suggestions,
            "high_suggestions": high_suggestions,
            "health_score": health_score,
            "health_level": (
                "healthy" if health_score >= 80
                else "warning" if health_score >= 50
                else "critical"
            ),
        }

    # ── Markdown Rendering ────────────────────────────────────────

    def _render_markdown(self, data: DailyReportData) -> str:
        """渲染 Markdown 报告。"""
        lines = [
            f"# 每日测试自动化报告 — {data.date}",
            "",
            f"**分析周期**: {data.period_days} 天 | **模块**: {', '.join(data.modules)}",
            "",
            "---",
            "",
            "## 📊 总览",
            "",
            f"| 指标 | 值 |",
            f"|------|-----|",
            f"| 总运行次数 | {data.summary.get('total_runs', 0)} |",
            f"| 异常数 | {data.summary.get('total_anomalies', 0)} |",
            f"| 优化建议数 | {data.summary.get('total_suggestions', 0)} |",
            f"| 高优先级建议 | {data.summary.get('high_suggestions', 0)} |",
            f"| 健康度评分 | {data.summary.get('health_score', 0)}/100 ({data.summary.get('health_level', 'unknown')}) |",
            "",
        ]

        # OnlineMonitor 模块详情
        lines.append("## 📈 线上指标")
        lines.append("")
        for module, report in data.online_monitor.items():
            if isinstance(report, dict) and "error" not in report:
                metrics = report.get("metrics", {})
                anomalies = report.get("anomalies", [])
                lines.append(f"### {module}")
                lines.append(f"- 运行次数: {report.get('total_runs', 0)}")
                lines.append(f"- 完成率: {metrics.get('task_completion_rate', 0):.1%}")
                lines.append(f"- 工具失败率: {metrics.get('tool_failure_rate', 0):.1%}")
                lines.append(f"- 超时率: {metrics.get('timeout_rate', 0):.1%}")
                lines.append(f"- 异常数: {len(anomalies)}")
                if anomalies:
                    for a in anomalies[:3]:  # 最多显示 3 个
                        lines.append(f"  - ⚠️ {a.get('metric', '')}: {a.get('current', 0):.3f} ({a.get('change_pct', 0):+.1f}%)")
                lines.append("")

        # 成本概览
        cost = data.cost_audit
        if isinstance(cost, dict) and "error" not in cost:
            lines.append("## 💰 成本概览")
            lines.append("")
            alerts = cost.get("alerts", [])
            lines.append(f"- 告警数: {len(alerts)}")
            for alert in alerts[:3]:
                lines.append(f"  - [{alert.get('severity', '')}] {alert.get('finding', '')}")
            lines.append("")

        # SOP 优化建议
        lines.append("## 🔧 SOP 优化建议")
        lines.append("")
        for module, info in data.sop_suggestions.items():
            if isinstance(info, dict) and "error" not in info:
                lines.append(f"- **{module}**: {info.get('count', 0)} 条建议（高优先级: {info.get('high', 0)}，可自动: {info.get('auto_applicable', 0)}）")
        lines.append("")

        lines.append("---")
        lines.append(f"*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")

        return "\n".join(lines)

    # ── Persistence ───────────────────────────────────────────────

    def _save(self, content: str, format: str) -> str:
        """保存报告到文件系统。"""
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        ext = "md" if format == "markdown" else "json"
        file_path = REPORTS_DIR / f"daily-report-{date_str}.{ext}"

        try:
            file_path.write_text(content, encoding="utf-8")
            _log.info(f"[DailyReport] Saved report → {file_path}")
        except Exception as e:
            _log.warning(f"[DailyReport] Failed to save report: {e}")

        return str(file_path)

    # ── Module Discovery ──────────────────────────────────────────

    def _discover_modules(self) -> list[str]:
        """从 KPI 数据目录中发现有数据的模块。"""
        try:
            from aitest.audit_engine.online_monitor import KPI_DATA_DIR
            modules = set()
            for f in KPI_DATA_DIR.glob("online-*.jsonl"):
                # online-{module}-{date}.jsonl
                parts = f.stem.split("-")
                if len(parts) >= 3:
                    # Rejoin everything between "online" and the date
                    module = "-".join(parts[1:-1])
                    modules.add(module)
            return sorted(modules) if modules else ["unknown"]
        except Exception:
            return ["unknown"]


# ── Convenience ───────────────────────────────────────────────────


def generate_daily_report(
    modules: list[str] = None,
    days: int = 7,
    save: bool = True,
) -> dict:
    """便捷函数 — 生成每日报告并返回汇总数据。"""
    report = DailyReport(save_report=save)
    content = report.generate(modules=modules, days=days, format="json")
    data = json.loads(content)
    return data.get("summary", {})


# ── CLI ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    modules = None
    days = 7
    fmt = "markdown"

    for arg in sys.argv[1:]:
        if arg.startswith("--modules="):
            modules = arg.split("=")[1].split(",")
        elif arg.startswith("--days="):
            days = int(arg.split("=")[1])
        elif arg.startswith("--format="):
            fmt = arg.split("=")[1]
        elif arg == "--json":
            fmt = "json"

    report = DailyReport()
    content = report.generate(modules=modules, days=days, format=fmt)
    print(content)
