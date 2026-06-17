"""
LangGraph Checkpoint 配置 — SqliteSaver 工厂 + 辅助函数。

用法:
    from aitest.graphs.checkpoint import get_checkpointer
    checkpointer = get_checkpointer()
    graph = builder.compile(checkpointer=checkpointer)
"""

import sqlite3
from pathlib import Path
from typing import Optional

from langgraph.checkpoint.sqlite import SqliteSaver

# ── 路径配置 ──────────────────────────────────────────────────────────
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
CHECKPOINT_DIR = WORKSTUDY / "governance" / ".graph_state"
DB_PATH = CHECKPOINT_DIR / "checkpoints.sqlite"


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
