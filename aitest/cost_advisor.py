"""
P2 可观测性: 自动成本优化建议引擎。

从 trace_log.jsonl 读取追踪数据，基于规则引擎识别成本浪费点，
输出按严重度排序的优化建议列表。

用法:
    from aitest.cost_advisor import analyze_trace_data
    suggestions = analyze_trace_data(days=7)
    for s in suggestions:
        print(f"{s['severity']} | {s['rule']}: {s['finding']}")

CLI:
    aitest trace advise --days=7
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional


WORKSTUDY = Path(__file__).resolve().parent.parent
TRACE_LOG = WORKSTUDY / "governance" / ".traces" / "trace_log.jsonl"


def _load_events(days: int = 7) -> list[dict]:
    """从 trace_log.jsonl 加载最近 N 天的所有事件。"""
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
                    ts = datetime.fromisoformat(entry.get("timestamp", "2000-01-01T00:00:00"))
                    if ts >= cutoff:
                        events.append(entry)
                except (json.JSONDecodeError, ValueError):
                    continue
    except Exception:
        pass

    return events


# ══════════════════════════════════════════════════════════════════════════
#  规则引擎
# ══════════════════════════════════════════════════════════════════════════

def _check_expensive_agent(aggregates: dict, total_cost: float) -> Optional[dict]:
    """规则: 某 Agent 占总成本 > 50%"""
    for agent, stats in aggregates.get("by_agent", {}).items():
        cost = stats.get("cost", 0)
        if total_cost > 0 and cost / total_cost > 0.5:
            return {
                "severity": "high",
                "rule": "expensive_agent",
                "finding": f"{agent} 占总成本的 {cost / total_cost * 100:.1f}%",
                "suggestion": "优先优化该 Agent: 启用 PAGE_INTERFACE.yaml + 规则化 LLM Plan 快捷路径",
                "evidence": {"agent": agent, "cost": cost, "total_cost": total_cost, "ratio": round(cost / total_cost, 2)},
            }
    return None


def _check_high_context(events: list[dict]) -> Optional[dict]:
    """规则: 某 Skill 平均 context_chars > 3000"""
    skill_contexts: dict[str, list[int]] = {}
    for e in events:
        if e.get("event_type") != "skill_execution":
            continue
        skill = e.get("skill_id", "")
        if not skill:
            continue
        meta = e.get("metadata", {})
        if isinstance(meta, dict):
            ctx_chars = meta.get("context_chars", 0)
            if ctx_chars > 0:
                skill_contexts.setdefault(skill, []).append(ctx_chars)

    worst_skill = ""
    worst_avg = 0
    for skill, ctx_list in skill_contexts.items():
        if ctx_list:
            avg = sum(ctx_list) / len(ctx_list)
            if avg > worst_avg:
                worst_avg = avg
                worst_skill = skill

    if worst_avg > 3000:
        return {
            "severity": "medium",
            "rule": "high_context_per_skill",
            "finding": f"{worst_skill} 平均注入上下文 {worst_avg:.0f} chars",
            "suggestion": "确认 PAGE_INTERFACE.yaml 存在且新鲜，或精简该 Skill 的上下文映射",
            "evidence": {"skill": worst_skill, "avg_context_chars": round(worst_avg, 0), "samples": len(skill_contexts.get(worst_skill, []))},
        }
    return None


def _check_low_cache_hit(events: list[dict]) -> Optional[dict]:
    """规则: file_cache 或 rag_cache 命中率 < 50%"""
    for e in events:
        if e.get("event_type") != "cache_summary":
            continue
        meta = e.get("metadata", {})
        if isinstance(meta, dict):
            fc = meta.get("file_cache", {})
            rc = meta.get("rag_cache", {})
            if isinstance(fc, dict) and fc.get("rate") is not None and fc["rate"] < 0.5:
                return {
                    "severity": "medium",
                    "rule": "low_cache_hit_rate",
                    "finding": f"文件缓存命中率仅 {fc['rate']*100:.0f}% ({fc.get('hits',0)}/{fc.get('hits',0)+fc.get('misses',0)})",
                    "suggestion": "检查模块/页面参数是否跨 Skill 变化过大，导致缓存键不匹配",
                    "evidence": fc,
                }
            if isinstance(rc, dict) and rc.get("rate") is not None and rc["rate"] < 0.5:
                return {
                    "severity": "medium",
                    "rule": "low_cache_hit_rate",
                    "finding": f"RAG 缓存命中率仅 {rc['rate']*100:.0f}% ({rc.get('hits',0)}/{rc.get('hits',0)+rc.get('misses',0)})",
                    "suggestion": "检查 RAG 查询是否因变量替换产生大量不同 query，考虑合并相似查询",
                    "evidence": rc,
                }
    return None


def _check_high_decision_ratio(events: list[dict]) -> Optional[dict]:
    """规则: agent_decision 事件 > 20% 总 LLM 调用"""
    llm_calls = 0
    decision_calls = 0
    for e in events:
        etype = e.get("event_type", "")
        if etype == "llm_call":
            llm_calls += 1
        elif etype == "agent_decision":
            decision_calls += 1

    if llm_calls > 0 and decision_calls / llm_calls > 0.2:
        return {
            "severity": "medium",
            "rule": "high_decision_ratio",
            "finding": f"agent_decision 占 LLM 调用的 {decision_calls / llm_calls * 100:.0f}% ({decision_calls}/{llm_calls})",
            "suggestion": "LLM Plan 调用过多，考虑在 plan() 中增加更多规则化快捷路径覆盖常见失败模式",
            "evidence": {"llm_calls": llm_calls, "decision_calls": decision_calls, "ratio": round(decision_calls / llm_calls, 2)},
        }
    return None


def _check_skill_retry_storm(events: list[dict]) -> Optional[dict]:
    """规则: 某 Skill 的 skill_execution 事件数 > 该 Skill 的预期次数 × 3"""
    skill_counts: dict[str, int] = {}
    for e in events:
        if e.get("event_type") == "skill_execution":
            skill = e.get("skill_id", "")
            if skill:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

    # automation-agent 有 5 个 Skill，每个预期执行 1 次
    base_counts = {
        "automation/tech-analysis": 1,
        "automation/auto-strategy": 1,
        "automation/page-object-generator": 1,
        "automation/test-script-generator": 1,
        "automation/code-consistency-checker": 1,
        "test-design/page-analysis": 1,
        "test-design/risk-modeling": 1,
        "test-design/testcase-design": 1,
    }

    for skill, count in skill_counts.items():
        base = base_counts.get(skill, 1)
        if count > base * 3:
            return {
                "severity": "high",
                "rule": "skill_retry_storm",
                "finding": f"{skill} 执行了 {count} 次（预期 {base} 次）",
                "suggestion": f"检查该 Skill 的失败模式，考虑增加 MAX_RETRIES 之前的规则化拦截或调整 Skill Prompt",
                "evidence": {"skill": skill, "count": count, "expected": base},
            }
    return None


def _check_stale_page_interface(events: list[dict]) -> Optional[dict]:
    """规则: preflight 中有 page_interface_fresh: false 的页面"""
    for e in events:
        if e.get("event_type") != "skill_execution":
            continue
        meta = e.get("metadata", {})
        if isinstance(meta, dict):
            sources = meta.get("sources", [])
            # 如果 source 中没有 "PAGE_INTERFACE" 字样但有 "PAGE_CONTEXT" 降级标记
            has_interface = any("PAGE_INTERFACE" in s.upper() for s in sources)
            has_fallback = any("降级" in s for s in sources)
            if has_fallback and not has_interface:
                return {
                    "severity": "low",
                    "rule": "stale_page_interface",
                    "finding": "检测到 PAGE_CONTEXT.md 降级消费（PAGE_INTERFACE.yaml 缺失或过期）",
                    "suggestion": "运行 page-analysis 重新生成 PAGE_INTERFACE.yaml",
                    "evidence": {"sources": sources},
                }
    return None


# ══════════════════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════════════════

def analyze_trace_data(days: int = 7) -> list[dict]:
    """
    P2: 自动成本优化建议 — 基于最近 N 天的追踪数据运行规则引擎。

    返回: 按 severity 排序的建议列表 (high → medium → low)
    """
    events = _load_events(days=days)
    if not events:
        return []

    # 预计算聚合数据
    aggregates = _compute_aggregates(events)
    total_cost = sum(
        e.get("token_cost_estimate", 0) or 0
        for e in events
        if e.get("event_type") in ("llm_call", "skill_execution", "agent_decision")
    )

    rules = [
        lambda: _check_expensive_agent(aggregates, total_cost),
        lambda: _check_skill_retry_storm(events),
        lambda: _check_high_context(events),
        lambda: _check_low_cache_hit(events),
        lambda: _check_high_decision_ratio(events),
        lambda: _check_stale_page_interface(events),
    ]

    suggestions = []
    for rule_fn in rules:
        try:
            result = rule_fn()
            if result:
                suggestions.append(result)
        except Exception:
            continue  # 单条规则失败不影响其他规则

    # 按严重度排序
    severity_order = {"high": 0, "medium": 1, "low": 2}
    suggestions.sort(key=lambda s: severity_order.get(s["severity"], 99))

    return suggestions


def _compute_aggregates(events: list[dict]) -> dict:
    """预聚合: by_agent 统计。"""
    by_agent: dict = {}
    for e in events:
        agent = e.get("agent_name", "") or "(unknown)"
        cost = e.get("token_cost_estimate", 0) or 0
        tokens_in = e.get("token_input", 0) or 0
        tokens_out = e.get("token_output", 0) or 0

        if agent not in by_agent:
            by_agent[agent] = {"calls": 0, "tokens_in": 0, "tokens_out": 0, "cost": 0.0}
        by_agent[agent]["calls"] += 1
        by_agent[agent]["tokens_in"] += tokens_in
        by_agent[agent]["tokens_out"] += tokens_out
        by_agent[agent]["cost"] += cost

    return {"by_agent": by_agent}
