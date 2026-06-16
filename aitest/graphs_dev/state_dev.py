"""
DevSOPState — 开发 SOP 图的状态定义 (完整版 9 Agent, 10 Phase)。

与 state.py（测试 SOP）并行。
"""

from typing import TypedDict, Optional, List, Dict, Any, Annotated, Literal
import operator

# ═══════════════════════════════════════════════════════════════
# Enums / Literals
# ═══════════════════════════════════════════════════════════════

DevSOPMode = Literal[
    "full", "resume", "status",
    "from-architecture", "from-frontend", "from-backend",
    "review-only",
]

DevPhaseName = Literal[
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

DevAgentName = Literal[
    "pm-agent",
    "req-agent",
    "arch-agent",
    "design-agent",
    "frontend-agent",
    "backend-agent",
    "review-agent",
    "dev-test-agent",
    "debug-agent",
    "build-agent",
]

# 规范阶段顺序
DEV_CANONICAL_PHASES: list[DevPhaseName] = [
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

# Mode → skip_phases
DEV_MODE_SKIP_MAP: dict[DevSOPMode, list[DevPhaseName]] = {
    "full": [],
    "resume": [],
    "status": [],
    "from-architecture": ["Plan", "Requirements"],
    "from-frontend": ["Plan", "Requirements", "Architecture", "Component Design"],
    "from-backend": ["Plan", "Requirements", "Architecture", "Component Design", "Frontend Impl"],
    "review-only": ["Plan", "Requirements", "Architecture", "Component Design",
                     "Frontend Impl", "Backend Impl"],
}

# Agent → Phase
DEV_AGENT_PHASE_MAP: dict[DevAgentName, DevPhaseName] = {
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

# Phase → Node name
DEV_PHASE_TO_NODE: dict[DevPhaseName, str] = {
    "Plan": "pm_agent",
    "Requirements": "req_agent",
    "Architecture": "arch_agent",
    "Component Design": "design_agent",
    "Frontend Impl": "frontend_agent",
    "Backend Impl": "backend_agent",
    "Code Review": "review_agent",
    "Dev Test": "dev_test_agent",
    "Debug & Fix": "debug_agent",
    "Build": "build_agent",
}

ALL_DEV_AGENT_NODES = list(set(DEV_PHASE_TO_NODE.values()))

# ═══════════════════════════════════════════════════════════════
# State TypedDict
# ═══════════════════════════════════════════════════════════════

class DevSOPState(TypedDict):
    module: str
    pages: List[str]
    mode: DevSOPMode
    provider: str
    run_id: str
    current_phase: DevPhaseName
    completed_phases: Annotated[List[DevPhaseName], operator.add]
    failed_phases: Annotated[List[DevPhaseName], operator.add]
    skip_phases: List[DevPhaseName]
    current_component_index: int
    per_component_results: Annotated[List[Dict[str, Any]], operator.add]
    agent_outputs: Dict[str, Any]
    artifact_map: Dict[str, List[str]]
    gate_results: Annotated[List[Dict[str, Any]], operator.add]
    fatal_error: Optional[str]
    status: str

# ═══════════════════════════════════════════════════════════════
# Helper
# ═══════════════════════════════════════════════════════════════

def create_initial_state_dev(
    module: str,
    pages: List[str] = None,
    mode: DevSOPMode = "full",
    provider: str = "claude",
    run_id: str = "",
) -> dict:
    import time
    if not run_id:
        run_id = f"dev-sop-{module}-{int(time.time())}"
    return {
        "module": module,
        "pages": pages or [],
        "mode": mode,
        "provider": provider,
        "run_id": run_id,
        "current_phase": "Plan",
        "completed_phases": [],
        "failed_phases": [],
        "skip_phases": DEV_MODE_SKIP_MAP.get(mode, []),
        "current_component_index": 0,
        "per_component_results": [],
        "agent_outputs": {},
        "artifact_map": {},
        "gate_results": [],
        "fatal_error": None,
        "status": "running",
    }
