"""
Step Efficiency Analyzer — P2: 过程效率分析。

基于 Agent 评估方法论过程层指标:
  - 无效工具调用率: 缺参数还调用 / 同样参数重复失败 / 查无关数据
  - 重复调用率: 同 tool + 同 params + 同 error 的重复
  - 关键路径长度: 去重后核心步骤数 vs 实际步数
  - 平均步数: 按 agent/skill 聚合

基于 trace_log.jsonl 做事后分析，零额外 LLM 调用。

用法:
    from aitest.governance.step_efficiency import StepEfficiencyAnalyzer

    analyzer = StepEfficiencyAnalyzer()
    report = analyzer.analyze("equipment", days=7)
    print(report["efficiency_score"])
"""

import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import defaultdict, Counter

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
TRACE_LOG = GOVERNANCE / ".traces" / "trace_log.jsonl"
KPI_DATA_DIR = GOVERNANCE / "kpi" / "timeseries"


@dataclass
class EfficiencyMetrics:
    """步骤效率指标。"""
    module: str
    period_days: int
    total_skill_executions: int = 0
    # 无效调用
    invalid_call_count: int = 0        # 缺参数/查无关数据
    invalid_call_rate: float = 0.0
    # 重复调用 (同 tool + 同 error)
    duplicate_call_count: int = 0
    duplicate_call_rate: float = 0.0
    # 路径效率
    unique_skill_count: int = 0        # 去重后（关键路径）
    total_step_count: int = 0          # 实际步数
    path_efficiency: float = 0.0       # unique / total
    # 延迟
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    # 按 skill 聚合
    skill_breakdown: list = field(default_factory=list)
    # 综合评分
    efficiency_score: float = 0.0      # 0-100


class StepEfficiencyAnalyzer:
    """
    步骤效率分析器 — 基于 trace log 做事后分析。

    用法:
        analyzer = StepEfficiencyAnalyzer()
        report = analyzer.analyze("equipment")
    """

    def __init__(self):
        pass

    def analyze(self, module: str, days: int = 7) -> dict:
        """
        分析指定模块的步骤效率。

        返回:
            {
                "module": "equipment",
                "period_days": 7,
                "efficiency_score": 85,
                "metrics": {...},
                "violations": [...],
            }
        """
        cutoff = datetime.now() - timedelta(days=days)
        events = self._load_events(module, cutoff)

        if not events:
            return {
                "module": module,
                "period_days": days,
                "efficiency_score": 100,
                "metrics": {"error": "no_data"},
                "violations": [],
            }

        # 按 run_id 分组分析
        runs = self._group_by_run(events)

        metrics = self._compute_metrics(runs)
        violations = self._detect_violations(runs)
        efficiency_score = self._compute_score(metrics, violations)

        report = {
            "module": module,
            "period_days": days,
            "efficiency_score": efficiency_score,
            "total_runs": len(runs),
            "metrics": metrics,
            "violations": violations,
        }

        # 记录 KPI
        try:
            from aitest.governance.governance_kpi import KPICollector
            kpi_data = {
                "step_efficiency": efficiency_score / 100,
                "invalid_call_rate": metrics.get("invalid_call_rate", 0),
                "duplicate_call_rate": metrics.get("duplicate_call_rate", 0),
            }
            KPICollector().record_audit("state", module, kpi_data)
        except Exception:
            pass

        return report

    def _group_by_run(self, events: list[dict]) -> dict:
        """按 run_id 分组事件。"""
        runs = {}
        for evt in events:
            rid = evt.get("run_id", "unknown")
            if rid not in runs:
                runs[rid] = []
            runs[rid].append(evt)
        # 每组内按时间排序
        for rid in runs:
            runs[rid].sort(key=lambda e: e.get("timestamp", ""))
        return runs

    def _compute_metrics(self, runs: dict) -> dict:
        """计算聚合效率指标。"""
        total_execs = 0
        invalid_count = 0
        dup_count = 0
        unique_skills = set()
        total_steps = 0
        latencies = []
        skill_counts = Counter()

        for rid, events in runs.items():
            seen_skills = set()
            # 检测无效调用: error 状态 + 无 output token
            for evt in events:
                total_execs += 1
                skill_id = evt.get("skill_id", "")
                unique_skills.add(skill_id)
                skill_counts[skill_id] += 1
                total_steps += 1

                lat = evt.get("latency_ms", 0)
                if lat > 0:
                    latencies.append(lat)

                # 无效调用: error 状态 + token_output = 0
                if (evt.get("status") == "error"
                        and evt.get("token_output", 0) == 0
                        and not evt.get("response_preview")):
                    invalid_count += 1

                # 同 skill 在第2次+出现 → 潜在重复
                if skill_id in seen_skills:
                    prev_events = [e for e in events if e.get("skill_id") == skill_id
                                  and e.get("timestamp", "") < evt.get("timestamp", "")]
                    if prev_events and self._same_error(prev_events[-1], evt):
                        dup_count += 1
                seen_skills.add(skill_id)

        # 路径效率
        path_eff = unique_skills.__len__() / max(total_steps, 1)

        # 延迟
        avg_lat = sum(latencies) / max(len(latencies), 1)
        sorted_lat = sorted(latencies)
        p95_idx = int(len(sorted_lat) * 0.95)
        p95_lat = sorted_lat[p95_idx] if sorted_lat else 0

        # 按 skill 聚合
        skill_breakdown = [
            {"skill_id": sid, "calls": cnt, "pct": round(cnt / max(total_execs, 1) * 100, 1)}
            for sid, cnt in skill_counts.most_common(10)
        ]

        return {
            "total_skill_executions": total_execs,
            "invalid_call_count": invalid_count,
            "invalid_call_rate": round(invalid_count / max(total_execs, 1), 3),
            "duplicate_call_count": dup_count,
            "duplicate_call_rate": round(dup_count / max(total_execs, 1), 3),
            "unique_skill_count": unique_skills.__len__(),
            "total_step_count": total_steps,
            "path_efficiency": round(path_eff, 3),
            "avg_latency_ms": round(avg_lat, 1),
            "p95_latency_ms": round(p95_lat, 1),
            "skill_breakdown": skill_breakdown,
        }

    def _detect_violations(self, runs: dict) -> list[dict]:
        """检测效率违规。"""
        violations = []

        for rid, events in runs.items():
            # 检测重复调用: 同 skill + 同 error ≥ 3 次
            skill_error_chain = defaultdict(list)
            for evt in events:
                key = (evt.get("skill_id", ""), evt.get("error_message", ""))

                skill_error_chain[key].append(evt)

            for (skill_id, error_msg), chain in skill_error_chain.items():
                if len(chain) >= 3 and error_msg:
                    violations.append({
                        "run_id": rid,
                        "type": "duplicate_calls",
                        "skill_id": skill_id,
                        "count": len(chain),
                        "error": error_msg[:100],
                        "severity": "warning",
                        "detail": f"Skill '{skill_id}' 以相同错误重复调用 {len(chain)} 次",
                        "suggestion": "Agent 缺少失败记忆，建议添加重复调用检测和退避逻辑",
                    })

            # 检测无效调用序列
            for i in range(len(events) - 1):
                curr = events[i]
                next_evt = events[i + 1]
                curr_skill = curr.get("skill_id", "")
                next_skill = next_evt.get("skill_id", "")

                # 同一 skill 连续 error → 无效重试
                if (curr_skill == next_skill
                        and curr.get("status") == "error"
                        and next_evt.get("status") == "error"):
                    violations.append({
                        "run_id": rid,
                        "type": "ineffective_retry",
                        "skill_id": curr_skill,
                        "severity": "info",
                        "detail": f"Skill '{curr_skill}' 连续失败未改变策略",
                        "suggestion": "应在重试前分析失败原因，改变参数或策略",
                    })
                    break  # 每个 run 最多报一次

        return violations

    @staticmethod
    def _same_error(evt_a: dict, evt_b: dict) -> bool:
        """判断两个事件是否有相同的错误。"""
        err_a = evt_a.get("error_message", "") or ""
        err_b = evt_b.get("error_message", "") or ""
        if err_a and err_b:
            # 至少相似 (前 50 字符相同或包含相同关键词)
            return err_a[:50] == err_b[:50] or (
                len(err_a) > 10 and len(err_b) > 10
                and err_a[:20] == err_b[:20]
            )
        # 都没有错误消息 → 看 status
        return (evt_a.get("status") == evt_b.get("status") == "error")

    def _compute_score(self, metrics: dict, violations: list[dict]) -> int:
        """计算综合效率评分 (0-100)。"""
        score = 100

        # 无效调用率: 每 10% 扣 10 分
        invalid_rate = metrics.get("invalid_call_rate", 0)
        score -= int(invalid_rate * 100)

        # 重复调用率: 每 5% 扣 5 分
        dup_rate = metrics.get("duplicate_call_rate", 0)
        score -= int(dup_rate * 100)

        # 路径效率低于 0.5: 扣分
        path_eff = metrics.get("path_efficiency", 1.0)
        if path_eff < 0.5:
            score -= int((0.5 - path_eff) * 100)

        # 违规数: 每个 warning 扣 2 分
        score -= sum(
            2 if v.get("severity") == "warning" else 1
            for v in violations
        )

        return max(0, min(100, score))

    def _load_events(self, module: str, cutoff: datetime) -> list[dict]:
        """加载 trace 事件。"""
        events = []
        if not TRACE_LOG.exists():
            return events
        try:
            with open(TRACE_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        evt = json.loads(line)
                        ts = datetime.fromisoformat(evt.get("timestamp", "2000-01-01T00:00:00"))
                        if ts < cutoff:
                            continue
                        if module and module not in evt.get("run_id", ""):
                            continue
                        events.append(evt)
                    except (json.JSONDecodeError, ValueError):
                        continue
        except OSError:
            pass
        return events


# ══════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python step_efficiency.py <module> [--days=<n>] [--json]")
        sys.exit(0)

    module_name = sys.argv[1]
    days_val = 7
    for o in sys.argv[2:]:
        if o.startswith("--days="):
            days_val = int(o.split("=")[1])

    analyzer = StepEfficiencyAnalyzer()
    report = analyzer.analyze(module_name, days=days_val)

    if "--json" in sys.argv:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        m = report["metrics"]
        print(f"\nStep Efficiency: {module_name} (score: {report['efficiency_score']}/100)")
        print(f"  Skill executions: {m.get('total_skill_executions', 0)}")
        print(f"  Invalid call rate: {m.get('invalid_call_rate', 0):.1%}")
        print(f"  Duplicate call rate: {m.get('duplicate_call_rate', 0):.1%}")
        print(f"  Path efficiency: {m.get('path_efficiency', 0):.1%}")
        print(f"  Avg latency: {m.get('avg_latency_ms', 0):.0f}ms (p95: {m.get('p95_latency_ms', 0):.0f}ms)")
        print(f"  Violations: {len(report.get('violations', []))}")
