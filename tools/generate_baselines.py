"""
Step 3: Golden Baseline Generator — 为回归测试用例生成/更新 baseline。

用法:
    # 生成全部 75 用例的 baseline (耗 token，建议按 tag 分批)
    python tools/generate_baselines.py --tags smoke
    python tools/generate_baselines.py --tags info-gap,tool-failure
    python tools/generate_baselines.py --all --dry-run   # 预览不执行

    # 对变更的 skill 重新生成 baseline
    python tools/generate_baselines.py --skill test-design/page-analysis

策略:
  - smoke 用例: 跑 LLM 生成 golden baseline
  - info-gap/tool-failure/high-risk/noise 用例: 零 LLM — 确定性评估，
    预期行为已在 test_cases.yaml 的 expected 字段定义
"""

import yaml
import json
import sys
import time
from pathlib import Path
from datetime import datetime

WORKSTUDY = Path(__file__).resolve().parent.parent
TEST_CASES_FILE = WORKSTUDY / "governance" / "tests" / "regression" / "test_cases.yaml"
BASELINE_DIR = WORKSTUDY / "governance" / "tests" / "regression" / "baselines"


def load_test_cases(tags: list[str] = None) -> list[dict]:
    """加载测试用例，可选按 tag 筛选。"""
    with open(TEST_CASES_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    cases = data.get("test_cases", [])
    if tags:
        cases = [c for c in cases if any(t in c.get("tags", []) for t in tags)]
    return cases


def generate_baseline_for_case(case: dict, provider: str = "claude",
                               dry_run: bool = False) -> dict:
    """
    为单个用例生成 baseline。

    对于确定性评估用例 (info-gap/tool-failure/high-risk/noise)，
    不调用 LLM，直接基于 expected criteria 生成 baseline reference。
    """
    skill_id = case.get("skill_id", "")
    case_id = case.get("id", "")
    tags = case.get("tags", [])
    expected = case.get("expected", {})

    # 确定性评估用例: 不调 LLM
    is_deterministic = any(t in tags for t in ["info-gap", "tool-failure",
                                                "high-risk", "noise"])
    if is_deterministic:
        return {
            "case_id": case_id,
            "skill_id": skill_id,
            "generated_at": datetime.now().isoformat(),
            "method": "deterministic",
            "baseline": {
                "expected_behavior": case.get("description", ""),
                "expected_criteria": expected,
                "note": "此用例使用确定性评估 (criteria-based)，不需要 LLM golden baseline。"
            },
            "status": "skipped" if dry_run else "stored",
        }

    # Smoke/cross-module 用例: 调用 LLM 生成 golden baseline
    if dry_run:
        return {
            "case_id": case_id,
            "skill_id": skill_id,
            "method": "llm",
            "status": "dry_run",
            "estimated_tokens": "~2000-5000",
        }

    # Actual LLM call
    try:
        from aitest.agents.agent_runner import run_skill
        context = case.get("context", {})
        response = run_skill(
            skill_id=skill_id,
            user_input=case.get("input", ""),
            provider=provider,
            context_vars=context,
        )
        output = response.content or ""

        # Store baseline
        baseline_path = BASELINE_DIR / skill_id.replace("/", "-") / f"{case_id}_baseline.md"
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(output, encoding="utf-8")

        return {
            "case_id": case_id,
            "skill_id": skill_id,
            "generated_at": datetime.now().isoformat(),
            "method": "llm",
            "output_length": len(output),
            "token_usage": response.token_usage,
            "baseline_path": str(baseline_path),
            "status": "generated",
        }

    except Exception as e:
        return {
            "case_id": case_id,
            "skill_id": skill_id,
            "method": "llm",
            "status": "error",
            "error": str(e)[:200],
        }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Generate golden baselines for regression tests")
    parser.add_argument("--tags", default="", help="Filter by comma-separated tags")
    parser.add_argument("--skill", default="", help="Filter by skill_id prefix")
    parser.add_argument("--all", action="store_true", help="Process all test cases")
    parser.add_argument("--dry-run", action="store_true", help="Preview without execution")
    parser.add_argument("--provider", default="claude", help="LLM provider")

    try:
        args = parser.parse_args()
    except SystemExit:
        # Fallback for environments without argparse
        print("Usage: python generate_baselines.py [--tags smoke,info-gap] [--dry-run]")
        tags_filter = sys.argv[2].split(",") if len(sys.argv) > 2 else None
        dry_run = "--dry-run" in sys.argv
        cases = load_test_cases(tags=tags_filter)
        print(f"Loaded {len(cases)} test cases")
        for c in cases[:5]:
            print(f"  {c['id']}: {c['skill_id']} {c.get('tags', [])}")
        return

    tags_filter = args.tags.split(",") if args.tags else None
    cases = load_test_cases(tags=tags_filter)
    if args.skill:
        cases = [c for c in cases if args.skill in c.get("skill_id", "")]
    if not args.all and not tags_filter and not args.skill:
        print("Specify --tags, --skill, or --all. Use --dry-run to preview.")
        return

    print(f"Processing {len(cases)} test cases...")
    if args.dry_run:
        print("DRY RUN — no LLM calls will be made\n")

    llm_count = 0
    det_count = 0
    for i, case in enumerate(cases):
        result = generate_baseline_for_case(case, provider=args.provider,
                                            dry_run=args.dry_run)
        if result["status"] == "error":
            print(f"  [{i+1}/{len(cases)}] ❌ {case['id']}: {result.get('error', '')}")
        elif result["method"] == "deterministic":
            det_count += 1
        elif result["method"] == "llm" and not args.dry_run:
            llm_count += 1
            print(f"  [{i+1}/{len(cases)}] ✅ {case['id']}: {result.get('output_length', 0)} chars, "
                  f"tokens={result.get('token_usage', {})}")

    print(f"\nDone. Deterministic: {det_count}, LLM-generated: {llm_count}, Total: {len(cases)}")


if __name__ == "__main__":
    main()
