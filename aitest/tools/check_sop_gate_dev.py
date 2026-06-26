"""
check_sop_gate_dev.py — Dev SOP 门禁检查器

使用方式:
  python aitest/tools/check_sop_gate_dev.py --module aitest-platform --json
  python aitest/tools/check_sop_gate_dev.py --module aitest-platform --agent review-agent
  python aitest/tools/check_sop_gate_dev.py --module aitest-platform --full

检查维度:
  1. SOP_STATUS 文件存在性 + JSON 合法性
  2. completed_phases 顺序合法性（前缀检查 + 前置依赖）
  3. Agent 前置 Phase 是否已完成（指定 --agent 时）
  4. 治理文档完整性（governance/sop_dev/ 目录）
  5. 开发产物存在性（指定 --full 时检查 artifact_map）

同步:
  Dev SOP 权威源: aitest/graphs_dev/state_dev.py (DEV_CANONICAL_PHASES)
  Agent 定义: governance/agents/agent-definitions-dev.yaml
  Phase 治理: governance/sop_dev/CANONICAL_PHASES.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from aitest.platform.paths import get_workstudy

# ═══════════════════════════════════════════════════════════════
# 路径常量
# ═══════════════════════════════════════════════════════════════

_WORKSTUDY = get_workstudy()
_GOVERNANCE = _WORKSTUDY / "governance"
_SOP_STATUS_DIR = _GOVERNANCE / "artifacts" / "sop-status-dev"
_SOP_DEV_DIR = _GOVERNANCE / "sop_dev"

# ═══════════════════════════════════════════════════════════════
# Dev SOP Phase 定义（同步自 state_dev.py DEV_CANONICAL_PHASES）
# ═══════════════════════════════════════════════════════════════

DEV_CANONICAL_PHASES: list[str] = [
    "Plan",
    "Requirements",
    "Architecture",
    "Component Design",
    "Frontend Impl",
    "Backend Impl",
    "Code Review",
    "Dev Test",
    "Debug & Fix",
    "Build",
]

# Phase → 前置 Phase（completed_phases 中必须在前）
DEV_PHASE_PREREQUISITES: dict[str, list[str]] = {
    "Plan": [],
    "Requirements": ["Plan"],
    "Architecture": ["Requirements"],
    "Component Design": ["Architecture"],
    "Frontend Impl": ["Component Design"],
    "Backend Impl": ["Component Design"],
    "Code Review": ["Frontend Impl", "Backend Impl"],
    "Dev Test": ["Code Review"],
    "Debug & Fix": ["Code Review"],     # 条件触发 — 仅 review 发现 issues 时
    "Build": ["Dev Test"],              # Debug & Fix 可能被跳过
}

# Agent → Phase 映射（同步自 state_dev.py DEV_AGENT_PHASE_MAP）
DEV_AGENT_PHASE_MAP: dict[str, str] = {
    "pm-agent": "Plan",
    "req-agent": "Requirements",
    "arch-agent": "Architecture",
    "design-agent": "Component Design",
    "frontend-agent": "Frontend Impl",
    "backend-agent": "Backend Impl",
    "review-agent": "Code Review",
    "dev-test-agent": "Dev Test",
    "debug-agent": "Debug & Fix",
    "build-agent": "Build",
}

# Phase → Agent（反向映射）
DEV_PHASE_AGENT_MAP: dict[str, str] = {v: k for k, v in DEV_AGENT_PHASE_MAP.items()}

# Agent → 预期产出物（同步自 agent-definitions-dev.yaml）
AGENT_ARTIFACTS: dict[str, list[str]] = {
    "pm-agent": ["PROJECT_PLAN.md", "PROGRESS_REPORT.md", "RISK_ANALYSIS.md"],
    "req-agent": ["FEATURE_SPEC.md", "USER_STORIES.md", "ACCEPTANCE_CRITERIA.md", "DATA_MODEL.md"],
    "arch-agent": ["PROJECT_STRUCTURE.md", "TECH_STACK.md", "COMPONENT_TREE.md", "API_CONTRACTS.md"],
    "design-agent": ["COMPONENT_SPEC.md", "PROPS_INTERFACE.yaml", "DATA_FLOW.md"],
    "frontend-agent": [],   # 前端产物路径可变，跳过静态检查
    "backend-agent": [],     # 后端产物路径可变，跳过静态检查
    "review-agent": ["CODE_REVIEW.md", "PERFORMANCE_REPORT.md", "SECURITY_REPORT.md", "CONSISTENCY_REPORT.md"],
    "dev-test-agent": ["COVERAGE_REPORT.md"],
    "debug-agent": ["ERROR_DIAGNOSIS.md", "STACK_ANALYSIS.md", "FIX_PROPOSAL.md", "REGRESSION_REPORT.md"],
    "build-agent": ["BUILD_REPORT.md", "TEST_RESULTS.md"],
}

# 必需的治理文档
REQUIRED_GOV_DOCS: list[str] = [
    "governance/sop_dev/README.md",
    "governance/sop_dev/CANONICAL_PHASES.md",
    "governance/sop_dev/AGENT_PHASE_MAP.md",
    "governance/sop_dev/MODE_SKIP_MAP.md",
    "governance/sop_dev/phases/00-INDEX.md",
]

# Phase 文件名映射
PHASE_FILES: dict[int, str] = {
    1: "01-plan.md", 2: "02-requirements.md", 3: "03-architecture.md",
    4: "04-component-design.md", 5: "05-frontend-impl.md", 6: "06-backend-impl.md",
    7: "07-code-review.md", 8: "08-dev-test.md", 9: "09-debug-fix.md",
    10: "10-build.md",
}


# ═══════════════════════════════════════════════════════════════
# SOP_STATUS 读写
# ═══════════════════════════════════════════════════════════════

def find_sop_status(module: str) -> Optional[Path]:
    """查找 SOP_STATUS 文件路径。"""
    p = _SOP_STATUS_DIR / f"SOP_STATUS_{module}.json"
    return p if p.exists() else None


def load_sop_status(module: str) -> Optional[dict]:
    """读取并解析 SOP_STATUS JSON。"""
    p = find_sop_status(module)
    if not p:
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"_parse_error": str(exc), "_path": str(p)}


# ═══════════════════════════════════════════════════════════════
# 检查函数
# ═══════════════════════════════════════════════════════════════

def _check_sop_status_exists(module: str) -> dict:
    """检查 1: SOP_STATUS 文件存在性。"""
    path = find_sop_status(module)
    if not path:
        return {
            "check": "sop_status_exists",
            "ok": False,
            "detail": f"SOP_STATUS_{module}.json not found in governance/artifacts/sop-status-dev/",
        }
    return {"check": "sop_status_exists", "ok": True, "detail": str(path)}


def _check_sop_status_valid(status: dict) -> dict:
    """检查 2: SOP_STATUS JSON 结构合法性。"""
    if status.get("_parse_error"):
        return {
            "check": "sop_status_valid_json",
            "ok": False,
            "detail": f"JSON parse error: {status['_parse_error']}",
        }
    required = ["module", "status", "completed_phases"]
    missing = [k for k in required if k not in status]
    if missing:
        return {
            "check": "sop_status_valid_json",
            "ok": False,
            "detail": f"Missing required keys: {missing}",
        }
    return {"check": "sop_status_valid_json", "ok": True, "detail": "ok"}


def _check_phase_order(completed: list[str]) -> dict:
    """检查 3: completed_phases 顺序合法性。"""
    issues = []
    # 过滤已知 Phase
    known = [p for p in completed if p in DEV_CANONICAL_PHASES]
    unknown = [p for p in completed if p not in DEV_CANONICAL_PHASES]

    if unknown:
        issues.append(f"Unknown phases in completed_phases: {unknown}. Known phases: {DEV_CANONICAL_PHASES}")

    # 前置依赖检查
    seen = set()
    for phase in known:
        for prereq in DEV_PHASE_PREREQUISITES.get(phase, []):
            if prereq not in seen:
                issues.append(
                    f"Phase '{phase}' completed but prerequisite '{prereq}' not found before it"
                )
        seen.add(phase)

    return {
        "check": "phase_order",
        "ok": not issues,
        "detail": "ok" if not issues else "; ".join(issues),
        "completed_count": len(known),
        "completed_phases": known,
        "unknown_phases": unknown,
    }


def _check_agent_prerequisites(agent: str, completed: list[str]) -> dict:
    """检查 4: 指定 Agent 的前置 Phase 是否完成。"""
    if agent not in DEV_AGENT_PHASE_MAP:
        return {
            "check": "agent_prerequisites",
            "ok": False,
            "detail": f"Unknown agent: '{agent}'. Known: {list(DEV_AGENT_PHASE_MAP.keys())}",
        }

    target_phase = DEV_AGENT_PHASE_MAP[agent]
    prereqs = DEV_PHASE_PREREQUISITES.get(target_phase, [])
    missing = [p for p in prereqs if p not in completed]

    return {
        "check": "agent_prerequisites",
        "ok": not missing,
        "detail": "ok" if not missing else (
            f"Agent '{agent}' targets phase '{target_phase}' but prerequisites "
            f"{missing} are not completed"
        ),
        "target_phase": target_phase,
        "required_prerequisites": prereqs,
        "missing_prerequisites": missing,
    }


def _check_governance_docs() -> dict:
    """检查 5: 治理文档完整性。"""
    missing = []
    for rel_path in REQUIRED_GOV_DOCS:
        if not (_WORKSTUDY / rel_path).exists():
            missing.append(rel_path)

    for i in range(1, 11):
        f = f"governance/sop_dev/phases/{PHASE_FILES[i]}"
        if not (_WORKSTUDY / f).exists():
            missing.append(f)

    return {
        "check": "governance_docs",
        "ok": not missing,
        "detail": "ok" if not missing else f"Missing {len(missing)} governance docs",
        "missing_docs": missing,
    }


def _check_agent_artifacts(module: str, completed: list[str]) -> dict:
    """检查 6: 已完成的 Phase 对应的 Agent 产出物存在性。"""
    missing = []
    artifacts_dir = _WORKSTUDY / "governance" / "artifacts" / "dev-artifacts" / module

    for phase in completed:
        agent = DEV_PHASE_AGENT_MAP.get(phase)
        if not agent:
            continue
        expected = AGENT_ARTIFACTS.get(agent, [])
        for artifact in expected:
            p = artifacts_dir / artifact
            if not p.exists():
                missing.append(f"Phase '{phase}' ({agent}): {artifact}")

    return {
        "check": "agent_artifacts",
        "ok": not missing,
        "detail": "ok" if not missing else f"Missing {len(missing)} artifacts",
        "missing_artifacts": missing,
        "artifacts_dir": str(artifacts_dir),
        "note": "frontend-agent/backend-agent artifacts not statically checked (variable paths)",
    }


# ═══════════════════════════════════════════════════════════════
# 主门禁函数
# ═══════════════════════════════════════════════════════════════

def check_sop_gate_dev(
    module: str,
    agent: Optional[str] = None,
    full: bool = False,
) -> dict:
    """
    执行 Dev SOP 门禁检查。

    Args:
        module: 模块名（如 "aitest-platform"）
        agent: 可选，检查特定 Agent 的前置条件
        full: 是否执行完整检查（含产物存在性）

    Returns:
        dict with keys: gate, module, checked_at, checks, issues
    """
    result: dict = {
        "gate": "pass",
        "module": module,
        "engine": "dev-sop",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "checks": [],
        "issues": [],
    }

    if agent:
        result["agent"] = agent

    # ── 检查 1: SOP_STATUS 存在性 ──
    r = _check_sop_status_exists(module)
    result["checks"].append(r)
    if not r["ok"]:
        result["gate"] = "blocked"
        result["issues"].append(r["detail"])
        return result

    # ── 检查 2: SOP_STATUS JSON 合法性 ──
    status = load_sop_status(module)
    if status is None:
        result["gate"] = "blocked"
        result["issues"].append("Failed to load SOP_STATUS")
        return result

    r = _check_sop_status_valid(status)
    result["checks"].append(r)
    if not r["ok"]:
        result["gate"] = "blocked"
        result["issues"].append(r["detail"])
        return result

    result["current_status"] = status.get("status")
    result["completed_phases"] = status.get("completed_phases", [])

    # ── 检查 3: Phase 顺序 ──
    completed = status.get("completed_phases", [])
    r = _check_phase_order(completed)
    result["checks"].append(r)
    if not r["ok"]:
        result["gate"] = "blocked"
        result["issues"].append(r["detail"])

    # ── 检查 4: Agent 前置条件（可选）──
    if agent:
        r = _check_agent_prerequisites(agent, completed)
        result["checks"].append(r)
        if not r["ok"]:
            result["gate"] = "blocked"
            result["issues"].append(r["detail"])

    # ── 检查 5: 治理文档 ──
    r = _check_governance_docs()
    result["checks"].append(r)
    if not r["ok"]:
        result["gate"] = "blocked"
        result["issues"].append(r["detail"])

    # ── 检查 6: 产物存在性（仅 --full）──
    if full:
        r = _check_agent_artifacts(module, completed)
        result["checks"].append(r)
        if not r["ok"]:
            result["issues"].append(r["detail"])
            # full 检查时产物缺失不阻塞 gate（开发中允许）
            result.setdefault("warnings", []).append(r["detail"])

    result["gate"] = "pass" if not result["issues"] else "blocked"
    return result


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="Dev SOP Gate Checker — 开发流水线门禁检查",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python aitest/tools/check_sop_gate_dev.py --module aitest-platform --json
  python aitest/tools/check_sop_gate_dev.py --module aitest-platform --agent review-agent
  python aitest/tools/check_sop_gate_dev.py --module aitest-platform --full --json
        """,
    )
    parser.add_argument("--module", "-m", required=True, help="模块名")
    parser.add_argument("--agent", "-a", help="检查特定 Agent 的前置条件")
    parser.add_argument("--full", action="store_true", help="完整检查（含产物存在性）")
    parser.add_argument("--json", action="store_true", help="JSON 输出")
    args = parser.parse_args()

    result = check_sop_gate_dev(
        module=args.module,
        agent=args.agent,
        full=args.full,
    )

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    else:
        _print_human(result)

    sys.exit(0 if result["gate"] == "pass" else 1)


def _print_human(result: dict):
    """Human-readable 输出。"""
    gate_icon = "✅ PASS" if result["gate"] == "pass" else "❌ BLOCKED"
    print(f"Dev SOP Gate Check — {gate_icon}")
    print(f"  Module:   {result.get('module')}")
    if result.get("agent"):
        print(f"  Agent:    {result['agent']}")
    print(f"  Status:   {result.get('current_status', 'N/A')}")
    print(f"  Checked:  {result.get('checked_at', 'N/A')}")
    print()

    if result.get("completed_phases"):
        print(f"  Completed Phases ({len(result['completed_phases'])}):")
        for p in result["completed_phases"]:
            print(f"    ✓ {p}")
        print()

    for check in result.get("checks", []):
        icon = "✅" if check.get("ok") else "❌"
        print(f"  {icon} {check['check']}: {check.get('detail', '?')}")

    if result.get("issues"):
        print(f"\n  Issues ({len(result['issues'])}):")
        for issue in result["issues"]:
            print(f"    ❌ {issue}")

    if result.get("warnings"):
        print(f"\n  Warnings ({len(result['warnings'])}):")
        for w in result["warnings"]:
            print(f"    ⚠️  {w}")

    print()


if __name__ == "__main__":
    main()
