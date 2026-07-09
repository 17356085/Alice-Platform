#!/usr/bin/env python3
"""Phase 8 统一验收门禁脚本

PH8-PR-8.7: 把所有 Phase 8 gate 命令集成到单一执行入口，便于本地验证和 CI 集成。

Usage:
    python tools/phase8_gate.py --all            # 运行全部 gate
    python tools/phase8_gate.py --pr 8.1         # 只运行指定 PR 的 gate
    python tools/phase8_gate.py --pr 8.1 8.2 8.3 # 运行多个 PR 的 gate
    python tools/phase8_gate.py --dependency     # 只运行依赖图检查
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON = sys.executable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def _subprocess_env() -> dict[str, str]:
    env = os.environ.copy()
    pythonpath_parts = [
        str(REPO_ROOT),
        str(REPO_ROOT / "packages" / "alice-engine"),
        str(REPO_ROOT / "packages" / "alice-governance"),
    ]
    existing_pythonpath = env.get("PYTHONPATH")
    if existing_pythonpath:
        pythonpath_parts.append(existing_pythonpath)
    env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


# Phase 8 Gate 配置
GATES: Dict[str, Dict] = {
    "8.1": {
        "name": "依赖图与 SCC 门禁基线",
        "commands": [
            [PYTHON, "tools/check_dependency_graph.py"],
        ],
        "expectations": [
            "依赖图报告可输出",
            "无 alice_engine -> aitest 静态或动态依赖回潮",
            "SCC 数量和最大 SCC 规模不超过已审查基线",
        ],
    },
    "8.2": {
        "name": "Runtime Contract Pack 冻结",
        "commands": [
            [
                PYTHON,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "packages/alice-engine/tests/test_runtime_contract_pack.py",
                "aitest/tests/platform/test_runtime_contract_projection.py",
                "aitest/tests/platform/test_runtime_event_contracts.py",
            ],
        ],
        "expectations": [
            "Runtime Contract Pack 合同测试通过",
            "RuntimeEventEnvelope -> RunEvent 投影测试通过",
            "RunEvent 核心事件字段 schema 与投影器表驱动一致性测试通过",
        ],
    },
    "8.3": {
        "name": "AgentLoop 边界减重第一轮",
        "commands": [
            [
                PYTHON,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "packages/alice-engine/tests/test_architecture.py",
                "packages/alice-engine/tests/test_provider_runtime_lifecycle.py",
                "packages/alice-engine/tests/test_runtime_lifecycle.py",
                "packages/alice-engine/tests/test_runtime_context_builder.py",
                "packages/alice-engine/tests/test_session_loop_orchestrator.py",
                "aitest/tests/agents/test_agent_runner.py",
                "aitest/tests/integration/test_agent_loop.py",
            ],
        ],
        "expectations": [
            "AgentLoop 的 runtime context / context vars 组装由内部 collaborator 承接",
            "Provider lifecycle 由内部 collaborator 承接，最终 provider/model 解析路径冻结",
            "Tool/MCP lifecycle 与 replay step sink 由内部 collaborator 承接",
            "单次 session 的 loop orchestration 从 AgentLoop 主体剥离，保留行为兼容",
            "新拆内部协作者对 executor 的反向依赖由架构测试持续门禁",
            "新增 runtime context 协作者单测通过，缓存与字段注入行为冻结",
            "现有 AgentLoop 初始化与集成回归继续通过",
        ],
    },
    "8.5": {
        "name": "Tool / MCP 异步生命周期统一",
        "commands": [
            [
                PYTHON,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "aitest/tests/mcp/test_mcp_client_degradation.py",
                "aitest/tests/mcp",
            ],
        ],
        "expectations": [
            "McpClientResult.close / .call_tool 类型标注通过 Awaitable/Coroutine 语义断言",
            "MCP SDK 缺失降级路径全部返回空结果，不抛异常",
            "sdk_ports._mcp_clients_factory 在事件循环冲突时走线程池 fallback",
            "非冲突 RuntimeError/Exception 记录 WARNING 并带 agent 名称，不再静默吞错",
            "AsyncToolProvider Protocol 可导入、runtime_checkable、且声明的 call_tool_async / close_async 均为 async def",
            "aitest/tests/mcp/ 全目录无回归",
        ],
    },
    "8.6": {
        "name": "Provider 单一事实源与兼容层退场计划",
        "commands": [
            [
                PYTHON,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "packages/alice-engine/tests/providers/test_claude_provider.py",
                "packages/alice-engine/tests/providers/test_openai_deepseek_provider.py",
                "aitest/tests/platform/test_provider_adapter.py",
            ],
        ],
        "expectations": [
            "SDK Provider complete() + stream() + tool calling 通过单元测试",
            "Prompt Caching、reasoning_content、错误响应合同通过测试",
            "平台 adapter 正确委托 SDK 层（API key 注入、trace 装饰器、base_url 注入）",
            "Legacy imports 兼容性保持",
            "未知 provider 错误处理正确",
        ],
    },
    "8.7": {
        "name": "V2 回归基线与边界验收套件",
        "commands": [
            [PYTHON, "tools/check_dependency_graph.py"],
            [
                PYTHON,
                "-m",
                "pytest",
                "-q",
                "-p",
                "no:cacheprovider",
                "packages/alice-engine/tests/test_dependency_graph_guard.py",
                "packages/alice-engine/tests/test_runtime_contract_pack.py",
                "aitest/tests/platform/test_runtime_contract_projection.py",
                "aitest/tests/platform/test_runtime_event_contracts.py",
            ],
        ],
        "expectations": [
            "Phase 8 依赖门禁仍通过",
            "Runtime Contract Pack 与 RunEvent schema / 投影 gate 全部通过",
            "文档中的 Phase 8 gate 命令与仓库实际测试文件一致",
        ],
    },
}


def run_command(cmd: List[str], description: str) -> bool:
    """运行单条命令，返回是否成功"""
    print(f"\n{'='*80}")
    print(f"🔧 {description}")
    print(f"{'='*80}")
    print(f"命令: {' '.join(cmd)}")
    print()

    try:
        result = subprocess.run(
            cmd,
            cwd=REPO_ROOT,
            capture_output=False,
            text=True,
            env=_subprocess_env(),
        )
        success = result.returncode == 0
        if success:
            print(f"\n✅ {description} — 通过")
        else:
            print(f"\n❌ {description} — 失败 (exit code: {result.returncode})")
        return success
    except Exception as e:
        print(f"\n❌ {description} — 执行错误: {e}")
        return False


def run_gate(pr_id: str) -> bool:
    """运行指定 PR 的 gate，返回是否全部通过"""
    gate = GATES.get(pr_id)
    if not gate:
        print(f"❌ 未知 PR ID: {pr_id}")
        return False

    print(f"\n{'#'*80}")
    print(f"# PH8-PR-{pr_id}: {gate['name']}")
    print(f"{'#'*80}")
    print("\n预期结果:")
    for exp in gate["expectations"]:
        print(f"  - {exp}")

    all_passed = True
    for cmd in gate["commands"]:
        if not run_command(cmd, f"PH8-PR-{pr_id}"):
            all_passed = False

    return all_passed


def main():
    parser = argparse.ArgumentParser(
        description="Phase 8 统一验收门禁脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tools/phase8_gate.py --all            # 运行全部 gate
  python tools/phase8_gate.py --pr 8.1         # 只运行 PH8-PR-8.1
  python tools/phase8_gate.py --pr 8.1 8.2 8.3 # 运行多个 PR 的 gate
  python tools/phase8_gate.py --dependency     # 只运行依赖图检查（快速验证）
        """,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="运行所有 Phase 8 gate（按顺序：8.1, 8.2, 8.3, 8.5, 8.6, 8.7）",
    )
    parser.add_argument(
        "--pr",
        nargs="+",
        choices=list(GATES.keys()),
        help="指定要运行的 PR ID（例如: 8.1 8.2 8.3）",
    )
    parser.add_argument(
        "--dependency",
        action="store_true",
        help="只运行依赖图检查（快速验证边界）",
    )

    args = parser.parse_args()

    if args.dependency:
        # 快速依赖图检查
        success = run_command(
            ["python", "tools/check_dependency_graph.py"],
            "依赖图与 SCC 门禁（快速验证）",
        )
        sys.exit(0 if success else 1)

    if args.all:
        # 按推荐顺序运行全部 gate
        pr_sequence = ["8.1", "8.2", "8.3", "8.5", "8.6", "8.7"]
    elif args.pr:
        pr_sequence = args.pr
    else:
        parser.print_help()
        sys.exit(1)

    print(f"\n{'#'*80}")
    print("# Phase 8 验收门禁开始")
    print(f"{'#'*80}")
    print(f"\n将运行以下 PR 的 gate: {', '.join(pr_sequence)}")

    results = {}
    for pr_id in pr_sequence:
        results[pr_id] = run_gate(pr_id)

    # 总结
    print(f"\n{'#'*80}")
    print("# Phase 8 验收门禁总结")
    print(f"{'#'*80}\n")

    all_passed = all(results.values())
    for pr_id, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"PH8-PR-{pr_id}: {status} — {GATES[pr_id]['name']}")

    if all_passed:
        print(f"\n{'='*80}")
        if len(results) == len(GATES):
            print("🎉 所有 Phase 8 gate 均通过！Phase 8 验收完成。")
        else:
            print("🎉 所选 Phase 8 gate 均通过！")
        print(f"{'='*80}\n")
        sys.exit(0)
    else:
        print(f"\n{'='*80}")
        print("❌ 部分 Phase 8 gate 未通过，请查看上方详细输出。")
        print(f"{'='*80}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
