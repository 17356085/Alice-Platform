"""
TLO CI Entrypoint — 通用 CI/CD 集成脚本。

支持任意 CI 系统 (GitHub Actions / Jenkins / GitLab CI / 本地)。

用法:
    # 1. 检测受影响的模块
    python ZJSN_Test-master526/ci/tlo_ci_entrypoint.py diff
    python ZJSN_Test-master526/ci/tlo_ci_entrypoint.py diff --base-ref=origin/main

    # 2. 运行受影响模块的 SOP
    python ZJSN_Test-master526/ci/tlo_ci_entrypoint.py run --modules=equipment,warehouse

    # 3. 生成回归推荐
    python ZJSN_Test-master526/ci/tlo_ci_entrypoint.py regression --base-ref=origin/main

    # 4. 全量运行 (门禁 + SOP + 回归)
    python ZJSN_Test-master526/ci/tlo_ci_entrypoint.py all --base-ref=origin/main
"""

import json
import os
import subprocess
import sys
from pathlib import Path

_WORKSTUDY = Path(__file__).resolve().parent.parent.parent


def detect_affected_modules(base_ref: str = "origin/main") -> list[str]:
    """
    通过 Git diff 检测受影响的测试模块。

    规则:
      - ZJSN_Test-master526/script/<m>/ → 模块 <m> 受影响
      - ZJSN_Test-master526/base/ → ALL 模块受影响
      - ZJSN_Test-master526/config/ → ALL 模块受影响
      - aitest/graphs/ → ALL 模块受影响
      - aitest/* (非 graphs) → 无直接测试影响
      - governance/agents/ → ALL 模块受影响
      - governance/skills/ → 受影响的 Skill 对应模块
    """
    result = subprocess.run(
        ["git", "diff", "--name-only", base_ref, "HEAD"],
        cwd=str(_WORKSTUDY), capture_output=True, text=True
    )
    changed = result.stdout.strip().split("\n") if result.stdout.strip() else []

    # Check for global-impact changes
    global_patterns = [
        "ZJSN_Test-master526/base/",
        "ZJSN_Test-master526/config/",
        "aitest/graphs/",
        "governance/agents/",
    ]
    is_global = any(
        any(f.startswith(p) for p in global_patterns)
        for f in changed
    )

    if is_global:
        # All modules need regression
        sop_dir = _WORKSTUDY / "governance" / "artifacts" / "sop-status"
        modules = []
        for f in sop_dir.glob("SOP_STATUS_*.json"):
            mod = f.stem.replace("SOP_STATUS_", "")
            modules.append(mod)
        return sorted(modules)

    # Module-specific detection
    modules = set()
    for f in changed:
        # ZJSN_Test-master526/script/<module>/...
        if f.startswith("ZJSN_Test-master526/script/"):
            parts = f.split("/")
            if len(parts) >= 3:
                modules.add(parts[2])

        # governance/skills/<category>/ → check skill-agent mapping
        if f.startswith("governance/skills/"):
            # Broad impact: include all modules that use this skill category
            skill_cat = f.split("/")[2] if len(f.split("/")) >= 3 else ""
            modules.update(_modules_for_skill_category(skill_cat))

    return sorted(modules) if modules else []


def _modules_for_skill_category(category: str) -> list[str]:
    """映射 Skill 类别到模块。"""
    # Simplified mapping — in production, read from skill-registry.yaml
    mapping = {
        "automation": ["equipment", "warehouse", "personnel", "sales", "production", "tank", "lab", "system", "dcs"],
        "test-design": ["equipment", "warehouse", "personnel", "sales", "production", "tank", "lab", "system", "system-management", "system-role", "dcs", "workflow"],
        "diagnosis": ["equipment", "warehouse", "personnel"],
        "execution": ["equipment", "warehouse", "personnel", "sales", "production"],
        "knowledge": [],
        "project": [],
    }
    return mapping.get(category, [])


def run_sop(modules: list[str], mode: str = "full", non_interactive: bool = True) -> dict:
    """对指定模块运行 TLO SOP。"""
    results = {}
    for mod in modules:
        print(f"\n{'='*60}")
        print(f"  TLO SOP: {mod}")
        print(f"{'='*60}")
        cmd = [
            sys.executable, "-m", "aitest.infra.cli", "sop", "run",
            f"--module={mod}",
            f"--mode={mode}",
        ]
        if non_interactive:
            cmd.append("--non-interactive")

        try:
            proc = subprocess.run(
                cmd, cwd=str(_WORKSTUDY),
                capture_output=True, text=True,
                timeout=1800,  # 30 min timeout
            )
            results[mod] = {
                "success": proc.returncode == 0,
                "output": proc.stdout[-2000:],
                "stderr": proc.stderr[-500:],
            }
        except subprocess.TimeoutExpired:
            results[mod] = {"success": False, "output": "TIMEOUT (>30min)"}
        except Exception as e:
            results[mod] = {"success": False, "output": str(e)}

    return results


def run_regression(base_ref: str = "origin/main") -> str:
    """运行回归推荐。"""
    try:
        from aitest.knowledge.knowledge_extractor import KnowledgeExtractor
        # Use KnowledgeExtractor to pull historical data
        # Then run regression-scope skill
        affected = detect_affected_modules(base_ref)
        if not affected:
            return "No modules affected by this change."

        return f"## TLO Regression Recommendation\n\n" \
               f"**Base**: {base_ref}\n" \
               f"**Affected modules**: {', '.join(affected)}\n\n" \
               f"Recommended regression: `aitest sop run --module={' --module='.join(affected)}`"

    except Exception as e:
        return f"Regression analysis failed: {e}"


# ── CLI ──

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="TLO CI Entrypoint")
    sub = parser.add_subparsers(dest="command")

    diff_p = sub.add_parser("diff", help="Detect affected modules")
    diff_p.add_argument("--base-ref", default="origin/main")
    diff_p.add_argument("--format", default="json", choices=["json", "list"])

    run_p = sub.add_parser("run", help="Run SOP for modules")
    run_p.add_argument("--modules", required=True)
    run_p.add_argument("--mode", default="full")

    reg_p = sub.add_parser("regression", help="Run regression advisor")
    reg_p.add_argument("--base-ref", default="origin/main")
    reg_p.add_argument("--format", default="markdown")

    all_p = sub.add_parser("all", help="Full CI pipeline")
    all_p.add_argument("--base-ref", default="origin/main")

    args = parser.parse_args()

    if args.command == "diff":
        modules = detect_affected_modules(args.base_ref)
        if args.format == "json":
            print(json.dumps(modules))
        else:
            for m in modules:
                print(m)

    elif args.command == "run":
        modules = [m.strip() for m in args.modules.split(",")]
        results = run_sop(modules)
        print(json.dumps(results, indent=2))

    elif args.command == "regression":
        report = run_regression(args.base_ref)
        print(report)

    elif args.command == "all":
        print("=== TLO CI Pipeline ===")
        modules = detect_affected_modules(args.base_ref)
        print(f"Affected modules: {modules}")
        if modules:
            results = run_sop(modules)
            success = all(r["success"] for r in results.values())
            print(f"\nSOP Results: {'ALL PASSED' if success else 'SOME FAILED'}")
            for mod, r in results.items():
                status = "✅" if r["success"] else "❌"
                print(f"  {status} {mod}")
            report = run_regression(args.base_ref)
            print(f"\n{report}")
        else:
            print("No modules affected — skipping SOP run")

    else:
        parser.print_help()
