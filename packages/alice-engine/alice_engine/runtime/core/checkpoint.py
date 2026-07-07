"""Checkpoint — LangGraph 检查点管理。

解耦: engine 只依赖 CheckpointStore 接口，不 import 任何具体存储实现
（sqlite3 是默认实现 SqliteCheckpointStore 内部细节，不是 engine 对外暴露的耦合点）。
Postgres 等其他后端由平台层（aitest/infra/checkpoint_pg.py）实现同一接口后注入，
engine 包本身不感知、也不依赖 Postgres/psycopg。

用法:
    from alice_engine.runtime.checkpoint import CheckpointManager

    manager = CheckpointManager(governance_path="./governance")
    checkpointer = manager.get_checkpointer()

    # 注入自定义后端（如 Postgres，由调用方在平台层组装）：
    manager = CheckpointManager(governance_path="./governance", store=PostgresCheckpointStore())
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# 保留策略
DEFAULT_MAX_AGE_DAYS = 7
DEFAULT_MAX_RUNS = 50
MAX_DB_SIZE_MB = 500


@runtime_checkable
class CheckpointStore(Protocol):
    """检查点存储接口。任何后端（SQLite/Postgres/...）实现这三个方法即可接入。"""

    def get_checkpointer(self) -> Any:
        """返回 LangGraph checkpointer 实例（如 SqliteSaver / PostgresSaver）。"""
        ...

    def list_runs(self) -> list[str]:
        """列出所有 run（thread_id）。"""
        ...

    def cleanup(self, max_age_days: int = DEFAULT_MAX_AGE_DAYS,
                max_runs: int = DEFAULT_MAX_RUNS) -> dict:
        """清理旧检查点，返回 {"cleaned": n} 或 {"cleaned": 0, "error": ...}。"""
        ...


class SqliteCheckpointStore:
    """默认实现：本地 SQLite 文件（单用户模式）。"""

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
        """清理超过 max_age_days 的旧检查点。"""
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


class CheckpointManager:
    """检查点管理门面（facade）。

    默认用 SqliteCheckpointStore；调用方可注入任意 CheckpointStore 实现
    （例如平台层的 Postgres 后端），engine 侧代码全程只见 CheckpointStore 接口。

    用法:
        manager = CheckpointManager(governance_path="./governance")
        checkpointer = manager.get_checkpointer()
        graph = builder.compile(checkpointer=checkpointer)
    """

    def __init__(self, governance_path: str | Path, store: CheckpointStore | None = None):
        self.governance = Path(governance_path)
        self._store = store or SqliteCheckpointStore(governance_path)

    def get_checkpointer(self):
        return self._store.get_checkpointer()

    def cleanup(self, max_age_days: int = DEFAULT_MAX_AGE_DAYS,
                max_runs: int = DEFAULT_MAX_RUNS) -> dict:
        return self._store.cleanup(max_age_days=max_age_days, max_runs=max_runs)

    def list_runs(self) -> list[str]:
        return self._store.list_runs()
