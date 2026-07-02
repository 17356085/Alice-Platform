#!/usr/bin/env python3
"""
覆盖率验证器 — 检查测试用例对需求/场景/元素/来源的覆盖质量。

独立于 check_sop_gate.py，供 CI pipeline 和手动调用使用。
输出 JSON 格式，退出码 0=通过, 1=不达标, 2=参数错误。

用法:
  python governance/validators/coverage-checker.py --module equipment --page alarm-config
  python governance/validators/coverage-checker.py --module equipment --page alarm-config --json
  python governance/validators/coverage-checker.py --module equipment --all-pages
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Optional

# 路径配置
SCRIPT_DIR = Path(__file__).resolve().parent
GOVERNANCE_DIR = SCRIPT_DIR.parent
WORKSTUDY_DIR = GOVERNANCE_DIR.parent
CONTEXT_MODULES = GOVERNANCE_DIR / "context" / "projects" / "web-automation" / "modules"

# 默认覆盖率目标（可被 environments.yaml 覆盖）
DEFAULT_TARGETS = {
    "min_p0_cases": 1,
    "min_positive": 1,
    "min_negative": 1,
    "min_boundary": 1,
    "min_element_coverage": 0.90,
    "require_source_field": True,
    "require_e2e": False,
}


def load_coverage_targets(module: str) -> dict:
    """从 environments.yaml 加载模块级覆盖率目标，合并默认值。"""
    targets = dict(DEFAULT_TARGETS)
    env_path = WORKSTUDY_DIR / "governance" / "context" / "environments.yaml"
    if not env_path.exists():
        return targets

    try:
        import yaml
        with open(env_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception:
        return targets

    coverage_cfg = data.get("coverage", {})
    targets.update(coverage_cfg.get("targets", {}))

    # 模块级覆盖
    per_module = coverage_cfg.get("per_module", {})
    if module in per_module:
        targets.update(per_module[module])

    return targets


def parse_test_cases(content: str) -> list[dict]:
    """从 TEST_CASES.md 解析用例列表。返回 [{id, title, priority, type, source, merged_from}, ...]

    支持多种表头格式：用例编号/编号/ID, 用例标题/测试场景/标题, 优先级, 类型, 来源.
    """
    cases = []
    in_table = False
    headers = []

    # Header detection keywords
    _case_id_keys = ("用例编号", "编号", "id", "case id")
    _title_keys = ("用例标题", "测试场景", "标题", "title", "场景名称")
    _priority_keys = ("优先级", "priority")
    _type_keys = ("类型", "type")
    _source_keys = ("来源", "source")

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        # Detect table start — flexible header detection
        if line.startswith("|"):
            header_cells = [h.strip().lower() for h in line.split("|")[1:-1]]
            # Check if this looks like a case table header
            has_case_id = any(k in " ".join(header_cells) for k in _case_id_keys)
            has_priority = any(k in " ".join(header_cells) for k in _priority_keys)
            if has_case_id and has_priority:
                in_table = True
                headers = [h.strip() for h in line.split("|")[1:-1]]
                continue

        if not in_table:
            continue

        # Skip separator line
        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue

        # End of table — non-pipe line or new section header
        if not line.startswith("|"):
            in_table = False
            continue

        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < 4:
            continue

        # Skip if first cell looks like a section header (e.g., "### 1.")
        if cells[0].startswith("#"):
            continue

        case = {"id": cells[0] if len(cells) > 0 else ""}

        # Map cells by header position
        for i, h in enumerate(headers):
            if i >= len(cells):
                break
            hl = h.lower()
            if any(k in hl for k in _priority_keys):
                case["priority"] = cells[i].upper().strip("* ")
            elif any(k in hl for k in _type_keys):
                case["type"] = cells[i].lower().strip("* ")
            elif any(k in hl for k in _source_keys):
                case["source"] = cells[i].lower().strip("* ")
            elif "合并来源" in hl or "merged" in hl:
                case["merged_from"] = cells[i].strip("* ")
            elif any(k in hl for k in _title_keys):
                case["title"] = cells[i].strip("* ")

        # Defaults
        case.setdefault("priority", "")
        case.setdefault("type", "")
        case.setdefault("source", "ai")
        case.setdefault("merged_from", "")

        if case["id"]:
            cases.append(case)

    return cases


def parse_page_elements(content: str) -> list[str]:
    """从 PAGE_CONTEXT.md 提取交互元素描述（用于在 TEST_CASES 中匹配）。

    优先用「元素描述」列（中文如"搜索"/"设备名称"），因为测试用例用自然语言编写。
    回退到「元素ID」列（英文如 btn-search）。
    """
    elements = []
    in_table = False
    headers = []

    for line in content.split("\n"):
        line = line.strip()
        if not line:
            continue

        if line.startswith("|") and ("元素ID" in line or "元素描述" in line or "控件类型" in line):
            in_table = True
            headers = [h.strip() for h in line.split("|")[1:-1]]
            continue

        if not in_table:
            continue

        if re.match(r"^\|[\s\-:|]+\|$", line):
            continue

        if not line.startswith("|"):
            in_table = False
            continue

        cells = [c.strip().strip("`").strip() for c in line.split("|")[1:-1]]
        if cells and len(cells) >= 2:
            desc = cells[1] if cells[1] else ""
            eid = cells[0] if cells[0] else ""
            if desc and desc != eid:
                elements.append(desc.lower())
            elif eid:
                elements.append(eid.lower())

    # Filter out display-only / metadata elements that don't need test coverage
    _display_only_patterns = [
        "列头", "列头：",        # column headers (visual labels, not interactive)
        "总条数", "每页条数",     # pagination metadata
        "分页组件",               # pagination wrapper
        "弹窗标题",               # dialog title label
        "面包屑",                 # breadcrumb
        "搜索区", "表格区", "操作按钮区", "分页区",  # layout regions
        "顶部导航", "左侧菜单",   # shell elements
        "所有列头单元格", "所有数据行",  # aggregate descriptors
        "空数据提示", "加载中",   # state indicators (not elements)
    ]
    filtered = []
    for elem in elements:
        if any(p in elem for p in _display_only_patterns):
            continue
        filtered.append(elem)
    return filtered


def check_coverage(module: str, page: str) -> dict:
    """检查单个页面的覆盖率指标。返回完整结果 dict。"""
    page_dir = CONTEXT_MODULES / module / "pages" / page
    targets = load_coverage_targets(module)

    result = {
        "module": module,
        "page": page,
        "passed": True,
        "checks": [],
        "metrics": {},
    }

    # Check 1: TEST_CASES.md exists
    tc_path = page_dir / "TEST_CASES.md"
    if not tc_path.exists():
        result["checks"].append({
            "check": "test_cases_exists",
            "passed": False,
            "level": "error",
            "message": f"TEST_CASES.md not found: {tc_path}",
        })
        result["passed"] = False
        return result

    try:
        tc_content = tc_path.read_text(encoding="utf-8")
    except Exception as e:
        result["checks"].append({
            "check": "test_cases_readable",
            "passed": False,
            "level": "error",
            "message": f"Cannot read TEST_CASES.md: {e}",
        })
        result["passed"] = False
        return result

    cases = parse_test_cases(tc_content)
    result["metrics"]["total_cases"] = len(cases)

    # Check 2: P0 count
    p0_cases = [c for c in cases if c["priority"] == "P0"]
    min_p0 = targets["min_p0_cases"]
    result["metrics"]["p0_count"] = len(p0_cases)
    result["checks"].append({
        "check": "p0_case_count",
        "passed": len(p0_cases) >= min_p0,
        "level": "warning" if len(p0_cases) < min_p0 else "pass",
        "message": f"P0 cases: {len(p0_cases)}/{min_p0} required",
        "detail": f"P0 cases: {[c['id'] for c in p0_cases]}",
    })

    # Check 3: Type diversity
    pos = [c for c in cases if c["type"] == "positive"]
    neg = [c for c in cases if c["type"] == "negative"]
    bnd = [c for c in cases if c["type"] == "boundary"]
    result["metrics"]["positive_count"] = len(pos)
    result["metrics"]["negative_count"] = len(neg)
    result["metrics"]["boundary_count"] = len(bnd)

    type_pass = (
        len(pos) >= targets.get("min_positive", 1)
        and len(neg) >= targets.get("min_negative", 1)
        and len(bnd) >= targets.get("min_boundary", 1)
    )
    result["checks"].append({
        "check": "scene_type_diversity",
        "passed": type_pass,
        "level": "warning" if not type_pass else "pass",
        "message": f"Type diversity: positive={len(pos)}, negative={len(neg)}, boundary={len(bnd)}",
    })

    # Check 4: Source field present
    has_source = any(c.get("source") and c["source"] != "ai" for c in cases)
    source_ai_count = sum(1 for c in cases if c.get("source") == "ai")
    source_pair_count = sum(1 for c in cases if c.get("source") == "pair")
    source_merged_count = sum(1 for c in cases if c.get("source") == "merged")
    result["metrics"]["source_ai"] = source_ai_count
    result["metrics"]["source_pair"] = source_pair_count
    result["metrics"]["source_merged"] = source_merged_count

    if targets.get("require_source_field", True):
        # All cases should have source field; warn if 100% are ai (no human input)
        is_all_ai = source_ai_count == len(cases) and len(cases) > 0
        result["checks"].append({
            "check": "source_field_present",
            "passed": not is_all_ai,  # pass if at least some non-ai sources exist
            "level": "info" if is_all_ai else "pass",
            "message": f"Source distribution: ai={source_ai_count}, pair={source_pair_count}, merged={source_merged_count}",
            "hint": "Consider creating PAIR_SEEDS.md to inject human seed scenarios" if is_all_ai else None,
        })

    # Check 5: Element coverage (cross-reference with PAGE_CONTEXT)
    pc_path = page_dir / "PAGE_CONTEXT.md"
    if pc_path.exists():
        try:
            pc_content = pc_path.read_text(encoding="utf-8")
            elements = parse_page_elements(pc_content)
            result["metrics"]["total_elements"] = len(elements)

            if elements:
                # Approximate: check if element names appear in test case steps
                tc_text = tc_content.lower()
                referenced = [e for e in elements if e.lower() in tc_text]
                coverage = len(referenced) / len(elements) if elements else 1.0
                result["metrics"]["element_coverage"] = round(coverage, 3)
                min_cov = targets.get("min_element_coverage", 0.90)
                result["checks"].append({
                    "check": "element_coverage",
                    "passed": coverage >= min_cov,
                    "level": "warning" if coverage < min_cov else "pass",
                    "message": f"Element coverage: {len(referenced)}/{len(elements)} ({coverage:.1%}, target {min_cov:.0%})",
                    "detail": f"Unreferenced: {[e for e in elements if e not in referenced][:10]}",
                })
        except Exception:
            pass

    # Check 6: E2E coverage (if required)
    if targets.get("require_e2e", False):
        e2e_cases = [c for c in cases if c.get("type") == "e2e"]
        result["metrics"]["e2e_count"] = len(e2e_cases)
        result["checks"].append({
            "check": "e2e_coverage",
            "passed": len(e2e_cases) > 0,
            "level": "warning",
            "message": f"E2E cases: {len(e2e_cases)} (required for {module})",
        })

    # Check 7: PAIR_SEEDS exists
    pair_seeds_path = page_dir / "PAIR_SEEDS.md"
    result["metrics"]["has_pair_seeds"] = pair_seeds_path.exists()
    result["checks"].append({
        "check": "pair_seeds_exists",
        "passed": True,  # always pass — informational only
        "level": "info",
        "message": f"PAIR_SEEDS.md: {'✅ exists' if pair_seeds_path.exists() else '❌ absent (AI-only generation)'}",
    })

    # Determine overall pass
    # Errors always fail. Warnings are advisory (don't fail).
    errors = [c for c in result["checks"] if c["level"] == "error" and not c["passed"]]
    warnings = [c for c in result["checks"] if c["level"] == "warning" and not c["passed"]]
    result["passed"] = len(errors) == 0
    result["summary"] = (
        f"{'[PASS]' if result['passed'] else '[FAIL]'} "
        f"{module}/{page}: "
        f"{len(cases)} cases, {len(p0_cases)} P0, "
        f"{len(errors)} errors, {len(warnings)} warnings"
    )

    return result


def check_all_pages(module: str) -> list[dict]:
    """检查模块下所有页面的覆盖率。"""
    module_dir = CONTEXT_MODULES / module / "pages"
    if not module_dir.exists():
        print(f"[ERROR] Module directory not found: {module_dir}", file=sys.stderr)
        sys.exit(2)

    results = []
    for page_dir in sorted(module_dir.iterdir()):
        if page_dir.is_dir():
            page = page_dir.name
            results.append(check_coverage(module, page))

    return results


def main():
    if sys.platform == "win32":
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except AttributeError:
            pass

    parser = argparse.ArgumentParser(
        description="覆盖率验证器 — 检查测试用例的覆盖质量",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python governance/validators/coverage-checker.py --module equipment --page alarm-config
  python governance/validators/coverage-checker.py --module equipment --all-pages --json
  python governance/validators/coverage-checker.py --module equipment --page alarm-config --json

退出码:
  0 = 覆盖率达标
  1 = 覆盖率不达标（有 error 级别失败）
  2 = 参数错误
        """,
    )
    parser.add_argument("--module", "-m", required=True, help="模块名 (e.g. equipment)")
    parser.add_argument("--page", "-p", default=None, help="页面名 (e.g. alarm-config)")
    parser.add_argument("--all-pages", action="store_true", help="检查该模块所有页面")
    parser.add_argument("--json", action="store_true", help="JSON 格式输出")

    args = parser.parse_args()

    if args.all_pages:
        results = check_all_pages(args.module)
    elif args.page:
        results = [check_coverage(args.module, args.page)]
    else:
        print("[ERROR] Must specify --page or --all-pages", file=sys.stderr)
        sys.exit(2)

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for r in results:
            print("=" * 58)
            print(f"  Coverage Check — {r['module']}/{r['page']}")
            print("  " + "-" * 54)
            for c in r["checks"]:
                icon = "✅" if c["passed"] else "❌"
                print(f"  {icon} [{c['level'].upper()}] {c['message']}")
                if c.get("hint"):
                    print(f"     💡 {c['hint']}")
                if c.get("detail"):
                    print(f"     📋 {c['detail'][:120]}")
            print("  " + "-" * 54)
            print(f"  {r['summary']}")
            print("=" * 58)

    # Exit code: 0 if all pass, 1 if any fail
    all_pass = all(r["passed"] for r in results)
    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    main()
