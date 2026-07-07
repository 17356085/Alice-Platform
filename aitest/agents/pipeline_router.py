"""Pipeline Router — complexity-aware SOP phase routing.

Task 1 (P0) — APERANT_MIGRATION_PLAN.md
Port of Aperant spec-orchestrator.ts COMPLEXITY_PHASES + PHASE_AGENT_MAP.

Maps aitest 18-factor complexity scores → SIMPLE/STANDARD/COMPLEX tiers,
each tier routes to a different Dev SOP phase subset and agent effort level.

Architecture (three-layer separation, Task 4):
  Layer 1: task_state_machine.py — pure FSM, zero I/O
  Layer 2: THIS FILE — reads FSM state, drives execution routing
  Layer 3: pause_handler.py — sentinel file communication

Usage:
    from aitest.agents.pipeline_router import route_dev_sop, ComplexityTier

    config = route_dev_sop(module="aitest-platform", tier=ComplexityTier.STANDARD)
    # → {"phases": [...], "agents": [...], "effort": "balanced", ...}
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from aitest.graphs_dev.state_dev import (
    DEV_CANONICAL_PHASES,
    DEV_AGENT_PHASE_MAP,
    DEV_PHASE_TO_NODE,
    DevPhaseName,
    DevAgentName,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Complexity tier (mirrors aitest.platform.complexity.factors.ComplexityTier)
# ═══════════════════════════════════════════════════════════════════════════════

class ComplexityTier(str, Enum):
    SIMPLE = "simple"
    STANDARD = "standard"
    COMPLEX = "complex"


# ═══════════════════════════════════════════════════════════════════════════════
# Per-tier phase routing (Dev SOP)
# ═══════════════════════════════════════════════════════════════════════════════

# Which phases run per complexity tier.
# SIMPLE: skip Requirements, Component Design, Dev Test, Debug & Fix
# STANDARD: all 10 phases
# COMPLEX: all 10 phases + extra Debug cycles (handled via max_debug_rounds)

COMPLEXITY_PHASES_DEV: dict[ComplexityTier, list[DevPhaseName]] = {
    ComplexityTier.SIMPLE: [
        "Plan",
        "Architecture",
        "Frontend Impl",
        "Backend Impl",
        "Code Review",
        "Build",
    ],
    ComplexityTier.STANDARD: list(DEV_CANONICAL_PHASES),  # all 10
    ComplexityTier.COMPLEX: list(DEV_CANONICAL_PHASES),   # all 10 + extras (see effort)
}


# ── Per-tier agent effort ─────────────────────────────────────────────────────

@dataclass
class AgentEffort:
    """Per-agent effort configuration for a complexity tier."""
    model_tier: str = "balanced"     # "econ" | "balanced" | "max"
    max_retries: int = 3
    deep_review: bool = False


# Default effort per tier
TIER_DEFAULT_EFFORT: dict[ComplexityTier, AgentEffort] = {
    ComplexityTier.SIMPLE: AgentEffort(
        model_tier="econ",
        max_retries=1,
        deep_review=False,
    ),
    ComplexityTier.STANDARD: AgentEffort(
        model_tier="balanced",
        max_retries=3,
        deep_review=True,
    ),
    ComplexityTier.COMPLEX: AgentEffort(
        model_tier="max",
        max_retries=5,
        deep_review=True,
    ),
}


# ── Additional agent-specific overrides per tier ──────────────────────────────

# Agents that ONLY run in COMPLEX tier
COMPLEX_ONLY_AGENTS: set[DevAgentName] = set()


# Agents whose model_tier is bumped in COMPLEX tier
COMPLEX_MODEL_BUMP: dict[DevAgentName, str] = {
    "arch-agent": "max",
    "review-agent": "max",
    "debug-agent": "max",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Routing result
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class PipelineConfig:
    """Result of complexity-based routing for a Dev SOP run.

    Consumed by agent_runner.py and cmd_graph_dev to configure the run.
    """
    tier: ComplexityTier = ComplexityTier.STANDARD
    phases: list[DevPhaseName] = field(default_factory=list)
    agents: list[DevAgentName] = field(default_factory=list)
    skip_phases: list[DevPhaseName] = field(default_factory=list)
    effort: AgentEffort = field(default_factory=AgentEffort)
    max_debug_rounds: int = 3
    module: str = ""
    source: str = ""  # "18factor" | "mode" | "manual"

    # ── Task 4 (P1): FSM integration ──
    def create_fsm(self):
        """Create a TaskStateContext initialized from this pipeline config.

        The FSM tracks task lifecycle within the pipeline.
        Layer 1 (task_state_machine.py) is pure — zero I/O, testable.
        """
        from alice_engine.core.state_machine import TaskState, TaskStateContext
        return TaskStateContext(state=TaskState.TEST_PLANNING)

    def validate_phase_transition(
        self, from_phase: str, to_phase: str,
    ) -> bool:
        """Check if a phase transition is valid per canonical ordering.

        Returns True if `to_phase` is the natural next phase after `from_phase`,
        or if `to_phase` is a valid skip-ahead (e.g. Debug & Fix → Build when
        no issues found).
        """
        if from_phase not in self.phases or to_phase not in self.phases:
            return False
        from_idx = self.phases.index(from_phase)
        to_idx = self.phases.index(to_phase)
        # Forward progress (including skip due to conditional phases)
        return to_idx > from_idx or (
            from_phase == "Debug & Fix" and to_phase == "Build"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Main routing functions
# ═══════════════════════════════════════════════════════════════════════════════

def route_dev_sop(
    module: str = "",
    tier: ComplexityTier | str = ComplexityTier.STANDARD,
    mode: str = "full",
    agent: str = "",
) -> PipelineConfig:
    """Route a Dev SOP run based on complexity tier.

    This is the PRIMARY entry point for complexity-based routing.
    Called by agent_runner during AgentLoop.__init__() and by cmd_graph_dev.

    Args:
        module: Business module name (e.g. "aitest-platform")
        tier: Complexity tier (SIMPLE/STANDARD/COMPLEX)
        mode: Execution mode (full/resume/from-architecture etc.)
        agent: Optional single-agent override (e.g. "review-agent")

    Returns:
        PipelineConfig with phases, agents, skip list, and effort.
    """
    if isinstance(tier, str):
        tier = ComplexityTier(tier.lower())

    # Resolve phases for this tier
    phases = list(COMPLEXITY_PHASES_DEV.get(tier, COMPLEXITY_PHASES_DEV[ComplexityTier.STANDARD]))

    # Apply mode-based skip on top of tier routing
    from aitest.graphs_dev.state_dev import DEV_MODE_SKIP_MAP
    mode_skips = set(DEV_MODE_SKIP_MAP.get(mode, []))
    phases = [p for p in phases if p not in mode_skips]

    # Single-agent override: only include phases up to and including target agent
    if agent:
        target_phase = DEV_AGENT_PHASE_MAP.get(agent)
        if target_phase and target_phase in phases:
            idx = phases.index(target_phase)
            phases = phases[:idx + 1]

    # Map phases to agents
    agents = _phases_to_agents(phases)

    # Effort config
    effort = _resolve_effort(tier, agents)

    return PipelineConfig(
        tier=tier,
        phases=phases,
        agents=agents,
        skip_phases=[p for p in DEV_CANONICAL_PHASES if p not in phases],
        effort=effort,
        max_debug_rounds=effort.max_retries,
        module=module,
        source="18factor",
    )


def assess_and_route(
    module: str = "",
    page_data: dict = None,
    page_title: str = "",
    mode: str = "full",
) -> PipelineConfig:
    """Full pipeline: assess complexity → route.

    Uses aitest.platform.complexity for 18-factor scoring, then
    maps score → tier → PipelineConfig via route_dev_sop().

    Args:
        module: Business module name.
        page_data: BrowserUse discovery data (optional).
        page_title: Page title (fallback).
        mode: Execution mode.

    Returns:
        PipelineConfig ready for agent_runner consumption.
    """
    try:
        from aitest.platform.complexity import complexity_assess
        result = complexity_assess(page_data=page_data, page_title=page_title)
        tier_str = result["tier"]
        score = result["score"]
    except Exception:
        tier_str = "standard"
        score = 0

    config = route_dev_sop(module=module, tier=tier_str, mode=mode)
    return config


def route_test_sop(
    module: str = "",
    tier: ComplexityTier | str = ComplexityTier.STANDARD,
) -> PipelineConfig:
    """Route a TEST SOP run based on complexity tier.

    Uses the existing complexity module's pipeline_for_tier() for agent sequence.
    This is the test-automation counterpart to route_dev_sop().
    """
    if isinstance(tier, str):
        tier = ComplexityTier(tier.lower())

    try:
        from aitest.platform.complexity.factors import (
            ComplexityTier as CT, pipeline_for_tier,
        )
        ct_map = {
            ComplexityTier.SIMPLE: CT.SIMPLE,
            ComplexityTier.STANDARD: CT.STANDARD,
            ComplexityTier.COMPLEX: CT.COMPLEX,
        }
        agent_ids = pipeline_for_tier(ct_map[tier])
    except Exception:
        agent_ids = ["automation-agent", "execution-agent"]

    return PipelineConfig(
        tier=tier,
        phases=[],
        agents=agent_ids,
        skip_phases=[],
        effort=TIER_DEFAULT_EFFORT.get(tier, AgentEffort()),
        module=module,
        source="18factor",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

# Reverse mapping: phase → agent (built once at import)
_PHASE_TO_AGENT: dict[DevPhaseName, DevAgentName] = {
    v: k for k, v in DEV_AGENT_PHASE_MAP.items()
}


def _phases_to_agents(phases: list[DevPhaseName]) -> list[DevAgentName]:
    """Map ordered phase list to ordered agent list (deduplicated)."""
    agents: list[DevAgentName] = []
    seen: set[DevAgentName] = set()
    for p in phases:
        a = _PHASE_TO_AGENT.get(p)
        if a and a not in seen:
            agents.append(a)
            seen.add(a)
    return agents


def _resolve_effort(
    tier: ComplexityTier,
    agents: list[DevAgentName],
) -> AgentEffort:
    """Resolve per-agent effort for a complexity tier."""
    base = TIER_DEFAULT_EFFORT.get(tier, AgentEffort())

    # COMPLEX tier: bump specific agents to max
    if tier == ComplexityTier.COMPLEX:
        base.model_tier = "balanced"  # default for non-bumped agents
        # Bumps are applied per-agent in agent_runner via resolve_agent_model()

    return base


def resolve_agent_model(
    agent_name: str,
    tier: ComplexityTier | str = ComplexityTier.STANDARD,
) -> str:
    """Resolve model_tier for a specific agent given complexity tier.

    Called by agent_runner to select the right model per agent.

    Returns: "econ" | "balanced" | "max"
    """
    if isinstance(tier, str):
        tier = ComplexityTier(tier.lower())

    # COMPLEX tier: bump specific agents
    if tier == ComplexityTier.COMPLEX:
        if agent_name in COMPLEX_MODEL_BUMP:
            return COMPLEX_MODEL_BUMP[agent_name]

    return TIER_DEFAULT_EFFORT.get(tier, AgentEffort()).model_tier


def get_available_tiers() -> list[str]:
    """List available complexity tiers."""
    return [t.value for t in ComplexityTier]


def get_tier_phases(tier: ComplexityTier | str) -> list[DevPhaseName]:
    """Get the phase list for a given tier (convenience accessor)."""
    if isinstance(tier, str):
        tier = ComplexityTier(tier.lower())
    return list(COMPLEXITY_PHASES_DEV.get(tier, COMPLEXITY_PHASES_DEV[ComplexityTier.STANDARD]))
