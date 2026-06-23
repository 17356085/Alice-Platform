"""
TLO Parallel Runner — 多模块并行 SOP 执行。

用法:
    python -m aitest.infra.parallel_runner run --modules=equipment,warehouse,tank
    python -m aitest.infra.parallel_runner run --all --max-workers=4
    python -m aitest.infra.parallel_runner perf --module=equipment --iterations=5
"""

import json
import subprocess
import sys
import time
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

_WORKSTUDY = Path(__file__).resolve().parent.parent.parent


@dataclass
class RunResult:
    module: str
    success: bool
    duration_s: float
    output: str = ""
    error: str = ""
    started_at: str = ""
    finished_at: str = ""


def run_module_sop(module: str, mode: str = "full", provider: str = "claude") -> RunResult:
    """单模块 SOP 执行（工作线程）。"""
    started = datetime.now().isoformat()
    start = time.time()
    cmd = [
        sys.executable, "-m", "aitest.infra.cli", "sop", "run",
        f"--module={module}",
        f"--mode={mode}",
        "--non-interactive",
        f"--provider={provider}",
    ]
    try:
        proc = subprocess.run(
            cmd, cwd=str(_WORKSTUDY),
            capture_output=True, text=True,
            timeout=1800,
            env={**os.environ, "AITEST_PARALLEL": "1", "AITEST_MODULE": module},
        )
        return RunResult(
            module=module,
            success=proc.returncode == 0,
            duration_s=round(time.time() - start, 1),
            output=proc.stdout[-2000:],
            error=proc.stderr[-500:],
            started_at=started,
            finished_at=datetime.now().isoformat(),
        )
    except subprocess.TimeoutExpired:
        return RunResult(
            module=module, success=False, duration_s=1800,
            error="TIMEOUT (>30min)",
            started_at=started, finished_at=datetime.now().isoformat(),
        )
    except Exception as e:
        return RunResult(
            module=module, success=False, duration_s=round(time.time() - start, 1),
            error=str(e),
            started_at=started, finished_at=datetime.now().isoformat(),
        )


def discover_modules() -> list[str]:
    """从 SOP_STATUS 自动发现所有可用模块。"""
    sop_dir = _WORKSTUDY / "governance" / "artifacts" / "sop-status"
    modules = []
    for f in sorted(sop_dir.glob("SOP_STATUS_*.json")):
        mod = f.stem.replace("SOP_STATUS_", "")
        modules.append(mod)
    return modules


def run_parallel(
    modules: list[str],
    max_workers: int = 4,
    mode: str = "full",
    provider: str = "claude",
) -> list[RunResult]:
    """
    并行运行多个模块的 SOP。

    Args:
        modules: 模块列表
        max_workers: 最大并行数（默认 4，避免 LLM rate limit）
        mode: SOP 模式
        provider: LLM Provider
    """
    print(f"\n{'='*60}")
    print(f"  TLO Parallel Runner — {len(modules)} modules, {max_workers} workers")
    print(f"{'='*60}\n")

    results = []
    total_start = time.time()

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_module_sop, mod, mode, provider): mod
            for mod in modules
        }
        for future in as_completed(futures):
            mod = futures[future]
            try:
                result = future.result()
                results.append(result)
                icon = "✅" if result.success else "❌"
                print(f"  {icon} {mod:20s} {result.duration_s:6.1f}s")
            except Exception as e:
                results.append(RunResult(module=mod, success=False, duration_s=0, error=str(e)))
                print(f"  ❌ {mod:20s} ERROR: {e}")

    total_s = round(time.time() - total_start, 1)
    passed = sum(1 for r in results if r.success)
    failed = len(results) - passed
    total_serial_s = sum(r.duration_s for r in results)

    print(f"\n{'='*60}")
    print(f"  Summary: {passed} passed / {failed} failed / {len(results)} total")
    print(f"  Wall clock: {total_s:.1f}s  |  Serial: {total_serial_s:.1f}s")
    if total_s > 0:
        print(f"  Speedup: {total_serial_s/total_s:.1f}x  (ideal: {max_workers}x)")
    print(f"{'='*60}\n")

    return results


def run_perf_benchmark(
    module: str,
    iterations: int = 5,
    mode: str = "smoke",
    provider: str = "claude",
) -> dict:
    """
    性能测试: 对单个模块重复执行 N 次，收集性能指标。

    Returns:
        {module, iterations, success_rate, avg_duration_s, p50_s, p95_s, p99_s,
         avg_tokens, avg_cost, failures: [...]}
    """
    print(f"\n{'='*60}")
    print(f"  TLO Perf Benchmark — {module} × {iterations}")
    print(f"{'='*60}\n")

    results = []
    for i in range(iterations):
        print(f"  [{i+1}/{iterations}] Running {module}...")
        result = run_module_sop(module, mode=mode, provider=provider)
        results.append(result)
        print(f"    {'✅' if result.success else '❌'} {result.duration_s:.1f}s")

    durations = [r.duration_s for r in results if r.success]
    durations.sort()
    n = len(durations)

    return {
        "module": module,
        "iterations": iterations,
        "success_rate": len([r for r in results if r.success]) / iterations,
        "avg_duration_s": round(sum(durations) / n, 1) if n else 0,
        "p50_s": durations[n // 2] if n else 0,
        "p95_s": durations[int(n * 0.95)] if n >= 20 else (durations[-1] if n else 0),
        "p99_s": durations[int(n * 0.99)] if n >= 100 else (durations[-1] if n else 0),
        "min_s": durations[0] if n else 0,
        "max_s": durations[-1] if n else 0,
        "failures": [r.error for r in results if not r.success],
    }


# ── CLI ──

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TLO Parallel Runner & Perf Benchmark")
    sub = parser.add_subparsers(dest="command")

    run_p = sub.add_parser("run", help="多模块并行执行")
    run_p.add_argument("--modules", default=None, help="逗号分隔模块列表")
    run_p.add_argument("--all", action="store_true", help="所有已发现模块")
    run_p.add_argument("--max-workers", type=int, default=4)
    run_p.add_argument("--mode", default="full")
    run_p.add_argument("--provider", default="claude")
    run_p.add_argument("--output", default=None, help="JSON 输出路径")

    perf_p = sub.add_parser("perf", help="性能测试基准")
    perf_p.add_argument("--module", required=True)
    perf_p.add_argument("--iterations", type=int, default=5)
    perf_p.add_argument("--mode", default="smoke")
    perf_p.add_argument("--provider", default="claude")
    perf_p.add_argument("--output", default=None)

    args = parser.parse_args()

    if args.command == "run":
        if args.all:
            modules = discover_modules()
        elif args.modules:
            modules = [m.strip() for m in args.modules.split(",")]
        else:
            print("Error: --modules or --all required")
            sys.exit(1)

        results = run_parallel(modules, max_workers=args.max_workers,
                               mode=args.mode, provider=args.provider)

        if args.output:
            out = [r.__dict__ for r in results]
            Path(args.output).write_text(json.dumps(out, indent=2, ensure_ascii=False))

    elif args.command == "perf":
        result = run_perf_benchmark(args.module, iterations=args.iterations,
                                     mode=args.mode, provider=args.provider)
        print(f"\n📊 Perf Summary:")
        for k, v in result.items():
            if k != "failures":
                print(f"  {k}: {v}")
        if result["failures"]:
            print(f"  failures ({len(result['failures'])}):")
            for f in result["failures"][:3]:
                print(f"    - {f[:120]}")

        if args.output:
            Path(args.output).write_text(json.dumps(result, indent=2, ensure_ascii=False))

    else:
        parser.print_help()
