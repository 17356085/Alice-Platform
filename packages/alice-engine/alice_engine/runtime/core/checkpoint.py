"""Checkpoint — LangGraph 检查点管理。

解耦: 路径通过 PathResolver 接口传入。

用法:
    from alice_engine.runtime.checkpoint import CheckpointManager

    manager = CheckpointManager(governance_path="./governance")
    checkpointer = manager.get_checkpointer()
"""

import logging
import sqlite3
import time
from pathlib import Path

logger = logging.getLogger(__name__)

# 保留策略
DEFAULT_MAX_AGE_DAYS = 7
DEFAULT_MAX_RUNS = 50
MAX_DB_SIZE_MB = 500


class CheckpointManager:
    """检查点管理器。

    用法:
        manager = CheckpointManager(governance_path="./governance")
        checkpointer = manager.get_checkpointer()
        graph = builder.compile(checkpointer=checkpointer)
    """

    def __init__(self, governance_path: str | Path):
        self.governance = Path(governance_path)
        self.checkpoint_dir = self.governance / ".graph_state"
        self.db_path = self.checkpoint_dir / "checkpoints.sqlite"

    def get_checkpointer(self):
        """返回 SqliteSaver 实例。"""
        try:
            from langgraph.checkpoint.sqlite import SqliteSaver
        except ImportError:
            logger.warning("langgraph-checkpoint-sqlite not available")
            return None

        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        return SqliteSaver(conn)

    def cleanup(self, max_age_days: int = DEFAULT_MAX_AGE_DAYS,
                max_runs: int = DEFAULT_MAX_RUNS) -> dict:
        """清理旧检查点。"""
        if not self.db_path.exists():
            return {"cleaned": 0}

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()

            # 删除超过 max_age_days 的记录
            cutoff = time.time() - (max_age_days * 86400)
            cursor.execute(
                "DELETE FROM checkpoints WHERE created_at < ?",
                (cutoff,)
            )
            cleaned = cursor.rowcount

            conn.commit()
            conn.close()

            return {"cleaned": cleaned}
        except Exception as e:
            logger.warning("Checkpoint cleanup failed: %s", e)
            return {"cleaned": 0, "error": str(e)}

    def list_runs(self) -> list[str]:
        """列出所有 run ID。"""
        if not self.db_path.exists():
            return []

        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT thread_id FROM checkpoints")
            runs = [row[0] for row in cursor.fetchall()]
            conn.close()
            return runs
        except Exception:
            return []
