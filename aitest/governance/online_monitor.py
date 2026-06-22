"""
Online Monitor — P0: 线上监控基础指标采集 + 异常诊断。

基于 Agent 评估方法论 12 项线上监控指标:
  完成类: 任务完成率、(用户追问率/取消率——预留)
  步骤类: 平均执行步数、工具调用次数、重复调用率
  错误类: 工具失败率、超时率
  安全类: (高风险动作确认率——由 SafetyAuditor 负责)
  用户类: (人工接管率/差评率——预留)

职责:
  1. AgentLoop 结束时自动采集 run_summary
  2. 时序存储到 governance/kpi/timeseries/online-{module}-{date}.jsonl
  3. 异常诊断: 工具失败率突升 / 平均步数突升 → 告警
  4. 与 review_trigger 集成

用法:
    from aitest.governance.online_monitor import OnlineMonitor, collect_run_metrics

    # AgentLoop 结束时的轻量采集
    metrics = collect_run_metrics(state, trace_events)
    OnlineMonitor().record_run("equipment", metrics)

    # 事后分析
    monitor = OnlineMonitor()
    report = monitor.analyze("equipment", days=7)
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from collections import Counter

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
KPI_DATA_DIR = GOVERNANCE / "kpi" / "timeseries"
TRACE_LOG = GOVERNANCE / ".traces" / "trace_log.jsonl"
AUDIT_DIR = GOVERNANCE / "artifacts" / "audits"


@dataclass
class RunMetrics:
    """单次 Agent 运行的指标快照。"""
    timestamp: str
    run_id: str
    module: str
    agent_name: str
    # 完成类
    task_completed: bool              # Agent 目标是否完成
    skills_total: int                 # 总 skill 数
    skills_passed: int                # 通过的 skill 数
    skills_failed: int                # 失败的 skill 数
    skills_skipped: int               # 跳过的 skill 数
    task_completion_rate: float       # skills_passed / skills_total
    # 步骤类
    total_steps: int                  # Agent 执行步数
    skill_executions: int             # 实际 skill 调用次数 (含重试)
    duplicate_calls: int              # 同 skill 同 error 重试 ≥3 次
    avg_latency_ms: float             # 平均延迟
    # 错误类
    tool_failures: int                # status=error 的 skill 数
    tool_failure_rate: float          # tool_failures / skill_executions
    timeouts: int                     # latency > 120s 的次数
    timeout_rate: float               # timeouts / skill_executions
    # Token/Cost
    total_tokens_in: int
    total_tokens_out: int
    total_cost_estimate: float
    # 安全
    safety_flags_count: int           # 运行时安全告警数
    # 预留字段 (无生产用户交互，记录为 -1)
    user_followup_rate: float = -1.0
    user_cancel_rate: float = -1.0
    human_takeover_rate: float = -1.0
    user_negative_rate: float = -1.0


class OnlineMonitor:
    """
    线上监控指标采集 + 异常诊断。

    用法:
        monitor = OnlineMonitor()
        monitor.record_run("equipment", metrics)
        report = monitor.analyze("equipment", days=7)
    """

    def __init__(self):
        KPI_DATA_DIR.mkdir(parents=True, exist_ok=True)

    def record_run(self, module: str, metrics: RunMetrics) -> str:
        """记录一次 Agent 运行的指标快照。返回文件路径。"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        daily_file = KPI_DATA_DIR / f"online-{module}-{date_str}.jsonl"
        with open(daily_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(metrics), ensure_ascii=False) + "\n")

        # 记录 KPI 数据点
        try:
            from aitest.governance.governance_kpi import KPICollector
            report = {
                "task_completion_rate": metrics.task_completion_rate,
                "avg_steps_per_run": metrics.total_steps,
                "tool_failure_rate": metrics.tool_failure_rate,
                "timeout_rate": metrics.timeout_rate,
            }
            KPICollector().record_audit("online", module, report)
        except Exception:
            pass

        return str(daily_file)

    def analyze(self, module: str, days: int = 7) -> dict:
        """
        分析指定模块的线上指标，检测异常。

        返回:
            {
                "module": "equipment",
                "period_days": 7,
                "total_runs": 10,
                "metrics": {...},
                "anomalies": [...],
                "trends": {...}
            }
        """
        cutoff = datetime.now() - timedelta(days=days)
        all_metrics = self._load_metrics(module, cutoff)

        if not all_metrics:
            return {
                "module": module,
                "period_days": days,
                "total_runs": 0,
                "metrics": {},
                "anomalies": [{"type": "no_data", "detail": "无线上运行数据"}],
                "trends": {},
            }

        # 计算聚合指标
        recent = all_metrics[-5:] if len(all_metrics) >= 5 else all_metrics
        older = all_metrics[:max(len(all_metrics)//2, 1)]

        aggregated = {
            "task_completion_rate": self._avg(recent, "task_completion_rate"),
            "avg_steps_per_run": self._avg(recent, "total_steps"),
            "tool_failure_rate": self._avg(recent, "tool_failure_rate"),
            "timeout_rate": self._avg(recent, "timeout_rate"),
            "avg_latency_ms": self._avg(recent, "avg_latency_ms"),
            "duplicate_call_rate": self._avg(recent, "duplicate_calls"),
            "total_tokens_in": sum(m.total_tokens_in for m in all_metrics),
            "total_tokens_out": sum(m.total_tokens_out for m in all_metrics),
            "total_cost": sum(m.total_cost_estimate for m in all_metrics),
            "total_runs": len(all_metrics),
        }

        # 异常诊断
        anomalies = self._detect_anomalies(recent, older)

        # 趋势
        trends = self._compute_trends(recent, older)

        return {
            "module": module,
            "period_days": days,
            "total_runs": len(all_metrics),
            "metrics": aggregated,
            "anomalies": anomalies,
            "trends": trends,
        }

    def _detect_anomalies(self, recent: list["RunMetrics"],
                          older: list["RunMetrics"]) -> list[dict]:
        """检测近期指标异常。"""
        anomalies = []

        if not older:
            return anomalies

        checks = [
            ("tool_failure_rate", "工具失败率", 0.3, ">"),
            ("avg_steps_per_run", "平均步数", 2.0, ">"),
            ("timeout_rate", "超时率", 0.2, ">"),
            ("task_completion_rate", "任务完成率", 0.3, "<"),
        ]

        for attr, label, threshold, direction in checks:
            recent_val = self._avg(recent, attr)
            older_val = self._avg(older, attr)

            if older_val == 0:
                continue
            change_ratio = (recent_val - older_val) / older_val

            if direction == ">" and change_ratio > threshold:
                anomalies.append({
                    "type": f"{attr}_spike",
                    "metric": label,
                    "current": round(recent_val, 3),
                    "baseline": round(older_val, 3),
                    "change_pct": round(change_ratio * 100, 1),
                    "direction": "up",
                    "severity": "warning" if change_ratio < 1.0 else "error",
                    "suggestion": self._suggest_cause(attr, change_ratio),
                })
            elif direction == "<" and change_ratio < -threshold:
                anomalies.append({
                    "type": f"{attr}_drop",
                    "metric": label,
                    "current": round(recent_val, 3),
                    "baseline": round(older_val, 3),
                    "change_pct": round(change_ratio * 100, 1),
                    "direction": "down",
                    "severity": "warning" if change_ratio > -0.5 else "error",
                    "suggestion": self._suggest_cause(attr, change_ratio),
                })

        return anomalies

    @staticmethod
    def _suggest_cause(metric_attr: str, change_ratio: float) -> str:
        """根据异常的指标推断可能原因。"""
        suggestions = {
            "tool_failure_rate": "可能是某工具接口挂了，非模型问题。检查依赖服务状态。",
            "avg_steps_per_run": "可能是 Prompt 改动导致 Agent 绕路，检查最近的 Skill 版本变更。",
            "timeout_rate": "可能是模型响应变慢或网络问题，检查 provider 延迟趋势。",
            "task_completion_rate": "完成率下降，可能是新增问题超出任务边界。检查新上线的 module。",
        }
        return suggestions.get(metric_attr, "建议检查最近的变更和 trace 日志。")

    def _compute_trends(self, recent: list["RunMetrics"],
                        older: list["RunMetrics"]) -> dict:
        """计算指标趋势。"""
        trends = {}
        for attr in ["task_completion_rate", "tool_failure_rate",
                     "avg_steps_per_run", "timeout_rate"]:
            recent_val = self._avg(recent, attr)
            older_val = self._avg(older, attr)
            if older_val == 0:
                direction = "stable"
                change_pct = 0.0
            else:
                change_pct = round((recent_val - older_val) / older_val * 100, 1)
                direction = "up" if change_pct > 10 else "down" if change_pct < -10 else "stable"
            trends[attr] = {
                "recent": round(recent_val, 3),
                "baseline": round(older_val, 3),
                "change_pct": change_pct,
                "direction": direction,
            }
        return trends

    def _load_metrics(self, module: str, cutoff: datetime) -> list[RunMetrics]:
        """加载指标数据。"""
        metrics = []
        for f in sorted(KPI_DATA_DIR.glob(f"online-{module}-*.jsonl")):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    for line in fp:
                        line = line.strip()
                        if not line:
                            continue
                        d = json.loads(line)
                        ts = datetime.fromisoformat(d.get("timestamp", "2000-01-01T00:00:00"))
                        if ts >= cutoff:
                            metrics.append(RunMetrics(**{
                                k: v for k, v in d.items()
                                if k in RunMetrics.__dataclass_fields__
                            }))
            except Exception:
                pass
        return metrics

    @staticmethod
    def _avg(metrics_list: list[RunMetrics], attr: str) -> float:
        if not metrics_list:
            return 0.0
        values = [getattr(m, attr, 0) for m in metrics_list]
        return sum(values) / len(values)


# ══════════════════════════════════════════════════════════════════════════
#  轻量采集函数 — AgentLoop.run() 结束时调用
# ══════════════════════════════════════════════════════════════════════════

def collect_run_metrics(state, trace_events: list[dict] = None) -> RunMetrics:
    """
    从 AgentState 和 trace events 中采集运行指标。

    在 AgentLoop.run() 返回前调用，零额外 LLM 调用。

    参数:
        state: AgentState (来自 agent_runner.py)
        trace_events: 该次运行的 trace event 列表 (可选)

    返回:
        RunMetrics 实例
    """
    observations = state.observations
    skills_total = len(state.completed_skills) + len(state.failed_skills)
    skills_passed = len(state.completed_skills)
    skills_failed = len(state.failed_skills)

    # 统计重复调用 (同 skill 重试 ≥2 次 = 重复)
    duplicate_count = sum(
        1 for c in state.retry_counts.values() if c >= 2
    )

    # 从 observations 统计
    tool_failures = sum(1 for o in observations if o.status in ("fail", "wrong_failure"))
    timeouts = sum(1 for o in observations if o.latency_ms > 120_000)

    skill_executions = len(observations)
    if skill_executions == 0:
        skill_executions = 1  # avoid division by zero

    # 延迟统计
    latencies = [o.latency_ms for o in observations if o.latency_ms > 0]
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    # Token 统计
    tokens_in = sum(o.token_usage.get("input", 0) for o in observations)
    tokens_out = sum(o.token_usage.get("output", 0) for o in observations)
    total_cost = sum(
        o.token_usage.get("cost_estimate", 0) +
        o.token_usage.get("cost", 0)
        for o in observations
    )

    # 安全告警
    safety_count = sum(len(o.safety_flags) for o in observations)

    return RunMetrics(
        timestamp=datetime.now().isoformat(),
        run_id=observations[0].run_id if observations else "",
        module=state.module or "unknown",
        agent_name=state.agent_name,
        task_completed=state.success,
        skills_total=skills_total,
        skills_passed=skills_passed,
        skills_failed=skills_failed,
        skills_skipped=sum(1 for o in observations if o.status == "skipped"),
        task_completion_rate=skills_passed / max(skills_total, 1),
        total_steps=state.step,
        skill_executions=skill_executions,
        duplicate_calls=duplicate_count,
        avg_latency_ms=round(avg_latency, 1),
        tool_failures=tool_failures,
        tool_failure_rate=round(tool_failures / skill_executions, 3),
        timeouts=timeouts,
        timeout_rate=round(timeouts / skill_executions, 3),
        total_tokens_in=tokens_in,
        total_tokens_out=tokens_out,
        total_cost_estimate=round(total_cost, 6),
        safety_flags_count=safety_count,
    )


# ══════════════════════════════════════════════════════════════════════════
#  Trace 回放 API — 可视化单次运行的完整步骤
# ══════════════════════════════════════════════════════════════════════════

def get_run_trace_replay(run_id: str) -> dict:
    """
    获取指定 run_id 的完整 trace 回放。

    返回每一步: 输入、工具调用、返回结果、token、延迟、偏离点。

    参数:
        run_id: 运行 ID

    返回:
        {
            "run_id": "sop-equipment-xxx",
            "steps": [
                {"seq": 1, "skill_id": "...", "event_type": "...",
                 "latency_ms": 1234, "tokens_in": 500, "tokens_out": 200,
                 "status": "success", "prompt_preview": "...", "response_preview": "...",
                 "error": "..."}
            ],
            "summary": {"total_steps": 5, "total_cost": 0.05, "total_latency_ms": 5000}
        }
    """
    if not TRACE_LOG.exists():
        return {"run_id": run_id, "steps": [], "summary": {}, "error": "No trace log found"}

    steps = []
    total_cost = 0.0
    total_latency = 0

    try:
        with open(TRACE_LOG, "r", encoding="utf-8") as f:
            seq = 0
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if evt.get("run_id") != run_id:
                    continue

                seq += 1
                steps.append({
                    "seq": seq,
                    "skill_id": evt.get("skill_id", ""),
                    "event_type": evt.get("event_type", ""),
                    "agent_name": evt.get("agent_name", ""),
                    "timestamp": evt.get("timestamp", ""),
                    "latency_ms": evt.get("latency_ms", 0),
                    "tokens_in": evt.get("token_input", 0),
                    "tokens_out": evt.get("token_output", 0),
                    "cost": evt.get("token_cost_estimate", 0),
                    "status": evt.get("status", ""),
                    "prompt_preview": evt.get("prompt_preview", ""),
                    "response_preview": evt.get("response_preview", ""),
                    "error": evt.get("error_message", ""),
                    "model": evt.get("model", ""),
                    "provider": evt.get("provider", ""),
                    "metadata": evt.get("metadata", {}),
                })
                total_cost += evt.get("token_cost_estimate", 0)
                total_latency += evt.get("latency_ms", 0)

    except OSError:
        return {"run_id": run_id, "steps": [], "summary": {}, "error": "Failed to read trace log"}

    # 按时间排序
    steps.sort(key=lambda s: s.get("timestamp", ""))

    return {
        "run_id": run_id,
        "steps": steps,
        "summary": {
            "total_steps": len(steps),
            "total_cost": round(total_cost, 6),
            "total_latency_ms": total_latency,
        },
    }


def list_recent_runs(limit: int = 20) -> list[dict]:
    """列出最近运行的 run_id 列表。"""
    if not TRACE_LOG.exists():
        return []

    runs = {}
    try:
        with open(TRACE_LOG, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    evt = json.loads(line)
                except json.JSONDecodeError:
                    continue
                rid = evt.get("run_id", "")
                if rid and rid not in runs:
                    runs[rid] = {
                        "run_id": rid,
                        "agent_name": evt.get("agent_name", ""),
                        "timestamp": evt.get("timestamp", ""),
                        "event_count": 1,
                    }
                elif rid:
                    runs[rid]["event_count"] += 1
    except OSError:
        pass

    # 按时间倒序
    sorted_runs = sorted(runs.values(), key=lambda r: r.get("timestamp", ""), reverse=True)
    return sorted_runs[:limit]


# ══════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python online_monitor.py analyze <module> [--days=<n>]")
        print("       python online_monitor.py trace <run_id>")
        print("       python online_monitor.py runs [--limit=<n>]")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "analyze":
        module_name = sys.argv[2] if len(sys.argv) > 2 else "system"
        days_val = 7
        for o in sys.argv[3:]:
            if o.startswith("--days="):
                days_val = int(o.split("=")[1])
        monitor = OnlineMonitor()
        report = monitor.analyze(module_name, days=days_val)
        print(json.dumps(report, ensure_ascii=False, indent=2))

    elif cmd == "trace":
        run_id = sys.argv[2] if len(sys.argv) > 2 else ""
        replay = get_run_trace_replay(run_id)
        print(json.dumps(replay, ensure_ascii=False, indent=2))

    elif cmd == "runs":
        limit = 20
        for o in sys.argv[2:]:
            if o.startswith("--limit="):
                limit = int(o.split("=")[1])
        runs = list_recent_runs(limit=limit)
        print(json.dumps(runs, ensure_ascii=False, indent=2))
