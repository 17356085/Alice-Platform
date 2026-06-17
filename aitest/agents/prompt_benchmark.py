"""
Prompt Benchmark — P2-1: 多版本/多变体对比矩阵 + 自动推荐最优版本。

功能:
  1. 同一数据集跑多个 Prompt 版本 → 对比矩阵
  2. 自动推荐最优版本 (基于质量/成本/延迟综合评分)
  3. 版本对比报告

用法:
    from aitest.agents.prompt_benchmark import PromptBenchmark

    bench = PromptBenchmark(provider="claude")
    # 对比两个版本
    result = bench.compare(
        skill_id="test-design/page-analysis",
        versions=["1.0", "2.0"],
        dataset_tag="smoke",
    )
    print(result["winner"], result["matrix"])

CLI:
    aitest benchmark prompt <skill_id> --versions=v1.0,v2.0 [--tag=smoke] [--provider=claude]
"""

import json
import time
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
BENCH_DIR = GOVERNANCE / "artifacts" / "benchmarks"
TRACE_LOG = GOVERNANCE / ".traces" / "trace_log.jsonl"


@dataclass
class VersionScore:
    """单个版本在某用例上的评估分数。"""
    version: str
    case_id: str
    rule_score: float = 0.0
    llm_score: float = 0.0
    composite_score: float = 0.0
    tokens: int = 0
    latency_ms: int = 0
    cost: float = 0.0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "case_id": self.case_id,
            "rule_score": self.rule_score,
            "llm_score": self.llm_score,
            "composite_score": self.composite_score,
            "tokens": self.tokens,
            "latency_ms": self.latency_ms,
            "cost": self.cost,
            "errors": self.errors,
        }


class PromptBenchmark:
    """
    P2-1: Prompt 版本对比基准测试。

    用法:
        bench = PromptBenchmark(provider="claude")
        result = bench.compare(
            skill_id="test-design/page-analysis",
            versions=["1.0", "2.0"],
            dataset_tag="smoke",
        )
    """

    def __init__(self, provider: str = "claude"):
        self.provider = provider
        self.scores: list[VersionScore] = []

    def compare(
        self,
        skill_id: str,
        versions: list[str],
        dataset_tag: str = "smoke",
        judge_model: str = "claude-haiku-4-5",
    ) -> dict:
        """
        对比同一 Skill 的多个版本在同一数据集上的表现。

        参数:
            skill_id:     Skill ID
            versions:     要对比的版本号列表
            dataset_tag:  数据集标签
            judge_model:  LLM Judge 使用的模型

        返回:
            {
                "skill_id": "test-design/page-analysis",
                "versions": ["1.0", "2.0"],
                "matrix": [VersionScore, ...],  # 版本×用例 矩阵
                "winner": "2.0",
                "summary": {...},
            }
        """
        # 加载测试用例
        cases = self._load_dataset(skill_id, dataset_tag)
        if not cases:
            return self._empty_result(skill_id, versions, "无匹配数据集")

        from aitest.testing.evaluator import EvalRunner, LLMJudge, CompositeJudge
        from aitest.testing.regression import _section_similarity

        llm_judge = LLMJudge(model=judge_model, provider=self.provider)
        comp_judge = CompositeJudge(rule_weight=0.4, llm_weight=0.6, llm_judge=llm_judge)

        self.scores = []

        for version in versions:
            runner = EvalRunner(provider=self.provider)
            for case in cases:
                case_id = case.get("id", "?")
                criteria = case.get("expected", {})
                input_text = case.get("input", "")
                golden = case.get("golden_output", "")

                start_ns = time.time()
                try:
                    eval_run = runner.run(
                        skill_id=f"{skill_id}@{version}",
                        input_text=input_text,
                        criteria=criteria,
                    )
                    latency_ms = int((time.time() - start_ns) * 1000)
                    tokens = (eval_run.token_usage.get("input", 0) +
                              eval_run.token_usage.get("output", 0))
                    cost_est = self._estimate_cost(tokens)

                    # 如果有 golden，用 CompositeJudge
                    if golden:
                        comp_result = comp_judge.evaluate(
                            output=eval_run.actual_output,
                            golden=golden,
                            rule_criteria=criteria,
                            llm_dimensions=["accuracy", "completeness", "actionability"],
                        )
                        llm_score = comp_result.overall
                    else:
                        llm_score = eval_run.score

                    self.scores.append(VersionScore(
                        version=version,
                        case_id=case_id,
                        rule_score=eval_run.score,
                        llm_score=round(llm_score, 3),
                        composite_score=round(eval_run.score * 0.4 + llm_score * 0.6, 3),
                        tokens=tokens,
                        latency_ms=latency_ms or eval_run.latency_ms,
                        cost=cost_est,
                        errors=eval_run.errors,
                    ))
                except Exception as e:
                    self.scores.append(VersionScore(
                        version=version,
                        case_id=case_id,
                        errors=[str(e)[:200]],
                    ))

        # 构建对比矩阵
        matrix = [s.to_dict() for s in self.scores]

        # 按版本聚合
        version_agg = {}
        for s in self.scores:
            if s.version not in version_agg:
                version_agg[s.version] = {
                    "total_cases": 0,
                    "total_score": 0.0,
                    "total_tokens": 0,
                    "total_latency": 0,
                    "total_cost": 0.0,
                    "errors": 0,
                }
            va = version_agg[s.version]
            va["total_cases"] += 1
            va["total_score"] += s.composite_score
            va["total_tokens"] += s.tokens
            va["total_latency"] += s.latency_ms
            va["total_cost"] += s.cost
            if s.errors:
                va["errors"] += 1

        # 计算综合得分: quality(60%) + efficiency(25%) + cost(15%)
        for ver, agg in version_agg.items():
            n = max(agg["total_cases"], 1)
            quality = agg["total_score"] / n  # 0-1
            # efficiency: 归一化 (越低越好 → 归一化到 0-1)
            max_tokens = max(v["total_tokens"] for v in version_agg.values()) or 1
            efficiency = 1.0 - (agg["total_tokens"] / n) / (max_tokens / n + 1)
            # cost: 归一化
            max_cost = max(v["total_cost"] for v in version_agg.values()) or 0.001
            cost_score = 1.0 - (agg["total_cost"] / max_cost + 0.001)
            agg["final_score"] = round(quality * 0.6 + efficiency * 0.25 + cost_score * 0.15, 3)
            agg["avg_composite"] = round(agg["total_score"] / n, 3)
            agg["avg_tokens"] = round(agg["total_tokens"] / n)
            agg["avg_latency_ms"] = round(agg["total_latency"] / n)
            agg["avg_cost"] = round(agg["total_cost"] / n, 6)

        # 选出 winner
        sorted_versions = sorted(version_agg.items(), key=lambda x: -x[1]["final_score"])
        winner = sorted_versions[0][0] if sorted_versions else "?"

        summary = {}
        for ver, agg in version_agg.items():
            summary[ver] = {
                "avg_composite_score": agg["avg_composite"],
                "avg_tokens": agg["avg_tokens"],
                "avg_latency_ms": agg["avg_latency_ms"],
                "avg_cost": agg["avg_cost"],
                "final_score": agg["final_score"],
                "errors": agg["errors"],
            }

        result = {
            "skill_id": skill_id,
            "versions": versions,
            "dataset_tag": dataset_tag,
            "bench_time": datetime.now().isoformat(),
            "winner": winner,
            "matrix": matrix,
            "summary": summary,
            "recommendation": (
                f"推荐使用 {skill_id}@{winner} "
                f"(综合得分 {summary[winner]['final_score']:.3f}, "
                f"质量 {summary[winner]['avg_composite_score']:.3f}, "
                f"平均 {summary[winner]['avg_tokens']} tokens/call)"
            ),
        }

        self._write_report(result)
        return result

    def quick_compare(
        self,
        skill_id: str,
        versions: list[str],
        input_text: str,
        criteria: dict = None,
    ) -> dict:
        """
        快速对比 — 单输入文本，不需要数据集。

        返回每个版本的 (score, tokens, latency, cost) 对比。
        """
        from aitest.testing.evaluator import EvalRunner

        results = {}
        for version in versions:
            runner = EvalRunner(provider=self.provider)
            start = time.time()
            try:
                eval_run = runner.run(
                    skill_id=f"{skill_id}@{version}",
                    input_text=input_text,
                    criteria=criteria or {},
                )
                latency = int((time.time() - start) * 1000)
                tokens = (eval_run.token_usage.get("input", 0) +
                          eval_run.token_usage.get("output", 0))
                results[version] = {
                    "score": eval_run.score,
                    "tokens": tokens,
                    "latency_ms": latency,
                    "cost": self._estimate_cost(tokens),
                    "errors": eval_run.errors,
                }
            except Exception as e:
                results[version] = {"error": str(e)[:200]}

        return results

    # ── 辅助 ──────────────────────────────────────────────────────────

    def _load_dataset(self, skill_id: str, tag: str) -> list[dict]:
        """加载测试数据集。"""
        from aitest.testing.regression import RegressionRunner
        try:
            r = RegressionRunner(provider=self.provider)
            cases = r.load_cases(tag=tag, skill_id=skill_id)
            # 尝试加载 golden outputs
            enriched = []
            for case in cases:
                bp = r._baseline_path(case)
                golden = ""
                if bp.exists():
                    golden = bp.read_text(encoding="utf-8")
                case["golden_output"] = golden
                enriched.append(case)
            return enriched
        except Exception:
            return []

    def _estimate_cost(self, tokens: int) -> float:
        """基于 token 数估算成本 (sonnet 价格)。"""
        return round(tokens / 1_000_000 * 3.0, 6)  # $3/M input, approximate

    def _empty_result(self, skill_id: str, versions: list[str], reason: str) -> dict:
        return {
            "skill_id": skill_id,
            "versions": versions,
            "bench_time": datetime.now().isoformat(),
            "winner": None,
            "matrix": [],
            "summary": {},
            "recommendation": f"无法执行: {reason}。请先创建回归测试用例。",
        }

    def _write_report(self, report: dict):
        """持久化基准测试报告。"""
        BENCH_DIR.mkdir(parents=True, exist_ok=True)
        skill_slug = report["skill_id"].replace("/", "-")
        path = BENCH_DIR / f"prompt-bench-{skill_slug}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        try:
            path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass


# ══════════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python prompt_benchmark.py <skill_id> --versions=v1,v2 [--tag=smoke] [--quick] [--input=<text>]")
        sys.exit(0)

    skill = sys.argv[1]
    versions = ["1.0"]
    tag = "smoke"
    quick_mode = False
    quick_input = ""

    for arg in sys.argv[2:]:
        if arg.startswith("--versions="):
            versions = arg.split("=")[1].split(",")
        elif arg.startswith("--tag="):
            tag = arg.split("=")[1]
        elif arg == "--quick":
            quick_mode = True
        elif arg.startswith("--input="):
            quick_input = arg.split("=", 1)[1]

    bench = PromptBenchmark()

    if quick_mode and quick_input:
        result = bench.quick_compare(skill, versions, quick_input)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = bench.compare(skill, versions, dataset_tag=tag)
        print(f"\nSkill: {result['skill_id']}")
        print(f"Winner: {result['winner']}")
        print(f"Recommendation: {result['recommendation']}")
        print(f"\nSummary:")
        for ver, stats in result["summary"].items():
            print(f"  {ver}: composite={stats['avg_composite_score']:.3f}, "
                  f"tokens={stats['avg_tokens']}, cost=${stats['avg_cost']:.4f}, "
                  f"final={stats['final_score']:.3f}")
