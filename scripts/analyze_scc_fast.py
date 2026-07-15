#!/usr/bin/env python3
"""
Fast SCC Analysis - Focus on core modules involved in refactoring.
"""
import ast
from pathlib import Path
from collections import defaultdict

# Core modules involved in the 6-step refactoring
CORE_MODULES = [
    'platform', 'infra', 'discovery', 'mcp', 'graphs',
    'knowledge', 'audit_engine', 'testing', 'llm', 'adapters', 'runtime'
]

def get_module_imports(file_path):
    """Extract module-level imports."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return imports
            tree = ast.parse(content, filename=str(file_path))

        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('aitest.'):
                    parts = node.module.split('.')
                    if len(parts) > 1 and parts[1] in CORE_MODULES:
                        imports.add(parts[1])
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('aitest.'):
                        parts = alias.name.split('.')
                        if len(parts) > 1 and parts[1] in CORE_MODULES:
                            imports.add(parts[1])
    except:
        pass
    return imports

def tarjan_scc(graph):
    """Tarjan's algorithm."""
    index_counter = [0]
    stack = []
    lowlinks = {}
    index = {}
    on_stack = defaultdict(bool)
    sccs = []

    def strongconnect(node):
        index[node] = index_counter[0]
        lowlinks[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)
        on_stack[node] = True

        for neighbor in graph.get(node, set()):
            if neighbor not in index:
                strongconnect(neighbor)
                lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
            elif on_stack[neighbor]:
                lowlinks[node] = min(lowlinks[node], index[neighbor])

        if lowlinks[node] == index[node]:
            scc = []
            while True:
                w = stack.pop()
                on_stack[w] = False
                scc.append(w)
                if w == node:
                    break
            sccs.append(scc)

    nodes = set(graph.keys()) | {n for neighbors in graph.values() for n in neighbors}
    for pkg in nodes:
        if pkg not in index:
            strongconnect(pkg)

    return sccs

def main():
    aitest_dir = Path(__file__).parent.parent / 'aitest'

    # Build graph
    graph = defaultdict(set)
    file_count = 0

    for pkg in CORE_MODULES:
        pkg_dir = aitest_dir / pkg
        if not pkg_dir.exists():
            continue

        for py_file in pkg_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            file_count += 1
            imports = get_module_imports(py_file)
            for imp in imports:
                if imp != pkg:
                    graph[pkg].add(imp)

    # Find SCCs
    sccs = tarjan_scc(graph)
    sccs.sort(key=len, reverse=True)

    # Print results
    print('=' * 60)
    print('SCC 分析结果 (核心模块)')
    print('=' * 60)
    print(f'分析文件数: {file_count}')
    print(f'核心模块数: {len(CORE_MODULES)}')
    print(f'SCC 数量: {len(sccs)}')
    print(f'最大 SCC 大小: {len(sccs[0]) if sccs else 0}')
    print()

    print('依赖关系:')
    for pkg in sorted(CORE_MODULES):
        deps = sorted(graph.get(pkg, set()))
        print(f'  {pkg} → {deps if deps else "(无依赖)"}')
    print()

    print('=' * 60)
    print('SCC 详情')
    print('=' * 60)
    for i, scc in enumerate(sccs, 1):
        if len(scc) > 1:
            print(f'\n[{i}] SCC 大小 {len(scc)}: {sorted(scc)}')
            print('    循环依赖:')
            for node in sorted(scc):
                deps = sorted(graph.get(node, set()) & set(scc))
                if deps:
                    print(f'      {node} → {deps}')
        else:
            print(f'[{i}] 独立: {scc[0]}')

    print()
    print('=' * 60)
    print('拆分验证')
    print('=' * 60)

    # Check specific refactoring results
    checks = [
        ('platform', 'mcp', 'Step 1'),
        ('platform', 'infra', 'Step 2'),
        ('platform', 'discovery', 'Step 4'),
    ]

    for mod1, mod2, step in checks:
        m1_deps = graph.get(mod1, set())
        m2_deps = graph.get(mod2, set())

        if mod2 in m1_deps and mod1 in m2_deps:
            print(f'❌ {step}: {mod1} ↔ {mod2} 仍存在循环')
        elif mod2 not in m1_deps and mod1 not in m2_deps:
            print(f'✅ {step}: {mod1} ⊥ {mod2} 完全独立')
        else:
            if mod2 in m1_deps:
                print(f'✅ {step}: {mod1} → {mod2} 单向依赖')
            else:
                print(f'✅ {step}: {mod2} → {mod1} 单向依赖')

if __name__ == '__main__':
    main()
