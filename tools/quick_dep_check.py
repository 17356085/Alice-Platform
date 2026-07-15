"""快速依赖检查 — 验证 platform ↔ mcp 循环依赖拆分效果."""

import ast
import sys
from pathlib import Path
from collections import defaultdict

def extract_imports(file_path):
    """提取文件中的 import 语句."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))

        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        return imports
    except Exception as e:
        return set()

def check_module_deps(module_dir):
    """检查模块的一级包依赖."""
    deps = defaultdict(set)
    module_path = Path(module_dir)

    for py_file in module_path.rglob('*.py'):
        if '__pycache__' in str(py_file):
            continue

        # 确定文件属于哪个一级包
        try:
            rel_path = py_file.relative_to(module_path)
            parts = rel_path.parts
            if parts[0] == 'aitest' and len(parts) > 1:
                pkg = parts[1]  # 一级包名
            else:
                continue
        except ValueError:
            continue

        imports = extract_imports(py_file)
        for imp in imports:
            if imp == 'aitest':
                # 需要更详细的分析
                pass

        # 检查对其他 aitest 一级包的依赖
        for imp in imports:
            if imp == 'aitest':
                # 读取文件内容检查具体子包
                try:
                    with open(py_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    for line in content.split('\n'):
                        if 'from aitest.' in line or 'import aitest.' in line:
                            # 提取子包名
                            for token in line.split():
                                if token.startswith('aitest.'):
                                    sub_pkg = token.split('.')[1] if len(token.split('.')) > 1 else None
                                    if sub_pkg and sub_pkg != pkg:
                                        deps[pkg].add(sub_pkg)
                except Exception:
                    pass

    return deps

# 检查 platform 和 mcp 之间的依赖
print("🔍 检查 platform ↔ mcp 循环依赖...\n")

aitest_dir = Path(__file__).parent.parent / 'aitest'
deps = check_module_deps(aitest_dir)

platform_deps = deps.get('platform', set())
mcp_deps = deps.get('mcp', set())

print(f"platform → {sorted(platform_deps)}")
print(f"mcp → {sorted(mcp_deps)}")

has_cycle = 'mcp' in platform_deps and 'platform' in mcp_deps

if has_cycle:
    print("\n❌ 仍存在 platform ↔ mcp 循环依赖")
    sys.exit(1)
elif 'mcp' in platform_deps:
    print("\n⚠️  platform → mcp 单向依赖存在（可接受）")
elif 'platform' in mcp_deps:
    print("\n⚠️  mcp → platform 单向依赖存在（需要继续拆分）")
else:
    print("\n✅ platform ↔ mcp 循环依赖已消除")

# 检查新增的 testing 模块
testing_deps = deps.get('testing', set())
print(f"\ntesting → {sorted(testing_deps)}")

if 'mcp' not in testing_deps and 'platform' not in testing_deps:
    print("✅ testing 模块独立于 mcp 和 platform")
else:
    print("⚠️  testing 仍依赖 mcp 或 platform")
