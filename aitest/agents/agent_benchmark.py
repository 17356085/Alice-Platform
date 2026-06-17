"""
Agent Benchmark — P2-2: 端到端 Agent 任务基准测试。

三维评估: 成功率 / 效率 / 成本

功能:
  1. 定义标准 Agent 任务
  2. 多次运行 → 统计成功率、平均耗时、token 消耗
  3. 三维评分: Quality × Efficiency × Cost

用法:
    from aitest.agents.agent_benchmark import AgentBenchmark

    bench = AgentBenchmark(provider="claude")
    result = bench.run(
        agent_name="automation-agent",
        task={"module": "equipment", "page": "alarm-config"},
        repeat=3,
    )
    print(result["success_rate"], result["three_d_score"])

CLI:
    aitest benchmark agent <agent_name> --module=<m> --page=<p> [--repeat=3]
"""

import json
import time
import math
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
GOVERNANCE = WORKSTUDY / "governance"
BENCH_DIR = GOVERNANCE / "artifacts" / "benchmarks"
TRACE_LOG = GOVERNANCE / ".traces" / "trace_log.jsonl"


@dataclass
class AgentRunResult:
    """单次 Agent 运行结果。"""
    run_index: int
    success: bool
    termination_reason: str = ""
    skills_completed: int = 0
    skills_failed: int = 0
    total_tokens: int = 0
    total_latency_ms: int = 0
    total_cost: float = 0.0
    artifacts_generated: int = 0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_index": self.run_index,
            "success": self.success,
            "termination_reason": self.termination_reason,
            "skills_completed": self.skills_completed,
            "skills_failed": self.skills_failed,
            "total_tokens": self.total_tokens,
            "total_latency_ms": self.total_latency_ms,
            "total_cost": self.total_cost,
            "artifacts_generated": self.artifacts_generated,
            "errors": self.errors,
        }


class AgentBenchmark:
    """
    P2-2: Agent 端到端基准测试。

    用法:
        bench = AgentBenchmark(provider="claude")
        result = bench.run(
            agent_name="automation-agent",
            task={"module": "equipment", "page": "alarm-config"},
            repeat=3,
        )
    """

    def __init__(self, provider: str = "claude"):
        self.provider = provider
        self.results: list[AgentRunResult] = []

    def run(
        self,
        agent_name: str,
        task: dict,
        repeat: int = 3,
        timeout_seconds: int = 600,
    ) -> dict:
        """
        运行 Agent 基准测试。

        参数:
            agent_name:       Agent 名称
            task:             任务参数 {module, page, ...}
            repeat:           重复次数
            timeout_seconds:  单次运行超时

        返回:
            {
                "agent_name": "automation-agent",
                "task": {...},
                "repeat": 3,
                "results": [AgentRunResult, ...],
                "success_rate": 0.67,
                "three_d_score": {"quality": 0.67, "efficiency": 0.85, "cost": 0.92},
                "overall_score": 0.78,
            }
        """
        self.results = []
        module = task.get("module", "")
        page = task.get("page", "")

        for i in range(repeat):
            start_ns = time.time()
            try:
                from aitest.agents.agent_runner import AgentLoop
                agent = AgentLoop(
                    agent_name=agent_name,
                    provider=self.provider,
                    module=module,
                    page=page,
                    max_steps=12,
                )
                state = agent.run()

                elapsed_ms = int((time.time() - start_ns) * 1000)
                total_tokens = sum(
                    (obs.token_usage or {}).get("input", 0) +
                    (obs.token_usage or {}).get("output", 0)
                    for obs in state.observations
                )
                # 估算成本 (sonnet pricing)
                cost = total_tokens / 1_000_000 * 3.0

                self.results.append(AgentRunResult(
                    run_index=i + 1,
                    success=state.success,
                    termination_reason=state.termination_reason or "",
                    skills_completed=len(state.completed_skills),
                    skills_failed=len(state.failed_skills),
                    total_tokens=total_tokens,
                    total_latency_ms=elapsed_ms,
                    total_cost=round(cost, 6),
                    artifacts_generated=sum(
                        len(obs.artifacts_found) for obs in state.observations
                    ),
                ))
            except Exception as e:
                elapsed_ms = int((time.time() - start_ns) * 1000)
                self.results.append(AgentRunResult(
                    run_index=i + 1,
                    success=False,
                    termination_reason=f"exception: {str(e)[:100]}",
                    total_latency_ms=elapsed_ms,
                    errors=[str(e)[:300]],
                ))

        # 聚合分析
        n = len(self.results)
        success_count = sum(1 for r in self.results if r.success)
        success_rate = success_count / n if n > 0 else 0.0

        # 效率: 平均 token 消耗 vs baseline (取所有运行中最低 token 作为 baseline)
        tokens_list = [r.total_tokens for r in self.results if r.total_tokens > 0]
        if tokens_list:
            min_tokens = min(tokens_list)
            avg_tokens = sum(tokens_list) / len(tokens_list)
            efficiency_score = min(1.0, min_tokens / max(avg_tokens, 1))
        else:
            efficiency_score = 0.0

        # 成本: 归一化
        costs = [r.total_cost for r in self.results if r.total_cost > 0]
        if costs:
            min_cost = min(costs)
            avg_cost = sum(costs) / len(costs)
            cost_score = min(1.0, min_cost / max(avg_cost, 0.0001))
        else:
            cost_score = 0.0

        # 稳定性: 方差惩罚
        if len(tokens_list) >= 2:
            mean_t = sum(tokens_list) / len(tokens_list)
            var = sum((t - mean_t) ** 2 for t in tokens_list) / len(tokens_list)
            cv = math.sqrt(var) / max(mean_t, 1)  # 变异系数
            stability_penalty = min(1.0, cv)
        else:
            stability_penalty = 0.0

        three_d = {
            "quality": round(success_rate, 3),
            "efficiency": round(efficiency_score, 3),
            "cost": round(cost_score, 3),
            "stability": round(1.0 - stability_penalty, 3),
        }
        overall = round(
            three_d["quality"] * 0.5 +
            three_d["efficiency"] * 0.2 +
            three_d["cost"] * 0.2 +
            three_d["stability"] * 0.1,
            3,
        )

        avg_latency = int(sum(r.total_latency_ms for r in self.results) / n) if n > 0 else 0
        avg_tokens_val = int(sum(r.total_tokens for r in self.results) / n) if n > 0 else 0

        result = {
            "agent_name": agent_name,
            "task": task,
            "repeat": repeat,
            "bench_time": datetime.now().isoformat(),
            "results": [r.to_dict() for r in self.results],
            "success_rate": round(success_rate, 3),
            "avg_latency_ms": avg_latency,
            "avg_tokens_per_run": avg_tokens_val,
            "total_cost_all_runs": round(sum(r.total_cost for r in self.results), 6),
            "three_d_score": three_d,
            "overall_score": overall,
            "grade": self._grade(overall),
        }

        self._write_report(result)
        return result

    def compare_agents(
        self,
        agent_names: list[str],
        task: dict,
        repeat: int = 2,
    ) -> dict:
        """
        横向对比多个 Agent 在同一任务上的表现。

        返回:
            {agent_name: benchmark_result, ...}
        """
        results = {}
        for agent_name in agent_names:
            results[agent_name] = self.run(agent_name, task, repeat=repeat)
        return results

    def compare_models(
        self,
        agent_name: str,
        task: dict,
        providers: list[str],
        repeat: int = 2,
    ) -> dict:
        """
        同一 Agent 在不同模型上的表现对比。

        返回:
            {provider: benchmark_result, ...}
        """
        results = {}
        for prov in providers:
            bench = AgentBenchmark(provider=prov)
            results[prov] = bench.run(agent_name, task, repeat=repeat)
        return results

    # ── 辅助 ──────────────────────────────────────────────────────────

    def _grade(self, score: float) -> str:
        if score >= 0.9:
            return "A"
        elif score >= 0.75:
            return "B"
        elif score >= 0.6:
            return "C"
        elif score >= 0.4:
            return "D"
        return "F"

    def _write_report(self, report: dict):
        """持久化基准测试报告。"""
        BENCH_DIR.mkdir(parents=True, exist_ok=True)
        agent_name = report["agent_name"]
        path = BENCH_DIR / f"agent-bench-{agent_name}-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
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
        print("Usage: python agent_benchmark.py <agent_name> --module=<m> [--page=<p>] [--repeat=3]")
        sys.exit(0)

    agent = sys.argv[1]
    kwargs = {"module": "", "page": ""}
    repeat = 3

    for arg in sys.argv[2:]:
        if arg.startswith("--module="):
            kwargs["module"] = arg.split("=")[1]
        elif arg.startswith("--page="):
            kwargs["page"] = arg.split("=")[1]
        elif arg.startswith("--repeat="):
            repeat = int(arg.split("=")[1])

    bench = AgentBenchmark()
    result = bench.run(agent, kwargs, repeat=repeat)

    print(f"\nAgent: {result['agent_name']}")
    print(f"Task: {result['task']}")
    print(f"Grade: {result['grade']} (overall={result['overall_score']:.3f})")
    print(f"Success Rate: {result['success_rate']:.0%}")
    print(f"3D Score: Q={result['three_d_score']['quality']:.3f} "
          f"E={result['three_d_score']['efficiency']:.3f} "
          f"C={result['three_d_score']['cost']:.3f} "
          f"S={result['three_d_score']['stability']:.3f}")
    print(f"Avg: {result['avg_tokens_per_run']} tokens, {result['avg_latency_ms']}ms")
    print(f"Total cost (all runs): ${result['total_cost_all_runs']:.4f}")
