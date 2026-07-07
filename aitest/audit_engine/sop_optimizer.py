"""SOP Optimizer — P2: 消费 OnlineMonitor 异常检测结果，建议 SOP 结构调整。

当某个 Agent 节点连续失败/跳过/超时时，生成结构调整建议:
  - 节点连续 N 次失败 → 建议设为可选节点
  - 工具失败率持续偏高 → 建议降级到简化流水线
  - 步骤数异常增加 → 建议检查 Prompt 是否导致绕路
  - 完成率持续下降 → 建议人工介入检查

不直接修改 SOP 图（sop_graph.py），只生成建议报告。
人工确认后通过配置调整 SOP 行为。

用法:
    from aitest.audit_engine.sop_optimizer import SOPOptimizer

    optimizer = SOPOptimizer()
    suggestions = optimizer.analyze("equipment", days=7)
    for s in suggestions:
        print(f"[{s.severity}] {s.node}: {s.suggestion}")
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

from aitest.platform.paths import get_workstudy
from aitest.audit_engine.online_monitor import OnlineMonitor

_log = logging.getLogger(__name__)

WORKSTUDY = get_workstudy()
GOVERNANCE = WORKSTUDY / "governance"
ARTIFACTS_DIR = GOVERNANCE / "artifacts" / "sop_suggestions"


# ── SOP Agent 节点定义 ──────────────────────────────────────────────

# 可选节点: 连续失败时可以跳过而不阻塞整个 SOP
OPTIONAL_NODES = {
    "knowledge_agent",
    "data_sanitization_agent",
    "bug_analysis_agent",
}

# 核心节点: 连续失败时需要人工介入，不能自动跳过
CORE_NODES = {
    "project_agent",
    "requirement_agent",
    "test_design_agent",
    "automation_agent_pre",
    "automation_agent_post",
    "execution_agent",
    "report_agent",
}

ALL_SOP_NODES = OPTIONAL_NODES | CORE_NODES


@dataclass
class OptimizationSuggestion:
    """单条 SOP 优化建议。"""
    timestamp: str
    module: str
    node: str                  # SOP 节点名
    suggestion_type: str       # skip_optional | downgrade_pipeline | check_prompt | human_review
    severity: str              # "high" | "medium" | "low"
    trigger_metric: str        # 触发建议的指标名
    trigger_value: float       # 指标当前值
    baseline_value: float      # 指标基线值
    suggestion: str            # 建议描述
    evidence: dict = field(default_factory=dict)
    auto_applicable: bool = False  # 是否可以自动应用


class SOPOptimizer:
    """SOP 结构优化器。

    分析 OnlineMonitor 的异常检测结果，生成结构调整建议。

    阈值策略:
      - 连续 3 次工具失败率 > 0.5 → 可选节点建议跳过
      - 连续 3 次工具失败率 > 0.5 → 核心节点建议人工介入
      - 步骤数增加 > 100% → 建议检查 Prompt
      - 完成率下降 > 50% → 建议降级到简化流水线
    """

    # 阈值配置
    FAILURE_RATE_HIGH = 0.5
    FAILURE_RATE_CRITICAL = 0.8
    STEP_INCREASE_THRESHOLD = 1.0    # 100% increase
    COMPLETION_DROP_THRESHOLD = 0.5  # 50% drop
    CONSECUTIVE_THRESHOLD = 3        # 连续 N 次异常触发建议

    def __init__(self, save_suggestions: bool = True):
        self.save_suggestions = save_suggestions

    def analyze(self, module: str, days: int = 7) -> list[OptimizationSuggestion]:
        """分析指定模块的 SOP 执行数据，生成优化建议。

        Args:
            module: 模块名
            days: 分析天数

        Returns:
            优化建议列表
        """
        monitor = OnlineMonitor()
        report = monitor.analyze(module, days=days)

        if report.get("total_runs", 0) == 0:
            _log.debug(f"[SOPOptimizer] No data for module={module}")
            return []

        suggestions = []
        anomalies = report.get("anomalies", [])
        trends = report.get("trends", {})
        metrics = report.get("metrics", {})

        # Rule 1: 工具失败率异常
        suggestions.extend(
            self._check_failure_rate(module, anomalies, metrics)
        )

        # Rule 2: 步骤数异常增加
        suggestions.extend(
            self._check_step_increase(module, anomalies, trends)
        )

        # Rule 3: 完成率持续下降
        suggestions.extend(
            self._check_completion_drop(module, anomalies, trends)
        )

        # Rule 4: 超时率异常
        suggestions.extend(
            self._check_timeout_rate(module, anomalies, metrics)
        )

        # 保存建议
        if self.save_suggestions and suggestions:
            self._save_suggestions(suggestions)

        return suggestions

    def analyze_multi_module(
        self, modules: list[str], days: int = 7
    ) -> dict[str, list[OptimizationSuggestion]]:
        """多模块批量分析。"""
        results = {}
        for module in modules:
            results[module] = self.analyze(module, days=days)
        return results

    # ── Rule Checks ───────────────────────────────────────────────

    def _check_failure_rate(
        self, module: str, anomalies: list[dict], metrics: dict
    ) -> list[OptimizationSuggestion]:
        """检查工具失败率异常。"""
        suggestions = []
        failure_anomalies = [
            a for a in anomalies
            if a.get("type", "").startswith("tool_failure_rate")
        ]

        if not failure_anomalies:
            return suggestions

        anomaly = failure_anomalies[0]
        current = anomaly.get("current", 0)
        baseline = anomaly.get("baseline", 0)

        # 对可选节点: 建议跳过
        for node in OPTIONAL_NODES:
            suggestions.append(OptimizationSuggestion(
                timestamp=datetime.now().isoformat(),
                module=module,
                node=node,
                suggestion_type="skip_optional",
                severity="medium" if current < self.FAILURE_RATE_CRITICAL else "high",
                trigger_metric="tool_failure_rate",
                trigger_value=current,
                baseline_value=baseline,
                suggestion=(
                    f"工具失败率 {current:.1%}（基线 {baseline:.1%}），"
                    f"可选节点 {node} 可暂时跳过以保证 SOP 主流程通畅"
                ),
                evidence=anomaly,
                auto_applicable=True,
            ))

        # 对核心节点: 建议人工介入
        for node in CORE_NODES:
            suggestions.append(OptimizationSuggestion(
                timestamp=datetime.now().isoformat(),
                module=module,
                node=node,
                suggestion_type="human_review",
                severity="high",
                trigger_metric="tool_failure_rate",
                trigger_value=current,
                baseline_value=baseline,
                suggestion=(
                    f"工具失败率 {current:.1%}（基线 {baseline:.1%}），"
                    f"核心节点 {node} 需人工检查依赖服务状态"
                ),
                evidence=anomaly,
                auto_applicable=False,
            ))

        return suggestions

    def _check_step_increase(
        self, module: str, anomalies: list[dict], trends: dict
    ) -> list[OptimizationSuggestion]:
        """检查步骤数异常增加。"""
        suggestions = []
        step_anomalies = [
            a for a in anomalies
            if "avg_steps_per_run" in a.get("type", "")
        ]

        if not step_anomalies:
            return suggestions

        anomaly = step_anomalies[0]
        current = anomaly.get("current", 0)
        baseline = anomaly.get("baseline", 0)

        if baseline > 0 and (current - baseline) / baseline > self.STEP_INCREASE_THRESHOLD:
            suggestions.append(OptimizationSuggestion(
                timestamp=datetime.now().isoformat(),
                module=module,
                node="all",
                suggestion_type="check_prompt",
                severity="medium",
                trigger_metric="avg_steps_per_run",
                trigger_value=current,
                baseline_value=baseline,
                suggestion=(
                    f"平均步数从 {baseline:.0f} 增加到 {current:.0f}（+{(current-baseline)/baseline:.0%}），"
                    f"可能是 Prompt 改动导致 Agent 绕路，检查最近的 Skill 版本变更"
                ),
                evidence=anomaly,
                auto_applicable=False,
            ))

        return suggestions

    def _check_completion_drop(
        self, module: str, anomalies: list[dict], trends: dict
    ) -> list[OptimizationSuggestion]:
        """检查完成率持续下降。"""
        suggestions = []
        completion_anomalies = [
            a for a in anomalies
            if "task_completion_rate" in a.get("type", "")
        ]

        if not completion_anomalies:
            return suggestions

        anomaly = completion_anomalies[0]
        current = anomaly.get("current", 0)
        baseline = anomaly.get("baseline", 0)

        if baseline > 0 and (baseline - current) / baseline > self.COMPLETION_DROP_THRESHOLD:
            suggestions.append(OptimizationSuggestion(
                timestamp=datetime.now().isoformat(),
                module=module,
                node="all",
                suggestion_type="downgrade_pipeline",
                severity="high",
                trigger_metric="task_completion_rate",
                trigger_value=current,
                baseline_value=baseline,
                suggestion=(
                    f"完成率从 {baseline:.1%} 下降到 {current:.1%}，"
                    f"建议降级到简化流水线（SIMPLE tier）或暂停自动执行"
                ),
                evidence=anomaly,
                auto_applicable=False,
            ))

        return suggestions

    def _check_timeout_rate(
        self, module: str, anomalies: list[dict], metrics: dict
    ) -> list[OptimizationSuggestion]:
        """检查超时率异常。"""
        suggestions = []
        timeout_anomalies = [
            a for a in anomalies
            if "timeout_rate" in a.get("type", "")
        ]

        if not timeout_anomalies:
            return suggestions

        anomaly = timeout_anomalies[0]
        current = anomaly.get("current", 0)

        # 超时率 > 20% → 建议增加超时阈值或检查网络
        if current > 0.2:
            suggestions.append(OptimizationSuggestion(
                timestamp=datetime.now().isoformat(),
                module=module,
                node="execution_agent",
                suggestion_type="human_review",
                severity="medium",
                trigger_metric="timeout_rate",
                trigger_value=current,
                baseline_value=anomaly.get("baseline", 0),
                suggestion=(
                    f"超时率 {current:.1%}，建议检查:"
                    f" 1) 模型 provider 延迟趋势"
                    f" 2) 网络连通性"
                    f" 3) 是否需要增加超时阈值"
                ),
                evidence=anomaly,
                auto_applicable=False,
            ))

        return suggestions

    # ── Persistence ───────────────────────────────────────────────

    def _save_suggestions(self, suggestions: list[OptimizationSuggestion]) -> str:
        """保存建议到文件系统。"""
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_path = ARTIFACTS_DIR / f"sop-suggestions-{date_str}.jsonl"

        try:
            with open(file_path, "a", encoding="utf-8") as f:
                for s in suggestions:
                    f.write(json.dumps(asdict(s), ensure_ascii=False) + "\n")
            _log.debug(f"[SOPOptimizer] Saved {len(suggestions)} suggestion(s) → {file_path}")
        except Exception as e:
            _log.warning(f"[SOPOptimizer] Failed to save suggestions: {e}")

        return str(file_path)

    # ── Reporting ─────────────────────────────────────────────────

    @staticmethod
    def format_report(suggestions: list[OptimizationSuggestion]) -> str:
        """格式化建议报告为 Markdown。"""
        if not suggestions:
            return "# SOP 优化建议\n\n无优化建议。"

        lines = [
            "# SOP 优化建议",
            f"\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"建议总数: {len(suggestions)}",
            "",
        ]

        # 按严重程度分组
        high = [s for s in suggestions if s.severity == "high"]
        medium = [s for s in suggestions if s.severity == "medium"]
        low = [s for s in suggestions if s.severity == "low"]

        for group, label in [(high, "🔴 高优先级"), (medium, "🟡 中优先级"), (low, "🟢 低优先级")]:
            if not group:
                continue
            lines.append(f"## {label}")
            lines.append("")
            for s in group:
                lines.append(f"### {s.node} — {s.suggestion_type}")
                lines.append(f"- **指标**: {s.trigger_metric} = {s.trigger_value:.3f}（基线: {s.baseline_value:.3f}）")
                lines.append(f"- **建议**: {s.suggestion}")
                lines.append(f"- **可自动应用**: {'是' if s.auto_applicable else '否'}")
                lines.append("")

        return "\n".join(lines)


# ── Convenience ───────────────────────────────────────────────────


def analyze_sop_health(module: str, days: int = 7) -> dict:
    """便捷函数 — 分析 SOP 健康度。

    返回简化的结果字典（用于 API/报告）。
    """
    optimizer = SOPOptimizer()
    suggestions = optimizer.analyze(module, days=days)
    return {
        "module": module,
        "period_days": days,
        "suggestion_count": len(suggestions),
        "high_severity": len([s for s in suggestions if s.severity == "high"]),
        "auto_applicable": len([s for s in suggestions if s.auto_applicable]),
        "suggestions": [asdict(s) for s in suggestions],
    }
