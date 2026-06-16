#!/usr/bin/env python3
"""
代码质量扫描器 — AST 深度扫描 + grep 精确匹配

检测维度:
  Level 1 (阻塞) — 绝对 XPath, time.sleep, print(), 未继承 BasePage, 重复文件
  Level 2 (警告) — 缺少 navigate(), PageObject 含 assert, 缺少 logger, 缺少 __init__

用法:
    python tools/check_code_quality.py                      # 扫描全部 page/ script/ 目录
    python tools/check_code_quality.py page/system_page/UserManagePage.py  # 单文件
    python tools/check_code_quality.py --staged             # 扫描 git stage 区（给 pre-commit 用）
    python tools/check_code_quality.py --fix-timeout        # 自动修复部分 time.sleep（实验性）
    python tools/check_code_quality.py --json               # JSON 格式输出（给 CI 用）

退出码:
    0 = 全部通过（或仅警告）
    1 = 有阻塞项
"""
import ast
import os
import re
import sys
import json


# ══════════════════════════════════════════════════════════════════════
#  配置
# ══════════════════════════════════════════════════════════════════════

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE_DIRS = ["page"]
SCRIPT_DIRS = ["script"]
SKIP_DIRS = ["__pycache__", ".git", "venv", ".venv", "node_modules"]
SKIP_FILES = ["__init__.py", "conftest.py"]  # conftest 允许少量 sleep

# 允许的 sleep 模式（正则，匹配到的 sleep 不报错）
ALLOWED_SLEEP_PATTERNS = [
    r'time\.sleep\(TIMEOUT_CONFIG\["micro_wait"\]\)',  # BasePage 定义的微等待常量
    r'time\.sleep\(TIMEOUT_CONFIG\["animate_wait"\]\)',  # 动画等待常量
]

# 已知的参照文件（已是最佳实践，检查时跳过）
REFERENCE_FILES = [
    "page/system_page/UserManagePage.py",
    "page/system_page/RoleManagePage.py",
    "page/system_page/SystemLogPage.py",
    "page/system_page/OperationLogPage.py",
]


# ══════════════════════════════════════════════════════════════════════
#  AST 分析器
# ══════════════════════════════════════════════════════════════════════

class PageObjectChecker(ast.NodeVisitor):
    """AST 分析：检查 Page Object 结构性问题（grep 查不了的）"""

    def __init__(self, filepath):
        self.filepath = filepath
        self.class_name = None
        self.has_basepage = False
        self.has_navigate = False
        self.has_init = False
        self.has_logger = False
        self.has_assert = False
        self.has_time_import = False
        self.has_logging_import = False
        self.method_names = []
        self.issues = []

    def visit_Import(self, node):
        for alias in node.names:
            if alias.name == "time":
                self.has_time_import = True
            if alias.name == "logging":
                self.has_logging_import = True
            if alias.name == "base.base_page":
                pass  # 用 from 导入
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        if node.module == "base.base_page":
            for alias in node.names:
                if alias.name == "BasePage":
                    pass  # 在 visit_ClassDef 中检查继承
        if node.module == "logging":
            self.has_logging_import = True
        self.generic_visit(node)

    def visit_ClassDef(self, node):
        self.class_name = node.name
        # 只检查以 Page 结尾的类
        if not self.class_name.endswith("Page"):
            return

        # 检查基类
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id == "BasePage":
                self.has_basepage = True

        # 遍历类内方法
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                self.method_names.append(item.name)
                if item.name == "navigate":
                    self.has_navigate = True
                if item.name == "__init__":
                    self.has_init = True
                    self._check_init(item)
                # 检查方法内是否有 assert
                self._check_assert_in_method(item)

        # 检查类级别的 logger 赋值
        self.generic_visit(node)

    def visit_Assign(self, node):
        """检查 logger = logging.getLogger(__name__)"""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id == "logger":
                self.has_logger = True
        self.generic_visit(node)

    def _check_init(self, node):
        """检查 __init__ 是否调用了 super().__init__"""
        for item in ast.walk(node):
            if isinstance(item, ast.Call):
                if isinstance(item.func, ast.Attribute):
                    if isinstance(item.func.value, ast.Call):
                        call = item.func.value
                        if isinstance(call.func, ast.Name) and call.func.id == "super":
                            if item.func.attr == "__init__":
                                return True
        self.issues.append("[WARN]  __init__ 未调用 super().__init__(driver, timeout)")
        return False

    def _check_assert_in_method(self, node):
        """检查 Page Object 方法中是否包含 assert"""
        for item in ast.walk(node):
            if isinstance(item, ast.Assert):
                self.has_assert = True
                self.issues.append(
                    f"[WARN]  Page Object 包含 assert (行 {item.lineno}) — assert 应只在测试脚本中"
                )
                return

    def report(self):
        """输出 AST 分析结果"""
        lines = []
        if not self.class_name:
            return lines

        is_page_obj = self.class_name.endswith("Page")

        if is_page_obj:
            if not self.has_basepage:
                lines.append(("[ERR]", f"Page Object {self.class_name} 未继承 BasePage"))
            if not self.has_navigate:
                lines.append(("[WARN]", f"{self.class_name} 缺少 navigate() 方法"))
            if not self.has_logger:
                lines.append(("[WARN]", f"{self.class_name} 未定义 logger"))
            if self.has_assert:
                pass  # 已在 _check_assert_in_method 中添加
            if not self.has_init:
                lines.append(("[WARN]", f"{self.class_name} 缺少 __init__ 方法"))

            # 检查日志导入
            if not self.has_logging_import:
                lines.append(("[WARN]", f"{self.class_name} 缺少 import logging"))

        return lines


# ══════════════════════════════════════════════════════════════════════
#  grep 扫描器（精确匹配显式违规）
# ══════════════════════════════════════════════════════════════════════

class GrepScanner:
    """grep-style 精确扫描（比 ast 更准的字符串匹配）"""

    def __init__(self, filepath):
        self.filepath = filepath
        self.content = ""
        self.lines = []
        self._load()

    def _load(self):
        with open(self.filepath, "r", encoding="utf-8", errors="replace") as f:
            self.content = f.read()
            self.lines = self.content.split("\n")

    def find_absolute_xpath(self):
        """绝对 XPath 检测"""
        results = []
        # 模式1: //*[@id="app"]/...
        pat1 = re.compile(r'//\*\[@id=["\']app["\']\]')
        # 模式2: /html/body/div[...]
        pat2 = re.compile(r'/html/body/div\[')

        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if pat1.search(stripped) or pat2.search(stripped):
                # 排除注释行
                if "#" in stripped and (pat1.search(stripped.split("#")[0]) or
                                        pat2.search(stripped.split("#")[0])):
                    results.append((i, stripped.strip()[:100]))
                elif "#" not in stripped:
                    results.append((i, stripped.strip()[:100]))
                elif pat1.search(stripped) or pat2.search(stripped):
                    results.append((i, stripped.strip()[:100]))
        return results

    def find_sleep(self):
        """time.sleep 检测（排除允许的模式和文档字符串）"""
        results = []
        pat = re.compile(r'time\.sleep\(')
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if not stripped:
                continue
            # 跳过注释行和文档字符串
            if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                continue
            if pat.search(stripped):
                # 检查是否在允许列表中
                is_allowed = any(
                    re.search(allow_pat, stripped)
                    for allow_pat in ALLOWED_SLEEP_PATTERNS
                )
                if not is_allowed:
                    results.append((i, stripped.strip()[:100]))
        return results

    def find_print(self):
        """print() 检测（排除注释和文档字符串中的）

        注意: Page Object 中的 print() 是阻塞项，测试脚本中是警告项。
        调用者根据文件路径区分。
        """
        results = []
        # 匹配 "print(" 但在注释/文档字符串中的不算
        pat = re.compile(r'^\s*print\(')
        in_multiline = False
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            if not stripped:
                continue
            # 跟踪多行字符串
            if stripped.startswith('"""') or stripped.startswith("'''"):
                if stripped.count('"""') if stripped.startswith('"""') else stripped.count("'''") < 2:
                    in_multiline = not in_multiline
                continue
            if in_multiline:
                continue
            if stripped.startswith("#"):
                continue
            # 真正的 print 调用
            if pat.search(stripped):
                results.append((i, stripped.strip()[:100]))
        return results

    def is_page_object(self):
        """判断是否 Page Object 文件"""
        return "page" in self.filepath.replace("\\", "/").split("/")

    def find_missing_navigate(self):
        """检查 Page Object 是否缺少 navigate()（仅在已继承 BasePage 的类中检查）"""
        # 在 AST 分析中已经做了，这里只做快速 grep 确认
        return len(re.findall(r'def navigate\(', self.content)) == 0


# ══════════════════════════════════════════════════════════════════════
#  重复文件检测
# ══════════════════════════════════════════════════════════════════════

def find_duplicate_files():
    """检测疑似重复的 .py 文件（_recovered, _copy, _backup 后缀）"""
    results = []
    dup_patterns = [
        (r'_recovered\.py$', 'Git 冲突恢复副本'),
        (r'_copy\.py$',      '手动复制副本'),
        (r'_backup\.py$',    '备份副本'),
        (r' - Copy\.py$',    'Windows 复制副本'),
    ]
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            for pat, desc in dup_patterns:
                if re.search(pat, f):
                    fullpath = os.path.join(root, f)
                    results.append((fullpath, desc))
                    break
    return results


# ══════════════════════════════════════════════════════════════════════
#  扫描入口
# ══════════════════════════════════════════════════════════════════════

def scan_file(filepath):
    """扫描单个文件，返回 (ast_issues, grep_results)"""
    relpath = os.path.relpath(filepath, PROJECT_ROOT)

    # AST 分析
    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            tree = ast.parse(f.read(), filename=filepath)
    except SyntaxError as e:
        return [(relpath, [(f"[ERR]", f"语法错误: {e}")])], [(relpath, [])]

    checker = PageObjectChecker(filepath)
    checker.visit(tree)
    ast_issues = checker.report()

    # grep 扫描
    scanner = GrepScanner(filepath)
    grep_issues = []
    for xpath_line, xpath_text in scanner.find_absolute_xpath():
        grep_issues.append(("[ERR]", f"绝对 XPath (行 {xpath_line}): {xpath_text}"))
    for sleep_line, sleep_text in scanner.find_sleep():
        grep_issues.append(("[ERR]", f"time.sleep (行 {sleep_line}): {sleep_text}"))
    is_po = scanner.is_page_object()
    for print_line, print_text in scanner.find_print():
        severity = "[ERR]" if is_po else "[WARN]"
        grep_issues.append((severity,
            f"{'Page Object: ' if is_po else ''}print() (行 {print_line}): {print_text}"))

    return (relpath, ast_issues), (relpath, grep_issues)


def scan_directory(target_dir):
    """扫描整个目录"""
    all_results = []
    for root, dirs, files in os.walk(target_dir):
        # 跳过隐藏目录和虚拟环境
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS and not d.startswith(".")]
        for f in files:
            if f.endswith(".py") and f not in SKIP_FILES:
                fullpath = os.path.join(root, f)
                # 跳过参考文件
                relpath = os.path.relpath(fullpath, PROJECT_ROOT)
                if relpath.replace("\\", "/") in REFERENCE_FILES:
                    continue
                all_results.append(scan_file(fullpath))
    return all_results


# ══════════════════════════════════════════════════════════════════════
#  报告格式化
# ══════════════════════════════════════════════════════════════════════

def format_report(all_results, dup_files, output_json=False):
    """格式化输出报告"""
    total_blockers = 0
    total_warnings = 0
    blocked_files = []
    warned_files = []
    clean_files = []

    for (relpath_a, ast_issues), (relpath_g, grep_issues) in all_results:
        file_blockers = 0
        file_warnings = 0
        file_lines = []
        has_content = False

        for severity, msg in ast_issues:
            if severity == "[ERR]":
                file_blockers += 1
            else:
                file_warnings += 1
            file_lines.append(f"    {severity} {msg}")
            has_content = True

        for severity, msg in grep_issues:
            if severity == "[ERR]":
                file_blockers += 1
            else:
                file_warnings += 1
            file_lines.append(f"    {severity} {msg}")
            has_content = True

        total_blockers += file_blockers
        total_warnings += file_warnings

        if file_blockers > 0:
            blocked_files.append(relpath_a)
        elif file_warnings > 0:
            warned_files.append(relpath_a)
        else:
            clean_files.append(relpath_a)

    if output_json:
        return json.dumps({
            "blockers": total_blockers,
            "warnings": total_warnings,
            "blocked_files": blocked_files,
            "warned_files": warned_files,
            "clean_files": clean_files,
            "duplicate_files": [{"path": p, "type": d} for p, d in dup_files],
            "passed": total_blockers == 0,
        }, ensure_ascii=False, indent=2)

    # 人类可读报告
    lines = []
    lines.append("")
    lines.append("═══ [BLOCK] 代码质量检查报告 ═══")
    lines.append("")

    has_any_issues = False

    # 重复文件
    if dup_files:
        has_any_issues = True
        lines.append(f"[DIR] 重复文件 ({len(dup_files)})")
        for path, desc in dup_files:
            lines.append(f"    [ERR] {desc}: {os.path.relpath(path, PROJECT_ROOT)}")
        lines.append("")

    # 逐文件输出
    for (relpath_a, ast_issues), (relpath_g, grep_issues) in all_results:
        all_issues = ast_issues + grep_issues
        if not all_issues:
            continue
        has_any_issues = True
        file_blockers = sum(1 for s, _ in all_issues if s == "[ERR]")
        file_warnings = sum(1 for s, _ in all_issues if s != "[ERR]")
        lines.append(f"[FILE] {relpath_a}")
        for severity, msg in all_issues:
            lines.append(f"    {severity} {msg}")
        lines.append("")

    if not has_any_issues:
        lines.append("  全部通过 [PASS]")

    lines.append("════════════════════════════")
    lines.append(f"  扫描文件: {len(all_results)}")
    lines.append(f"  阻塞项:   {total_blockers}")
    lines.append(f"  警告项:   {total_warnings}")
    lines.append(f"  违规文件: {len(blocked_files)}")
    lines.append(f"  警告文件: {len(warned_files)}")
    lines.append(f"  洁净文件: {len(clean_files)}")
    if dup_files:
        lines.append(f"  重复文件: {len(dup_files)}")
    lines.append("")

    if total_blockers > 0:
        lines.append("  [ERR] 检查不通过 — 请修复阻塞项后重试")
        lines.append(f"     违规文件: {', '.join(blocked_files)}")
    else:
        lines.append("  [PASS] 检查通过")

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════
#  CLI 入口
# ══════════════════════════════════════════════════════════════════════

def main():
    import argparse

    parser = argparse.ArgumentParser(description="代码质量扫描器")
    parser.add_argument("target", nargs="?", default=None,
                        help="目标文件或目录 (默认: page/ + script/)")
    parser.add_argument("--staged", action="store_true",
                        help="扫描 git stage 区的 .py 文件（给 pre-commit 用）")
    parser.add_argument("--json", action="store_true",
                        help="JSON 格式输出")
    parser.add_argument("--skip-dup", action="store_true",
                        help="跳过重复文件检测")
    args = parser.parse_args()

    # 检测重复文件
    dup_files = [] if args.skip_dup else find_duplicate_files()

    # 确定扫描目标
    if args.staged:
        # 从 git stage 区获取文件列表
        import subprocess
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACMR"],
            capture_output=True, text=True, cwd=PROJECT_ROOT
        )
        py_files = [
            os.path.join(PROJECT_ROOT, f)
            for f in result.stdout.strip().split("\n")
            if f.endswith(".py") and
            (f.startswith("page/") or f.startswith("script/"))
        ]
        if not py_files:
            print("  无新增/修改的测试文件，跳过")
            return 0
        results = [scan_file(f) for f in py_files]
    elif args.target:
        target = os.path.join(PROJECT_ROOT, args.target)
        if os.path.isfile(target):
            results = [scan_file(target)]
        elif os.path.isdir(target):
            results = scan_directory(target)
        else:
            print(f"错误: 找不到 {target}", file=sys.stderr)
            return 1
    else:
        # 默认扫描 page/ 和 script/
        results = []
        for d in PAGE_DIRS + SCRIPT_DIRS:
            dirpath = os.path.join(PROJECT_ROOT, d)
            if os.path.isdir(dirpath):
                results.extend(scan_directory(dirpath))

    # 输出报告
    report = format_report(results, dup_files, output_json=args.json)
    print(report)

    # 计算阻塞项
    total_blockers = sum(
        sum(1 for s, _ in ast_issues + grep_issues if s == "[ERR]")
        for (_, ast_issues), (_, grep_issues) in results
    ) + len(dup_files)

    return 1 if total_blockers > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
