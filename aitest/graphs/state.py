"""Re-export from alice_engine.workflow.state — 保持向后兼容。"""

from alice_engine.workflow.state import (  # noqa: F401
    SOPState,
    SOPMode,
    PhaseName,
    AgentName,
    GateLevel,
    GateResult,
    CommonSOPStage,
    SkillObservation,
    PageResult,
    AgentResult,
    CANONICAL_PHASES,
    MODE_SKIP_MAP,
    AGENT_PHASE_MAP,
    create_initial_state as _create_initial_state,
    validate_phase_artifacts,
    MAX_PHASE_RETRY_ROUNDS,
    configure_paths,
    get_module_dir,
    get_page_dir,
    get_test_project_root,
)

def create_initial_state(*args, **kwargs):
    state = _create_initial_state(*args, **kwargs)
    if kwargs.get("provider") is None and state.get("provider") == "anthropic":
        state["provider"] = "claude"
    return state
