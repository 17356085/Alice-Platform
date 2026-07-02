"""Re-export from alice_engine.core.task — 保持向后兼容。"""

from alice_engine.core.task import (  # noqa: F401
    Observation,
    AgentState,
    AgentEvent,
    AgentEventType,
    ArtifactRule,
)

# 兼容旧接口
from aitest.engine.task import (
    _ALL_ARTIFACT_RULES,
    CODE_REDLINE_CHECKS,
    AUTOMATION_ARTIFACT_RULES,
    DEV_ARTIFACT_RULES,
)
