#!/usr/bin/env python
"""Add logger setup to files that have print() but no logging import, then replace print()→logger.

Usage:
  python tools/add_logger_to_files.py --dry-run    # Preview
  python tools/add_logger_to_files.py --apply       # Apply
"""

import argparse
import re
import sys
from pathlib import Path

# Target files: have print() but no logger setup, non-CLI, non-test
TARGET_FILES = [
    "aitest/agents/ab_test.py",
    "aitest/audit_engine/cost_auditor.py",
    "aitest/audit_engine/event_bus.py",
    "aitest/audit_engine/failure_attributor.py",
    "aitest/audit_engine/governance_kpi.py",
    "aitest/audit_engine/qa_loop.py",
    "aitest/audit_engine/review_trigger.py",
    "aitest/audit_engine/scheduled_audit.py",
    "aitest/audit_engine/sop_auditor.py",
    "aitest/audit_engine/step_efficiency.py",
    "aitest/infra/parallel_runner.py",
    "aitest/infra/webhook_server.py",
    "aitest/llm/provider_base.py",
    "aitest/mcp/__init__.py",
    "aitest/mcp/prompts/templates.py",
    "aitest/server/api/chat.py",
]

# Standalone scripts — keep print()
SKIP_FILES = [
    "aitest/provider_verify.py",   # Standalone verification tool
    "aitest/cost_advisor.py",      # Standalone CLI tool
    "aitest/infra/trace.py",       # Debug instrumentation
    "aitest/server/auth.py",       # Auth module — already uses logging
]


def add_logger_import(content: str) -> str:
    """Add 'import logging' and 'logger = logging.getLogger(__name__)' after last import."""
    lines = content.split('\n')

    # Check if already has logger
    if 'logging.getLogger' in content or 'get_logger' in content:
        return content

    # Find the last import line
    last_import_idx = -1
    for i, line in enumerate(lines):
        if re.match(r'^(import |from )', line):
            last_import_idx = i

    if last_import_idx < 0:
        return content  # No imports found, can't safely add

    # Insert after last import
    insert_idx = last_import_idx + 1
    # Skip blank lines after imports
    while insert_idx < len(lines) and lines[insert_idx].strip() == '':
        insert_idx += 1

    new_lines = lines[:insert_idx] + [
        '',
        'import logging',
        '',
        'logger = logging.getLogger(__name__)',
        '',
    ] + lines[insert_idx:]

    return '\n'.join(new_lines)


def replace_prints(content: str) -> tuple[str, int]:
    """Replace print(...) with logger calls based on content heuristics."""
    lines = content.split('\n')
    new_lines = []
    count = 0

    for line in lines:
        m = re.match(r'^(\s*)print\((.*)\)\s*$', line)
        if not m:
            new_lines.append(line)
            continue

        indent = m.group(1)
        args = m.group(2).strip()

        # Skip prints inside strings
        if '"""' in line or "'''" in line:
            new_lines.append(line)
            continue

        # Determine level
        args_lower = args.lower()
        if any(kw in args_lower for kw in ['error', 'traceback', 'exception', 'fail', '✗', '✘', '❌']):
            level = 'error'
        elif any(kw in args_lower for kw in ['warn', 'warning', '⚠']):
            level = 'warning'
        elif any(kw in args_lower for kw in ['debug']):
            level = 'debug'
        else:
            level = 'info'

        new_line = f'{indent}logger.{level}({args})'
        new_lines.append(new_line)
        count += 1

    return '\n'.join(new_lines), count


def process_file(filepath: Path, dry_run: bool = True) -> int:
    """Process single file. Returns replacement count."""
    try:
        content = filepath.read_text(encoding='utf-8')
    except Exception as e:
        print(f"  SKIP {filepath}: {e}")
        return 0

    # Step 1: Add logger import if needed
    if 'import logging' not in content:
        content = add_logger_import(content)
        if 'import logging' not in content:
            print(f"  SKIP {filepath}: could not add logger import")
            return 0

    # Step 2: Replace prints
    new_content, count = replace_prints(content)

    if count == 0:
        return 0

    if dry_run:
        print(f"  WOULD: {filepath.name} — {count} print()→logger")
        return count

    # Backup
    bak = filepath.with_suffix('.py.bak')
    filepath.rename(bak)
    filepath.write_text(new_content, encoding='utf-8')
    print(f"  DONE: {filepath.name} — {count} print()→logger (backup: {bak.name})")
    return count


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--apply", action="store_true", dest="apply_changes")
    args = parser.parse_args()

    dry_run = not args.apply_changes
    root = Path.cwd()

    print(f"\n{'DRY RUN' if dry_run else 'APPLYING'} — {len(TARGET_FILES)} files\n")

    total = 0
    for rel_path in TARGET_FILES:
        f = root / rel_path
        if not f.exists():
            print(f"  SKIP {rel_path}: not found")
            continue
        if any(rel_path.endswith(s) for s in SKIP_FILES):
            continue
        count = process_file(f, dry_run=dry_run)
        total += count

    print(f"\n{'Would replace' if dry_run else 'Replaced'} {total} print() calls.")
    if dry_run and total > 0:
        print("Run with --apply to apply.")


if __name__ == "__main__":
    main()
