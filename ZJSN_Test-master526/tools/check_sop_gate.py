#!/usr/bin/env python3
"""
SOP 门禁检查器 — 验证当前 Agent 是否满足前置 Phase 条件

每个 Agent 启动前调用本脚本验证门禁。门禁不通过 → 拒绝执行，引导走 /full-sop。

用法:
    python tools/check_sop_gate.py --module tank --agent automation-agent
    python tools/check_sop_gate.py --module equipment --agent test-design-agent --page alarm-config
    python tools/check_sop_gate.py --module tank --agent knowledge-agent --json
    python tools/check_sop_gate.py --module tank --agent execution-agent --project web-automation

退出码:
    0 = 门禁通过，可以执行
    1 = 门禁阻断，前置 Phase 未完成
    2 = 参数错误
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional


# ══════════════════════════════════════════════════════════════════════
#  配置
# ══════════════════════════════════════════════════════════════════════

# 脚本所在目录 → ZJSN_Test-master526/tools/
SCRIPT_DIR = Path(__file__).resolve().parent
# → ZJSN_Test-master526/
PROJECT_CODE_DIR = SCRIPT_DIR.parent
# → WorkStudy/
WORKSTUDY_DIR = PROJECT_CODE_DIR.parent

GOVERNANCE_DIR = WORKSTUDY_DIR / "governance"
CONTEXT_DIR = GOVERNANCE_DIR / "context"
ARTIFACTS_DIR = GOVERNANCE_DIR / "artifacts"

# Agent → 前置 Phase 门禁定义
# 每个 agent 定义其上游必须满足的条件
AGENT_GATES = {
    "project-agent": {
        "label": "Project Init (Phase 0)",
        "upstream_phase": None,  # 无前置依赖，始终允许
        "checks": [],  # 无检查项
        "help": "project-agent 无前置依赖，始终可执行",
    },
    "requirement-agent": {
        "label": "Module Modeling (Phase 0.5)",
        "upstream_phase": "Project Init",
        "checks": [
            {
                "type": "file_exists",
                "path_template": "{context_dir}/projects/{project}/PROJECT_CONTEXT.md",
                "label": "PROJECT_CONTEXT.md",
                "help": "请先执行 /project-agent 或 /full-sop mode=full",
            },
            {
                "type": "file_exists",
                "path_template": "{context_dir}/projects/{project}/MODULE_INDEX.md",
                "label": "MODULE_INDEX.md",
                "help": "请先执行 /project-agent",
            },
        ],
    },
    "test-design-agent": {
        "label": "Test Design (Phase 1~2.5)",
        "upstream_phase": "Module Modeling",
        "checks": [
            {
                "type": "file_exists",
                "path_template": "{context_dir}/projects/{project}/PROJECT_CONTEXT.md",
                "label": "PROJECT_CONTEXT.md",
                "help": "请先执行 /project-agent",
            },
            {
                "type": "file_nonempty",
                "path_template": "{context_dir}/projects/{project}/modules/{module}/MODULE_CONTEXT.md",
                "label": "MODULE_CONTEXT.md (非空)",
                "help": "请先执行 /requirement-agent 或 /full-sop mode=from-requirement",
            },
        ],
    },
    "automation-agent": {
        "label": "Automation (Phase 3~4)",
        "upstream_phase": "Test Design",
        "checks": [
            {
                "type": "file_nonempty",
                "path_template": "{context_dir}/projects/{project}/modules/{module}/pages/{page}/PAGE_CONTEXT.md",
                "label": "PAGE_CONTEXT.md (非空)",
                "help": "请先对 {page} 页面执行 /test-design-agent 或 /full-sop",
            },
            {
                "type": "file_nonempty",
                "path_template": "{context_dir}/projects/{project}/modules/{module}/pages/{page}/TEST_CASES.md",
                "label": "TEST_CASES.md (非空)",
                "help": "请先对 {page} 页面执行 /test-design-agent",
            },
        ],
    },
    "execution-agent": {
        "label": "Execution (Phase 4.5~7)",
        "upstream_phase": "Automation",
        "checks": [
            {
                "type": "any_file_matches",
                "path_template": "{code_dir}/page/{module}_page/*.py",
                "label": "至少一个 PageObject .py 文件",
                "help": "请先执行 /automation-agent 生成 PageObject 代码",
            },
            {
                "type": "any_file_matches",
                "path_template": "{code_dir}/script/{module}/*.py",
                "label": "至少一个 test_*.py 文件",
                "help": "请先执行 /automation-agent 生成测试脚本",
            },
        ],
    },
    "bug-analysis-agent": {
        "label": "Bug Analysis (Phase 4.5~7, 条件性)",
        "upstream_phase": "Execution (有失败)",
        "checks": [
            {
                "type": "dir_nonempty",
                "path_template": "{code_dir}/allure-results",
                "label": "allure-results/ 目录存在且非空",
                "help": "请先执行 /execution-agent 运行测试",
            },
        ],
    },
    "report-agent": {
        "label": "Report (Phase 8)",
        "upstream_phase": "Execution (成功) 或 Bug Analysis",
        "checks": [
            {
                "type": "dir_nonempty",
                "path_template": "{code_dir}/allure-results",
                "label": "allure-results/ 目录存在且非空",
                "help": "请先执行 /execution-agent 运行测试",
            },
        ],
    },
    "knowledge-agent": {
        "label": "Knowledge (Phase 9, 横向贯穿)",
        "upstream_phase": "任意 Phase 完成后",
        "checks": [
            {
                "type": "file_exists",
                "path_template": "{context_dir}/projects/{project}/PROJECT_CONTEXT.md",
                "label": "PROJECT_CONTEXT.md",
                "help": "knowledge-agent 至少需要项目上下文存在",
            },
        ],
    },
}

# 兼容旧的 agent 名称映射
AGENT_ALIASES = {
    "analysis-agent": "requirement-agent",  # deprecated → requirement
    "design-agent": "test-design-agent",    # deprecated → test-design
    "code-agent": "automation-agent",        # deprecated → automation
    "diagnosis-agent": "bug-analysis-agent", # deprecated → bug-analysis
}


# ══════════════════════════════════════════════════════════════════════
#  检查函数
# ══════════════════════════════════════════════════════════════════════

def _format_path(template: str, context_dir: str, code_dir: str, project: str, module: str, page: Optional[str]) -> str:
    """Fill template path with actual values."""
    return template.format(
        context_dir=context_dir,
        code_dir=code_dir,
        project=project,
        module=module,
        page=page or "{page}",  # if page is None, leave placeholder for error messages
    )


def _has_page_in_status(status_data: dict, module: str, page: Optional[str]) -> bool:
    """Check if page status exists in SOP_STATUS file."""
    # Check sub_pages top-level key
    sub_pages = status_data.get("sub_pages", {})
    if not sub_pages:
        # Also check legacy pages array
        pages = status_data.get("pages", [])
        for p in pages:
            if p.get("slug") == page or p.get("name") == page:
                return True
        return False

    # Check sub_pages keys
    if page and page in sub_pages:
        page_status = sub_pages[page].get("status", "")
        return page_status in ("completed", "code_complete_docs_pending", "code_ready_env_blocked")

    return False


def run_check(check: dict, context_dir: str, code_dir: str, project: str, module: str, page: Optional[str]) -> tuple[bool, str]:
    """
    Execute a single gate check.
    Returns (passed: bool, message: str).
    """
    check_type = check["type"]
    label = check["label"]
    path = _format_path(check["path_template"], context_dir, code_dir, project, module, page)
    help_msg = check.get("help", "").format(module=module, page=page or "?")

    if check_type == "file_exists":
        if os.path.isfile(path):
            return True, f"[PASS] {label}: {path}"
        return False, f"[FAIL] {label}: file not found -> {path}\n   [HINT] {help_msg}"

    elif check_type == "file_nonempty":
        if not os.path.isfile(path):
            return False, f"[FAIL] {label}: file not found -> {path}\n   [HINT] {help_msg}"
        try:
            size = os.path.getsize(path)
        except OSError:
            return False, f"[FAIL] {label}: cannot read file -> {path}"
        if size < 50:  # less than 50 bytes is effectively empty/template-only
            return False, f"[FAIL] {label}: file empty or too small ({size} bytes) -> {path}\n   [HINT] {help_msg}"
        return True, f"[PASS] {label}: {path} ({size} bytes)"

    elif check_type == "any_file_matches":
        import glob as glob_mod
        matches = glob_mod.glob(path)
        if matches:
            return True, f"[PASS] {label}: found {len(matches)} file(s) -> {matches[0]} ..."
        return False, f"[FAIL] {label}: no matching files -> {path}\n   [HINT] {help_msg}"

    elif check_type == "dir_nonempty":
        if not os.path.isdir(path):
            return False, f"[FAIL] {label}: directory not found -> {path}\n   [HINT] {help_msg}"
        contents = os.listdir(path)
        if contents:
            return True, f"[PASS] {label}: {path} ({len(contents)} files)"
        return False, f"[FAIL] {label}: directory empty -> {path}\n   [HINT] {help_msg}"

    return False, f"[WARN] unknown check type: {check_type}"


def check_sop_gate(
    agent: str,
    module: str,
    project: str = "web-automation",
    page: Optional[str] = None,
) -> dict:
    """
    Main gate check function.
    Returns a dict with:
        - passed: bool
        - agent: str
        - module: str
        - page: str or null
        - upstream_phase: str or null
        - checks: list of {label, passed, message}
        - blocked: bool (True if gate is blocked)
        - summary: str
        - recommendation: str
    """
    # Resolve aliases
    agent = AGENT_ALIASES.get(agent, agent)

    gate_def = AGENT_GATES.get(agent)
    if gate_def is None:
        return {
            "passed": False,
            "blocked": True,
            "agent": agent,
            "module": module,
            "page": page,
            "upstream_phase": None,
            "checks": [],
            "summary": f"未知 Agent: {agent}",
            "recommendation": f"支持的 Agent: {', '.join(sorted(AGENT_GATES.keys()))}",
        }

    context_dir = str(CONTEXT_DIR)
    code_dir = str(PROJECT_CODE_DIR)

    # No upstream dependency → always pass
    if not gate_def["checks"]:
        return {
            "passed": True,
            "blocked": False,
            "agent": agent,
            "module": module,
            "page": page,
            "upstream_phase": None,
            "checks": [],
            "summary": f"{agent} 无前置 Phase 依赖，门禁通过",
            "recommendation": "可以执行",
        }

    # Run each check (skip page-specific checks if page is None — fix mode)
    check_results = []
    all_passed = True
    skipped_checks = []

    for check_def in gate_def["checks"]:
        # Skip page-specific checks if page is not provided (e.g., automation-agent fix mode)
        if "{page}" in check_def.get("path_template", "") and not page:
            skipped_checks.append({
                "label": check_def["label"],
                "passed": True,
                "message": f"[SKIP] {check_def['label']}: page not specified, skipping page-level check (fix mode)",
            })
            continue

        passed, message = run_check(check_def, context_dir, code_dir, project, module, page)
        check_results.append({
            "label": check_def["label"],
            "passed": passed,
            "message": message,
        })
        if not passed:
            all_passed = False

    # Append skipped checks to results (informational)
    for sc in skipped_checks:
        check_results.append(sc)

    # If page-specific checks were skipped, add module-level fallback for automation-agent
    if skipped_checks and agent == "automation-agent":
        # Add module-level code existence check as fallback
        import glob as glob_mod
        page_dir = os.path.join(code_dir, f"page/{module}_page")
        script_dir = os.path.join(code_dir, f"script/{module}")
        page_files = glob_mod.glob(os.path.join(page_dir, "*.py")) if os.path.isdir(page_dir) else []
        script_files = glob_mod.glob(os.path.join(script_dir, "*.py")) if os.path.isdir(script_dir) else []
        has_code = len(page_files) > 0 or len(script_files) > 0
        check_results.append({
            "label": "Module code files (fix mode fallback)",
            "passed": has_code,
            "message": f"[{'PASS' if has_code else 'FAIL'}] Module code: {len(page_files)} PageObject(s), {len(script_files)} test script(s) → {'fix-ready' if has_code else 'no code to fix'}",
        })
        if not has_code:
            all_passed = False

    # Also check SOP_STATUS if it exists (bonus: additional context)
    status_path = ARTIFACTS_DIR / f"SOP_STATUS_{module}.json"
    sop_status_note = ""
    if status_path.exists():
        try:
            with open(status_path, "r", encoding="utf-8") as f:
                status_data = json.load(f)
            current_phase = status_data.get("current_phase", "unknown")
            completed = status_data.get("completed_phases", [])
            sop_status_note = f"\n[SOP_STATUS] current_phase={current_phase}, completed={len(completed)} phases"
        except (json.JSONDecodeError, OSError):
            sop_status_note = "\n[WARN] SOP_STATUS file corrupted, cannot read"

    # Build recommendation
    if all_passed:
        summary = f"[PASS] {gate_def['label']} gate passed - all upstream artifacts ready"
        recommendation = "Agent can proceed"
    else:
        failed_labels = [c["label"] for c in check_results if not c["passed"]]
        summary = f"[BLOCKED] {gate_def['label']} gate blocked - missing: {', '.join(failed_labels)}"
        recommendation = f"Complete upstream phase ({gate_def.get('upstream_phase', 'unknown')}) first. Recommend: /full-sop module={module}"

    return {
        "passed": all_passed,
        "blocked": not all_passed,
        "agent": agent,
        "module": module,
        "page": page,
        "upstream_phase": gate_def.get("upstream_phase"),
        "checks": check_results,
        "summary": summary + sop_status_note,
        "recommendation": recommendation,
    }


# ══════════════════════════════════════════════════════════════════════
#  CLI
# ══════════════════════════════════════════════════════════════════════

def main():
    # Force UTF-8 output on Windows
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    parser = argparse.ArgumentParser(
        description="SOP 门禁检查器 — 验证当前 Agent 是否满足前置 Phase 条件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python tools/check_sop_gate.py --module tank --agent automation-agent
  python tools/check_sop_gate.py --module equipment --agent test-design-agent --page alarm-config
  python tools/check_sop_gate.py --module tank --agent knowledge-agent --json

退出码:
  0 = 门禁通过
  1 = 门禁阻断
  2 = 参数错误
        """,
    )
    parser.add_argument("--module", "-m", required=True, help="模块名 (e.g. tank, equipment)")
    parser.add_argument("--agent", "-a", required=True, help="Agent 名 (e.g. automation-agent, test-design-agent)")
    parser.add_argument("--page", "-p", default=None, help="页面名 (e.g. alarm-config). automation-agent/test-design-agent 需要")
    parser.add_argument("--project", default="web-automation", help="项目名 (default: web-automation)")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")
    parser.add_argument("--quiet", "-q", action="store_true", help="静默模式，仅输出结果")

    args = parser.parse_args()

    # Page is required for test-design-agent (always per-page)
    page_required_agents = {"test-design-agent", "design-agent"}
    resolved_agent = AGENT_ALIASES.get(args.agent, args.agent)
    if resolved_agent in page_required_agents and not args.page:
        print(f"[ERROR] {args.agent} requires --page parameter", file=sys.stderr)
        print(f"   Usage: python tools/check_sop_gate.py --module {args.module} --agent {args.agent} --page <page_name>", file=sys.stderr)
        sys.exit(2)
    # automation-agent: page is optional (fix mode doesn't need it; generate mode should provide it for full checks)
    if resolved_agent == "automation-agent" and not args.page:
        print(f"[INFO] automation-agent called without --page (likely fix mode). Page-level artifact checks skipped.", file=sys.stderr)

    result = check_sop_gate(
        agent=args.agent,
        module=args.module,
        project=args.project,
        page=args.page,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif not args.quiet:
        lines = []
        lines.append("=" * 58)
        lines.append(f"  SOP Gate Check -- {result['agent']} / {result['module']} / {result.get('page') or '(no page)'}")
        lines.append("  " + "-" * 54)
        lines.append(f"  Upstream Phase: {result.get('upstream_phase') or 'none'}")
        lines.append("  " + "-" * 54)
        for c in result["checks"]:
            lines.append(f"  {c['message'][:120]}")
        lines.append("  " + "-" * 54)
        lines.append(f"  {result['summary']}")
        lines.append(f"  [NEXT] {result['recommendation']}")
        lines.append("=" * 58)
        print("\n".join(lines))

    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
