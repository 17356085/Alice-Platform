#!/usr/bin/env python
"""Migrate print() calls to logger in aitest/ library code.

Usage:
  python tools/migrate_print_to_logger.py --dry-run       # Preview changes
  python tools/migrate_print_to_logger.py --apply          # Apply changes
  python tools/migrate_print_to_logger.py --target <file>  # Single file

Safety:
  - Skips CLI files (cli/*.py) — print() is legitimate user output there
  - Skips testing/*.py — print() is test instrumentation
  - Skips files that already import logging + have logger
  - Only converts lines that start a statement (not inside strings)
  - Backs up each file as .bak before modifying
"""

import argparse
import re
import sys
from pathlib import Path

# Files/dirs to skip — print() is legitimate user-facing output
SKIP_PATTERNS = [
    "cli/",           # CLI commands — print to terminal
    "testing/",       # Test instrumentation
    "tools/",         # Standalone tools
    "provider_verify.py",  # Standalone verification script
    "__init__.py",    # Package init — usually intentional
    "cost_advisor.py",     # Standalone CLI tool
]

# Files that need print→logger but require manual review
MANUAL_REVIEW = [
    "parallel_runner.py",  # Subprocess orchestration — print used for progress
    "webhook_server.py",   # Standalone server
]


def find_py_files(root: Path) -> list[Path]:
    """Find all .py files in aitest/ that should be processed."""
    aitest_dir = root / "aitest"
    if not aitest_dir.exists():
        print(f"Error: {aitest_dir} not found")
        sys.exit(1)

    files = []
    for py_file in aitest_dir.rglob("*.py"):
        rel = str(py_file.relative_to(root))
        if any(p in rel for p in SKIP_PATTERNS):
            continue
        if any(rel.endswith(m) for m in MANUAL_REVIEW):
            continue
        files.append(py_file)
    return sorted(files)


def file_has_logger(content: str) -> bool:
    """Check if file already has a logger import."""
    return bool(re.search(r'import logging|from.*import.*logging|get_logger|getLogger', content))


def needs_logger_import(content: str, filepath: Path) -> tuple[bool, str]:
    """Determine if we need to add 'import logging' and/or 'logger = ...'."""
    has_import_logging = bool(re.search(r'^import logging', content, re.MULTILINE))
    has_logger_instance = bool(re.search(r'logger\s*=\s*', content))

    if has_import_logging and has_logger_instance:
        return False, content

    lines = content.split('\n')
    new_lines = []
    added_import = False
    added_logger = False

    for i, line in enumerate(lines):
        new_lines.append(line)

        # Add import after last import line
        if not added_import and not has_import_logging:
            # Find last import statement
            if i < len(lines) - 1 and not lines[i + 1].startswith(('import ', 'from ')):
                # Check if this is the last import or if next line is not an import
                remaining_imports = any(
                    l.startswith(('import ', 'from '))
                    for l in lines[i + 1:i + 5]
                )
                if not remaining_imports and line.strip():
                    new_lines.append('import logging')
                    added_import = True
                    continue

        # Add logger after imports, before first code
        if added_import and not added_logger and not has_logger_instance:
            if line.strip() and not line.startswith(('#', 'import ', 'from ', '"', "'")):
                # Don't insert right before a class/function if we can help it
                pass  # We'll insert at a better position

    if added_import and not added_logger and not has_logger_instance:
        # Insert logger = logging.getLogger(__name__) after the last import
        result_lines = []
        last_import_idx = -1
        for i, line in enumerate(new_lines):
            if line.startswith(('import ', 'from ')):
                last_import_idx = i
        for i, line in enumerate(new_lines):
            result_lines.append(line)
            if i == last_import_idx:
                result_lines.append('')
                result_lines.append('logger = logging.getLogger(__name__)')
        return True, '\n'.join(result_lines)

    return added_import, '\n'.join(new_lines)


def replace_prints(content: str) -> tuple[str, int]:
    """Replace print(...) calls with logger.info/debug.

    Heuristics:
      - print(f"[ERROR] ...")  → logger.error(...)
      - print(f"[WARN] ...")   → logger.warning(...)
      - print(f"[DEBUG] ...")  → logger.debug(...)
      - print(traceback...)    → logger.error(..., exc_info=True)
      - print(...)             → logger.info(...)

    Only matches print at the start of a line (possibly indented).
    Skips print() inside string literals.
    """
    lines = content.split('\n')
    new_lines = []
    count = 0

    # Pattern: start of line, optional whitespace, print(
    print_pattern = re.compile(r'^(\s*)print\((.*)\)\s*$')

    for line in lines:
        m = print_pattern.match(line)
        if not m:
            new_lines.append(line)
            continue

        indent = m.group(1)
        args = m.group(2).strip()

        # Skip if this looks like print inside a string (heuristic)
        if '"""' in line or "'''" in line:
            new_lines.append(line)
            continue

        # Determine log level
        args_lower = args.lower()
        if any(kw in args_lower for kw in ['[error]', 'error', 'traceback', 'exception', 'fail']):
            level = 'error'
        elif any(kw in args_lower for kw in ['[warn]', 'warn', 'warning']):
            level = 'warning'
        elif any(kw in args_lower for kw in ['[debug]', 'debug']):
            level = 'debug'
        else:
            level = 'info'

        # Build replacement
        if level == 'error' and ('traceback' in args_lower or 'exc_info' in args_lower):
            new_line = f'{indent}logger.error({args}, exc_info=True)'
        else:
            new_line = f'{indent}logger.{level}({args})'

        new_lines.append(new_line)
        count += 1

    return '\n'.join(new_lines), count


def process_file(filepath: Path, dry_run: bool = True) -> int:
    """Process a single file. Returns number of replacements made."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  SKIP {filepath}: read error: {e}")
        return 0

    if not file_has_logger(content):
        print(f"  SKIP {filepath}: no logger import found (needs manual setup)")
        return 0

    new_content, count = replace_prints(content)

    if count == 0:
        return 0

    if dry_run:
        print(f"  WOULD REPLACE {count} print() calls in {filepath.name}")
        return count

    # Backup
    bak_path = filepath.with_suffix('.py.bak')
    filepath.rename(bak_path)

    # Write new
    filepath.write_text(new_content, encoding='utf-8')
    print(f"  REPLACED {count} print() → logger in {filepath.name} (backup: {bak_path.name})")
    return count


def main():
    parser = argparse.ArgumentParser(description="Migrate print() to logger calls")
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Preview changes without applying (default)")
    parser.add_argument("--apply", action="store_true", dest="apply_changes",
                        help="Actually apply the changes")
    parser.add_argument("--target", type=str,
                        help="Process a single file (relative to repo root)")
    args = parser.parse_args()

    dry_run = not args.apply_changes

    root = Path.cwd()
    # Ensure we're in the Alice repo root
    if not (root / "aitest").exists():
        # Try parent
        root = root.parent
        if not (root / "aitest").exists():
            print("Error: must run from Alice repo root")
            sys.exit(1)

    if args.target:
        files = [root / args.target]
    else:
        files = find_py_files(root)

    total_replacements = 0
    files_modified = 0

    print(f"\n{'DRY RUN' if dry_run else 'APPLYING'}: Scanning {len(files)} files...\n")

    for f in files:
        count = process_file(f, dry_run=dry_run)
        if count > 0:
            total_replacements += count
            files_modified += 1

    print(f"\n{'Would replace' if dry_run else 'Replaced'} "
          f"{total_replacements} print() calls across {files_modified} files.")

    if dry_run and total_replacements > 0:
        print("Run with --apply to apply changes.")


if __name__ == "__main__":
    main()
