# Demo Execution Flow

> 架构解耦分析 — 文档 4/7
> 目标: 设计 demo.py 启动方式，三层架构: Core / Extensions / Platform
> 注: 05 升级为四层 (Core/Runtime/Workflow/Adapter)，07 提供迁移地图

## 1. 执行流程图

```
用户执行:
  python demo.py --module equipment --pages alarm-config camera

                    │
                    ▼
┌─────────────────────────────────────────────────────────────┐
│ demo.py                                                       │
│   1. 解析参数 (--module, --pages, --mode, --extensions)       │
│   2. 初始化 Engine(workstudy, governance, llm_provider)       │
│   3. 注册 Extensions (audit, complexity, knowledge, ...)      │
│   4. 调用 engine.run(module, pages, mode)                     │
│   5. 输出结果 (JSON / 表格)                                    │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Engine.run()                                                  │
│   1. 创建初始状态 (SOPState)                                   │
│   2. 构建 SOP Graph (build_sop_graph)                         │
│   3. 编译图 (compile + checkpointer)                          │
│   4. 执行 (compiled.invoke(state))                            │
│   5. 触发 Extensions.on_cycle_end()                           │
│   6. 返回结果                                                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ Core: SOP Graph 执行                                          │
│                                                               │
│  entry ─→ preflight ─→ route ─┬→ project_agent               │
│                                ├→ requirement_agent           │
│                                ├→ test_design_agent           │
│                                ├→ automation_agent_pre        │
│                                │   ─→ hitl_approval           │
│                                │   ─→ automation_agent_post   │
│                                │   ─→ page_advance            │
│                                ├→ execution_agent             │
│                                ├→ bug_analysis_agent          │
│                                ├→ data_sanitization           │
│                                ├→ report_agent                │
│                                └→ knowledge_agent             │
│                                └→ exit                        │
│                                                               │
│  每个 Agent 节点:                                              │
│    AgentLoop → SkillLoader → SkillExecutor → LLM              │
│    → 产物写入 (.md / .py)                                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 输出                                                          │
│   - 控制台: 实时进度 + 最终结果                                 │
│   - 文件: SOP_STATUS_<module>.json                            │
│   - 产物: governance/artifacts/ 下的 .md / .py 文件            │
└─────────────────────────────────────────────────────────────┘
```

## 2. demo.py 实现

```python
#!/usr/bin/env python3
"""
demo.py — Standalone Engine 启动入口。

三层架构:
  - Core:       串行必须，SOP 编排 + Agent 执行 + LLM 调用
  - Extensions:  可插拔子引擎 (audit, complexity, knowledge, memory, browser-use)
  - Platform:    不属于引擎 (Web API, Dashboard, Auth, Tenant, ...)

用法:
    # 基本用法 (Core only)
    python demo.py --module equipment

    # 带 Extension
    python demo.py --module equipment --extensions audit complexity

    # 指定页面
    python demo.py --module equipment --pages alarm-config camera key-param

    # 指定模式
    python demo.py --module equipment --mode from-automation

    # Dry run
    python demo.py --module equipment --dry-run

    # Mock LLM (测试模式)
    python demo.py --module equipment --mock-llm

环境变量:
    ENGINE_WORKSTUDY    工作目录路径
    ENGINE_GOVERNANCE   Governance 目录路径
    LLM_PROVIDER        LLM Provider (anthropic/deepseek/openai)
    ANTHROPIC_API_KEY   Anthropic API Key
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path

DEMO_DIR = Path(__file__).parent
sys.path.insert(0, str(DEMO_DIR))


# ── Extension 注册表 ───────────────────────────────────────────────

EXTENSION_REGISTRY = {
    "audit": "aitest.engine.extensions.audit:AuditExtension",
    "complexity": "aitest.engine.extensions.complexity:ComplexityExtension",
    "knowledge": "aitest.engine.extensions.knowledge:KnowledgeExtension",
    "memory": "aitest.engine.extensions.memory:MemoryExtension",
}


def load_extension(name: str):
    """按名称加载 Extension 类。"""
    if name not in EXTENSION_REGISTRY:
        raise ValueError(f"Unknown extension: {name}. Available: {list(EXTENSION_REGISTRY.keys())}")

    module_path, class_name = EXTENSION_REGISTRY[name].rsplit(":", 1)
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)()


def setup_logging(verbose: bool = False) -> None:
    """配置日志。"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def parse_args(args=None) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="Standalone Engine — SOP 流水线执行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python demo.py --module equipment
  python demo.py --module equipment --extensions audit complexity
  python demo.py --module equipment --pages alarm-config camera
  python demo.py --module equipment --mode from-automation
  python demo.py --module equipment --dry-run
  python demo.py --module equipment --mock-llm

可用 Extensions:
  audit        — 状态漂移 + SOP 合规审计
  complexity   — 按复杂度选择 SOP 流水线
  knowledge    — 跨 Run 知识复用
  memory       — ChromaDB 向量记忆
        """,
    )

    parser.add_argument("--module", "-m", required=True,
                        help="模块名 (如 equipment, tank, production)")
    parser.add_argument("--pages", "-p", nargs="*", default=None,
                        help="页面列表 (可选，默认自动发现)")
    parser.add_argument("--mode",
                        choices=["full", "resume", "from-automation",
                                 "from-test-design", "from-requirement", "status"],
                        default="full",
                        help="执行模式 (默认: full)")
    parser.add_argument("--workstudy", "-w", default=None,
                        help="工作目录路径")
    parser.add_argument("--governance", "-g", default=None,
                        help="Governance 目录路径")
    parser.add_argument("--llm",
                        choices=["anthropic", "deepseek", "openai"],
                        default=None,
                        help="LLM Provider")
    parser.add_argument("--run-id", default=None,
                        help="运行 ID (默认: 自动生成)")
    parser.add_argument("--extensions", "-e", nargs="*", default=[],
                        help=f"加载的 Extensions (可选: {list(EXTENSION_REGISTRY.keys())})")
    parser.add_argument("--dry-run", action="store_true",
                        help="Dry run: 只显示执行计划")
    parser.add_argument("--mock-llm", action="store_true",
                        help="使用 Mock LLM (测试模式)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="详细日志输出")
    parser.add_argument("--output", "-o", default=None,
                        help="结果输出文件路径")

    return parser.parse_args(args)


def dry_run(module: str, pages: list[str], mode: str,
            extensions: list[str]) -> None:
    """Dry run: 显示执行计划。"""
    print("\n" + "=" * 60)
    print("  DRY RUN — 执行计划")
    print("=" * 60)
    print(f"\n  模块:    {module}")
    print(f"  页面:    {', '.join(pages) if pages else '(自动发现)'}")
    print(f"  模式:    {mode}")
    print(f"  Extensions: {', '.join(extensions) if extensions else '(无)'}")

    from aitest.graphs.state import CANONICAL_PHASES, MODE_SKIP_MAP

    skip_phases = MODE_SKIP_MAP.get(mode, [])
    active_phases = [p for p in CANONICAL_PHASES if p not in skip_phases]

    print(f"\n  将执行 {len(active_phases)} 个 Phase:")
    for i, phase in enumerate(active_phases, 1):
        print(f"    {i}. {phase}")

    from aitest.graphs.sop_graph import PHASE_TO_NODE
    print(f"\n  将加载 {len(active_phases)} 个 Agent:")
    for phase in active_phases:
        node = PHASE_TO_NODE.get(phase, "N/A")
        print(f"    - {phase} → {node}")

    if extensions:
        print(f"\n  将注册 {len(extensions)} 个 Extension:")
        for ext in extensions:
            print(f"    - {ext}")

    print("\n" + "=" * 60)
    print("  去掉 --dry-run 来实际执行")
    print("=" * 60 + "\n")


def run_engine(args: argparse.Namespace) -> dict:
    """执行 Engine。"""
    if args.workstudy:
        os.environ["ENGINE_WORKSTUDY"] = args.workstudy
    if args.governance:
        os.environ["ENGINE_GOVERNANCE"] = args.governance
    if args.llm:
        os.environ["LLM_PROVIDER"] = args.llm
    if args.mock_llm:
        os.environ["MOCK_LLM"] = "1"
        print("\n⚠️  Mock LLM 模式 — 不调用真实 API")

    from aitest.engine import Engine

    engine = Engine(
        workstudy=args.workstudy,
        governance=args.governance,
        llm_provider=args.llm,
    )

    # 注册 Extensions
    for ext_name in (args.extensions or []):
        try:
            ext = load_extension(ext_name)
            engine.add_extension(ext)
            print(f"  ✅ Extension loaded: {ext_name}")
        except Exception as e:
            print(f"  ⚠️  Extension failed: {ext_name} — {e}")

    print(f"\n🚀 启动 Engine: module={args.module}, mode={args.mode}")
    if args.extensions:
        print(f"   Extensions: {', '.join(args.extensions)}")
    print("-" * 60)

    try:
        result = engine.run(
            module=args.module,
            pages=args.pages,
            mode=args.mode,
            run_id=args.run_id,
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断执行")
        return {"status": "interrupted", "error": "KeyboardInterrupt"}
    except Exception as e:
        print(f"\n\n❌ 执行失败: {e}")
        logging.getLogger("demo").error("Engine failed", exc_info=True)
        return {"status": "failed", "error": str(e)}

    return result


def print_result(result: dict) -> None:
    """打印执行结果。"""
    print("\n" + "=" * 60)
    print("  执行结果")
    print("=" * 60)

    status = result.get("status", "unknown")
    status_icon = {
        "completed": "✅",
        "completed_with_issues": "⚠️",
        "failed": "❌",
        "interrupted": "⏹️",
    }.get(status, "❓")

    print(f"\n  状态: {status_icon} {status}")
    print(f"  Run ID: {result.get('run_id', 'N/A')}")
    print(f"  耗时: {result.get('elapsed_seconds', 0):.1f}s")
    print(f"  模块: {result.get('module', 'N/A')}")
    print(f"  模式: {result.get('mode', 'N/A')}")

    completed = result.get("completed_phases", [])
    if completed:
        print(f"\n  已完成 Phase ({len(completed)}):")
        for phase in completed:
            print(f"    ✅ {phase}")

    failed = result.get("failed_phases", [])
    if failed:
        print(f"\n  失败 Phase ({len(failed)}):")
        for phase in failed:
            print(f"    ❌ {phase}")

    pages = result.get("pages", [])
    if pages:
        print(f"\n  处理页面 ({len(pages)}):")
        for page in pages:
            print(f"    📄 {page}")

    agent_outputs = result.get("agent_outputs", {})
    if agent_outputs:
        print(f"\n  Agent 输出 ({len(agent_outputs)}):")
        for name, output in agent_outputs.items():
            if isinstance(output, dict):
                success = output.get("success", False)
                icon = "✅" if success else "❌"
                skills = len(output.get("completed_skills", []))
                print(f"    {icon} {name}: {skills} skills completed")

    # Extension 输出
    audit = result.get("audit")
    if audit:
        print(f"\n  审计结果:")
        print(f"    漂移: {audit.get('drift_count', 0)}")
        print(f"    错误: {audit.get('error_count', 0)}")
        print(f"    警告: {audit.get('warning_count', 0)}")

    error = result.get("error")
    if error:
        print(f"\n  错误: {error}")

    print("\n" + "=" * 60 + "\n")


def save_result(result: dict, output_path: str) -> None:
    """保存结果到文件。"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n💾 结果已保存到: {path}")


def main(args=None) -> int:
    """主入口。"""
    parsed = parse_args(args)
    setup_logging(parsed.verbose)

    if parsed.dry_run:
        dry_run(parsed.module, parsed.pages, parsed.mode, parsed.extensions)
        return 0

    result = run_engine(parsed)
    print_result(result)

    if parsed.output:
        save_result(result, parsed.output)

    status = result.get("status", "unknown")
    if status == "completed":
        return 0
    elif status == "completed_with_issues":
        return 1
    else:
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

## 3. 使用示例

### 3.1 Core Only (最小运行)

```bash
# 只用 Core，不加载任何 Extension
python demo.py --module equipment

# 指定页面
python demo.py --module equipment --pages alarm-config camera

# 指定模式
python demo.py --module equipment --mode from-automation
```

### 3.2 Core + Extensions

```bash
# 加载 Audit Extension
python demo.py --module equipment --extensions audit

# 加载多个 Extensions
python demo.py --module equipment --extensions audit complexity

# 加载全部 Extensions
python demo.py --module equipment --extensions audit complexity knowledge memory
```

### 3.3 测试模式

```bash
# Dry run — 查看执行计划
python demo.py --module equipment --dry-run

# Dry run + Extensions
python demo.py --module equipment --extensions audit --dry-run

# Mock LLM — 不调用真实 API
python demo.py --module equipment --mock-llm

# Mock LLM + Extensions
python demo.py --module equipment --mock-llm --extensions audit complexity
```

### 3.4 高级用法

```bash
# 指定工作目录
python demo.py --module equipment --workstudy /path/to/workstudy

# 指定 LLM Provider
python demo.py --module equipment --llm deepseek

# 保存结果到文件
python demo.py --module equipment --output result.json

# Resume 中断的执行
python demo.py --module equipment --mode resume --run-id engine-a1b2c3d4
```

## 4. 输出示例

### 4.1 Core Only 输出

```
$ python demo.py --module equipment --pages alarm-config

🚀 启动 Engine: module=equipment, mode=full
------------------------------------------------------------
2026-07-01 10:30:00 [INFO] Engine initialized: workstudy=., governance=./governance, llm=anthropic
2026-07-01 10:30:01 [INFO] AgentLoop: agent=project-agent, skills=1
2026-07-01 10:30:05 [INFO] AgentLoop: completed, status=success
...

============================================================
  执行结果
============================================================

  状态: ✅ completed
  Run ID: engine-a1b2c3d4
  耗时: 45.2s
  模块: equipment
  模式: full

  已完成 Phase (9):
    ✅ Project Init
    ✅ Requirement
    ✅ Test Design
    ✅ Automation
    ✅ Execute & Debug
    ✅ Report
    ✅ Knowledge
    ✅ Data Sanitization

  处理页面 (1):
    📄 alarm-config

============================================================
```

### 4.2 Core + Audit Extension 输出

```
$ python demo.py --module equipment --extensions audit

  ✅ Extension loaded: audit

🚀 启动 Engine: module=equipment, mode=full
   Extensions: audit
------------------------------------------------------------
...

============================================================
  执行结果
============================================================

  状态: ✅ completed
  Run ID: engine-e5f6g7h8
  耗时: 48.1s
  模块: equipment
  模式: full

  已完成 Phase (9):
    ✅ Project Init
    ✅ Requirement
    ...

  审计结果:
    漂移: 0
    错误: 0
    警告: 2

============================================================
```

### 4.3 Dry Run 输出

```
$ python demo.py --module equipment --extensions audit complexity --dry-run

============================================================
  DRY RUN — 执行计划
============================================================

  模块:    equipment
  页面:    (自动发现)
  模式:    full
  Extensions: audit, complexity

  将执行 9 个 Phase:
    1. Project Init
    2. Requirement
    3. Test Design
    ...

  将加载 9 个 Agent:
    - Project Init → project_agent
    - Requirement → requirement_agent
    ...

  将注册 2 个 Extension:
    - audit
    - complexity

============================================================
  去掉 --dry-run 来实际执行
============================================================
```

## 5. 错误处理

```bash
# 模块不存在
$ python demo.py --module nonexistent
❌ 执行失败: Module not found: nonexistent

# Extension 不存在
$ python demo.py --module equipment --extensions unknown_ext
  ⚠️  Extension failed: unknown_ext — Unknown extension: unknown_ext

🚀 启动 Engine: module=equipment, mode=full
...

# API Key 缺失
$ python demo.py --module equipment
❌ 执行 failed: ANTHROPIC_API_KEY not set

# 中断恢复
$ python demo.py --module equipment --mode resume --run-id engine-a1b2c3d4
```

## 6. 性能基准

| 场景 | 耗时 | Token 消耗 |
|------|------|-----------|
| Dry run | <0.1s | 0 |
| Mock LLM (9 Phase) | ~2s | 0 |
| Core only (1 page, 9 Phase) | ~60s | ~50K |
| Core + Audit (1 page) | ~65s | ~50K |
| Core + All Extensions (1 page) | ~70s | ~50K |
| Core only (4 pages, 9 Phase) | ~180s | ~150K |

Extensions 的开销很小 (<10%)，因为它们主要在 Core 执行完成后运行。

## 7. 架构对照

| 启动方式 | Core | Extensions | Platform |
|----------|------|------------|----------|
| `python -m aitest.server.main` | ✅ | ✅ (全部) | ✅ (全部) |
| `python demo.py -m equipment` | ✅ | ❌ | ❌ |
| `python demo.py -m equipment -e audit` | ✅ | ✅ (audit) | ❌ |
| `python demo.py -m equipment -e audit complexity` | ✅ | ✅ (audit+complexity) | ❌ |
| `python demo.py -m equipment --mock-llm` | ✅ (Mock) | ❌ | ❌ |
