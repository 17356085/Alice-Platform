"""Re-export — 保持向后兼容。"""

from alice_engine.runtime.core.checkpoint import (  # noqa: F401
    CheckpointManager,
)

# 兼容旧接口
from aitest.runtime.paths import get_workstudy

WORKSTUDY = get_workstudy()
CHECKPOINT_DIR = WORKSTUDY / "governance" / ".graph_state"
DB_PATH = CHECKPOINT_DIR / "checkpoints.sqlite"

DEFAULT_MAX_AGE_DAYS = 7
DEFAULT_MAX_RUNS = 50
MAX_DB_SIZE_MB = 500

_manager = None

def _get_manager():
    global _manager
    if _manager is None:
        _manager = CheckpointManager(governance_path=WORKSTUDY / "governance")
    return _manager

def get_checkpointer():
    """兼容旧接口。"""
    return _get_manager().get_checkpointer()

def get_checkpointer_for_thread(thread_id: str):
    """兼容旧接口。"""
    return get_checkpointer()

def list_runs():
    """兼容旧接口。"""
    return _get_manager().list_runs()

def get_latest_state(thread_id: str):
    """兼容旧接口。"""
    return None

def cleanup_run(thread_id: str):
    """兼容旧接口。"""
    pass

def cleanup_old_checkpoints():
    """兼容旧接口。"""
    return _get_manager().cleanup()

def get_checkpoint_stats():
    """兼容旧接口。"""
    return {"runs": len(list_runs())}
