"""Re-export from alice_engine.core.state_machine — 保持向后兼容。"""

from alice_engine.core.state_machine import (  # noqa: F401
    TaskState,
    VALID_TRANSITIONS,
    TaskStateContext,
    update_agent_state,
    MILESTONE_SKILLS,
)
