"""LangGraph checkpoint — PostgreSQL 后端。

与 database_pg.py（业务表, docker exec psql）不同：LangGraph 的 checkpoint
表结构由 LangGraph 自己的 PostgresSaver 管理（checkpoints / checkpoint_writes /
checkpoint_blobs），走 psycopg 原生连接更直接，不必套用 docker-exec 那一层。

本机环境已验证 TCP 可直连 Docker PG（network_mode: host），历史上
database_pg.py 里"asyncpg/psycopg2 连不上 Windows Docker PG"的坑在这台机器上
不复现。若换环境后连不上，回退方案是切回 docker exec + 自研 saver（见架构
诊断报告 P0 备选方案）。

用法（由 aitest/graphs/checkpoint.py 按 AITEST_DB_BACKEND 选择性注入）:
    from aitest.infra.checkpoint_pg import PostgresCheckpointStore
    from alice_engine.runtime.checkpoint import CheckpointManager

    manager = CheckpointManager(governance_path=..., store=PostgresCheckpointStore())

PostgresCheckpointStore 实现的是 alice_engine.runtime.core.checkpoint.CheckpointStore
协议（get_checkpointer / list_runs / cleanup 三个方法），engine 侧不需要、也不
import 这个模块 —— 后端选择完全发生在平台层。
"""

import os
import logging

logger = logging.getLogger("checkpoint.pg")

DEFAULT_CONN_STRING = "postgresql://aitest:aitest@localhost:5432/aitest"

_saver = None
_saver_cm = None  # PostgresSaver.from_conn_string() 返回的 context manager，需持有引用防止连接被回收


def _get_conn_string() -> str:
    """复用 database_pg.py 的 AITEST_DATABASE_URL 约定，去掉 +asyncpg 方言后缀给 psycopg 用。"""
    url = os.environ.get("AITEST_DATABASE_URL", DEFAULT_CONN_STRING)
    return url.replace("postgresql+asyncpg://", "postgresql://")


def build_postgres_checkpointer():
    """返回（懒加载单例）PostgresSaver 实例，首次调用自动建表。"""
    global _saver, _saver_cm

    if _saver is not None:
        return _saver

    try:
        from langgraph.checkpoint.postgres import PostgresSaver
    except ImportError:
        raise ImportError(
            "langgraph-checkpoint-postgres 未安装。"
            "请运行: pip install langgraph-checkpoint-postgres psycopg[binary]"
        )

    conn_string = _get_conn_string()
    _saver_cm = PostgresSaver.from_conn_string(conn_string)
    _saver = _saver_cm.__enter__()
    _saver.setup()  # 幂等建表
    logger.info("postgres_checkpointer_ready")
    return _saver


def list_runs_pg() -> list[str]:
    """列出所有 run（thread_id），直接查 LangGraph 的 checkpoints 表。"""
    try:
        import psycopg

        with psycopg.connect(_get_conn_string()) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT DISTINCT thread_id FROM checkpoints")
                return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logger.warning("list_runs_pg failed: %s", e)
        return []


def cleanup_pg(max_age_days: int = 7, max_runs: int = 50) -> dict:
    """清理旧检查点 —— 按 run 数量保留，不是按时间。

    注意：LangGraph 官方 PostgresSaver 的 checkpoints 表没有独立的时间戳列
    （`checkpoint_id` 是可字典序排序的 UUID6-like id，但解码时间戳不划算）。
    因此 PG 分支用「每个 thread_id 保留最新 max_runs 个，其余整条删除」代替
    sqlite 分支的按 max_age_days 删除；max_age_days 参数在此分支被忽略。
    """
    try:
        import psycopg

        with psycopg.connect(_get_conn_string()) as conn:
            with conn.cursor() as cur:
                # 按每个 thread 最新 checkpoint_id 排序，找出超出 max_runs 的旧 thread
                cur.execute(
                    """
                    SELECT thread_id FROM (
                        SELECT thread_id, MAX(checkpoint_id) AS latest
                        FROM checkpoints
                        GROUP BY thread_id
                        ORDER BY latest DESC
                        OFFSET %s
                    ) stale
                    """,
                    (max_runs,),
                )
                stale_threads = [row[0] for row in cur.fetchall()]

                cleaned = 0
                for thread_id in stale_threads:
                    for table in ("checkpoint_writes", "checkpoint_blobs", "checkpoints"):
                        cur.execute(f"DELETE FROM {table} WHERE thread_id = %s", (thread_id,))
                    cleaned += 1
            conn.commit()
        return {"cleaned": cleaned}
    except Exception as e:
        logger.warning("cleanup_pg failed: %s", e)
        return {"cleaned": 0, "error": str(e)}


class PostgresCheckpointStore:
    """CheckpointStore 接口的 Postgres 实现（见 alice_engine.runtime.core.checkpoint.CheckpointStore）。

    薄封装，实际逻辑复用上面的模块级函数（模块级单例连接/saver 复用，
    不必每个 store 实例各自维护连接状态）。
    """

    def get_checkpointer(self):
        return build_postgres_checkpointer()

    def list_runs(self) -> list[str]:
        return list_runs_pg()

    def cleanup(self, max_age_days: int = 7, max_runs: int = 50) -> dict:
        return cleanup_pg(max_age_days=max_age_days, max_runs=max_runs)
