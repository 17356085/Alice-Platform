"""
LangGraph Checkpoint 配置 — SqliteSaver 工厂 + 辅助函数。

用法:
    from aitest.graphs.checkpoint import get_checkpointer
    checkpointer = get_checkpointer()
    graph = builder.compile(checkpointer=checkpointer)
"""

import logging
import sqlite3
import time
from pathlib import Path
from typing import Optional

from langgraph.checkpoint.sqlite import SqliteSaver
from aitest.platform.paths import get_workstudy

logger = logging.getLogger(__name__)

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = get_workstudy()
CHECKPOINT_DIR = WORKSTUDY / "governance" / ".graph_state"
DB_PATH = CHECKPOINT_DIR / "checkpoints.sqlite"

# ── 保留策略 ──────────────────────────────────────────────────────────
DEFAULT_MAX_AGE_DAYS = 7        # 默认保留 7 天
DEFAULT_MAX_RUNS = 50           # 最多保留 50 个 run
MAX_DB_SIZE_MB = 500            # 超过此大小强制 VACUUM


def _ensure_dir() -> None:
    """确保 checkpoint 目录存在。"""
    CHECKPOINT_DIR.mkdir(parents=True, exist_ok=True)


def get_checkpointer() -> SqliteSaver:
    """
    返回 SqliteSaver 实例（使用默认 SQLite 数据库）。

    数据库路径: governance/.graph_state/checkpoints.sqlite
    """
    _ensure_dir()
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    return SqliteSaver(conn)


def get_checkpointer_for_thread(thread_id: str) -> SqliteSaver:
    """
    返回特定 thread 的 SqliteSaver。

    可用于多模块并行运行时的隔离。
    """
    _ensure_dir()
    db_path = CHECKPOINT_DIR / f"{thread_id}.sqlite"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    return SqliteSaver(conn)


def list_runs(limit: int = 20) -> list[dict]:
    """
    列出所有最近的 checkpoint 运行。

    返回: [{"run_id": str, "updated_at": str}, ...]
    """
    _ensure_dir()
    if not DB_PATH.exists():
        return []

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.execute(
            """SELECT DISTINCT thread_id, MAX(created_at) as updated_at
               FROM checkpoints
               GROUP BY thread_id
               ORDER BY updated_at DESC
               LIMIT ?""",
            (limit,)
        )
        return [
            {"run_id": row[0], "updated_at": row[1]}
            for row in cursor.fetchall()
        ]
    except sqlite3.OperationalError:
        # 数据库存在但 checkpoints 表尚未创建
        return []


def get_latest_state(run_id: str) -> Optional[dict]:
    """
    获取最近一次 checkpoint 的完整状态（用于 CLI status 命令）。

    返回: 状态字典，如果未找到则返回 None
    """
    _ensure_dir()
    if not DB_PATH.exists():
        return None

    from aitest.graphs.sop_graph import build_sop_graph
    graph = build_sop_graph()

    checkpointer = get_checkpointer()
    compiled = graph.compile(checkpointer=checkpointer)

    thread = {"configurable": {"thread_id": run_id}}
    try:
        state = compiled.get_state(thread)
        if state and state.values:
            return state.values
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("checkpoint.get_latest_state", "get_state", e, {"run_id": run_id})
    return None


def cleanup_run(run_id: str) -> bool:
    """
    删除一个 run 的所有 checkpoint。

    返回: True 如果成功删除
    """
    _ensure_dir()
    if not DB_PATH.exists():
        return False

    try:
        conn = sqlite3.connect(str(DB_PATH))
        conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (run_id,))
        conn.commit()
        return True
    except sqlite3.OperationalError:
        return False


def cleanup_old_checkpoints(
    max_age_days: int = DEFAULT_MAX_AGE_DAYS,
    max_runs: int = DEFAULT_MAX_RUNS,
) -> int:
    """
    清理过期 checkpoint。

    策略:
    1. 删除超过 max_age_days 天的 checkpoint
    2. 如果 run 数量超过 max_runs，删除最旧的 run
    3. 清理后执行 VACUUM（如果 DB 超过阈值）

    返回: 删除的 run 数量
    """
    _ensure_dir()
    if not DB_PATH.exists():
        return 0

    deleted = 0
    try:
        conn = sqlite3.connect(str(DB_PATH))

        # Step 1: 按时间清理
        cutoff = time.time() - (max_age_days * 86400)
        # LangGraph stores created_at as ISO format string; we use ROWID as proxy
        # First delete by age using the checkpoint_id ordering (monotonic)
        cursor = conn.execute(
            "SELECT DISTINCT thread_id FROM checkpoints "
            "GROUP BY thread_id "
            "HAVING MAX(created_at) < ?",
            (cutoff,)
        )
        old_threads = [row[0] for row in cursor.fetchall()]
        for tid in old_threads:
            conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (tid,))
            deleted += 1

        # Step 2: 按数量清理（保留最近 max_runs 个 run）
        if max_runs > 0:
            cursor = conn.execute(
                "SELECT thread_id FROM checkpoints "
                "GROUP BY thread_id "
                "ORDER BY MAX(checkpoint_id) DESC"
            )
            all_threads = [row[0] for row in cursor.fetchall()]
            if len(all_threads) > max_runs:
                excess = all_threads[max_runs:]
                for tid in excess:
                    conn.execute("DELETE FROM checkpoints WHERE thread_id = ?", (tid,))
                    deleted += 1

        conn.commit()

        # Step 3: VACUUM if needed
        _maybe_vacuum(conn)

        conn.close()

        if deleted > 0:
            logger.info("Checkpoint cleanup: removed %d old runs", deleted)
    except sqlite3.OperationalError as e:
        logger.debug("Checkpoint cleanup skipped: %s", e)

    return deleted


def _maybe_vacuum(conn: sqlite3.Connection) -> None:
    """如果 DB 文件超过阈值，执行 VACUUM 回收磁盘空间。"""
    try:
        if DB_PATH.exists():
            size_mb = DB_PATH.stat().st_size / (1024 * 1024)
            if size_mb > MAX_DB_SIZE_MB:
                logger.info("Checkpoint DB %.1f MB > %d MB threshold, VACUUM...",
                           size_mb, MAX_DB_SIZE_MB)
                conn.execute("VACUUM")
                new_size = DB_PATH.stat().st_size / (1024 * 1024)
                logger.info("Checkpoint DB after VACUUM: %.1f MB", new_size)
    except Exception:
        pass


def get_checkpoint_stats() -> dict:
    """返回 checkpoint 存储统计信息，用于观测 dashboard。"""
    _ensure_dir()
    stats = {
        "db_path": str(DB_PATH),
        "exists": DB_PATH.exists(),
        "size_mb": 0,
        "run_count": 0,
        "total_checkpoints": 0,
        "oldest_run": None,
        "newest_run": None,
    }

    if not DB_PATH.exists():
        return stats

    try:
        stats["size_mb"] = round(DB_PATH.stat().st_size / (1024 * 1024), 2)
        conn = sqlite3.connect(str(DB_PATH))

        row = conn.execute("SELECT COUNT(DISTINCT thread_id) FROM checkpoints").fetchone()
        stats["run_count"] = row[0] if row else 0

        row = conn.execute("SELECT COUNT(*) FROM checkpoints").fetchone()
        stats["total_checkpoints"] = row[0] if row else 0

        row = conn.execute(
            "SELECT thread_id, MIN(created_at) FROM checkpoints GROUP BY thread_id ORDER BY created_at ASC LIMIT 1"
        ).fetchone()
        if row:
            stats["oldest_run"] = {"run_id": row[0], "created_at": row[1]}

        row = conn.execute(
            "SELECT thread_id, MAX(created_at) FROM checkpoints GROUP BY thread_id ORDER BY created_at DESC LIMIT 1"
        ).fetchone()
        if row:
            stats["newest_run"] = {"run_id": row[0], "created_at": row[1]}

        conn.close()
    except sqlite3.OperationalError:
        pass

    return stats
