"""
Consistency Checker — P2-2: 自动化跨层一致性校验

检测:
  1. agent-definitions.yaml ↔ AGENT_SKILL_MAP 是否同步
  2. skill-registry.yaml 中 active skill 的 .md 文件是否存在
  3. AGENT_SKILL_MAP 引用的 skill 是否在 registry 中注册
  4. PAGE_INTERFACE.yaml 是否比 PAGE_CONTEXT.md 更新（过期检测）
  5. agent 是否引用了已废弃的 skill

用法:
  python -m aitest.consistency_checker                  # 全量检查
  python -m aitest.consistency_checker --json           # JSON 输出 (CI 用)
  aitest check --consistency                            # CLI 入口

返回码: 0=全部通过, 1=发现问题, 2=运行错误
"""

import json
import sys
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

import yaml

WORKSTUDY = Path(__file__).resolve().parent.parent
GOVERNANCE = WORKSTUDY / "governance"
AGENT_DEFS = GOVERNANCE / "agents" / "agent-definitions.yaml"
SKILL_REGISTRY = GOVERNANCE / "skills" / "skill-registry.yaml"
CONTEXT_MODULES = GOVERNANCE / "context" / "projects" / "web-automation" / "modules"


@dataclass
class CheckResult:
    """单次检查结果。"""
    check: str
    ok: bool
    message: str = ""
    details: list[str] = field(default_factory=list)


def _load_yaml(path: Path) -> dict:
    """安全加载 YAML，返回空 dict 如果失败。"""
    if not path.exists():
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except Exception:
        return {}


# ══════════════════════════════════════════════════════════════════════════
#  检查 1: agent-definitions.yaml ↔ AGENT_SKILL_MAP
# ══════════════════════════════════════════════════════════════════════════

def check_agent_skill_sync() -> CheckResult:
    """检查 agent-definitions.yaml 和 AGENT_SKILL_MAP 是否同步。"""
    from aitest.agent_runner import AGENT_SKILL_MAP

    yaml_data = _load_yaml(AGENT_DEFS)
    agents = yaml_data.get("agents", {})
    details = []

    for agent_id, defn in agents.items():
        if defn.get("is_orchestrator"):
            continue
        yaml_skills = set(defn.get("skills", []))
        code_skills = set(AGENT_SKILL_MAP.get(agent_id, []))

        only_yaml = yaml_skills - code_skills
        only_code = code_skills - yaml_skills

        if only_yaml:
            details.append(f"{agent_id}: YAML has but code missing: {sorted(only_yaml)}")
        if only_code:
            details.append(f"{agent_id}: code has but YAML missing: {sorted(only_code)}")
        if not yaml_skills and not code_skills:
            details.append(f"{agent_id}: empty skill list (both sides)")

    ok = len(details) == 0
    return CheckResult(
        check="agent-definitions.yaml <-> AGENT_SKILL_MAP",
        ok=ok,
        message="In sync" if ok else f"{len(details)} drift(s) found",
        details=details,
    )


# ══════════════════════════════════════════════════════════════════════════
#  检查 2: skill-registry.yaml ↔ 实际 .md 文件
# ══════════════════════════════════════════════════════════════════════════

def check_skill_files_exist() -> CheckResult:
    """检查 registry 中 active skill 的 .md 文件是否存在。"""
    reg = _load_yaml(SKILL_REGISTRY)
    skills = reg.get("skills", [])
    details = []

    for skill in skills:
        if skill.get("status") != "active":
            continue
        file_path = GOVERNANCE / skill.get("file", "")
        if not file_path.exists():
            details.append(f"{skill['id']}: file not found — {skill.get('file', '?')}")

    ok = len(details) == 0
    return CheckResult(
        check="skill .md files exist",
        ok=ok,
        message=f"All {len([s for s in skills if s.get('status') == 'active'])} active skill files exist" if ok else f"{len(details)} file(s) missing",
        details=details,
    )


# ══════════════════════════════════════════════════════════════════════════
#  检查 3: AGENT_SKILL_MAP 引用的 skill 都在 registry 中
# ══════════════════════════════════════════════════════════════════════════

def check_skill_registry_completeness() -> CheckResult:
    """检查 AGENT_SKILL_MAP 中的 skill 是否都在 registry 注册。"""
    from aitest.agent_runner import AGENT_SKILL_MAP

    reg = _load_yaml(SKILL_REGISTRY)
    # registry uses category/id convention: {category}/{id} = full skill ID
    registered_ids = {f"{s['category']}/{s['id']}" for s in reg.get("skills", [])}
    # Also include bare IDs for backward compat
    registered_ids |= {s["id"] for s in reg.get("skills", [])}
    details = []

    for agent_id, skills in AGENT_SKILL_MAP.items():
        for skill_id in skills:
            if skill_id not in registered_ids:
                details.append(f"{agent_id} -> {skill_id}: not in skill-registry.yaml")

    ok = len(details) == 0
    return CheckResult(
        check="all AGENT_SKILL_MAP skills registered",
        ok=ok,
        message="All registered" if ok else f"{len(details)} skills not registered",
        details=details,
    )


# ══════════════════════════════════════════════════════════════════════════
#  检查 4: PAGE_INTERFACE.yaml 过期检测
# ══════════════════════════════════════════════════════════════════════════

def check_page_interface_freshness() -> CheckResult:
    """检查 PAGE_INTERFACE.yaml 是否比 PAGE_CONTEXT.md 更新。"""
    details = []
    checked = 0
    stale = 0

    if not CONTEXT_MODULES.exists():
        return CheckResult(check="PAGE_INTERFACE.yaml freshness", ok=True, message="无模块目录", details=[])

    for module_dir in sorted(CONTEXT_MODULES.iterdir()):
        if not module_dir.is_dir():
            continue
        pages_dir = module_dir / "pages"
        if not pages_dir.exists():
            continue

        for page_dir in sorted(pages_dir.iterdir()):
            if not page_dir.is_dir():
                continue
            page_context = page_dir / "PAGE_CONTEXT.md"
            page_interface = page_dir / "PAGE_INTERFACE.yaml"

            if not page_context.exists() or not page_interface.exists():
                continue

            checked += 1
            pc_mtime = page_context.stat().st_mtime
            pi_mtime = page_interface.stat().st_mtime

            if pi_mtime < pc_mtime:
                stale += 1
                details.append(
                    f"{module_dir.name}/{page_dir.name}: "
                    f"PAGE_INTERFACE.yaml 过期 (PAGE_CONTEXT.md 更新于 {pc_mtime:.0f}, "
                    f"PAGE_INTERFACE.yaml 更新于 {pi_mtime:.0f})"
                )

    ok = stale == 0
    return CheckResult(
        check="PAGE_INTERFACE.yaml freshness",
        ok=ok,
        message=f"Checked {checked} pages, {stale} stale" if checked > 0 else "No PAGE_INTERFACE.yaml files",
        details=details,
    )


# ══════════════════════════════════════════════════════════════════════════
#  检查 5: Agent 未引用已废弃 Skill
# ══════════════════════════════════════════════════════════════════════════

def check_no_deprecated_skills() -> CheckResult:
    """检查 active agent 是否引用了 status=deprecated 的 skill。"""
    from aitest.agent_runner import AGENT_SKILL_MAP

    reg = _load_yaml(SKILL_REGISTRY)
    deprecated_ids = {s["id"] for s in reg.get("skills", []) if s.get("status") == "deprecated"}
    details = []

    for agent_id, skills in AGENT_SKILL_MAP.items():
        for skill_id in skills:
            if skill_id in deprecated_ids:
                merged_into = ""
                for s in reg.get("skills", []):
                    if s["id"] == skill_id:
                        merged_into = s.get("merged_into", "unknown")
                        break
                details.append(f"{agent_id} 引用了已废弃 skill: {skill_id} → 应改用 {merged_into}")

    ok = len(details) == 0
    return CheckResult(
        check="no deprecated skill references",
        ok=ok,
        message="No deprecated refs" if ok else f"{len(details)} deprecated ref(s)",
        details=details,
    )


# ══════════════════════════════════════════════════════════════════════════
#  主入口
# ══════════════════════════════════════════════════════════════════════════

def check_regression_status() -> CheckResult:
    """
    P1-4: 回归测试基线状态检查。

    检查关键回归测试用例的基线文件是否存在。
    不重新运行测试，仅检查基线存在性。
    """
    from pathlib import Path
    import yaml

    GOVERNANCE = Path(__file__).resolve().parent.parent / "governance"
    test_cases_path = GOVERNANCE / "tests" / "regression" / "test_cases.yaml"

    if not test_cases_path.exists():
        return CheckResult(
            check="regression baselines",
            ok=True,
            message="No regression test cases defined yet",
        )

    try:
        with open(test_cases_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except Exception as e:
        return CheckResult(
            check="regression baselines",
            ok=False,
            message=f"Cannot read test_cases.yaml: {e}",
        )

    cases = data.get("test_cases", [])
    critical_cases = [c for c in cases if "critical" in c.get("tags", [])]

    if not critical_cases:
        return CheckResult(
            check="regression baselines",
            ok=True,
            message=f"{len(cases)} total cases, 0 critical — no baseline required",
        )

    baseline_dir = GOVERNANCE / "tests" / "regression" / "baselines"
    missing = []
    for c in critical_cases:
        skill_id = c.get("skill_id", "unknown/unknown")
        cat, name = skill_id.split("/", 1) if "/" in skill_id else ("unknown", skill_id)
        baseline_path = baseline_dir / cat / name / f"{c['id']}_baseline.md"
        if not baseline_path.exists():
            missing.append(c["id"])

    ok = len(missing) == 0
    return CheckResult(
        check="regression baselines",
        ok=ok,
        message=(
            f"All {len(critical_cases)} critical baselines present"
            if ok else
            f"{len(missing)}/{len(critical_cases)} critical baselines missing"
        ),
        details=[f"Missing baseline: {m}" for m in missing],
    )


ALL_CHECKS = [
    check_agent_skill_sync,
    check_skill_files_exist,
    check_skill_registry_completeness,
    check_page_interface_freshness,
    check_no_deprecated_skills,
    check_regression_status,
]


def run_all_checks() -> list[CheckResult]:
    """运行全部一致性检查。"""
    results = []
    for check_fn in ALL_CHECKS:
        try:
            result = check_fn()
        except Exception as e:
            result = CheckResult(
                check=check_fn.__name__,
                ok=False,
                message=f"检查异常: {str(e)[:200]}",
            )
        results.append(result)
    return results


def main():
    """CLI 入口。"""
    use_json = "--json" in sys.argv

    results = run_all_checks()
    all_ok = all(r.ok for r in results)
    issues = sum(len(r.details) for r in results)

    if use_json:
        output = {
            "status": "pass" if all_ok else "fail",
            "checks": [
                {"name": r.check, "ok": r.ok, "message": r.message, "details": r.details}
                for r in results
            ],
            "summary": f"{sum(1 for r in results if r.ok)}/{len(results)} checks passed, {issues} issues found",
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        width = 60
        print()
        print("=" * width)
        print("  Consistency Checker -- P2-2")
        print("=" * width)

        for r in results:
            icon = "[OK]" if r.ok else "[FAIL]"
            print(f"\n  {icon} {r.check}")
            print(f"      {r.message}")
            for d in r.details[:5]:
                print(f"        - {d}")
            if len(r.details) > 5:
                print(f"        ... and {len(r.details) - 5} more")

        print()
        print(f"  Summary: {sum(1 for r in results if r.ok)}/{len(results)} passed, {issues} issues")
        print("=" * width)
        print()

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
