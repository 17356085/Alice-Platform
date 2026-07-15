#!/usr/bin/env python3
"""
SCC Analysis - Detect Strongly Connected Components in aitest module dependencies.
"""
import ast
from pathlib import Path
from collections import defaultdict


def get_module_level_imports(file_path):
    """Extract module-level imports (excluding function-level imports)."""
    imports = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read(), filename=str(file_path))
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('aitest.'):
                    parts = node.module.split('.')
                    if len(parts) > 1:
                        imports.add(parts[1])
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('aitest.'):
                        parts = alias.name.split('.')
                        if len(parts) > 1:
                            imports.add(parts[1])
    except Exception:
        pass
    return imports


def tarjan_scc(graph):
    """Tarjan's algorithm for finding strongly connected components."""
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
    packages = [
        d.name for d in aitest_dir.iterdir()
        if d.is_dir() and not d.name.startswith('_') and d.name != '__pycache__'
    ]

    # Build dependency graph
    graph = defaultdict(set)
    for pkg in packages:
        pkg_dir = aitest_dir / pkg
        for py_file in pkg_dir.rglob('*.py'):
            if '__pycache__' in str(py_file):
                continue
            imports = get_module_level_imports(py_file)
            for imp in imports:
                if imp in packages and imp != pkg:
                    graph[pkg].add(imp)

    # Find SCCs
    sccs = tarjan_scc(graph)
    sccs.sort(key=len, reverse=True)

    # Print results
    print('=' * 60)
    print('强连通分量 (SCC) 分析')
    print('=' * 60)
    print(f'总模块数: {len(packages)}')
    print(f'SCC 数量: {len(sccs)}')
    print(f'最大 SCC 大小: {len(sccs[0]) if sccs else 0}')
    print()

    print('=' * 60)
    print('SCC 详情 (按大小排序)')
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
            print(f'[{i}] 独立模块: {scc[0]}')

    print()
    print('=' * 60)
    print('统计')
    print('=' * 60)
    circular_modules = sum(len(scc) for scc in sccs if len(scc) > 1)
    independent_modules = len([scc for scc in sccs if len(scc) == 1])
    print(f'循环依赖模块数: {circular_modules}')
    print(f'独立模块数: {independent_modules}')
    print(f'循环依赖占比: {circular_modules / len(packages) * 100:.1f}%')


if __name__ == '__main__':
    main()
