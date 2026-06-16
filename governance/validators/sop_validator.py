"""SOP validator helpers.

Provide reusable checks for workflow and agent gatekeeping.
The rules here intentionally stay small and explicit so callers can
fail closed when a required artifact is missing or empty.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
import re


WORKSTUDY = Path(__file__).resolve().parents[2]
GOVERNANCE = WORKSTUDY / "governance"
PROJECTS = GOVERNANCE / "context" / "projects"
WEB_MODULES = PROJECTS / "web-automation" / "modules"
ARTIFACTS = GOVERNANCE / "artifacts"

# ── SOP Phase 状态机定义 ─────────────────────────────────────────────
# ★ 权威源: aitest/graphs/state.py CANONICAL_PHASES
# 此处为同步副本。修改 Phase 名称/顺序请在 state.py 中修改，然后同步此处。
CANONICAL_PHASES = [
    "Project Init",
    "Requirement",
    "Test Design",
    "Automation",
    "Execute & Debug",
    "Bug Analysis",
    "Data Sanitization",
    "Report",
    "Knowledge",
]

# 每个 Phase 的前置依赖（完成的 Phase 必须是前缀）
PHASE_PREREQUISITES = {
    "Project Init": [],
    "Requirement": ["Project Init"],
    "Test Design": ["Requirement"],
    "Automation": ["Test Design"],
    "Execute & Debug": ["Automation"],
    "Bug Analysis": ["Execute & Debug"],
    "Data Sanitization": ["Execute & Debug", "Bug Analysis"],
    "Report": ["Execute & Debug"],
    "Knowledge": [],  # 可随时触发（横向贯穿）
}

# Phase 别名映射（兼容旧格式名称 → 规范名称）
PHASE_ALIASES = {
    # snake_case 别名
    "project_init": "Project Init",
    "requirement": "Requirement",
    "test_design": "Test Design",
    "automation": "Automation",
    "execute_&_debug": "Execute & Debug",
    "execution": "Execute & Debug",       # 旧名 → 新名
    "bug_analysis": "Bug Analysis",
    "data_sanitization": "Data Sanitization",
    "report": "Report",
    "knowledge": "Knowledge",
    # 旧格式 "Phase N (Description)" → 规范名称
    "Phase 0 (Project Init)": "Project Init",
    "Phase 0.5 (Module Modeling": "Requirement",
    "Phase 0.8": "Requirement",
    "Phase 1 (Page Analysis": "Test Design",
    "Phase 1.5 (Risk Modeling": "Test Design",
    "Phase 2 (Test Design": "Test Design",
    "Phase 2.5 (Test Cases": "Test Design",
    "Phase 3 (Tech Analysis": "Automation",
    "Phase 3.5 (Auto Strategy": "Automation",
    "Phase 3-4 (Automation": "Automation",
    "Phase 4 (Code Generation": "Automation",
    "Phase 4.5": "Bug Analysis",
    "Phase 4.5-7": "Execute & Debug",
    "Phase 5": "Bug Analysis",
    "Phase 6": "Test Design",
    "Phase 7": "Bug Analysis",
    "Phase 8": "Report",
    "Phase 9": "Knowledge",
    "Preflight": None,                     # 隐式阶段，不在 CANONICAL_PHASES 中
}

# 内容级检查的标记词（各文档类型应包含的关键结构）
PAGE_CONTEXT_MARKERS = [
    ("元素", "element"),
    ("定位", "locator"),
    ("等待", "wait"),
]

TEST_CASES_MARKERS = [
    ("用例", "test case"),
    ("预期", "expected"),
]

TECH_ANALYSIS_MARKERS = [
    ("定位器", "locator"),
    ("优先级", "priority"),
    ("等待策略", "wait strategy"),
]

AUTO_STRATEGY_MARKERS = [
    ("覆盖", "coverage"),
    ("自动化", "automation"),
    ("PageObject", "page object"),
]


@dataclass
class CheckResult:
    ok: bool
    message: str
    details: dict[str, Any]


@dataclass
class PageCheckResult:
    """单个页面的检查结果。"""
    page_name: str
    ok: bool
    file_checks: dict[str, bool] = field(default_factory=dict)
    content_checks: dict[str, dict] = field(default_factory=dict)
    missing_files: list[str] = field(default_factory=list)
    empty_files: list[str] = field(default_factory=list)
    content_issues: list[str] = field(default_factory=list)


def module_dir(module_name: str, project: str = "web-automation") -> Path:
    return GOVERNANCE / "context" / "projects" / project / "modules" / module_name


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def _glob_non_empty(paths: list[Path]) -> list[str]:
    return [str(p) for p in paths if p.exists() and p.stat().st_size > 0]


def _glob_existing(paths: list[Path]) -> list[str]:
    return [str(p) for p in paths if p.exists()]


def _normalize_phase_name(name: str) -> str | None:
    """将 phase 名称标准化为规范形式。返回 None 表示该 phase 应被跳过（如 Preflight）。"""
    if name in CANONICAL_PHASES:
        return name
    aliased = PHASE_ALIASES.get(name, name)
    if aliased is None:
        return None  # 隐式阶段，跳过
    return aliased


def _content_has_markers(text: str, marker_pairs: list[tuple[str, str]]) -> dict[str, bool]:
    """检查文本是否包含标记词（大小写不敏感，至少一对中的一个匹配即通过）。"""
    text_lower = text.lower()
    result = {}
    for cn, en in marker_pairs:
        result[cn] = cn in text or en.lower() in text_lower
    return result


# ══════════════════════════════════════════════════════════════════════
#  文件集校验
# ══════════════════════════════════════════════════════════════════════

def validate_file_set(paths: list[Path], *, require_non_empty: bool = False) -> CheckResult:
    matched = _glob_existing(paths)
    if not matched:
        return CheckResult(
            ok=False,
            message="required artifacts missing",
            details={"matched": [], "required_non_empty": require_non_empty},
        )
    if require_non_empty:
        non_empty = _glob_non_empty(paths)
        if len(non_empty) != len(matched):
            return CheckResult(
                ok=False,
                message="some artifacts are empty",
                details={
                    "matched": matched,
                    "non_empty": non_empty,
                    "empty": [p for p in matched if p not in non_empty],
                },
            )
    return CheckResult(
        ok=True,
        message="ok",
        details={"matched": matched, "required_non_empty": require_non_empty},
    )


# ══════════════════════════════════════════════════════════════════════
#  模块级校验
# ══════════════════════════════════════════════════════════════════════

def validate_module_context(module_name: str, project: str = "web-automation") -> CheckResult:
    path = module_dir(module_name, project) / "MODULE_CONTEXT.md"
    if not path.exists():
        return CheckResult(False, "MODULE_CONTEXT.md missing", {"path": str(path)})
    text = _read_text(path)
    page_markers = ["页面", "page", "子页面", "路由", "模块边界"]
    has_structure = any(marker in text for marker in page_markers)
    return CheckResult(
        ok=bool(text.strip()) and has_structure,
        message="ok" if bool(text.strip()) and has_structure else "MODULE_CONTEXT.md lacks structural content",
        details={
            "path": str(path),
            "size": len(text),
            "line_count": text.count("\n") + 1,
            "has_structure": has_structure,
        },
    )


def validate_sop_state(module_name: str) -> CheckResult:
    path = ARTIFACTS / f"SOP_STATUS_{module_name}.json"
    if not path.exists():
        return CheckResult(False, "SOP status file missing", {"path": str(path)})
    try:
        data = json.loads(_read_text(path))
    except json.JSONDecodeError as exc:
        return CheckResult(False, f"invalid JSON: {exc}", {"path": str(path)})
    required = ["module", "status", "completed_phases"]
    missing = [key for key in required if key not in data]
    if missing:
        return CheckResult(False, "SOP status missing required keys", {"path": str(path), "missing": missing})

    # 状态流转校验
    transition_check = _validate_sop_transitions(data.get("completed_phases", []))
    if not transition_check.ok:
        return transition_check

    return CheckResult(
        True,
        "ok",
        {
            "path": str(path),
            "status": data.get("status"),
            "current_phase": data.get("current_phase"),
            "completed_phases": data.get("completed_phases"),
        },
    )


def _validate_sop_transitions(completed_phases: list[str]) -> CheckResult:
    """验证 completed_phases 的状态流转合法性。

    规则：
    1. completed_phases 必须是 CANONICAL_PHASES 的前缀
    2. 不能跳阶段（除非是 Knowledge 这种横向贯穿 phase）
       Note: Bug Analysis 和 Report 不再互斥 — sop_graph.py 中 Report 总是在
       Bug Analysis 之后执行（或跳过 Bug Analysis 直接到 Report），两者是顺序关系。
    """
    if not completed_phases:
        return CheckResult(True, "ok — 无已完成 Phase", {"completed_phases": []})

    normalized = []
    unknown = []
    for p in completed_phases:
        np = _normalize_phase_name(p)
        if np is None:
            continue  # 跳过隐式阶段（如 Preflight）
        if np not in CANONICAL_PHASES:
            unknown.append(p)
        else:
            normalized.append(np)

    if unknown:
        return CheckResult(
            False,
            f"unknown phases in completed_phases: {unknown}",
            {"unknown_phases": unknown, "known": CANONICAL_PHASES},
        )

    # 检查前缀顺序
    seen = set()
    for phase in normalized:
        seen.add(phase)
        for prereq in PHASE_PREREQUISITES.get(phase, []):
            if prereq not in seen:
                return CheckResult(
                    False,
                    f"phase '{phase}' completed but prerequisite '{prereq}' is missing",
                    {
                        "completed": normalized,
                        "violation": f"{phase} requires {prereq}",
                        "missing_prereq": prereq,
                    },
                )

    # 检查是否为规范前缀（允许 Knowledge 在非末尾位置，因为它是横向贯穿的）
    canonical_prefix = []
    for cp in CANONICAL_PHASES:
        if cp in normalized:
            canonical_prefix.append(cp)

    return CheckResult(
        True,
        "ok",
        {
            "completed": normalized,
            "phase_count": len(normalized),
            "is_valid_prefix": True,
        },
    )


# ══════════════════════════════════════════════════════════════════════
#  页面级校验 (存在性 + 内容结构)
# ══════════════════════════════════════════════════════════════════════

def validate_page_bundle(
    module_name: str,
    *,
    require_tech: bool = False,
    require_execution: bool = False,
    require_content_check: bool = False,
    project: str = "web-automation",
) -> CheckResult:
    """检查模块下所有页面的产物完整性。

    参数:
        require_tech: 是否要求 TECH_ANALYSIS.md + AUTO_STRATEGY.md
        require_execution: 是否要求 TEST_DESIGN.md
        require_content_check: 是否进一步检查页面文档的内容结构（而不仅是存在性）
    """
    base = module_dir(module_name, project)
    pages_dir = base / "pages"
    if not pages_dir.exists():
        return CheckResult(False, "pages directory missing", {"path": str(pages_dir)})

    page_dirs = sorted([p for p in pages_dir.iterdir() if p.is_dir()])
    if not page_dirs:
        return CheckResult(
            ok=False,
            message="no page directories found",
            details={"pages_dir": str(pages_dir), "pages_total": 0},
        )
    page_results = []
    missing_pages = []

    required_files = ["PAGE_CONTEXT.md", "TEST_CASES.md"]
    if require_tech:
        required_files += ["TECH_ANALYSIS.md", "AUTO_STRATEGY.md"]
    if require_execution:
        required_files += ["TEST_DESIGN.md"]

    for page_dir in page_dirs:
        per_page_missing = []
        per_page_empty = []
        per_page_content_issues = []

        for filename in required_files:
            target = page_dir / filename
            if not target.exists():
                per_page_missing.append(filename)
            elif target.stat().st_size == 0:
                per_page_empty.append(filename)

        # 内容级检查（可选）
        if require_content_check and not per_page_missing and not per_page_empty:
            page_context_path = page_dir / "PAGE_CONTEXT.md"
            test_cases_path = page_dir / "TEST_CASES.md"
            tech_analysis_path = page_dir / "TECH_ANALYSIS.md"
            auto_strategy_path = page_dir / "AUTO_STRATEGY.md"

            if page_context_path.exists():
                pc_text = _read_text(page_context_path)
                pc_markers = _content_has_markers(pc_text, PAGE_CONTEXT_MARKERS)
                if not all(pc_markers.values()):
                    per_page_content_issues.append(
                        f"PAGE_CONTEXT.md lacks structural content: {[k for k, v in pc_markers.items() if not v]}"
                    )

            if test_cases_path.exists():
                tc_text = _read_text(test_cases_path)
                tc_markers = _content_has_markers(tc_text, TEST_CASES_MARKERS)
                if not all(tc_markers.values()):
                    per_page_content_issues.append(
                        f"TEST_CASES.md lacks structural content: {[k for k, v in tc_markers.items() if not v]}"
                    )

            if require_tech and tech_analysis_path.exists():
                ta_text = _read_text(tech_analysis_path)
                ta_markers = _content_has_markers(ta_text, TECH_ANALYSIS_MARKERS)
                if not all(ta_markers.values()):
                    per_page_content_issues.append(
                        f"TECH_ANALYSIS.md lacks structural content: {[k for k, v in ta_markers.items() if not v]}"
                    )

            if require_tech and auto_strategy_path.exists():
                as_text = _read_text(auto_strategy_path)
                as_markers = _content_has_markers(as_text, AUTO_STRATEGY_MARKERS)
                if not all(as_markers.values()):
                    per_page_content_issues.append(
                        f"AUTO_STRATEGY.md lacks structural content: {[k for k, v in as_markers.items() if not v]}"
                    )

        page_entry = {
            "page": page_dir.name,
            "missing": per_page_missing,
            "empty": per_page_empty,
            "content_issues": per_page_content_issues,
        }
        page_results.append(page_entry)

        if per_page_missing or per_page_empty or per_page_content_issues:
            missing_pages.append(page_dir.name)

    return CheckResult(
        ok=not missing_pages,
        message="ok" if not missing_pages else "some pages are missing required artifacts or have content issues",
        details={
            "pages_total": len(page_dirs),
            "pages_missing": missing_pages,
            "page_results": page_results,
            "required_files": required_files,
            "content_check_enabled": require_content_check,
        },
    )


def validate_page_content(
    module_name: str,
    page_name: str,
    *,
    check_tech: bool = False,
    project: str = "web-automation",
) -> CheckResult:
    """校验单个页面的所有产物内容完整性。

    返回: CheckResult，details 包含每个文件的标记检查结果。
    """
    page_dir = module_dir(module_name, project) / "pages" / page_name
    if not page_dir.exists():
        return CheckResult(False, f"page directory missing: {page_dir}", {"page_name": page_name})

    checks = {}
    all_ok = True

    # PAGE_CONTEXT.md
    pc_path = page_dir / "PAGE_CONTEXT.md"
    if pc_path.exists():
        text = _read_text(pc_path)
        markers = _content_has_markers(text, PAGE_CONTEXT_MARKERS)
        line_count = text.count("\n") + 1
        checks["PAGE_CONTEXT.md"] = {
            "exists": True,
            "non_empty": bool(text.strip()),
            "line_count": line_count,
            "markers": markers,
            "minimal_ok": line_count >= 20 and all(markers.values()),
        }
        if not checks["PAGE_CONTEXT.md"]["minimal_ok"]:
            all_ok = False
    else:
        checks["PAGE_CONTEXT.md"] = {"exists": False, "non_empty": False}
        all_ok = False

    # TEST_CASES.md
    tc_path = page_dir / "TEST_CASES.md"
    if tc_path.exists():
        text = _read_text(tc_path)
        markers = _content_has_markers(text, TEST_CASES_MARKERS)
        line_count = text.count("\n") + 1
        checks["TEST_CASES.md"] = {
            "exists": True,
            "non_empty": bool(text.strip()),
            "line_count": line_count,
            "markers": markers,
            "minimal_ok": line_count >= 15 and all(markers.values()),
        }
        if not checks["TEST_CASES.md"]["minimal_ok"]:
            all_ok = False
    else:
        checks["TEST_CASES.md"] = {"exists": False, "non_empty": False}
        all_ok = False

    # TECH_ANALYSIS.md (仅在要求技术检查时)
    if check_tech:
        ta_path = page_dir / "TECH_ANALYSIS.md"
        if ta_path.exists():
            text = _read_text(ta_path)
            markers = _content_has_markers(text, TECH_ANALYSIS_MARKERS)
            line_count = text.count("\n") + 1
            checks["TECH_ANALYSIS.md"] = {
                "exists": True,
                "non_empty": bool(text.strip()),
                "line_count": line_count,
                "markers": markers,
                "minimal_ok": line_count >= 10 and all(markers.values()),
            }
            if not checks["TECH_ANALYSIS.md"]["minimal_ok"]:
                all_ok = False
        else:
            checks["TECH_ANALYSIS.md"] = {"exists": False, "non_empty": False}
            all_ok = False

        # AUTO_STRATEGY.md
        as_path = page_dir / "AUTO_STRATEGY.md"
        if as_path.exists():
            text = _read_text(as_path)
            markers = _content_has_markers(text, AUTO_STRATEGY_MARKERS)
            line_count = text.count("\n") + 1
            checks["AUTO_STRATEGY.md"] = {
                "exists": True,
                "non_empty": bool(text.strip()),
                "line_count": line_count,
                "markers": markers,
                "minimal_ok": line_count >= 10 and all(markers.values()),
            }
            if not checks["AUTO_STRATEGY.md"]["minimal_ok"]:
                all_ok = False
        else:
            checks["AUTO_STRATEGY.md"] = {"exists": False, "non_empty": False}
            all_ok = False

    return CheckResult(
        ok=all_ok,
        message="ok" if all_ok else "page content incomplete",
        details={"page_name": page_name, "checks": checks},
    )


# ══════════════════════════════════════════════════════════════════════
#  全量模块校验（聚合所有检查）
# ══════════════════════════════════════════════════════════════════════

def validate_module_full(
    module_name: str,
    *,
    check_content: bool = True,
    check_tech: bool = False,
    project: str = "web-automation",
) -> CheckResult:
    """对模块执行全量校验，聚合所有子检查的结果。

    返回: CheckResult，details 包含所有子检查的汇总。
    """
    results = {}

    # 1. SOP 状态
    results["sop_state"] = validate_sop_state(module_name).__dict__

    # 2. MODULE_CONTEXT
    results["module_context"] = validate_module_context(module_name, project).__dict__

    # 3. 页面 bundle（基础）
    results["page_bundle_basic"] = validate_page_bundle(
        module_name, project=project, require_content_check=check_content
    ).__dict__

    # 4. 页面 bundle（技术）
    if check_tech:
        results["page_bundle_tech"] = validate_page_bundle(
            module_name, require_tech=True, require_content_check=check_content, project=project
        ).__dict__

    # 聚合判定
    all_ok = all(
        r.get("ok", False) for r in results.values()
    )

    failed = [k for k, v in results.items() if not v.get("ok", False)]

    return CheckResult(
        ok=all_ok,
        message="all checks passed" if all_ok else f"checks failed: {failed}",
        details={
            "module": module_name,
            "project": project,
            "results": results,
            "failed_checks": failed,
        },
    )


# ══════════════════════════════════════════════════════════════════════
#  CLI（用于独立验证）
# ══════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python sop_validator.py <module_name> [--tech] [--content] [--full]")
        print()
        print("Modes:")
        print("  default     - basic checks (sop_state, module_context, page_bundle)")
        print("  --tech      - include tech artifact checks")
        print("  --content   - enable content-level marker checks")
        print("  --full      - full validation (all checks + content)")
        sys.exit(0)

    module = sys.argv[1]
    opts = set(sys.argv[2:])

    if "--full" in opts:
        result = validate_module_full(module, check_content=True, check_tech=True)
    elif "--tech" in opts and "--content" in opts:
        result = validate_module_full(module, check_content=True, check_tech=True)
    elif "--tech" in opts:
        result = validate_module_full(module, check_content=False, check_tech=True)
    elif "--content" in opts:
        result = validate_module_full(module, check_content=True, check_tech=False)
    else:
        result = validate_module_full(module, check_content=False, check_tech=False)

    print(json.dumps(result.__dict__, ensure_ascii=False, indent=2, default=str))
    sys.exit(0 if result.ok else 1)
