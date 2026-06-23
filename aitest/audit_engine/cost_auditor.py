"""
Cost Auditor Agent — P1-4: Token 异常检测 + Context 膨胀检测 + 成本趋势。

基于 trace_log.jsonl 的统计异常检测和成本治理。

职责:
  1. Spike Detection — Z-score 滚动窗口异常检测
  2. Context Bloat Detection — Phase 间 context 膨胀趋势
  3. Skill/Agent Cost Trend — 时间序列成本分析
  4. Optimization Recommendations — 降本建议

用法:
    from aitest.audit_engine.cost_auditor import CostAuditor, run_cost_audit

    auditor = CostAuditor()
    report = auditor.audit(days=7)
    for alert in report["alerts"]:
        print(f"[{alert['severity']}] {alert['finding']}")

CLI:
    aitest audit cost --days=7 [--json]
"""

import json
import math
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
TRACE_LOG = GOVERNANCE / ".traces" / "trace_log.jsonl"
AUDIT_DIR = GOVERNANCE / "artifacts" / "audits"


@dataclass
class CostAlert:
    """单条成本告警/发现。"""
    severity: str           # "high" | "medium" | "low"
    rule: str               # 规则名称
    finding: str            # 发现描述
    suggestion: str = ""
    evidence: dict = field(default_factory=dict)


class CostAuditor:
    """
    Cost Auditor Agent — 成本治理。

    用法:
        auditor = CostAuditor()
        report = auditor.audit(days=7)
        print(f"Total cost: ${report['total_cost']:.4f}")
        for alert in report["alerts"]:
            print(f"[{alert['severity']}] {alert['finding']}")
    """

    def __init__(self):
        self.alerts: list[CostAlert] = []
        self.events: list[dict] = []
        self.total_cost = 0.0

    def audit(self, days: int = 7) -> dict:
        """
        运行成本审计。

        参数:
            days: 回溯天数

        返回:
            {
                "period": "7d",
                "total_cost": 4.32,
                "total_events": 150,
                "alerts": [...],
                "trends": [...],
                "optimizations": [...]
            }
        """
        self.alerts = []
        self.events = self._load_events(days)

        if not self.events:
            return self._empty_report(days)

        self.total_cost = sum(
            e.get("token_cost_estimate", 0) or 0 for e in self.events
        )

        # 1. Spike Detection (Z-score)
        self._run_spike_check()

        # 2. Context Bloat Detection
        self._run_bloat_check()

        # 3. Skill Cost Trend
        self._run_trend_check()

        # 4. Optimization Recommendations
        self._run_optimization_check()

        # 汇总
        trends = self._compute_trends()
        optimizations = self._suggest_optimizations()

        severity_order = {"high": 0, "medium": 1, "low": 2}
        sorted_alerts = sorted(self.alerts, key=lambda a: severity_order.get(a.severity, 99))

        # P0-FIX (2026-06-15): 发射 CostAnomaly 事件
        for alert in sorted_alerts:
            if alert.severity in ("high", "medium"):
                try:
                    from aitest.audit_engine.event_bus import emit
                    emit("CostAnomaly",
                         skill_id=alert.evidence.get("skill_id", ""),
                         agent=alert.evidence.get("agent", ""),
                         anomaly_type=alert.rule,
                         detail=alert.finding)
                except Exception as e:
                    from aitest.infra.error_logger import log_error
                    log_error("cost_auditor.emit", "CostAnomaly", e, {"rule": alert.rule})

        # P0-ACTIVATION (2026-06-15): AuditCompleted 事件
        try:
            from aitest.audit_engine.event_bus import emit
            emit("AuditCompleted",
                 audit_type="cost",
                 module="all",
                 report_path=str(AUDIT_DIR / "cost-audit-*.json"),
                 overall_status="warning" if self.alerts else "ok")
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("cost_auditor.emit", "AuditCompleted", e, {})

        report = {
            "period": f"{days}d",
            "audit_time": datetime.now().isoformat(),
            "total_cost": round(self.total_cost, 6),
            "total_events": len(self.events),
            "alert_count": len(self.alerts),
            "alerts": [a.__dict__ for a in sorted_alerts],
            "trends": trends,
            "optimizations": optimizations,
        }

        # L4-MEASURED (2026-06-15): 记录 KPI 数据点
        try:
            from aitest.audit_engine.governance_kpi import KPICollector
            KPICollector().record_audit("cost", "all", report)
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("cost_auditor.kpi", "record", e, {})

        self._write_report(report)
        return report

    # ══════════════════════════════════════════════════════════════════
    #  Spike Detection — Z-score 异常检测
    # ══════════════════════════════════════════════════════════════════

    def _run_spike_check(self):
        """P1-4: 基于 Z-score 的 token 异常 spike 检测。"""
        # 按 skill_id 分组，计算每个 skill 的 token 分布
        skill_tokens: dict[str, list[int]] = {}
        for e in self.events:
            sid = e.get("skill_id", "")
            if not sid:
                continue
            tokens = (e.get("token_input", 0) or 0) + (e.get("token_output", 0) or 0)
            if tokens > 0:
                skill_tokens.setdefault(sid, []).append(tokens)

        for skill_id, tokens_list in skill_tokens.items():
            if len(tokens_list) < 3:
                continue  # 样本太少，无法计算统计量

            mean_t = sum(tokens_list) / len(tokens_list)
            if mean_t == 0:
                continue

            variance = sum((t - mean_t) ** 2 for t in tokens_list) / len(tokens_list)
            std_dev = math.sqrt(variance)
            if std_dev == 0:
                continue

            # 检查最近一次是否超过 3σ
            latest = tokens_list[-1]
            z_score = (latest - mean_t) / std_dev

            if z_score > 3.0:
                self.alerts.append(CostAlert(
                    severity="high",
                    rule="token_spike",
                    finding=f"Skill '{skill_id}' 最近一次消耗 {latest} tokens "
                            f"(均值 {mean_t:.0f}, σ={std_dev:.0f}, z={z_score:.1f})",
                    suggestion="检查是否: 1) 新页面元素过多 2) Prompt 未正确截断 3) RAG 检索过多条目",
                    evidence={
                        "skill_id": skill_id,
                        "mean": round(mean_t, 0),
                        "std_dev": round(std_dev, 0),
                        "latest": latest,
                        "z_score": round(z_score, 2),
                        "sample_count": len(tokens_list),
                    },
                ))
            elif z_score > 2.0:
                self.alerts.append(CostAlert(
                    severity="medium",
                    rule="token_spike",
                    finding=f"Skill '{skill_id}' 最近一次 token 偏高 (z={z_score:.1f})",
                    suggestion="轻微异常，持续观察。如持续出现则需排查。",
                    evidence={"skill_id": skill_id, "z_score": round(z_score, 2)},
                ))

    # ══════════════════════════════════════════════════════════════════
    #  Context Bloat Detection
    # ══════════════════════════════════════════════════════════════════

    def _run_bloat_check(self):
        """P1-4: Context 膨胀检测 — 检查 skill_execution 的 context_chars 趋势。"""
        # 收集每个 skill 的 context_chars 历史
        skill_context: dict[str, list[int]] = {}
        for e in self.events:
            if e.get("event_type") != "skill_execution":
                continue
            sid = e.get("skill_id", "")
            if not sid:
                continue
            meta = e.get("metadata", {})
            if isinstance(meta, dict):
                ctx = meta.get("context_chars", 0)
                if ctx > 0:
                    skill_context.setdefault(sid, []).append(ctx)

        for skill_id, ctx_list in skill_context.items():
            if len(ctx_list) < 2:
                continue

            avg = sum(ctx_list) / len(ctx_list)
            if avg > 5000:
                self.alerts.append(CostAlert(
                    severity="medium",
                    rule="context_bloat",
                    finding=f"Skill '{skill_id}' 平均注入上下文 {avg:.0f} chars",
                    suggestion="检查该 Skill 的 context 映射: 1) PAGE_INTERFACE.yaml 是否可用 (替代全量 PAGE_CONTEXT) "
                               "2) RAG 检索是否返回过多条目 3) 是否注入了不必要的知识库条目",
                    evidence={
                        "skill_id": skill_id,
                        "avg_context_chars": round(avg, 0),
                        "sample_count": len(ctx_list),
                        "max": max(ctx_list),
                        "min": min(ctx_list),
                    },
                ))

            # 检测膨胀趋势: 最近 3 次 vs 之前平均
            if len(ctx_list) >= 5:
                recent = ctx_list[-3:]
                older = ctx_list[:-3]
                recent_avg = sum(recent) / len(recent)
                older_avg = sum(older) / len(older)
                if older_avg > 0 and recent_avg > older_avg * 1.5:
                    self.alerts.append(CostAlert(
                        severity="low",
                        rule="context_bloat_trend",
                        finding=f"Skill '{skill_id}' context 有膨胀趋势: "
                                f"{older_avg:.0f} → {recent_avg:.0f} chars (+{(recent_avg/older_avg-1)*100:.0f}%)",
                        suggestion="检查最近 3 次运行的 context 增量来源。可能是模块 Context 文档膨胀。",
                        evidence={
                            "skill_id": skill_id,
                            "older_avg": round(older_avg, 0),
                            "recent_avg": round(recent_avg, 0),
                            "inflate_ratio": round(recent_avg / older_avg, 2),
                        },
                    ))

    # ══════════════════════════════════════════════════════════════════
    #  Cost Trend
    # ══════════════════════════════════════════════════════════════════

    def _run_trend_check(self):
        """P1-4: 成本趋势分析。"""
        # 按 agent 统计
        agent_costs: dict[str, list[float]] = {}
        # 按 run_id 聚合
        run_costs: dict[str, float] = {}

        for e in self.events:
            agent = e.get("agent_name", "") or "(unknown)"
            cost = e.get("token_cost_estimate", 0) or 0
            rid = e.get("run_id", "")

            if cost > 0:
                agent_costs.setdefault(agent, []).append(cost)
            if rid and cost > 0:
                run_costs[rid] = run_costs.get(rid, 0) + cost

        # 检查是否有 agent 单次调用成本 > $0.50
        for agent, costs in agent_costs.items():
            for c in costs:
                if c > 0.50:
                    self.alerts.append(CostAlert(
                        severity="medium",
                        rule="expensive_call",
                        finding=f"Agent '{agent}' 单次调用成本 ${c:.4f}",
                        suggestion="检查该调用的 token 消耗，考虑切换更小模型或精简 context",
                        evidence={"agent": agent, "cost": round(c, 4)},
                    ))
                    break  # 每个 agent 只报告一次

        # 按 run_id 成本排序
        sorted_runs = sorted(run_costs.items(), key=lambda x: -x[1])
        if sorted_runs and sorted_runs[0][1] > 5.0:
            top_run = sorted_runs[0]
            self.alerts.append(CostAlert(
                severity="high",
                rule="expensive_run",
                finding=f"Run '{top_run[0]}' 总成本 ${top_run[1]:.4f}，超过 $5 阈值",
                suggestion="检查该次运行的 Phase 分布，定位高消耗 Phase",
                evidence={"run_id": top_run[0], "cost": round(top_run[1], 4)},
            ))

    # ══════════════════════════════════════════════════════════════════
    #  Optimization Recommendations
    # ══════════════════════════════════════════════════════════════════

    def _run_optimization_check(self):
        """P1-4: 自动降本建议。"""
        # 检查 knowledge-manager 是否用了高成本模型
        for e in self.events:
            if e.get("skill_id") == "knowledge/knowledge-manager":
                model = e.get("model", "")
                if "sonnet" in model.lower() or "opus" in model.lower() or "gpt-4" in model.lower():
                    self.alerts.append(CostAlert(
                        severity="low",
                        rule="model_downgrade",
                        finding=f"knowledge-manager 使用了 {model}，可降级到 haiku 节省 ~60% 成本",
                        suggestion="knowledge-manager 任务复杂度低，claude-haiku-4-5 足以胜任",
                        evidence={"skill_id": "knowledge/knowledge-manager", "current_model": model},
                    ))
                    break

    # ══════════════════════════════════════════════════════════════════
    #  趋势 ＋ 优化建议
    # ══════════════════════════════════════════════════════════════════

    def _compute_trends(self) -> list[dict]:
        """计算 skill/agent 成本趋势。"""
        # 按 skill 聚合
        skill_stats: dict[str, dict] = {}
        for e in self.events:
            sid = e.get("skill_id", "")
            if not sid:
                continue
            tokens = (e.get("token_input", 0) or 0) + (e.get("token_output", 0) or 0)
            cost = e.get("token_cost_estimate", 0) or 0
            if sid not in skill_stats:
                skill_stats[sid] = {"calls": 0, "tokens": 0, "cost": 0.0}
            skill_stats[sid]["calls"] += 1
            skill_stats[sid]["tokens"] += tokens
            skill_stats[sid]["cost"] += cost

        trends = []
        for sid, stats in skill_stats.items():
            if stats["calls"] > 0:
                trends.append({
                    "skill_id": sid,
                    "calls": stats["calls"],
                    "avg_tokens": round(stats["tokens"] / stats["calls"]),
                    "total_cost": round(stats["cost"], 6),
                })

        trends.sort(key=lambda t: -t["total_cost"])
        return trends[:10]  # Top 10

    def _suggest_optimizations(self) -> list[dict]:
        """生成降本优化建议。"""
        suggestions = []

        # 统计模型使用频次
        model_usage: dict[str, int] = {}
        total_tokens_by_model: dict[str, int] = {}
        for e in self.events:
            model = e.get("model", "")
            if model:
                model_usage[model] = model_usage.get(model, 0) + 1
                tokens = (e.get("token_input", 0) or 0) + (e.get("token_output", 0) or 0)
                total_tokens_by_model[model] = total_tokens_by_model.get(model, 0) + tokens

        # 如果 haiku 使用率低，建议多用 haiku
        total_calls = sum(model_usage.values())
        haiku_calls = sum(v for k, v in model_usage.items() if "haiku" in k.lower())
        if total_calls > 20 and haiku_calls / total_calls < 0.3:
            suggestions.append({
                "type": "model_selection",
                "action": "增加 haiku 使用比例",
                "current_haiku_ratio": round(haiku_calls / total_calls, 2),
                "est_saving": "~40-60% for low-complexity skills",
                "applicable_skills": [
                    "knowledge/knowledge-manager",
                    "project/context-sync",
                    "execution/excel-exporter",
                ],
            })

        return suggestions

    # ══════════════════════════════════════════════════════════════════
    #  P2-3: 成本预测 + 跨模型对比 + 归因
    # ══════════════════════════════════════════════════════════════════

    def predict_run_cost(self, agent_name: str, module: str = "") -> dict:
        """
        P2-3: 基于历史数据预测下一次 SOP 运行的预期成本。

        使用简单移动平均 + 趋势外推。

        返回:
            {"agent": "...", "predicted_tokens": 12000, "predicted_cost": 0.036,
             "confidence": "medium", "based_on": 5}
        """
        # 收集该 agent 的历史 token 消耗
        agent_tokens: list[int] = []
        for e in self.events:
            if e.get("agent_name") == agent_name:
                tokens = (e.get("token_input", 0) or 0) + (e.get("token_output", 0) or 0)
                if tokens > 0:
                    agent_tokens.append(tokens)

        if not agent_tokens:
            return {
                "agent": agent_name,
                "predicted_tokens": 0,
                "predicted_cost": 0.0,
                "confidence": "none",
                "based_on": 0,
                "note": "无历史数据",
            }

        n = len(agent_tokens)
        mean_t = sum(agent_tokens) / n

        # 简单趋势: 最近 3 次 vs 整体平均
        if n >= 5:
            recent_avg = sum(agent_tokens[-3:]) / 3
            trend_factor = recent_avg / mean_t if mean_t > 0 else 1.0
            predicted = int(recent_avg * min(trend_factor, 1.2))  # 封顶 20% 增长
            confidence = "high" if n >= 10 else "medium"
        else:
            predicted = int(mean_t)
            confidence = "low"

        cost = round(predicted / 1_000_000 * 3.0, 6)  # sonnet pricing

        return {
            "agent": agent_name,
            "module": module,
            "predicted_tokens": predicted,
            "predicted_cost": cost,
            "confidence": confidence,
            "based_on": n,
            "historical_mean": int(mean_t),
            "historical_std": int(math.sqrt(sum((t - mean_t)**2 for t in agent_tokens) / n)) if n > 1 else 0,
        }

    def compare_models(
        self,
        skill_id: str = None,
        agent_name: str = None,
        days: int = 30,
    ) -> dict:
        """
        P2-3: 跨模型成本/性能对比。

        分析同一 Skill/Agent 在不同模型上的 token 消耗和成本差异。

        返回:
            {"skill_id": "...", "models": {"claude-sonnet-4-6": {...}, "deepseek-v3": {...}}}
        """
        model_stats: dict[str, dict] = {}

        for e in self.events:
            sid = e.get("skill_id", "")
            agent = e.get("agent_name", "")

            # 过滤
            if skill_id and sid != skill_id and skill_id not in sid:
                continue
            if agent_name and agent != agent_name:
                continue

            model = e.get("model", "") or "unknown"
            tokens = (e.get("token_input", 0) or 0) + (e.get("token_output", 0) or 0)
            cost = e.get("token_cost_estimate", 0) or 0
            latency = e.get("latency_ms", 0) or 0

            if model not in model_stats:
                model_stats[model] = {
                    "calls": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0,
                    "total_latency_ms": 0,
                }
            model_stats[model]["calls"] += 1
            model_stats[model]["total_tokens"] += tokens
            model_stats[model]["total_cost"] += cost
            model_stats[model]["total_latency_ms"] += latency

        # 计算平均值
        comparison = {}
        for model, stats in model_stats.items():
            n = max(stats["calls"], 1)
            comparison[model] = {
                "calls": stats["calls"],
                "avg_tokens_per_call": round(stats["total_tokens"] / n),
                "avg_cost_per_call": round(stats["total_cost"] / n, 6),
                "avg_latency_ms": round(stats["total_latency_ms"] / n),
                "total_cost": round(stats["total_cost"], 6),
            }

        # 找出性价比最优
        best_value = None
        best_score = float("inf")
        for model, stats in comparison.items():
            # 性价比 = cost / call (越低越好) × latency penalty
            cost_per_call = stats["avg_cost_per_call"]
            if cost_per_call > 0 and stats["calls"] >= 3:
                score = cost_per_call * (1 + stats["avg_latency_ms"] / 10000)
                if score < best_score:
                    best_score = score
                    best_value = model

        return {
            "skill_id": skill_id,
            "agent_name": agent_name,
            "models": comparison,
            "best_value_model": best_value,
            "recommendation": (
                f"性价比最优: {best_value} (avg ${comparison[best_value]['avg_cost_per_call']:.4f}/call)"
                if best_value else "数据不足，无法判断"
            ),
        }

    def attribute_cost(self, skill_id: str = None) -> dict:
        """
        P2-3: 成本归因 — 分析成本在 Prompt Section 间的分布。

        从 trace metadata 中提取 context 注入来源，归因 token 消耗。

        返回:
            {
                "skill_id": "...",
                "attribution": {
                    "system_prompt": {"tokens_pct": 30, "est_cost": 0.01},
                    "context_injection": {"tokens_pct": 50, "est_cost": 0.015},
                    "user_input": {"tokens_pct": 20, "est_cost": 0.006},
                },
                "top_context_sources": [...],
            }
        """
        attribution = {
            "system_prompt": {"tokens_pct": 0, "avg_chars": 0, "calls": 0},
            "context_injection": {"tokens_pct": 0, "avg_chars": 0, "calls": 0},
            "user_input": {"tokens_pct": 0, "avg_chars": 0, "calls": 0},
        }
        context_sources: dict[str, int] = {}

        relevant = [e for e in self.events
                    if not skill_id or e.get("skill_id") == skill_id or skill_id in e.get("skill_id", "")]
        if not relevant:
            return {"skill_id": skill_id, "attribution": attribution, "top_context_sources": [], "note": "无数据"}

        total_tokens = 0
        for e in relevant:
            tokens_in = e.get("token_input", 0) or 0
            total_tokens += tokens_in

            # 从 metadata 提取 context 信息
            meta = e.get("metadata", {})
            if isinstance(meta, dict):
                ctx_chars = meta.get("context_chars", 0)
                src_count = meta.get("source_count", 0)
                sources = meta.get("sources", [])

                if ctx_chars > 0:
                    attribution["context_injection"]["avg_chars"] += ctx_chars
                    attribution["context_injection"]["calls"] += 1
                if src_count > 0:
                    attribution["context_injection"]["tokens_pct"] += src_count

                for src in (sources or []):
                    if isinstance(src, str):
                        context_sources[src] = context_sources.get(src, 0) + 1

            # Prompt preview 长度
            preview = e.get("prompt_preview", "")
            if preview:
                attribution["system_prompt"]["avg_chars"] += len(preview)
                attribution["system_prompt"]["calls"] += 1

        # 归一化
        n = len(relevant)
        if attribution["system_prompt"]["calls"] > 0:
            attribution["system_prompt"]["avg_chars"] //= attribution["system_prompt"]["calls"]
            attribution["system_prompt"]["tokens_pct"] = round(
                attribution["system_prompt"]["avg_chars"] / max(total_tokens / max(n, 1) * 4, 1) * 100
            )
        if attribution["context_injection"]["calls"] > 0:
            attribution["context_injection"]["avg_chars"] //= attribution["context_injection"]["calls"]
            attribution["context_injection"]["tokens_pct"] = round(
                attribution["context_injection"]["avg_chars"] / max(total_tokens / max(n, 1) * 4, 1) * 100
            )

        # Top context sources
        top_sources = sorted(context_sources.items(), key=lambda x: -x[1])[:5]

        return {
            "skill_id": skill_id,
            "sample_count": n,
            "total_tokens_sampled": total_tokens,
            "attribution": attribution,
            "top_context_sources": [{"source": s, "occurrences": c} for s, c in top_sources],
        }

    # ══════════════════════════════════════════════════════════════════
    #  数据加载
    # ══════════════════════════════════════════════════════════════════

    def _load_events(self, days: int) -> list[dict]:
        """加载最近 N 天的 trace 事件。"""
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
                        if ts >= cutoff:
                            events.append(entry)
                    except (json.JSONDecodeError, ValueError):
                        continue
        except Exception:
            pass

        return events

    def _empty_report(self, days: int) -> dict:
        return {
            "period": f"{days}d",
            "audit_time": datetime.now().isoformat(),
            "total_cost": 0.0,
            "total_events": 0,
            "alert_count": 0,
            "alerts": [],
            "trends": [],
            "optimizations": [],
        }

    def _write_report(self, report: dict):
        """持久化审计报告。"""
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        report_path = AUDIT_DIR / f"cost-audit-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
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

def run_cost_audit(days: int = 7, json_output: bool = False) -> dict:
    """
    P1-4: 运行 Cost Auditor。

    参数:
        days:       回溯天数
        json_output: 输出 JSON

    返回:
        审计报告 dict
    """
    auditor = CostAuditor()
    report = auditor.audit(days=days)

    if json_output:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return report

    print(f"\n{'='*60}")
    print(f"  Cost Audit: Last {days}d")
    print(f"  Total Cost: ${report['total_cost']:.4f}")
    print(f"  Events: {report['total_events']} | Alerts: {report['alert_count']}")
    print(f"{'='*60}\n")

    if not report["alerts"]:
        print("  ✅ 无成本异常检测到\n")
    else:
        for a in report["alerts"]:
            icon = {"high": "❌", "medium": "⚠️", "low": "ℹ️"}.get(a["severity"], "•")
            print(f"  {icon} [{a['severity'].upper()}] [{a['rule']}] {a['finding']}")
            if a.get("suggestion"):
                print(f"     → {a['suggestion']}")
            print()

    if report["trends"]:
        print(f"  Top cost skills:")
        for t in report["trends"][:5]:
            print(f"    {t['skill_id']}: ${t['total_cost']:.4f} ({t['calls']} calls, avg {t['avg_tokens']} tokens)")

    if report["optimizations"]:
        print(f"\n  🔧 Optimization suggestions:")
        for o in report["optimizations"]:
            print(f"    {o['type']}: {o['action']} — est. saving: {o['est_saving']}")

    print(f"\n  Report saved to: {AUDIT_DIR}\n")
    return report


if __name__ == "__main__":
    import sys

    days = 7
    opts = set(sys.argv[1:])
    for opt in sys.argv[1:]:
        if opt.startswith("--days="):
            days = int(opt.split("=")[1])
    run_cost_audit(days=days, json_output="--json" in opts)
