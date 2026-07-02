"""Re-export from alice_engine.workflow.state — 保持向后兼容。"""

from alice_engine.workflow.state import (  # noqa: F401
    SOPState,
    SOPMode,
    PhaseName,
    AgentName,
    GateLevel,
    GateResult,
    CommonSOPStage,
    CANONICAL_PHASES,
    MODE_SKIP_MAP,
    AGENT_PHASE_MAP,
    create_initial_state,
    configure_paths,
    get_module_dir,
    get_page_dir,
    get_test_project_root,
)

# 兼容旧接口: 配置路径
try:
    from aitest.runtime.paths import get_workstudy, get_context_modules, get_test_project_root as _get_tpr
    configure_paths(
        workstudy=get_workstudy(),
        context_modules=get_context_modules(),
        test_project_root=_get_tpr(),
    )
except Exception:
    pass

# 兼容旧接口: SkillObservation 别名
from alice_engine.core.task import Observation as SkillObservation  # noqa: F401

# 兼容旧接口: AgentResult
from dataclasses import dataclass, field
from typing import Any

@dataclass
class AgentResult:
    """Agent 执行结果。"""
    agent_name: str = ""
    status: str = "pending"
    output: dict = field(default_factory=dict)
    error: str = None
    elapsed_seconds: float = 0.0

# 兼容旧接口: validate_phase_artifacts
def validate_phase_artifacts(state, phase_name):
    """兼容旧接口。"""
    return {"passed": True, "issues": []}

MAX_PHASE_RETRY_ROUNDS = 3
