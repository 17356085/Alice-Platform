"""
Failure Attributor — P1: 失败归因 Pipeline。

基于 Agent 评估方法论: "只知道成功率 70% 没用，需知道失败来自哪里。"

归因分类 (6 类):
  1. Prompt 问题: 指令模糊/冲突/缺失边界条件
  2. 工具描述问题: 参数说明不清/缺少示例
  3. Schema 问题: 必填字段缺失/格式不匹配
  4. 上下文污染: 无关日志/过期结论/错误 RAG 片段混入
  5. 检索问题: RAG 返回空/返回无关内容
  6. 环境/权限问题: 网络超时/权限不足/服务不可用

用法:
    from aitest.governance.failure_attributor import FailureAttributor, attribute_failure

    attributor = FailureAttributor()
    category = attributor.classify(observation, response_text)
    # → "prompt" | "tool_desc" | "schema" | "context_pollution" | "retrieval" | "env_permission"

    # AgentLoop 集成 (observe 检测到 fail 时自动调用):
    failure_category = attribute_failure(obs, response.content)
"""

import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timedelta

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
ARTIFACTS_DIR = GOVERNANCE / "artifacts"


@dataclass
class FailureRecord:
    """单次失败归因记录。"""
    timestamp: str
    run_id: str
    module: str
    skill_id: str
    status: str                    # "fail" | "wrong_failure"
    category: str                  # prompt | tool_desc | schema | context_pollution | retrieval | env_permission
    confidence: float              # 0-1
    evidence: list[str]            # 匹配到的关键词/模式
    summary: str = ""
    suggestion: str = ""


# ── 分类规则 ──────────────────────────────────────────────────────────
# 每个分类定义一组正则模式，按优先级从高到低排列
FAILURE_CATEGORY_RULES = {
    "env_permission": {
        "label": "环境/权限问题",
        "priority": 100,  # 最先匹配
        "patterns": [
            r"(?i)(timeout|timed? ?out|超时|connection (refused|reset|error)|网络(错误|超时|异常))",
            r"(?i)(permission denied|权限不足|unauthorized|forbidden|403|401|access denied|无权限|未授权)",
            r"(?i)(service (unavailable|error)|服务(不可用|异常|错误)|rate.?limit|限流)",
            r"(?i)(disk full|内存不足|out of memory|OOM|资源不足|quota exceeded)",
        ],
        "suggestion": "检查依赖服务状态、网络连接、权限配置。非模型问题。",
    },
    "context_pollution": {
        "label": "上下文污染",
        "priority": 90,
        "patterns": [
            r"(?i)(irrelevant (context|log|data)|无关(日志|上下文|数据))",
            r"(?i)(expired (conclusion|data|context)|过期(结论|数据|上下文))",
            r"(?i)(contradictory (context|information)|(上下文|信息)(冲突|矛盾))",
            r"(?i)(noise|噪音|干扰|hallucinat|幻觉|编造)",
        ],
        "suggestion": "检查 RAG 召回质量，清理过期上下文，减少无关信息注入。",
    },
    "retrieval": {
        "label": "检索问题",
        "priority": 80,
        "patterns": [
            r"(?i)(no (relevant |matching )?(results?|data|documents?|information)( found)?|无(相关)?(结果|数据|文档|信息))",
            r"(?i)(empty (result|response)|空(结果|响应|返回))",
            r"(?i)(RAG (returned|failed|empty)|检索(失败|为空|无结果))",
            r"(?i)(missing (context|document|reference)|缺少(上下文|文档|参考))",
        ],
        "suggestion": "检查知识库内容、检索策略、索引更新状态。",
    },
    "schema": {
        "label": "Schema 问题",
        "priority": 70,
        "patterns": [
            r"(?i)((missing|required) (field|parameter|argument|property)|(缺少|必需)(字段|参数|属性))",
            r"(?i)((invalid|wrong) (format|type|schema)|(格式|类型|schema)(不匹配|无效|错误))",
            r"(?i)(validation (error|failed)|校验(失败|错误)|不符合.*格式)",
            r"(?i)(expected .+ but got|期望.*但(收到|返回))",
        ],
        "suggestion": "检查输入/输出 Schema 定义，确保必填字段完整、格式正确。",
    },
    "tool_desc": {
        "label": "工具描述问题",
        "priority": 60,
        "patterns": [
            r"(?i)(tool (description|definition|doc) (unclear|missing|wrong)|工具(描述|定义|文档)(不清|缺失|错误))",
            r"(?i)(ambiguous (parameter|argument|description)|(参数|描述)模糊|歧义)",
            r"(?i)(missing (example|usage|instruction)|缺少(示例|用法|说明))",
            r"(?i)(wrong tool|选错工具|工具(选择)?错误|不(适合|适用)的工具)",
        ],
        "suggestion": "完善工具描述和参数说明，添加使用示例。",
    },
    "prompt": {
        "label": "Prompt 问题",
        "priority": 50,
        "patterns": [
            r"(?i)((instruction|prompt) (unclear|ambiguous|vague|confusing)|指令(不清|模糊|歧义))",
            r"(?i)((missing|conflicting) (instruction|requirement|constraint)|(缺少|冲突的)(指令|要求|约束))",
            r"(?i)(boundary (condition|case) (missing|undefined)|边界(条件|情况)(缺失|未定义))",
            r"(?i)((hallucinat|confabulat|fabricated?|made.?up|编造|虚构|捏造))",
        ],
        "suggestion": "检查 Prompt 模板，明确指令、边界条件和约束。",
    },
}


class FailureAttributor:
    """
    失败归因分类器。

    基于规则 (正则匹配) 做主要分类，可选用 LLM 辅助确认。

    用法:
        attributor = FailureAttributor()
        category = attributor.classify(observation, response_text)
    """

    def __init__(self, use_llm_confirm: bool = False):
        self.use_llm_confirm = use_llm_confirm

    def classify(self, observation, response_text: str = "") -> str:
        """
        对一次失败进行归因分类。

        参数:
            observation: Observation 对象 (来自 runner_state)
            response_text: LLM 响应文本 (可选，优先从 observation 中取)

        返回:
            分类字符串: prompt | tool_desc | schema | context_pollution | retrieval | env_permission | unknown
        """
        text = response_text or observation.raw_output_preview or ""
        error_summary = observation.summary or ""
        quality_issues = " ".join(observation.quality_issues)
        combined = f"{text} {error_summary} {quality_issues}"

        # 按优先级匹配规则
        sorted_rules = sorted(
            FAILURE_CATEGORY_RULES.items(),
            key=lambda x: x[1]["priority"],
            reverse=True,
        )

        for category, rule in sorted_rules:
            for pattern in rule["patterns"]:
                if re.search(pattern, combined):
                    return category

        # 启发式回退
        return self._fallback_classify(observation)

    def classify_with_evidence(self, observation,
                               response_text: str = "") -> FailureRecord:
        """
        归因分类 + 证据详情。

        返回 FailureRecord，包含匹配到的证据和建议。
        """
        text = response_text or observation.raw_output_preview or ""
        error_summary = observation.summary or ""
        quality_issues = " ".join(observation.quality_issues)
        combined = f"{text} {error_summary} {quality_issues}"

        sorted_rules = sorted(
            FAILURE_CATEGORY_RULES.items(),
            key=lambda x: x[1]["priority"],
            reverse=True,
        )

        evidence_list = []
        matched_category = "unknown"

        for category, rule in sorted_rules:
            for pattern in rule["patterns"]:
                match = re.search(pattern, combined)
                if match:
                    evidence_list.append(f"{rule['label']}: {match.group(0)[:80]}")
                    matched_category = category
                    break
            if matched_category != "unknown":
                break

        if matched_category == "unknown":
            matched_category = self._fallback_classify(observation)
            evidence_list.append("无明确模式匹配，使用启发式分类")

        rule = FAILURE_CATEGORY_RULES.get(matched_category, {})

        return FailureRecord(
            timestamp=observation.timestamp,
            run_id=observation.run_id,
            module="",
            skill_id=observation.skill_id,
            status=observation.status,
            category=matched_category,
            confidence=0.8 if evidence_list and "无明确模式匹配" not in evidence_list[0] else 0.3,
            evidence=evidence_list,
            summary=error_summary[:200],
            suggestion=rule.get("suggestion", "建议检查 trace 日志和审计报告。"),
        )

    def _fallback_classify(self, observation) -> str:
        """无规则匹配时的启发式回退。"""
        summary = (observation.summary or "").lower()
        quality = " ".join(observation.quality_issues).lower()

        # 有 artifacts_missing → 可能是工具或 Schema 问题
        if observation.artifacts_missing:
            for missing in observation.artifacts_missing:
                if "schema" in missing.lower() or "format" in missing.lower() or "字段" in missing:
                    return "schema"
            return "tool_desc"

        # LLM 响应过短 → 可能是检索或 prompt 问题
        if "过短" in summary or "short" in summary or len(observation.raw_output_preview) < 50:
            if any(kw in quality for kw in ["rag", "检索", "retriev", "知识库", "无结果"]):
                return "retrieval"
            return "prompt"

        # 超时 → 环境问题
        if "timeout" in summary or "超时" in summary or observation.latency_ms > 120_000:
            return "env_permission"

        return "unknown"

    def analyze_trends(self, module: str, days: int = 30) -> dict:
        """
        分析模块的失败归因趋势。

        从 trace 日志中提取失败事件并统计归因分布。
        """
        trace_log = GOVERNANCE / ".traces" / "trace_log.jsonl"
        if not trace_log.exists():
            return {"module": module, "period_days": days, "categories": {}, "total_failures": 0}

        cutoff = datetime.now() - timedelta(days=days)
        category_counts = {}
        total = 0

        try:
            with open(trace_log, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        evt = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    ts_str = evt.get("timestamp", "")
                    try:
                        ts = datetime.fromisoformat(ts_str)
                    except ValueError:
                        continue
                    if ts < cutoff:
                        continue
                    if module and module not in evt.get("run_id", ""):
                        continue

                    if evt.get("status") not in ("error", "fail", "partial"):
                        continue

                    # 使用规则分类
                    resp = evt.get("response_preview", "")
                    err = evt.get("error_message", "")
                    combined = f"{resp} {err}"

                    matched = "unknown"
                    sorted_rules = sorted(
                        FAILURE_CATEGORY_RULES.items(),
                        key=lambda x: x[1]["priority"],
                        reverse=True,
                    )
                    for cat, rule in sorted_rules:
                        if any(re.search(p, combined) for p in rule["patterns"]):
                            matched = cat
                            break

                    category_counts[matched] = category_counts.get(matched, 0) + 1
                    total += 1

        except OSError:
            pass

        # 转换为百分比
        distribution = {
            cat: {
                "count": cnt,
                "pct": round(cnt / max(total, 1) * 100, 1),
            }
            for cat, cnt in sorted(category_counts.items(),
                                   key=lambda x: x[1], reverse=True)
        }

        return {
            "module": module,
            "period_days": days,
            "total_failures": total,
            "categories": distribution,
            "primary_category": max(distribution, key=lambda k: distribution[k]["count"]) if distribution else "unknown",
        }


# ══════════════════════════════════════════════════════════════════════════
#  轻量级归因函数 — AgentLoop observe() 集成
# ══════════════════════════════════════════════════════════════════════════

def attribute_failure(observation, response_text: str = "") -> str:
    """
    AgentLoop 中使用的一行归因调用。

    参数:
        observation: Observation 对象
        response_text: LLM 响应文本

    返回:
        分类字符串
    """
    attributor = FailureAttributor()
    return attributor.classify(observation, response_text)


# ══════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python failure_attributor.py trends <module> [--days=<n>]")
        print("       python failure_attributor.py classify '<response_text>'")
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "trends":
        module_name = sys.argv[2] if len(sys.argv) > 2 else "system"
        days_val = 30
        for o in sys.argv[3:]:
            if o.startswith("--days="):
                days_val = int(o.split("=")[1])
        attributor = FailureAttributor()
        result = attributor.analyze_trends(module_name, days=days_val)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == "classify":
        text = " ".join(sys.argv[2:])
        from aitest.agents.runner_state import Observation
        obs = Observation(skill_id="test", status="fail", summary="",
                         raw_output_preview=text[:200])
        category = attribute_failure(obs, text)
        rule = FAILURE_CATEGORY_RULES.get(category, {})
        print(f"Category: {category} ({rule.get('label', 'unknown')})")
        print(f"Suggestion: {rule.get('suggestion', 'N/A')}")
