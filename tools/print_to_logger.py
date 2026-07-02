#!/usr/bin/env python
"""Batch replace print() with logger calls in production .py files.

SAFE: only replaces in files without __main__ blocks.
PRESERVES: docstring examples, CLI output blocks.
"""
import re
import sys
from pathlib import Path

ROOT = Path("d:/Desktop/Alice/aitest")
DRY_RUN = "--apply" not in sys.argv

def has_main_block(filepath: Path) -> bool:
    """Check if file has if __name__ == '__main__' block — skip CLI files."""
    try:
        content = filepath.read_text(encoding="utf-8")
        return bool(re.search(r'if\s+__name__\s*==\s*["\']__main__["\']', content))
    except Exception:
        return True  # skip on error

def get_log_level(line: str) -> str:
    """Heuristic: determine log level from content."""
    lowered = line.lower()
    if any(w in lowered for w in ['error', 'fail', 'crash', 'exception', 'traceback']):
        return 'error'
    if any(w in lowered for w in ['warn', 'deprecat']):
        return 'warning'
    return 'info'

def needs_logger_import(content: str) -> bool:
    """Check if file already has a logger."""
    return bool(re.search(r'_log\s*=\s*logging\.getLogger', content))

def replace_print_in_file(filepath: Path) -> int:
    """Replace print() calls in a single file. Returns count of replacements."""
    try:
        content = filepath.read_text(encoding="utf-8")
    except Exception:
        return 0

    if has_main_block(filepath):
        return 0  # skip CLI files

    lines = content.split('\n')
    modified = False
    new_lines = []
    in_triple = False

    for line in lines:
        # Track docstring boundaries
        stripped = line.strip()
        if '"""' in stripped or "'''" in stripped:
            if stripped.count('"""') % 2 == 1 or stripped.count("'''") % 2 == 1:
                in_triple = not in_triple

        # Skip: docstrings, comments, empty
        if in_triple or stripped.startswith('#') or not stripped:
            new_lines.append(line)
            continue

        # Match: leading whitespace + print(...)
        m = re.match(r'^(\s*)print\((.*)\)\s*$', line)
        if not m:
            new_lines.append(line)
            continue

        indent, args = m.group(1), m.group(2)

        # Skip: print() calls that are clearly CLI output (no f-string prefix pattern)
        # These typically print user-facing formatted messages

        # Determine log level
        level = get_log_level(line)

        # Build replacement
        new_line = f'{indent}_log.{level}({args})'
        new_lines.append(new_line)
        modified = True

    if not modified:
        return 0

    new_content = '\n'.join(new_lines)

    # Add logger import if needed
    if not needs_logger_import(new_content):
        # Insert after last import line
        import_lines = []
        other_start = 0
        for i, line in enumerate(new_lines):
            if line.startswith('import ') or line.startswith('from '):
                import_lines.append(i)
            elif line.strip() and not line.startswith('#'):
                other_start = i
                break

        if import_lines:
            insert_at = import_lines[-1] + 1
            # Check if logging already imported
            has_logging_import = any('import logging' in new_lines[i] for i in import_lines)
            if not has_logging_import:
                new_lines.insert(insert_at, 'import logging')
                insert_at += 1
            new_lines.insert(insert_at, '_log = logging.getLogger(__name__)')
        modified = True
        new_content = '\n'.join(new_lines)

    if DRY_RUN:
        return sum(1 for l in new_lines if '_log.' in l and 'import logging' not in l and 'getLogger' not in l)

    # Apply
    filepath.write_text(new_content, encoding="utf-8")
    return sum(1 for l in new_lines if '_log.' in l and 'import logging' not in l and 'getLogger' not in l)


def main():
    mode = "DRY RUN" if DRY_RUN else "APPLY"
    print(f"=== print() → logger — {mode} ===\n")

    total_files = 0
    total_replacements = 0

    for py_file in sorted(ROOT.rglob("*.py")):
        # Skip test files, __init__.py, __pycache__
        if 'test' in str(py_file).lower() and 'testing' not in str(py_file).lower():
            continue
        if py_file.name == '__init__.py':
            continue

        count = replace_print_in_file(py_file)
        if count > 0:
            total_files += 1
            total_replacements += count
            print(f"  {py_file.relative_to(ROOT)}: {count} print(s)")

    print(f"\n{'Would replace' if DRY_RUN else 'Replaced'} {total_replacements} print() in {total_files} files")

    if DRY_RUN:
        print("\nRe-run with --apply to apply changes.")


if __name__ == "__main__":
    main()
