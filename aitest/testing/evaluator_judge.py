"""Evaluator Judge — LLM-based evaluation judges.

Extracted from evaluator.py for single-responsibility.
"""

import json
import logging
from dataclasses import dataclass, field
from collections.abc import Callable
from typing import Optional

logger = logging.getLogger(__name__)

_provider_factory: Callable | None = None


def register_provider_factory(factory: Callable) -> None:
    """Inject the LLM provider factory from the package composition root."""
    global _provider_factory
    _provider_factory = factory


def _get_provider(provider: str):
    if _provider_factory is None:
        raise RuntimeError("LLM judge provider factory is not registered")
    return _provider_factory(provider)


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
            llm = _get_provider(self.provider)
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


# ══════════════════════════════════════════════════════════════════════════
#  P1 (Phase 4): 正确失败 vs 错误失败分类
# ══════════════════════════════════════════════════════════════════════════

# 正确失败的标记: Agent 诚实说明原因/追问/停止
CORRECT_FAILURE_MARKERS = [
    r"(?i)(无法|不能|无法完成|cannot|unable to|not possible)",
    r"(?i)(缺少(必要)?信息|需要更多|need more|missing (required |necessary )?information)",
    r"(?i)(请提供|请补充|please provide|需要.*参数|requires? .* parameter)",
    r"(?i)(超出.*(范围|能力)|beyond.*(scope|capability)|not supported)",
    r"(?i)(建议|推荐|suggest|recommend|alternatively)",
    r"(?i)(当前.*限制|current limitation|目前仅|currently only)",
    r"(?i)(抱歉|遗憾|sorry|unfortunately)",
]

# 错误失败的标记: 编造/伪造/给出不可验证的结论
WRONG_FAILURE_MARKERS = [
    r"(?i)(已经(完成|执行|处理|删除|修改)|(has been|was) (completed|executed|processed|deleted|modified))",
    r"(?i)(结果(如下|为|是)|the (result|answer) is|结果是)",
    r"(?i)(确认|验证通过|confirmed|verified|validated).*(但|but|however)",
    r"(?i)(确认|verified|validated).*(已生效|已完成|成功|completed|success|passed|updated)",
    r"(?i)(数据(显示|表明)|data (shows|indicates|suggests)).*(?=.*(但|but|however))",
    r"(?i)(fabricat|hallucinat|confabulat|编造|虚构|捏造)",
]



def classify_failure_type(output: str, error_summary: str = "") -> str:
    """
    P1 (Phase 4): 区分正确失败 vs 错误失败。

    正确失败 (correct_failure): 任务未完成但诚实说明原因
    错误失败 (wrong_failure): 任务未完成且给出错误/编造结论

    返回: "correct_failure" | "wrong_failure"
    """
    combined = f"{output} {error_summary}"

    # 先检查错误失败标记（更危险）
    wrong_hits = 0
    for pattern in WRONG_FAILURE_MARKERS:
        if re.search(pattern, combined):
            wrong_hits += 1

    # 检查正确失败标记
    correct_hits = 0
    for pattern in CORRECT_FAILURE_MARKERS:
        if re.search(pattern, combined):
            correct_hits += 1

    # 决策逻辑
    if wrong_hits > correct_hits:
        return "wrong_failure"
    elif correct_hits > 0:
        return "correct_failure"
    elif wrong_hits > 0:
        return "wrong_failure"

    # 启发式: 输出包含具体数据/结论但缺少证据链 → wrong
    has_concrete_data = bool(re.search(
        r'(?i)(\d{2,}.*(条|个|项|次|records?|items?|results?|entries?))|'
        r'(ID[:\s]+\w+|编号[:\s]+\w+)',
        output
    ))
    has_evidence = bool(re.search(
        r'(?i)(根据|依据|来源|引用|based on|according to|referenc|source)',
        output
    ))
    if has_concrete_data and not has_evidence:
        return "wrong_failure"

    return "correct_failure"  # 默认: 疑罪从无


# ══════════════════════════════════════════════════════════════════════════
#  P2 (Phase 7): AdversarialJudge — 多模型对抗评估
# ══════════════════════════════════════════════════════════════════════════

@dataclass

class AdversarialResult:
    """对抗评估的综合结果。"""
    passed: bool                     # 是否通过（多数模型确认）
    confirmed_by: int                # 确认的模型数
    refuted_by: int                  # 反驳的模型数
    total_judges: int                # 总 judge 数
    scores: dict[str, float]         # {model_name: score}
    refutations: list[str]           # 每个模型的反驳理由
    overall_score: float             # 平均分
    verdict: str                     # "confirmed" | "refuted" | "split"
    summary: str = ""



class AdversarialJudge:
    """
    P2 (Phase 7): 多模型对抗评估器。

    从单模型 (haiku) 改为多模型 panel，每个 judge 同时给出:
      - 评分
      - 是否 refute (反驳)

    综合规则: ≥2/3 确认 → 通过，≥2/3 refute → 驳回。

    用法:
        judge = AdversarialJudge(
            models=["claude-haiku-4-5", "claude-sonnet-4-6"],
        )
        result = judge.evaluate(output, golden, dimensions=["accuracy", "completeness"])
        print(result.verdict, result.overall_score)
    """

    ADVERSARIAL_PROMPT = """You are an adversarial evaluator. Your job is to:
1. Score the OUTPUT against the GOLDEN reference on each dimension (0.0-1.0)
2. Determine whether the output should be REFUTED (contains false claims, fabrications, or critical errors)

{dimensions}

OUTPUT:
{output}

GOLDEN REFERENCE:
{golden}

CRITICAL: If the output contains fabricated data, unsupported claims, or assertions
that contradict the golden reference, you MUST set refute=true and explain why.

Respond in JSON:
{{"dimensions": {{"dim1": 0.X, ...}}, "overall": 0.Z, "refute": true|false, "refute_reason": "..."}}"""

    def __init__(self, models: list[str] = None, provider: str = "claude"):
        """
        参数:
            models: 评估模型列表 (默认 haiku + sonnet)
            provider: LLM provider
        """
        self.models = models or ["claude-haiku-4-5", "claude-sonnet-4-6"]
        self.provider = provider

    def evaluate(
        self,
        output: str,
        golden: str = "",
        dimensions: list[str] = None,
    ) -> AdversarialResult:
        """
        多模型对抗评估。

        参数:
            output:     待评估输出
            golden:     Golden reference
            dimensions: 评估维度列表

        返回:
            AdversarialResult
        """
        if dimensions is None:
            dimensions = ["accuracy", "completeness", "clarity"]

        dims_text = "\n".join(f"  - {d}" for d in dimensions)

        scores = {}
        refutations = []
        confirmed = 0
        refuted = 0

        for model in self.models:
            try:
                result = self._judge_with_model(
                    model=model,
                    output=output,
                    golden=golden,
                    dims_text=dims_text,
                )
                scores[model] = result.get("overall", 0.0)
                is_refute = result.get("refute", False)
                if is_refute:
                    refuted += 1
                    refutations.append(
                        f"[{model}] REFUTED: {result.get('refute_reason', 'no reason given')[:200]}"
                    )
                else:
                    confirmed += 1
            except Exception as e:
                scores[model] = 0.0
                refutations.append(f"[{model}] ERROR: {str(e)[:100]}")
                refuted += 1

        total = len(self.models)
        overall = sum(scores.values()) / max(len(scores), 1)

        # 综合裁决
        if confirmed >= total * 2 / 3:
            verdict = "confirmed"
            passed = True
        elif refuted >= total * 2 / 3:
            verdict = "refuted"
            passed = False
        else:
            verdict = "split"
            passed = overall >= 0.5

        return AdversarialResult(
            passed=passed,
            confirmed_by=confirmed,
            refuted_by=refuted,
            total_judges=total,
            scores=scores,
            refutations=refutations,
            overall_score=round(overall, 3),
            verdict=verdict,
            summary=f"{verdict}: {confirmed}/{total} confirmed, {refuted}/{total} refuted",
        )

    def _judge_with_model(self, model: str, output: str, golden: str,
                          dims_text: str) -> dict:
        """用指定模型执行单次判断。"""
        prompt = self.ADVERSARIAL_PROMPT.format(
            dimensions=dims_text,
            output=output[:8000],
            golden=golden[:4000] if golden else "(no golden reference)",
        )

        llm = _get_provider(self.provider)
        response = llm.complete(
            system_prompt=prompt,
            user_prompt="Evaluate and determine if the output should be refuted. Respond with JSON only.",
            temperature=0.1,
            max_tokens=1024,
            model=model,
        )
        content = response.content or "{}"

        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group())
        return json.loads(content)
