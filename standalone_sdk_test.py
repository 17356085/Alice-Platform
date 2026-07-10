#!/usr/bin/env python3
"""
独立 SDK 验证脚本（静态检查版）

验证 alice-engine SDK 可以零平台依赖独立运行。
由于 SDK 要求 Python 3.11+，此脚本在 3.10 环境下执行静态检查。

用法:
    python standalone_sdk_test.py
"""

import sys
from pathlib import Path


def main():
    """独立 SDK 验证主函数（静态检查）。"""
    print("=" * 60)
    print("独立 SDK 验证测试（静态检查版）")
    print("=" * 60)
    print()

    # Step 1: 验证 SDK 文件存在
    print("[1/6] 验证 SDK 文件结构...")
    try:
        sdk_root = Path(__file__).parent / "packages/alice-engine"
        if not sdk_root.exists():
            print(f"✗ SDK 目录不存在: {sdk_root}")
            return 1

        required_files = [
            "alice_engine/__init__.py",
            "alice_engine/engine.py",
            "alice_engine/extension.py",
            "alice_engine/extensions/__init__.py",
            "alice_engine/extensions/knowledge.py",
            "alice_engine/extensions/memory.py",
            "alice_engine/runtime/__init__.py",
            "alice_engine/runtime/intelligence/knowledge.py",
            "alice_engine/runtime/intelligence/memory.py",
            "alice_engine/providers/__init__.py",
        ]

        missing = []
        for f in required_files:
            if not (sdk_root / f).exists():
                missing.append(f)

        if missing:
            print(f"✗ 缺失文件: {missing}")
            return 1

        print("✓ SDK 文件结构完整")
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return 1

    # Step 2: 验证零平台依赖
    print("\n[2/6] 验证零平台依赖...")
    try:
        sdk_path = Path(__file__).parent / "packages/alice-engine/alice_engine"

        has_platform_import = False
        for py_file in sdk_path.rglob("*.py"):
            if py_file.name.startswith("test_"):
                continue
            content = py_file.read_text(encoding="utf-8")
            if "from aitest." in content or "import aitest." in content:
                print(f"✗ 发现平台依赖: {py_file}")
                has_platform_import = True

        if not has_platform_import:
            print("✓ SDK 零平台依赖")
        else:
            return 1
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return 1

    # Step 3: 验证 Extensions 导出
    print("\n[3/6] 验证 Extensions 导出...")
    try:
        ext_init = Path(__file__).parent / "packages/alice-engine/alice_engine/extensions/__init__.py"
        content = ext_init.read_text(encoding="utf-8")

        required_exports = [
            "KnowledgeExtension",
            "MemoryExtension",
            "AuditExtension",
            "ComplexityExtension",
        ]

        missing = []
        for exp in required_exports:
            if exp not in content:
                missing.append(exp)

        if missing:
            print(f"✗ 缺失导出: {missing}")
            return 1

        print("✓ Extensions 导出完整（4 个）")
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return 1

    # Step 4: 验证 Runtime 接口
    print("\n[4/6] 验证 Runtime 接口...")
    try:
        runtime_init = Path(__file__).parent / "packages/alice-engine/alice_engine/runtime/__init__.py"
        content = runtime_init.read_text(encoding="utf-8")

        required_interfaces = [
            "KnowledgeStore",
            "InMemoryKnowledgeStore",
            "MemoryStore",
            "InMemoryMemoryStore",
        ]

        missing = []
        for intf in required_interfaces:
            if intf not in content:
                missing.append(intf)

        if missing:
            print(f"✗ 缺失接口: {missing}")
            return 1

        print("✓ Runtime 接口完整（Knowledge + Memory）")
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return 1

    # Step 5: 验证平台 re-export 层
    print("\n[5/6] 验证平台 re-export 层...")
    try:
        platform_ext_init = Path(__file__).parent / "aitest/engine/extensions/__init__.py"
        content = platform_ext_init.read_text(encoding="utf-8")

        if "from alice_engine" not in content:
            print("✗ 平台未从 SDK re-export")
            return 1

        if "from aitest.engine.extensions." in content:
            print("✗ 平台仍有内部导入")
            return 1

        print("✓ 平台正确 re-export SDK Extensions")
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return 1

    # Step 6: 验证 CLI 使用 SDK 导入
    print("\n[6/6] 验证 CLI 使用 SDK 导入...")
    try:
        cli_files = [
            "aitest/cli/adapters/engine_adapter.py",
            "aitest/cli/commands/run.py",
        ]

        has_platform_import = False
        for cli_file in cli_files:
            file_path = Path(__file__).parent / cli_file
            if not file_path.exists():
                continue

            content = file_path.read_text(encoding="utf-8")
            if "from aitest.engine.extensions import" in content:
                print(f"✗ CLI 仍有平台导入: {cli_file}")
                has_platform_import = True

        if has_platform_import:
            return 1

        print("✓ CLI 正确使用 SDK 导入")
    except Exception as e:
        print(f"✗ 检查失败: {e}")
        return 1

    # 总结
    print("\n" + "=" * 60)
    print("✅ 独立 SDK 验证通过（静态检查）")
    print("=" * 60)
    print("\n检查项:")
    print("  ✓ SDK 文件结构完整")
    print("  ✓ SDK 零平台依赖")
    print("  ✓ Extensions 导出完整（Knowledge, Memory, Audit, Complexity）")
    print("  ✓ Runtime 接口完整（KnowledgeStore, MemoryStore）")
    print("  ✓ 平台正确 re-export SDK Extensions")
    print("  ✓ CLI 正确使用 SDK 导入")
    print("\n迁移成果:")
    print("  - KnowledgeExtension 已迁移到 SDK")
    print("  - MemoryExtension 已迁移到 SDK")
    print("  - 平台层改为 re-export 兼容层")
    print("  - CLI 层使用 SDK 公共 API")
    print("\n下一步:")
    print("  1. 在 Python 3.11+ 环境运行功能测试")
    print("  2. SDK PyPI 发布（见 docs/guides/sdk-pypi-publishing.md）")
    print("  3. 性能基准测试")

    return 0


if __name__ == "__main__":
    sys.exit(main())
