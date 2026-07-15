#!/usr/bin/env python3
"""
Analyze the knowledge ↔ mcp ↔ platform circular dependency in detail.
"""
import ast
from pathlib import Path
from collections import defaultdict

def analyze_imports_detailed(file_path, target_modules):
    """Extract imports with line numbers and names."""
    imports = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                return imports
            tree = ast.parse(content, filename=str(file_path))

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                if node.module and node.module.startswith('aitest.'):
                    parts = node.module.split('.')
                    if len(parts) > 1 and parts[1] in target_modules:
                        names = [alias.name for alias in node.names] if node.names else []
                        imports.append({
                            'line': node.lineno,
                            'type': 'from',
                            'module': node.module,
                            'target': parts[1],
                            'names': names,
                            'in_function': _is_in_function(node, tree)
                        })
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith('aitest.'):
                        parts = alias.name.split('.')
                        if len(parts) > 1 and parts[1] in target_modules:
                            imports.append({
                                'line': node.lineno,
                                'type': 'import',
                                'module': alias.name,
                                'target': parts[1],
                                'names': [alias.name],
                                'in_function': _is_in_function(node, tree)
                            })
    except Exception as e:
        pass
    return imports

def _is_in_function(node, tree):
    """Check if node is inside a function definition."""
    for parent in ast.walk(tree):
        if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if any(n is node for n in ast.walk(parent)):
                return True
    return False

def main():
    aitest_dir = Path(__file__).parent.parent / 'aitest'

    # Focus on the circular dependency triangle
    modules = {
        'knowledge': ['platform'],
        'mcp': ['knowledge'],
        'platform': ['mcp']
    }

    print('=' * 80)
    print('知识库 ↔ MCP ↔ 平台 三角循环依赖详细分析')
    print('=' * 80)
    print()

    for source_mod, target_mods in modules.items():
        print(f'\n{"=" * 80}')
        print(f'{source_mod.upper()} → {target_mods}')
        print('=' * 80)

        source_dir = aitest_dir / source_mod
        if not source_dir.exists():
            print(f'⚠️  {source_mod} 目录不存在')
            continue

        module_level_count = 0
        function_level_count = 0

        for target_mod in target_mods:
            print(f'\n--- {source_mod} → {target_mod} ---\n')

            found_imports = []

            for py_file in source_dir.rglob('*.py'):
                if '__pycache__' in str(py_file):
                    continue

                imports = analyze_imports_detailed(py_file, [target_mod])

                for imp in imports:
                    if imp['target'] == target_mod:
                        rel_path = py_file.relative_to(aitest_dir)
                        found_imports.append((rel_path, imp))

                        if imp['in_function']:
                            function_level_count += 1
                        else:
                            module_level_count += 1

            # Group by file
            by_file = defaultdict(list)
            for rel_path, imp in found_imports:
                by_file[rel_path].append(imp)

            if not by_file:
                print(f'  ✅ 未找到依赖（可能是误报）')
                continue

            for rel_path in sorted(by_file.keys()):
                print(f'\n  📄 {rel_path}')
                imps = by_file[rel_path]

                # Separate module-level and function-level
                module_imps = [i for i in imps if not i['in_function']]
                func_imps = [i for i in imps if i['in_function']]

                if module_imps:
                    print('    ⚠️  模块级导入 (形成循环):')
                    for imp in sorted(module_imps, key=lambda x: x['line']):
                        if imp['type'] == 'from':
                            names_str = ', '.join(imp['names'][:3])
                            if len(imp['names']) > 3:
                                names_str += f', ... (共 {len(imp["names"])} 个)'
                            print(f'      L{imp["line"]}: from {imp["module"]} import {names_str}')
                        else:
                            print(f'      L{imp["line"]}: import {imp["module"]}')

                if func_imps:
                    print('    ✅ 函数级导入 (延迟加载，不形成循环):')
                    for imp in sorted(func_imps, key=lambda x: x['line']):
                        if imp['type'] == 'from':
                            names_str = ', '.join(imp['names'][:3])
                            if len(imp['names']) > 3:
                                names_str += f', ... (共 {len(imp["names"])} 个)'
                            print(f'      L{imp["line"]}: from {imp["module"]} import {names_str}')
                        else:
                            print(f'      L{imp["line"]}: import {imp["module"]}')

        print(f'\n  📊 统计: 模块级 {module_level_count} 处 | 函数级 {function_level_count} 处')

    print('\n' + '=' * 80)
    print('总结')
    print('=' * 80)
    print('''
三角循环拆分策略:
1. 优先消除模块级导入，保留函数级导入
2. 检查 mcp → knowledge 的必要性（这是关键突破点）
3. 考虑将共享类型/逻辑提取到更底层模块
4. 使用 re-export 或 protocol/abc 解耦
''')

if __name__ == '__main__':
    main()
