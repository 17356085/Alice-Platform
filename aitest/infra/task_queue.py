"""
Task Queue — SQLite 持久化异步任务队列。

设计原则:
  1. 零外部依赖 — 纯 Python + SQLite
  2. 适合单机/低频场景（多用户/高并发时再切 Celery+Redis）
  3. 通过 FastAPI BackgroundTasks 消费

表结构:
  tasks:
    - id: TEXT PRIMARY KEY     # UUID
    - agent: TEXT              # Agent 名称
    - module: TEXT             # 模块名
    - page: TEXT               # 页面名（可空）
    - provider: TEXT           # LLM Provider
    - status: TEXT             # queued | running | completed | failed
    - result_json: TEXT        # JSON 结果（完成后写入）
    - error_msg: TEXT          # 错误信息
    - created_at: REAL         # 创建时间戳
    - started_at: REAL         # 开始执行时间戳
    - completed_at: REAL       # 完成时间戳

用法:
    from aitest.infra.task_queue import TaskQueue
    queue = TaskQueue()
    task_id = queue.enqueue("test-design-agent", module="equipment", page="alarm-config")
    status = queue.get(task_id)
"""
import os
import json
import time
import uuid
import sqlite3
import threading
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

# ── 路径 ──
WORKSTUDY = Path(__file__).resolve().parent.parent.parent
DB_PATH = WORKSTUDY / "aitest" / "tasks.db"


# ══════════════════════════════════════════════════════════════════════════
#  TaskQueue
# ══════════════════════════════════════════════════════════════════════════

class TaskQueue:
    """SQLite 持久化异步任务队列。"""

    def __init__(self, db_path: str = None):
        self._db = db_path or str(DB_PATH)
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self):
        with self._lock:
            conn = self._get_conn()
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    agent TEXT NOT NULL,
                    module TEXT NOT NULL,
                    page TEXT DEFAULT '',
                    provider TEXT DEFAULT 'claude',
                    status TEXT DEFAULT 'queued',
                    result_json TEXT DEFAULT '',
                    error_msg TEXT DEFAULT '',
                    created_at REAL,
                    started_at REAL,
                    completed_at REAL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)
            """)
            conn.commit()
            conn.close()

    def enqueue(
        self,
        agent: str,
        module: str,
        page: str = "",
        provider: str = "claude",
    ) -> str:
        """入队一个任务。返回 task_id。"""
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        now = time.time()

        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """INSERT INTO tasks (id, agent, module, page, provider, status, created_at)
                   VALUES (?, ?, ?, ?, ?, 'queued', ?)""",
                (task_id, agent, module, page, provider, now)
            )
            conn.commit()
            conn.close()

        return task_id

    def dequeue(self) -> Optional[dict]:
        """取出下一个 queued 任务并标记为 running。返回任务 dict 或 None。"""
        with self._lock:
            conn = self._get_conn()
            row = conn.execute(
                "SELECT * FROM tasks WHERE status='queued' ORDER BY created_at LIMIT 1"
            ).fetchone()

            if not row:
                conn.close()
                return None

            now = time.time()
            conn.execute(
                "UPDATE tasks SET status='running', started_at=? WHERE id=?",
                (now, row["id"])
            )
            conn.commit()
            conn.close()

            return dict(row)

    def mark_completed(self, task_id: str, result: dict):
        """标记任务完成并写入结果。"""
        now = time.time()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """UPDATE tasks SET status='completed', result_json=?, completed_at=?
                   WHERE id=?""",
                (json.dumps(result, ensure_ascii=False), now, task_id)
            )
            conn.commit()
            conn.close()

    def mark_failed(self, task_id: str, error: str):
        """标记任务失败。"""
        now = time.time()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """UPDATE tasks SET status='failed', error_msg=?, completed_at=?
                   WHERE id=?""",
                (error, now, task_id)
            )
            conn.commit()
            conn.close()

    def get(self, task_id: str) -> Optional[dict]:
        """查询单个任务状态。"""
        conn = self._get_conn()
        row = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        conn.close()

        if not row:
            return None

        task = dict(row)
        if task.get("result_json"):
            try:
                task["result"] = json.loads(task["result_json"])
            except json.JSONDecodeError:
                task["result"] = {}
        return task

    def list_tasks(self, status: str = None, limit: int = 20) -> list[dict]:
        """列出任务。"""
        conn = self._get_conn()
        if status:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC LIMIT ?",
                (status, limit)
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
                (limit,)
            ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def count_by_status(self) -> dict:
        """按状态统计任务数。"""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status"
        ).fetchall()
        conn.close()
        return {r["status"]: r["cnt"] for r in rows}

    def cleanup(self, older_than_hours: int = 24):
        """清理旧任务记录。"""
        cutoff = time.time() - (older_than_hours * 3600)
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "DELETE FROM tasks WHERE completed_at < ? AND status IN ('completed', 'failed')",
                (cutoff,)
            )
            deleted = conn.total_changes
            conn.commit()
            conn.close()
        return deleted


# ══════════════════════════════════════════════════════════════════════════
#  Task Runner（后台消费线程）
# ══════════════════════════════════════════════════════════════════════════

class TaskRunner:
    """后台任务执行器 — 轮询队列并消费任务。"""

    def __init__(self, queue: TaskQueue = None, poll_interval: float = 2.0):
        self.queue = queue or TaskQueue()
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """启动后台消费线程。"""
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止消费线程。"""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self):
        while self._running:
            task = self.queue.dequeue()
            if task:
                try:
                    self._execute(task)
                except Exception as e:
                    self.queue.mark_failed(task["id"], str(e))
            else:
                time.sleep(self.poll_interval)

    def _execute(self, task: dict):
        """执行单个任务（在后台线程中）。"""
        try:
            from aitest.agents.agent_runner import run_agent

            result = run_agent(
                agent_name=task["agent"],
                provider=task.get("provider", "claude"),
                module=task["module"],
                page=task.get("page", ""),
                verbose=False,
            )
            self.queue.mark_completed(task["id"], result)
        except Exception as e:
            self.queue.mark_failed(task["id"], str(e))


# ══════════════════════════════════════════════════════════════════════════
#  全局实例
# ══════════════════════════════════════════════════════════════════════════

_queue = TaskQueue()
_runner = TaskRunner(_queue)


def get_queue() -> TaskQueue:
    return _queue


def get_runner() -> TaskRunner:
    return _runner
