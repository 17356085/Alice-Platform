"""Re-export from alice_engine.runtime.checkpoint — 保持向后兼容。"""

from alice_engine.runtime.checkpoint import (  # noqa: F401
    CheckpointManager,
)

# 兼容旧接口
_manager = None

def get_checkpointer():
    """兼容旧接口。"""
    global _manager
    if _manager is None:
        from aitest.runtime.paths import get_workstudy
        _manager = CheckpointManager(governance_path=get_workstudy() / "governance")
    return _manager.get_checkpointer()
