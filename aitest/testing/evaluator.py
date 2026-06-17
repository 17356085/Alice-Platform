"""
Eval Harness — P1-2: Skill 级评估框架。

功能:
  1. EvalRunner: 对任意 Skill 输入运行评估，按 criteria 评分
  2. EvalMetric: 从 trace JSONL 聚合每个 skill 的统计指标
  3. 确定性评分 (_score_response): 不依赖 LLM-as-judge，纯规则评分

用法:
    from aitest.testing.evaluator import EvalRunner, EvalMetric, _score_response

    runner = EvalRunner(provider="claude")
    result = runner.run("test-design/page-analysis", "分析 alarm-config 页面",
                        criteria={"min_length": 200, "contains": ["元素清单"]})
    print(result.passed, result.score)

    metrics = runner.metric_from_traces(skill_id="test-design/page-analysis")
    for m in metrics:
        print(f"{m.skill_id}: {m.success_rate:.0%} success, avg {m.avg_latency_ms}ms")

CLI:
    aitest eval run <skill_id> --input=<text> [--criteria=<json>]
    aitest eval agent <agent_name> --module=<m> [--page=<p>]
    aitest eval summary [--skill=<s>] [--run-id=<r>]
"""

import json
import re
import sys
import time
import uuid
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
TRACE_LOG = WORKSTUDY / "governance" / ".traces" / "trace_log.jsonl"


# ══════════════════════════════════════════════════════════════════════════
#  Data classes
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class EvalMetric:
    """单个 Skill 的聚合评估指标。"""
    skill_id: str
    total_runs: int = 0
    success_count: int = 0
    failure_count: int = 0
    partial_count: int = 0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_latency_ms: int = 0
    quality_issue_count: int = 0
    total_cost: float = 0.0

    @property
    def success_rate(self) -> float:
        return self.success_count / self.total_runs if self.total_runs else 0.0

    @property
    def avg_latency_ms(self) -> float:
        return round(self.total_latency_ms / self.total_runs) if self.total_runs else 0.0

    @property
    def avg_cost_per_run(self) -> float:
        return round(self.total_cost / self.total_runs, 6) if self.total_runs else 0.0

    @property
    def tokens_per_run(self) -> int:
        total = self.total_tokens_input + self.total_tokens_output
        return total // self.total_runs if self.total_runs else 0

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "total_runs": self.total_runs,
            "success_rate": round(self.success_rate, 3),
            "avg_latency_ms": int(self.avg_latency_ms),
            "avg_cost_per_run": self.avg_cost_per_run,
            "tokens_per_run": self.tokens_per_run,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
        }


@dataclass
class EvalRun:
    """单次 Skill 评估执行记录。"""
    run_id: str
    skill_id: str
    input_text: str
    criteria: dict = field(default_factory=dict)
    actual_output: str = ""
    passed: bool = False
    score: float = 0.0
    token_usage: dict = field(default_factory=dict)
    latency_ms: int = 0
    errors: list[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "skill_id": self.skill_id,
            "input_text": self.input_text[:200],
            "criteria": self.criteria,
            "actual_output_preview": self.actual_output[:300],
            "passed": self.passed,
            "score": self.score,
            "token_usage": self.token_usage,
            "latency_ms": self.latency_ms,
            "errors": self.errors,
            "timestamp": self.timestamp,
        }


# ══════════════════════════════════════════════════════════════════════════
#  Scoring function
# ══════════════════════════════════════════════════════════════════════════

def _score_response(output: str, criteria: dict) -> tuple:
    """
    确定性评分函数：对照 criteria 对 output 打分，零 LLM 依赖。

    支持的 criteria 键:
      - min_length: int        — 输出最少字符数
      - max_length: int        — 输出最多字符数
      - contains: list[str]    — 必须包含的关键词（不区分大小写）
      - not_contains: list[str] — 禁止出现的关键词
      - regex: str             — 必须匹配的正则表达式
      - structure: list[str]   — 必须包含的 Markdown section headers (如 "## 元素清单")

    返回:
        (score_0_to_1: float, errors: list[str])

    分数 = satisfied_checks / total_checks。无 checks 时默认 1.0。
    """
    errors = []
    if not output:
        return 0.0, ["Empty output"]

    satisfied = 0
    total_checks = 0

    min_len = criteria.get("min_length", 0)
    if min_len > 0:
        total_checks += 1
        if len(output) >= min_len:
            satisfied += 1
        else:
            errors.append(f"Output too short: {len(output)} < {min_len}")

    max_len = criteria.get("max_length")
    if max_len is not None and max_len > 0:
        total_checks += 1
        if len(output) <= max_len:
            satisfied += 1
        else:
            errors.append(f"Output too long: {len(output)} > {max_len}")

    for keyword in criteria.get("contains", []):
        total_checks += 1
        if keyword.lower() in output.lower():
            satisfied += 1
        else:
            errors.append(f"Missing keyword: '{keyword}'")

    for keyword in criteria.get("not_contains", []):
        total_checks += 1
        if keyword.lower() not in output.lower():
            satisfied += 1
        else:
            errors.append(f"Forbidden keyword found: '{keyword}'")

    for section in criteria.get("structure", []):
        total_checks += 1
        # 匹配 Markdown header: ## Section 或 ### Section
        if re.search(rf'^#{{2,3}}\s+{re.escape(section)}', output, re.MULTILINE):
            satisfied += 1
        else:
            errors.append(f"Missing section: '{section}'")

    if "regex" in criteria:
        total_checks += 1
        try:
            if re.search(criteria["regex"], output):
                satisfied += 1
            else:
                errors.append(f"Regex mismatch: {criteria['regex']}")
        except re.error as e:
            errors.append(f"Invalid regex: {e}")

    if total_checks == 0:
        return 1.0, []

    return round(satisfied / total_checks, 3), errors


# ══════════════════════════════════════════════════════════════════════════
#  EvalRunner
# ══════════════════════════════════════════════════════════════════════════

class EvalRunner:
    """
    Skill 评估运行器。

    用法:
        runner = EvalRunner(provider="claude")
        result = runner.run("automation/tech-analysis", "分析页面HTML...",
                           criteria={"min_length": 200, "contains": ["定位器"]})
        print(result.passed, result.score, result.errors)

        # 从已有 trace 数据聚合指标（无需重跑）
        metrics = runner.metric_from_traces(skill_id="automation/tech-analysis")
    """

    def __init__(self, provider: str = "claude"):
        self.provider = provider
        self.results: list[EvalRun] = []

    def run(
        self,
        skill_id: str,
        input_text: str,
        criteria: Optional[dict] = None,
        context_vars: Optional[dict] = None,
        variant: str = None,
    ) -> EvalRun:
        """
        执行单次 Skill 评估。

        参数:
            skill_id:     Skill ID (e.g. "test-design/page-analysis")
            input_text:   用户输入/任务描述
            criteria:     评分标准 dict（传给 _score_response）
            context_vars: 上下文变量 dict (module, page 等)
            variant:      可选 Prompt 变体 ID

        返回:
            EvalRun 记录
        """
        run_id = f"eval-{uuid.uuid4().hex[:12]}"
        criteria = criteria or {}
        start_ns = time.time()

        actual_output = ""
        token_usage = {}
        errors = []

        try:
            from aitest.agents.agent_runner import run_skill
            response = run_skill(
                skill_id=skill_id,
                user_input=input_text,
                provider=self.provider,
                context_vars=context_vars or {},
                variant=variant,
            )
            actual_output = response.content or ""
            token_usage = response.token_usage or {}
        except Exception as e:
            errors.append(f"Skill execution error: {str(e)[:200]}")
            actual_output = ""

        latency_ms = int((time.time() - start_ns) * 1000)
        score, crit_errors = _score_response(actual_output, criteria)
        errors.extend(crit_errors)
        passed = score >= 0.5 and not any(
            e.startswith("Skill execution error") for e in errors
        )

        eval_run = EvalRun(
            run_id=run_id,
            skill_id=skill_id,
            input_text=input_text[:200],
            criteria=criteria,
            actual_output=actual_output,
            passed=passed,
            score=score,
            token_usage=token_usage,
            latency_ms=latency_ms,
            errors=errors,
        )
        self.results.append(eval_run)
        return eval_run

    def run_agent(
        self,
        agent_name: str,
        module: str = "",
        page: str = "",
        max_steps: int = 12,
    ) -> dict:
        """
        执行完整 Agent 运行并收集所有 Skill 的评估指标。

        内部调用 AgentLoop 并聚合 Observation 数据。

        参数:
            agent_name: Agent 名称 (e.g. "automation-agent")
            module:     模块名
            page:       页面名
            max_steps:  最大步数

        返回:
            {
                "agent_name": "automation-agent",
                "success": True/False,
                "skill_results": [ {skill_id, status, tokens, ...}, ... ],
                "total_latency_ms": ...,
                "total_tokens": ...,
            }
        """
        from aitest.agents.agent_runner import AgentLoop

        agent = AgentLoop(
            agent_name=agent_name,
            provider=self.provider,
            module=module,
            page=page,
            max_steps=max_steps,
        )
        state = agent.run()

        skill_results = []
        for obs in state.observations:
            sr = {
                "skill_id": obs.skill_id,
                "status": obs.status,
                "quality_issues": obs.quality_issues,
                "artifact_count": len(obs.artifacts_found),
                "missing_count": len(obs.artifacts_missing),
            }
            if obs.token_usage:
                sr["token_usage"] = obs.token_usage
            if obs.latency_ms:
                sr["latency_ms"] = obs.latency_ms
            skill_results.append(sr)

        total_tokens = sum(
            sr.get("token_usage", {}).get("input", 0) +
            sr.get("token_usage", {}).get("output", 0)
            for sr in skill_results
        )
        total_latency = sum(
            sr.get("latency_ms", 0) for sr in skill_results
        )

        return {
            "agent_name": agent_name,
            "success": state.success,
            "termination_reason": state.termination_reason,
            "skill_results": skill_results,
            "total_latency_ms": total_latency,
            "total_tokens": total_tokens,
            "completed_skills": state.completed_skills,
            "failed_skills": state.failed_skills,
        }

    def metric_from_traces(
        self,
        skill_id: str = None,
        run_id: str = None,
    ) -> list[EvalMetric]:
        """
        从已有 trace JSONL 数据聚合指标（无需重跑 Skill）。

        参数:
            skill_id: 按 Skill ID 筛选（None = 全部）
            run_id:   按运行 ID 筛选（None = 全部）

        返回:
            EvalMetric 列表
        """
        if not TRACE_LOG.exists():
            return []

        metrics: dict[str, EvalMetric] = {}

        try:
            with open(TRACE_LOG, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                        sid = entry.get("skill_id", "")
                        if not sid:
                            continue
                        if skill_id and skill_id not in sid:
                            continue
                        if run_id and entry.get("run_id") != run_id:
                            continue

                        if sid not in metrics:
                            metrics[sid] = EvalMetric(skill_id=sid)

                        m = metrics[sid]
                        m.total_runs += 1
                        status = entry.get("status", "")
                        if status == "success":
                            m.success_count += 1
                        elif status == "error":
                            m.failure_count += 1
                        else:
                            m.partial_count += 1

                        m.total_tokens_input += entry.get("token_input", 0)
                        m.total_tokens_output += entry.get("token_output", 0)
                        m.total_latency_ms += entry.get("latency_ms", 0)
                        m.total_cost += entry.get("token_cost_estimate", 0)

                        # 从 response_preview 中粗略统计 quality issues
                        preview = entry.get("response_preview", "")
                        if "❌" in preview or "FAIL" in preview:
                            m.quality_issue_count += 1

                    except json.JSONDecodeError:
                        continue
        except Exception:
            return list(metrics.values())

        return sorted(metrics.values(), key=lambda m: -m.total_runs)

    def export_jsonl(self, path: str = None) -> str:
        """
        将所有 EvalRun 结果导出为 JSONL。

        参数:
            path: 输出路径（None = 自动生成到 governance/.traces/eval_results.jsonl）

        返回:
            实际写入路径
        """
        if path is None:
            path = str(WORKSTUDY / "governance" / ".traces" / "eval_results.jsonl")

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "a", encoding="utf-8") as f:
            for result in self.results:
                f.write(json.dumps(result.to_dict(), ensure_ascii=False) + "\n")

        return str(output_path)

    def summary(self) -> dict:
        """当前会话中所有评估结果的汇总。"""
        if not self.results:
            return {"total": 0, "passed": 0, "failed": 0, "avg_score": 0.0}

        passed = sum(1 for r in self.results if r.passed)
        avg_score = sum(r.score for r in self.results) / len(self.results)
        total_tokens = sum(
            r.token_usage.get("input", 0) + r.token_usage.get("output", 0)
            for r in self.results
        )

        by_skill = {}
        for r in self.results:
            sid = r.skill_id
            if sid not in by_skill:
                by_skill[sid] = {"count": 0, "passed": 0, "avg_score": 0.0}
            by_skill[sid]["count"] += 1
            if r.passed:
                by_skill[sid]["passed"] += 1
            by_skill[sid]["avg_score"] = round(
                (by_skill[sid]["avg_score"] * (by_skill[sid]["count"] - 1) + r.score) / by_skill[sid]["count"], 3
            )

        return {
            "total": len(self.results),
            "passed": passed,
            "failed": len(self.results) - passed,
            "pass_rate": round(passed / len(self.results), 3) if self.results else 0.0,
            "avg_score": round(avg_score, 3),
            "total_tokens": total_tokens,
            "by_skill": by_skill,
        }


# ══════════════════════════════════════════════════════════════════════════
#  P1-3: LLM-as-Judge — LLM 评估 + 组合评估器
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class JudgeResult:
    """单次 Judge 评估结果。"""
    dimensions: dict[str, float] = field(default_factory=dict)  # {"accuracy": 0.9, ...}
    overall: float = 0.0
    reasoning: str = ""
    passed: bool = False
    errors: list[str] = field(default_factory=list)


class LLMJudge:
    """
    P1-3: LLM-as-Judge — 用 LLM 评估 LLM 输出质量。

    用小模型（默认 haiku）降成本。支持多维度打分。

    用法:
        judge = LLMJudge(model="claude-haiku-4-5")
        result = judge.evaluate(
            output=actual_page_context,
            golden=expected_page_context,
            dimensions=["completeness", "accuracy", "actionability"],
        )
        print(result.overall, result.dimensions)
    """

    JUDGE_PROMPT = """You are an expert evaluator for AI-generated test documentation.
Evaluate the OUTPUT against the GOLDEN reference on the following dimensions:

{dimensions}

For each dimension, assign a score from 0.0 (worst) to 1.0 (perfect).
Then provide an overall score and brief reasoning.

OUTPUT:
{output}

GOLDEN REFERENCE:
{golden}

Respond in JSON format:
{{"dimensions": {{"dim1": 0.X, "dim2": 0.Y, ...}}, "overall": 0.Z, "reasoning": "..."}}"""

    def __init__(self, model: str = "claude-haiku-4-5", provider: str = "claude"):
        self.model = model
        self.provider = provider

    def evaluate(
        self,
        output: str,
        golden: str = "",
        dimensions: list[str] = None,
        rubric: str = "",
    ) -> JudgeResult:
        """
        用 LLM 评估输出质量。

        参数:
            output:     待评估的实际输出
            golden:     Golden reference (为空时仅检查输出本身质量)
            dimensions: 评估维度列表
            rubric:     自定义评分标准（叠加到默认 prompt）

        返回:
            JudgeResult
        """
        if dimensions is None:
            dimensions = ["completeness", "accuracy", "clarity"]

        dims_text = "\n".join(f"  - {d}" for d in dimensions)
        judge_prompt = self.JUDGE_PROMPT.format(
            dimensions=dims_text,
            output=output[:8000],   # 截断以控制 token
            golden=golden[:4000] if golden else "(no golden reference — evaluate standalone quality)",
        )
        if rubric:
            judge_prompt += f"\n\nADDITIONAL RUBRIC:\n{rubric}"

        try:
            from aitest.llm.provider import get_provider
            llm = get_provider(self.provider)
            response = llm.complete(
                system_prompt=judge_prompt,
                user_prompt="Evaluate the output. Respond with JSON only.",
                temperature=0.1,  # 低温度，更一致的评估
                max_tokens=1024,
            )
            content = response.content or "{}"

            # 提取 JSON (LLM 可能包裹在 ```json``` 中)
            import re as _re
            json_match = _re.search(r'\{[\s\S]*\}', content)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                parsed = json.loads(content)

            dims = parsed.get("dimensions", {})
            overall = float(parsed.get("overall", 0.5))
            reasoning = parsed.get("reasoning", "")

            return JudgeResult(
                dimensions=dims,
                overall=round(overall, 3),
                reasoning=reasoning[:500],
                passed=overall >= 0.6,
            )

        except Exception as e:
            return JudgeResult(
                overall=0.0,
                reasoning=f"LLM Judge error: {str(e)[:200]}",
                passed=False,
                errors=[str(e)[:200]],
            )

    def batch_evaluate(
        self,
        cases: list[dict],
        dimensions: list[str] = None,
    ) -> list[JudgeResult]:
        """
        批量评估多个 case。

        参数:
            cases: [{"output": "...", "golden": "...", "id": "..."}, ...]

        返回:
            [JudgeResult, ...]
        """
        results = []
        for case in cases:
            result = self.evaluate(
                output=case.get("output", ""),
                golden=case.get("golden", ""),
                dimensions=dimensions,
            )
            results.append(result)
        return results


class CompositeJudge:
    """
    P1-3: 组合评估器 — 组合 RuleJudge + LLMJudge + 权重求和。

    用法:
        comp = CompositeJudge(
            rule_weight=0.4,
            llm_weight=0.6,
            llm_judge=LLMJudge(),
        )
        result = comp.evaluate(output, golden, rule_criteria, llm_dimensions)
        print(result.overall, result.breakdown)
    """

    def __init__(
        self,
        rule_weight: float = 0.4,
        llm_weight: float = 0.6,
        llm_judge: LLMJudge = None,
    ):
        self.rule_weight = rule_weight
        self.llm_weight = llm_weight
        self.llm_judge = llm_judge or LLMJudge()

    def evaluate(
        self,
        output: str,
        golden: str = "",
        rule_criteria: dict = None,
        llm_dimensions: list[str] = None,
    ) -> JudgeResult:
        """
        组合评估: RuleJudge + LLMJudge 加权求和。

        返回 composite JudgeResult。
        """
        # 1. Rule Judge
        rule_score, rule_errors = _score_response(output, rule_criteria or {})

        # 2. LLM Judge
        llm_result = self.llm_judge.evaluate(
            output=output,
            golden=golden,
            dimensions=llm_dimensions,
        )

        # 3. 加权组合
        composite_overall = round(
            rule_score * self.rule_weight + llm_result.overall * self.llm_weight,
            3,
        )

        # 合并维度
        composite_dims = {"rule_score": round(rule_score, 3)}
        composite_dims.update(llm_result.dimensions)

        return JudgeResult(
            dimensions=composite_dims,
            overall=composite_overall,
            reasoning=f"Rule({rule_score:.2f}×{self.rule_weight}) + LLM({llm_result.overall:.2f}×{self.llm_weight})"
                      f" = {composite_overall:.2f}. {llm_result.reasoning}",
            passed=composite_overall >= 0.6,
            errors=rule_errors + llm_result.errors,
        )
