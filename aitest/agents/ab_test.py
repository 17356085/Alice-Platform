"""
A/B Test Runner — P1-3: Prompt 变体对比测试。

对同一 Skill 的两种 Prompt 变体执行相同输入，比较输出质量和成本。

用法:
    from aitest.agents.ab_test import ABTestRunner

    runner = ABTestRunner(provider="claude")
    result = runner.compare(
        "test-design/page-analysis",
        variant_a="page-analysis-v1",
        variant_b="page-analysis-v2",
        test_input="分析 equipment/alarm-config 页面",
        criteria={"min_length": 200, "contains": ["元素清单"]},
    )
    print(result.winner, result.score_diff, result.cost_diff)

CLI:
    aitest ab list [<skill_id>]
    aitest ab compare <skill_id> --a=<v1> --b=<v2> --input=<text> --criteria=<json>
    aitest ab batch <skill_id> --a=<v1> --b=<v2> --cases=<yaml-file>
"""

import json
import sys
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent


@dataclass
class ABTestResult:
    """单次 A/B 对比结果。"""
    skill_id: str
    variant_a: str
    variant_b: str
    test_input: str
    run_a: dict = field(default_factory=dict)   # EvalRun.to_dict()
    run_b: dict = field(default_factory=dict)
    winner: str = "tie"                          # "A" | "B" | "tie"
    score_diff: float = 0.0                      # A.score - B.score
    cost_diff: float = 0.0                       # A.cost - B.cost ($)
    latency_diff_ms: int = 0                     # A.latency - B.latency

    def to_dict(self) -> dict:
        return {
            "skill_id": self.skill_id,
            "variant_a": self.variant_a,
            "variant_b": self.variant_b,
            "test_input": self.test_input[:200],
            "winner": self.winner,
            "score_diff": self.score_diff,
            "cost_diff": round(self.cost_diff, 6),
            "latency_diff_ms": self.latency_diff_ms,
            "run_a_score": self.run_a.get("score", 0),
            "run_b_score": self.run_b.get("score", 0),
            "run_a_errors": self.run_a.get("errors", []),
            "run_b_errors": self.run_b.get("errors", []),
        }


class ABTestRunner:
    """
    A/B 测试运行器：在两个 Prompt 变体上执行相同输入，对比评分。

    用法:
        runner = ABTestRunner(provider="claude", n_runs=3)
        result = runner.compare(
            "test-design/page-analysis",
            variant_a="page-analysis-v1",
            variant_b="page-analysis-v2",
            test_input="分析 equipment/alarm-config 页面",
            criteria={"min_length": 200, "contains": ["元素清单"]},
        )
    """

    def __init__(self, provider: str = "claude", n_runs: int = 1):
        """
        参数:
            provider: LLM Provider
            n_runs:   每个变体的运行次数（>1 用于统计对比）
        """
        self.provider = provider
        self.n_runs = max(1, n_runs)
        self.results: list[ABTestResult] = []

    def compare(
        self,
        skill_id: str,
        variant_a: str,
        variant_b: str,
        test_input: str,
        criteria: Optional[dict] = None,
    ) -> ABTestResult:
        """
        对比两个变体在单个输入上的表现。

        参数:
            skill_id:   Skill ID
            variant_a:  变体 A ID
            variant_b:  变体 B ID
            test_input: 测试输入
            criteria:   评分标准

        返回:
            ABTestResult
        """
        from aitest.testing.evaluator import EvalRunner

        runner = EvalRunner(provider=self.provider)

        # 验证变体存在
        from aitest.llm.skill_loader import list_variants, load_variant
        available = [v.variant_id for v in list_variants(skill_id)]
        if variant_a not in available:
            raise ValueError(f"Variant '{variant_a}' not found. Available: {available}")
        if variant_b not in available:
            raise ValueError(f"Variant '{variant_b}' not found. Available: {available}")

        # 验证变体内容可加载
        content_a = load_variant(skill_id, variant_a)
        content_b = load_variant(skill_id, variant_b)

        # 运行变体 A（通过 monkey-patch load_skill 注入变体内容）
        runs_a = []
        runs_b = []

        for _ in range(self.n_runs):
            run_a = runner.run(
                skill_id=skill_id,
                input_text=test_input,
                criteria=criteria or {},
                variant=variant_a,
            )
            runs_a.append(run_a)

            run_b = runner.run(
                skill_id=skill_id,
                input_text=test_input,
                criteria=criteria or {},
                variant=variant_b,
            )
            runs_b.append(run_b)

        # 聚合多次运行的结果
        avg_score_a = sum(r.score for r in runs_a) / len(runs_a)
        avg_score_b = sum(r.score for r in runs_b) / len(runs_b)
        avg_latency_a = sum(r.latency_ms for r in runs_a) / len(runs_a)
        avg_latency_b = sum(r.latency_ms for r in runs_b) / len(runs_b)

        cost_a = sum(
            r.token_usage.get("input", 0) + r.token_usage.get("output", 0)
            for r in runs_a
        ) / len(runs_a)
        cost_b = sum(
            r.token_usage.get("input", 0) + r.token_usage.get("output", 0)
            for r in runs_b
        ) / len(runs_b)

        score_diff = round(avg_score_a - avg_score_b, 3)
        if abs(score_diff) < 0.05:
            winner = "tie"
        elif score_diff > 0:
            winner = "A"
        else:
            winner = "B"

        result = ABTestResult(
            skill_id=skill_id,
            variant_a=variant_a,
            variant_b=variant_b,
            test_input=test_input,
            run_a=runs_a[0].to_dict(),
            run_b=runs_b[0].to_dict(),
            winner=winner,
            score_diff=score_diff,
            cost_diff=round(cost_a - cost_b, 6),
            latency_diff_ms=int(avg_latency_a - avg_latency_b),
        )
        self.results.append(result)
        return result

    def batch_compare(
        self,
        skill_id: str,
        variant_a: str,
        variant_b: str,
        test_cases: list[tuple],
    ) -> list[ABTestResult]:
        """
        批量对比：多个测试用例上的 A/B 测试。

        参数:
            skill_id:   Skill ID
            variant_a:  变体 A ID
            variant_b:  变体 B ID
            test_cases: [(input_text, criteria_dict), ...]

        返回:
            ABTestResult 列表
        """
        results = []
        for i, (test_input, criteria) in enumerate(test_cases):
            print(f"  [{i+1}/{len(test_cases)}] Testing: {test_input[:60]}...")
            try:
                result = self.compare(
                    skill_id=skill_id,
                    variant_a=variant_a,
                    variant_b=variant_b,
                    test_input=test_input,
                    criteria=criteria,
                )
                results.append(result)
            except Exception as e:
                print(f"    Error: {e}")
        return results

    def load_cases_from_yaml(self, yaml_path: str) -> list[tuple]:
        """
        从 YAML 文件加载测试用例。

        期望格式:
            test_cases:
              - input: "..."
                criteria:
                  min_length: 200
                  contains: ["..."]
        """
        import yaml
        with open(yaml_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        cases = []
        for case in data.get("test_cases", []):
            input_text = case.get("input", "")
            criteria = case.get("criteria", {})
            cases.append((input_text, criteria))
        return cases

    def summary(self) -> dict:
        """聚合所有 A/B 结果。"""
        if not self.results:
            return {"total": 0}

        a_wins = sum(1 for r in self.results if r.winner == "A")
        b_wins = sum(1 for r in self.results if r.winner == "B")
        ties = sum(1 for r in self.results if r.winner == "tie")

        avg_score_diff = sum(r.score_diff for r in self.results) / len(self.results)

        return {
            "total": len(self.results),
            "a_wins": a_wins,
            "b_wins": b_wins,
            "ties": ties,
            "avg_score_diff": round(avg_score_diff, 3),
            "recommendation": (
                f"Variant B wins ({b_wins}/{len(self.results)})" if b_wins > a_wins
                else f"Variant A wins ({a_wins}/{len(self.results)})" if a_wins > b_wins
                else "Tie — no significant difference"
            ),
        }
