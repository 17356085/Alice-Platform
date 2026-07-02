"""
Preflight — execution dependency checker.

Before running an agent/phase, verify that all required inputs exist.
Returns PASS/WARN/BLOCK with details.

Usage:
    from aitest.platform.preflight import preflight_check

    result = preflight_check("automation-agent", module="equipment", page="alarm-config")
    if result.blocked:
        print(f"BLOCKED: {result.reason}")
    elif result.warnings:
        print(f"WARN: {result.warnings}")
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from aitest.platform.artifact_lineage import PHASE_ARTIFACTS


@dataclass
class PreflightResult:
    """Result of a preflight dependency check."""
    agent: str
    status: str = "PASS"  # PASS | WARN | BLOCK
    missing: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    details: dict = field(default_factory=dict)

    @property
    def blocked(self) -> bool:
        return self.status == "BLOCK"

    @property
    def ok(self) -> bool:
        return self.status == "PASS"

    def to_dict(self) -> dict:
        return {
            "agent": self.agent,
            "status": self.status,
            "missing": self.missing,
            "warnings": self.warnings,
            "details": self.details,
        }


# ── Artifact resolution ──────────────────────────────────────────────

def _resolve_artifact_path(artifact: str, module: str, page: str = "") -> Optional[Path]:
    """Resolve an artifact name to an actual file path.

    Checks multiple locations:
      1. Module-level: <module_dir>/<artifact>
      2. Page-level: <module_dir>/pages/<page>/<artifact>
      3. Project-level: ./<artifact>
    """
    from alice_engine.workflow.state import get_module_dir, get_page_dir

    # Module-level artifacts
    module_dir = get_module_dir(module)
    if module_dir:
        p = module_dir / artifact
        if p.exists():
            return p

    # Page-level artifacts
    if page:
        page_dir = get_page_dir(module, page)
        if page_dir:
            p = page_dir / artifact
            if p.exists():
                return p

    # Project-level artifacts (PROJECT_CONTEXT.md, etc.)
    project_path = Path(".") / artifact
    if project_path.exists():
        return project_path

    return None


def _is_valid_artifact(path: Path) -> bool:
    """Check if artifact exists and has content."""
    if not path.exists():
        return False
    if path.is_file():
        return path.stat().st_size > 0
    if path.is_dir():
        # Directory counts as valid if it has any files
        try:
            return any(path.iterdir())
        except OSError:
            return False
    return False


# ── Main check ───────────────────────────────────────────────────────

def preflight_check(
    agent: str,
    module: str = "",
    page: str = "",
    mode: str = "full",
) -> PreflightResult:
    """Check if all dependencies for an agent are satisfied.

    Args:
        agent: Agent name (e.g., "automation-agent")
        module: Target module
        page: Target page (for page-level artifacts)
        mode: Execution mode (full, resume, from-automation, etc.)

    Returns:
        PreflightResult with PASS/WARN/BLOCK status
    """
    result = PreflightResult(agent=agent)

    # Get dependency spec
    spec = PHASE_ARTIFACTS.get(agent)
    if not spec:
        result.status = "WARN"
        result.warnings.append(f"Unknown agent: {agent}")
        return result

    depends_on = spec.get("depends_on", [])

    # "all" dependency = depends on all previous phases (knowledge-agent)
    if depends_on == ["all"]:
        # Check all other agents' outputs
        all_agents = [a for a in PHASE_ARTIFACTS if a != agent and a != "knowledge-agent"]
        for prev_agent in all_agents:
            sub_result = preflight_check(prev_agent, module=module, page=page, mode=mode)
            if sub_result.blocked:
                result.missing.extend(sub_result.missing)
        if result.missing:
            result.status = "BLOCK"
            result.details["reason"] = f"knowledge-agent requires all phases complete"
        return result

    # Check each dependency
    for dep in depends_on:
        path = _resolve_artifact_path(dep, module, page)
        if path is None or not _is_valid_artifact(path):
            result.missing.append(dep)

    # Determine status
    if result.missing:
        # In resume mode, missing deps are warnings (agent might handle them)
        if mode == "resume":
            result.status = "WARN"
            result.warnings.append(f"Missing dependencies (resume mode): {result.missing}")
        else:
            result.status = "BLOCK"
            result.details["reason"] = f"Missing required artifacts: {result.missing}"
    else:
        result.status = "PASS"

    return result


def preflight_check_all(module: str, pages: list[str] = None, mode: str = "full") -> dict:
    """Run preflight checks for all agents.

    Returns:
        Dict mapping agent name to PreflightResult
    """
    results = {}
    for agent in PHASE_ARTIFACTS:
        # For page-level agents, check with first page
        page = pages[0] if pages else ""
        results[agent] = preflight_check(agent, module=module, page=page, mode=mode)
    return results


def format_preflight_report(results: dict) -> str:
    """Format preflight results as a human-readable report."""
    lines = ["=== Preflight Report ===\n"]

    for agent, result in results.items():
        status_icon = {"PASS": "✅", "WARN": "⚠️", "BLOCK": "❌"}[result.status]
        lines.append(f"{status_icon} {agent}: {result.status}")

        if result.missing:
            lines.append(f"   Missing: {', '.join(result.missing)}")
        if result.warnings:
            for w in result.warnings:
                lines.append(f"   Warning: {w}")
        if result.details.get("reason"):
            lines.append(f"   Reason: {result.details['reason']}")

    # Summary
    blocked = sum(1 for r in results.values() if r.blocked)
    warned = sum(1 for r in results.values() if r.status == "WARN")
    passed = sum(1 for r in results.values() if r.ok)

    lines.append(f"\nSummary: {passed} passed, {warned} warnings, {blocked} blocked")
    return "\n".join(lines)
