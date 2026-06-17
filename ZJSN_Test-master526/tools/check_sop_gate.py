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

# ══════════════════════════════════════════════════════════════════════
#  BrowserUse checks (W04: BU dimension gate coverage)
# ══════════════════════════════════════════════════════════════════════

BU_SKILL_FILES = [
    # page-observe: new Skill (BrowserUse page structure observation)
    "governance/skills/test-design/page-observe.md",
    # page-object-generator: existing Skill enhanced with browser-use mode
    "governance/skills/automation/page-object-generator.md",
    # self-healing: fixture-based, no standalone Skill file needed
    # see: ZJSN_Test-master526/base/bu_heal_fixture.py
]


def check_bu_imports() -> dict:
    """Check BrowserUse package importability."""
    try:
        import browser_use  # noqa: F401
        return {
            "check": "bu-imports",
            "passed": True,
            "message": "[PASS] browser_use package is importable",
        }
    except ImportError as e:
        return {
            "check": "bu-imports",
            "passed": False,
            "message": f"[FAIL] browser_use not installed: {e}",
            "hint": "pip install browser-use",
        }


def check_bu_skills() -> dict:
    """Check BrowserUse Skill definition files exist."""
    results = []
    all_exist = True
    for skill_rel in BU_SKILL_FILES:
        path = WORKSTUDY_DIR / skill_rel
        if path.exists() and path.stat().st_size > 0:
            results.append(f"[PASS] {skill_rel}")
        else:
            results.append(f"[FAIL] {skill_rel} — missing or empty")
            all_exist = False
    return {
        "check": "bu-skills",
        "passed": all_exist,
        "message": f"{'[PASS]' if all_exist else '[FAIL]'} {sum(1 for r in results if '[PASS]' in r)}/{len(BU_SKILL_FILES)} BU skill files exist",
        "details": results,
        "hint": "Run BU embedding plan Step 2 (Skill definitions)" if not all_exist else None,
    }


def run_bu_checks(check_imports: bool = False, check_skills: bool = False) -> dict:
    """Run BrowserUse dimension gate checks. Returns dict compatible with check_sop_gate()."""
    checks = []
    if check_imports:
        checks.append(check_bu_imports())
    if check_skills:
        checks.append(check_bu_skills())

    if not checks:
        return None

    all_passed = all(c["passed"] for c in checks)
    return {
        "passed": all_passed,
        "blocked": not all_passed,
        "agent": "bu-gate",
        "module": "system",
        "page": None,
        "upstream_phase": "BU Prerequisites",
        "checks": checks,
        "summary": f"[{'PASS' if all_passed else 'BLOCKED'}] BrowserUse prerequisites: "
                   f"{sum(1 for c in checks if c['passed'])}/{len(checks)} checks passed",
        "recommendation": "BU prerequisites met" if all_passed
                          else "Complete BU embedding plan Steps 1-2 first",
    }


# ══════════════════════════════════════════════════════════════════════
#  Prompt Engineering checks (P3: PE dimension gate coverage)
# ══════════════════════════════════════════════════════════════════════

PE_SIX_SECTIONS = [
    "### 目标",
    "### 输入",
    "### 输出",
    "### 规则",
    "### 边界",
    "### 检查清单",
]

PE_SKILL_DIRS = [
    "governance/skills",
    "governance/skills-dev",
]


def _find_skill_files() -> list[Path]:
    """Discover all skill prompt files across test and dev skill dirs."""
    files = []
    for skill_dir_rel in PE_SKILL_DIRS:
        skill_dir = WORKSTUDY_DIR / skill_dir_rel
        if skill_dir.exists():
            for md in skill_dir.rglob("*.md"):
                # Skip README and non-skill files
                if md.name in ("README.md", "prompt-library-index.md"):
                    continue
                files.append(md)
    return sorted(files)


def check_pe_template(skill_path: Path) -> dict:
    """Verify a skill prompt file has the standard six-section template."""
    try:
        content = skill_path.read_text(encoding="utf-8")
    except Exception as e:
        return {
            "skill": str(skill_path.relative_to(WORKSTUDY_DIR)),
            "passed": False,
            "message": f"[FAIL] Cannot read: {e}",
        }

    found = []
    missing = []
    for section in PE_SIX_SECTIONS:
        if section in content:
            found.append(section.replace("### ", ""))
        else:
            missing.append(section.replace("### ", ""))

    score = len(found)
    passed = score >= 4  # At least 4 of 6 sections present

    rel_path = str(skill_path.relative_to(WORKSTUDY_DIR))
    if passed:
        msg = f"[PASS] {rel_path}: {score}/6 sections ({', '.join(found)})"
    else:
        msg = f"[FAIL] {rel_path}: {score}/6 sections — missing: {', '.join(missing)}"

    return {
        "skill": rel_path,
        "passed": passed,
        "score": score,
        "found": found,
        "missing": missing,
        "message": msg,
    }


def check_pe_reviewed(skill_id: str) -> dict:
    """Check if a PROMPT_REVIEW artifact exists for this skill."""
    review_dir = GOVERNANCE_DIR / "artifacts" / "reviews" / skill_id.replace("/", "-")
    if not review_dir.exists():
        # Try system-level review directory
        review_dir = GOVERNANCE_DIR / "artifacts" / "reviews" / "system"

    prompt_reviews = []
    if review_dir.exists():
        prompt_reviews = sorted(
            review_dir.glob("PROMPT_REVIEW*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )

    if prompt_reviews:
        latest = prompt_reviews[0]
        return {
            "skill_id": skill_id,
            "passed": True,
            "message": f"[PASS] {skill_id}: reviewed ({latest.name}, {latest.stat().st_mtime:.0f})",
            "review_file": str(latest.relative_to(WORKSTUDY_DIR)),
        }
    return {
        "skill_id": skill_id,
        "passed": False,
        "message": f"[WARN] {skill_id}: no PROMPT_REVIEW found — never been reviewed",
    }


def check_pe_optimized(skill_id: str) -> dict:
    """Check if a skill has been PE-optimized after review."""
    # Check for .pe-optimized.md files
    skill_dirs = [
        WORKSTUDY_DIR / "governance" / "skills",
        WORKSTUDY_DIR / "governance" / "skills-dev",
    ]
    optimized_files = []
    for sd in skill_dirs:
        if sd.exists():
            optimized_files.extend(sd.rglob("*.pe-optimized.md"))

    # Check for PROMPT_OPTIMIZATION reports
    opt_dir = GOVERNANCE_DIR / "artifacts" / "reviews" / skill_id.replace("/", "-")
    opt_reports = []
    if opt_dir.exists():
        opt_reports = sorted(
            opt_dir.glob("PROMPT_OPTIMIZATION*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    if not opt_reports:
        # Try system-level
        sys_opt = GOVERNANCE_DIR / "artifacts" / "reviews" / "system"
        if sys_opt.exists():
            opt_reports = sorted(
                sys_opt.glob("PROMPT_OPTIMIZATION*.md"),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )

    has_optimized_file = any(skill_id.replace("/", "-") in str(f) for f in optimized_files)
    has_opt_report = len(opt_reports) > 0

    if has_optimized_file or has_opt_report:
        detail_parts = []
        if has_optimized_file:
            detail_parts.append("optimized prompt file exists")
        if has_opt_report:
            detail_parts.append(f"optimization report: {opt_reports[0].name}")
        return {
            "skill_id": skill_id,
            "passed": True,
            "message": f"[PASS] {skill_id}: PE optimized ({'; '.join(detail_parts)})",
        }
    return {
        "skill_id": skill_id,
        "passed": False,
        "message": f"[INFO] {skill_id}: not yet PE-optimized — run automation/prompt-engineering-expert",
    }


def run_pe_checks(
    check_template: bool = False,
    check_reviewed: bool = False,
    check_optimized: bool = False,
    skill_filter: Optional[str] = None,
) -> dict:
    """Run Prompt Engineering dimension gate checks."""
    checks = []

    if check_template:
        skill_files = _find_skill_files()
        if skill_filter:
            skill_files = [f for f in skill_files if skill_filter in str(f)]
        template_results = []
        for sf in skill_files:
            template_results.append(check_pe_template(sf))
        passed_count = sum(1 for r in template_results if r["passed"])
        total = len(template_results)
        failed = [r for r in template_results if not r["passed"]]
        checks.append({
            "check": "pe-template",
            "passed": passed_count == total,
            "score": f"{passed_count}/{total}",
            "message": f"{'[PASS]' if passed_count == total else '[FAIL]'} PE template: {passed_count}/{total} skills have ≥4/6 sections",
            "details": [r["message"] for r in failed][:10] if failed else [],
            "hint": f"{len(failed)} skills need template fixes. Run review/prompt-engineering for details."
                    if failed else None,
        })

    if check_reviewed:
        # Check specific skills from registries
        import yaml
        skill_ids = []
        for registry_rel in ["governance/skills/skill-registry.yaml",
                              "governance/skills-dev/skill-registry-dev.yaml"]:
            reg_path = WORKSTUDY_DIR / registry_rel
            if reg_path.exists():
                try:
                    with open(reg_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    skills = data.get("skills", [])
                    if isinstance(skills, list):
                        skill_ids.extend(s.get("id", "") for s in skills if s.get("id"))
                    elif isinstance(skills, dict):
                        skill_ids.extend(skills.keys())
                except Exception:
                    pass

        if skill_filter:
            skill_ids = [s for s in skill_ids if skill_filter in s]

        reviewed_results = [check_pe_reviewed(sid) for sid in skill_ids]
        reviewed_count = sum(1 for r in reviewed_results if r["passed"])
        total = len(reviewed_results)
        unreviewed = [r for r in reviewed_results if not r["passed"]]
        checks.append({
            "check": "pe-reviewed",
            "passed": reviewed_count == total,
            "score": f"{reviewed_count}/{total}",
            "message": f"{'[PASS]' if reviewed_count == total else '[FAIL]'} PE reviewed: {reviewed_count}/{total} skills have PROMPT_REVIEW",
            "details": [r["message"] for r in unreviewed][:10] if unreviewed else [],
            "hint": f"{len(unreviewed)} skills never reviewed. Run review/prompt-engineering."
                    if unreviewed else None,
        })

    if check_optimized:
        # Check skills that have been reviewed but not optimized
        import yaml
        skill_ids = []
        for registry_rel in ["governance/skills/skill-registry.yaml",
                              "governance/skills-dev/skill-registry-dev.yaml"]:
            reg_path = WORKSTUDY_DIR / registry_rel
            if reg_path.exists():
                try:
                    with open(reg_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                    skills = data.get("skills", [])
                    if isinstance(skills, list):
                        skill_ids.extend(s.get("id", "") for s in skills if s.get("id"))
                    elif isinstance(skills, dict):
                        skill_ids.extend(skills.keys())
                except Exception:
                    pass

        if skill_filter:
            skill_ids = [s for s in skill_ids if skill_filter in s]

        optimized_results = [check_pe_optimized(sid) for sid in skill_ids]
        optimized_count = sum(1 for r in optimized_results if r["passed"])
        total = len(optimized_results)
        not_optimized = [r for r in optimized_results if not r["passed"]]
        checks.append({
            "check": "pe-optimized",
            "passed": optimized_count > 0,  # At least some skills optimized
            "score": f"{optimized_count}/{total}",
            "message": f"{'[PASS]' if optimized_count > 0 else '[INFO]'} PE optimized: {optimized_count}/{total} skills optimized",
            "details": [r["message"] for r in not_optimized][:10] if not_optimized else [],
            "hint": "Run automation/prompt-engineering-expert to optimize prompt quality."
                    if optimized_count == 0 else None,
        })

    if not checks:
        return None

    all_passed = all(c["passed"] for c in checks)
    return {
        "passed": all_passed,
        "blocked": not all_passed,
        "agent": "pe-gate",
        "module": "system",
        "page": None,
        "upstream_phase": "PE Quality",
        "checks": checks,
        "summary": f"[{'PASS' if all_passed else 'BLOCKED'}] Prompt Engineering quality: "
                   f"{sum(1 for c in checks if c['passed'])}/{len(checks)} checks passed",
        "recommendation": "PE quality standards met" if all_passed
                          else "Run review/prompt-engineering → automation/prompt-engineering-expert",
    }


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
    parser.add_argument("--check-progress-sync", action="store_true", help="检查 progress-tracking.md 是否与 SOP_STATUS 同步")
    parser.add_argument("--check-context-freshness", action="store_true", help="检查 context/ + knowledge/ 下所有文档是否与 SOP_STATUS 同步")
    parser.add_argument("--check-bu-imports", action="store_true", help="BrowserUse: 检查 browser_use 依赖是否可导入")
    parser.add_argument("--check-bu-skills", action="store_true", help="BrowserUse: 检查 3 个 BU Skill 定义文件是否存在")
    parser.add_argument("--check-pe-template", action="store_true", help="Prompt Engineering: 检查所有 Skill prompt 是否遵循六段式模板")
    parser.add_argument("--check-pe-reviewed", action="store_true", help="Prompt Engineering: 检查 Skill 是否经过 PROMPT_REVIEW 评审")
    parser.add_argument("--check-pe-optimized", action="store_true", help="Prompt Engineering: 检查 Skill 是否经过 PE 优化")
    parser.add_argument("--check-pe-all", action="store_true", help="Prompt Engineering: 运行全部 3 项 PE 质量检查")
    parser.add_argument("--pe-skill-filter", default=None, help="PE 检查: 仅检查匹配的 Skill (substring match)")

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

    # Progress sync check — verify progress-tracking.md freshness
    if args.check_progress_sync:
        sync_script = WORKSTUDY_DIR / "tools" / "sync_progress.py"
        if sync_script.exists():
            import subprocess as _sp
            result = _sp.run(
                [sys.executable, str(sync_script), "--check"],
                capture_output=True, text=True, timeout=15,
                cwd=str(WORKSTUDY_DIR),
            )
            if args.json:
                print(json.dumps({
                    "check": "progress-sync",
                    "passed": result.returncode == 0,
                    "message": result.stdout.strip() if result.returncode == 0 else result.stderr.strip(),
                }, ensure_ascii=False, indent=2))
            elif not args.quiet:
                status = "[PASS]" if result.returncode == 0 else "[STALE]"
                print(f"  {status} progress-tracking.md: {result.stdout.strip() or result.stderr.strip()}")
            if result.returncode != 0:
                sys.exit(1 if not args.json else 0)
        else:
            if args.json:
                print(json.dumps({"check": "progress-sync", "passed": False, "message": "sync_progress.py not found"}, ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("  [SKIP] sync_progress.py not found")
        if not args.agent or args.agent == "progress-sync":
            sys.exit(0)

    # Context freshness check — verify all context/ + knowledge/ docs
    if args.check_context_freshness:
        sync_script = WORKSTUDY_DIR / "tools" / "sync_progress.py"
        if sync_script.exists():
            import subprocess as _sp
            result = _sp.run(
                [sys.executable, str(sync_script), "--check-context"],
                capture_output=True, text=True, timeout=30,
                cwd=str(WORKSTUDY_DIR),
            )
            if args.json:
                print(json.dumps({
                    "check": "context-freshness",
                    "passed": result.returncode == 0,
                    "message": result.stdout.strip() if result.returncode == 0 else result.stderr.strip(),
                }, ensure_ascii=False, indent=2))
            elif not args.quiet:
                status = "[PASS]" if result.returncode == 0 else "[STALE]"
                print(f"  {status} context/knowledge freshness: {result.stdout.strip() or result.stderr.strip()}")
            if result.returncode != 0:
                sys.exit(1 if not args.json else 0)
        if not args.agent or args.agent == "context-freshness":
            sys.exit(0)

    # W04: BrowserUse dimension checks — run before (or in addition to) standard gate
    if args.check_bu_imports or args.check_bu_skills:
        bu_result = run_bu_checks(check_imports=args.check_bu_imports, check_skills=args.check_bu_skills)
        if args.json:
            print(json.dumps(bu_result, ensure_ascii=False, indent=2))
        elif not args.quiet:
            print("=" * 58)
            print(f"  BrowserUse Gate Check")
            print("  " + "-" * 54)
            for c in bu_result["checks"]:
                print(f"  {c['message']}")
                if "details" in c:
                    for d in c["details"]:
                        print(f"    {d}")
                if c.get("hint"):
                    print(f"    [HINT] {c['hint']}")
            print("  " + "-" * 54)
            print(f"  {bu_result['summary']}")
            print(f"  [NEXT] {bu_result['recommendation']}")
            print("=" * 58)
        # If only BU checks requested (no --agent), exit now
        if not args.agent or args.agent == "bu-gate":
            sys.exit(0 if bu_result["passed"] else 1)
        # Otherwise fall through to standard gate check below

    # P3: Prompt Engineering dimension checks
    pe_run = args.check_pe_all or args.check_pe_template or args.check_pe_reviewed or args.check_pe_optimized
    if pe_run:
        pe_result = run_pe_checks(
            check_template=args.check_pe_all or args.check_pe_template,
            check_reviewed=args.check_pe_all or args.check_pe_reviewed,
            check_optimized=args.check_pe_all or args.check_pe_optimized,
            skill_filter=args.pe_skill_filter,
        )
        if pe_result:
            if args.json:
                print(json.dumps(pe_result, ensure_ascii=False, indent=2))
            elif not args.quiet:
                print("=" * 58)
                print(f"  Prompt Engineering Gate Check")
                print("  " + "-" * 54)
                for c in pe_result["checks"]:
                    print(f"  {c['message']}")
                    for d in c.get("details", []):
                        print(f"    {d}")
                    if c.get("hint"):
                        print(f"    [HINT] {c['hint']}")
                print("  " + "-" * 54)
                print(f"  {pe_result['summary']}")
                print(f"  [NEXT] {pe_result['recommendation']}")
                print("=" * 58)
            # If only PE checks requested (no --agent), exit now
            if not args.agent or args.agent == "pe-gate":
                sys.exit(0 if pe_result["passed"] else 1)
        # Otherwise fall through to standard gate check below

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
