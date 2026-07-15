"""轻量级 SCC 检查 — 仅检查 platform 和 mcp 之间的循环依赖."""

import ast
from pathlib import Path
from collections import defaultdict, deque

def get_direct_imports(file_path):
    """提取文件的直接 aitest 子包导入."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 简单的字符串匹配，避免完整 AST 解析的开销
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('from aitest.') or line.startswith('import aitest.'):
                # 提取子包名
                if 'from aitest.' in line:
                    parts = line.split('from aitest.')[1].split()[0].split('.')
                    if parts[0]:
                        imports.add(parts[0])
                elif 'import aitest.' in line:
                    parts = line.split('import aitest.')[1].split()[0].split('.')
                    if parts[0]:
                        imports.add(parts[0])
    except Exception as e:
        pass

    return imports

def build_dep_graph(aitest_dir, target_packages):
    """构建指定包之间的依赖图."""
    graph = defaultdict(set)

    for pkg in target_packages:
        pkg_dir = aitest_dir / pkg
        if not pkg_dir.exists():
            continue

        for py_file in pkg_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue

            imports = get_direct_imports(py_file)
            for imp in imports:
                if imp in target_packages and imp != pkg:
                    graph[pkg].add(imp)

    return graph

def find_cycles(graph, nodes):
    """查找循环依赖."""
    cycles = []

    for start in nodes:
        # BFS 查找从 start 回到 start 的路径
        queue = deque([(start, [start])])
        visited_paths = set()

        while queue:
            node, path = queue.popleft()
            path_key = tuple(path)

            if path_key in visited_paths:
                continue
            visited_paths.add(path_key)

            for neighbor in graph.get(node, set()):
                if neighbor == start and len(path) > 1:
                    # 找到循环
                    cycle = path + [start]
                    cycles.append(cycle)
                elif neighbor not in path and len(path) < 10:  # 限制路径长度
                    queue.append((neighbor, path + [neighbor]))

    return cycles

# 主逻辑
print("🔍 检查 platform ↔ mcp 循环依赖...\n")

aitest_dir = Path(__file__).parent.parent / 'aitest'
target_pkgs = ['platform', 'mcp', 'testing']

graph = build_dep_graph(aitest_dir, target_pkgs)

print("=== 依赖关系 ===")
for pkg in sorted(target_pkgs):
    deps = sorted(graph.get(pkg, set()))
    if deps:
        print(f"{pkg} → {deps}")
    else:
        print(f"{pkg} → (无依赖)")

print("\n=== 循环检测 ===")
cycles = find_cycles(graph, target_pkgs)

if cycles:
    print(f"❌ 发现 {len(cycles)} 个循环:")
    for i, cycle in enumerate(cycles, 1):
        print(f"  {i}. {' → '.join(cycle)}")
else:
    print("✅ 未发现循环依赖")

# 检查 platform ↔ mcp 双向依赖
has_platform_to_mcp = 'mcp' in graph.get('platform', set())
has_mcp_to_platform = 'platform' in graph.get('mcp', set())

print("\n=== platform ↔ mcp 状态 ===")
if has_platform_to_mcp and has_mcp_to_platform:
    print("❌ 存在双向依赖 (循环)")
elif has_platform_to_mcp:
    print("✅ platform → mcp (单向，架构合理)")
elif has_mcp_to_platform:
    print("⚠️  mcp → platform (单向，需要审查)")
else:
    print("✅ 完全独立")

# 检查 testing 模块
print("\n=== testing 模块状态 ===")
testing_deps = graph.get('testing', set())
if not testing_deps:
    print("✅ testing 模块无依赖于 platform/mcp")
elif 'platform' in testing_deps or 'mcp' in testing_deps:
    print(f"⚠️  testing → {sorted(testing_deps)}")
else:
    print(f"ℹ️  testing → {sorted(testing_deps)} (其他依赖)")
