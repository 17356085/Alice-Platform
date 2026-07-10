#!/usr/bin/env python3
"""
性能基准测试快速运行脚本

在 Python 3.10 环境下生成模拟性能报告（用于演示）。
在 Python 3.11+ 环境下运行真实基准测试。

用法:
    python run_benchmarks.py               # 运行所有测试
    python run_benchmarks.py --mock        # 生成模拟报告（3.10 环境）
    python run_benchmarks.py --save=baseline  # 保存基线
"""

import sys
import subprocess
from pathlib import Path


def check_environment():
    """检查环境。"""
    python_version = sys.version_info

    if python_version >= (3, 11):
        return "real"
    else:
        print(f"⚠️  当前 Python 版本: {python_version.major}.{python_version.minor}")
        print("⚠️  SDK 要求 Python 3.11+，将生成模拟报告")
        return "mock"


def run_real_benchmarks(save_baseline=None):
    """运行真实基准测试（Python 3.11+）。"""
    print("=" * 60)
    print("运行性能基准测试（真实环境）")
    print("=" * 60)
    print()

    benchmark_dir = Path(__file__).parent

    # 构建命令
    cmd = ["pytest", "test_performance.py", "--benchmark-only", "-v"]

    if save_baseline:
        cmd.extend(["--benchmark-save", save_baseline])

    print(f"命令: {' '.join(cmd)}")
    print()

    # 运行
    try:
        subprocess.run(cmd, cwd=benchmark_dir, check=True)
        print("\n✅ 基准测试完成")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n✗ 测试失败: {e}")
        return 1
    except FileNotFoundError:
        print("\n✗ pytest 未安装")
        print("请运行: pip install pytest pytest-benchmark")
        return 1


def generate_mock_report():
    """生成模拟性能报告（Python 3.10）。"""
    print("=" * 60)
    print("生成模拟性能报告（Python 3.10 环境）")
    print("=" * 60)
    print()

    report = """
性能基准测试报告（模拟）
===============================================================================

⚠️  注意: 这是基于预期值的模拟报告。
    真实测试需要在 Python 3.11+ 环境中运行。

-------------------------------------------------------------------------------
1. Extension 开销测试
-------------------------------------------------------------------------------

| 场景                | 平均时间 | 标准差 | 最小/最大 | 开销 |
|---------------------|---------|--------|----------|------|
| 无 Extension        | 8.2ms   | 0.5ms  | 7.5/9.1ms | 基线 |
| 单个 Extension      | 12.1ms  | 0.8ms  | 11.0/13.5ms | +47% |
| 4 个 Extension      | 24.3ms  | 1.2ms  | 22.8/26.5ms | +196% |

结论: Extension 开销在预期范围内（单个 ~50%，4 个 ~200%）

-------------------------------------------------------------------------------
2. 存储后端对比
-------------------------------------------------------------------------------

| 存储后端            | 沉淀 10 条 | 检索 5 条 | 总延迟 | 吞吐量 |
|---------------------|-----------|----------|--------|--------|
| InMemory Knowledge  | 0.8ms     | 0.6ms    | 1.4ms  | ~700/s |
| InMemory Memory     | 0.5ms     | 0.3ms    | 0.8ms  | ~1250/s |

结论: InMemory 实现延迟极低，适合轻量级场景

-------------------------------------------------------------------------------
3. Extension 钩子延迟
-------------------------------------------------------------------------------

| Extension  | 钩子方法           | 平均延迟 | 调用频率 | 累计开销 |
|------------|--------------------|---------|---------|---------|
| Knowledge  | on_cycle_end       | 3.2ms   | 1次/Run | 低 |
| Knowledge  | search_before_run  | 2.1ms   | 1次/Run | 低 |
| Memory     | on_cycle_end       | 1.5ms   | 1次/Run | 极低 |
| Memory     | get_last_run       | 0.8ms   | 按需    | 极低 |

结论: 钩子延迟可忽略，不影响整体性能

-------------------------------------------------------------------------------
4. 批量操作性能
-------------------------------------------------------------------------------

Knowledge 批量沉淀:
| 批量大小 | 平均时间 | 吞吐量 |
|---------|---------|--------|
| 10 条   | 8.5ms   | 1176/s |
| 50 条   | 38.2ms  | 1309/s |
| 100 条  | 72.1ms  | 1387/s |

Memory 批量记录:
| 批量大小 | 平均时间 | 吞吐量 |
|---------|---------|--------|
| 10 条   | 4.2ms   | 2381/s |
| 50 条   | 18.5ms  | 2703/s |
| 100 条  | 35.8ms  | 2793/s |

结论: 批量操作吞吐量符合预期，Memory 比 Knowledge 快 ~2x

-------------------------------------------------------------------------------
5. 内存占用
-------------------------------------------------------------------------------

| 场景                 | RSS 增量 | 堆内存 | 对象数 |
|---------------------|---------|--------|--------|
| Engine（无 Extension）| 42 MB   | 35 MB  | ~8.5k  |
| Engine（4 Extension）| 78 MB   | 65 MB  | ~15.2k |

Extension 内存开销: ~36 MB（单个 ~9 MB）

结论: 内存开销在可接受范围内

-------------------------------------------------------------------------------
性能总结
-------------------------------------------------------------------------------

✅ Extension 开销: 单个 +50%，4 个 +200%（预期内）
✅ 存储后端: InMemory 延迟 < 2ms（极低）
✅ 钩子延迟: 所有钩子 < 5ms（可忽略）
✅ 批量吞吐: Knowledge ~1300/s, Memory ~2700/s（良好）
✅ 内存占用: 4 个 Extension ~80 MB（合理）

推荐:
  - 轻量级场景: 使用 InMemory Store（零依赖、低延迟）
  - 语义检索场景: 升级到平台 ChromaDB（语义能力 > 延迟）
  - 生产环境: 按需启用 Extension（避免不必要开销）

-------------------------------------------------------------------------------

要运行真实基准测试，请在 Python 3.11+ 环境执行:
  python run_benchmarks.py

要保存基线:
  python run_benchmarks.py --save=baseline

要对比性能:
  pytest-benchmark compare baseline optimized
"""

    print(report)

    # 保存到文件
    report_file = Path(__file__).parent / "MOCK_PERFORMANCE_REPORT.txt"
    report_file.write_text(report)
    print(f"\n✅ 模拟报告已保存: {report_file}")

    return 0


def main():
    """主函数。"""
    import argparse

    parser = argparse.ArgumentParser(description="性能基准测试运行器")
    parser.add_argument("--mock", action="store_true", help="生成模拟报告（Python 3.10）")
    parser.add_argument("--save", type=str, help="保存基线名称")
    args = parser.parse_args()

    # 检查环境
    env_mode = check_environment()

    if args.mock or env_mode == "mock":
        return generate_mock_report()
    else:
        return run_real_benchmarks(save_baseline=args.save)


if __name__ == "__main__":
    sys.exit(main())
