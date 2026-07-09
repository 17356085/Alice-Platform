"""Task Queue — PostgreSQL persistent task queue with retry + stale recovery. v3.1

v3.1: Uses parameterized queries via aitest.infra.sql (no more f-string SQL).
"""

import json
import sqlite3
import time
import uuid
import random
import threading
from typing import Optional
from pathlib import Path
from aitest.infra.sql import safe_exec, safe_query
from aitest.infra.logging import get_logger
from aitest.infra.config_registry import cfg

logger = get_logger("task_queue")
DEFAULT_MAX_RETRIES = 3
STALE_TASK_TIMEOUT_S = cfg.task_stale_timeout_s


class TaskQueue:
    def __init__(self, db_path: str | Path | None = None):
        self._db_path = Path(db_path) if db_path is not None else None
        if self._db_path is not None:
            from aitest.infra import database as _db
            from aitest.infra import database_sqlite as _sqlite

            _db._backend = "sqlite"
            _sqlite._DB_PATH = self._db_path
            _sqlite._DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            safe_exec("SELECT 1")

    def _get_conn(self):
        if self._db_path is None:
            raise RuntimeError("TaskQueue._get_conn() is only available for sqlite-backed test queues")
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def enqueue(self, agent: str, module: str, page: str = "",
                provider: str = "claude", max_retries: int = DEFAULT_MAX_RETRIES) -> str:
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        now = time.time()
        safe_exec(
            "INSERT INTO tasks (id, agent, module, page, provider, status, max_retries, created_at) "
            "VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)",
            [task_id, agent, module, page, provider, max_retries, now],
        )
        return task_id

    def dequeue(self) -> Optional[dict]:
        now = time.time()
        rows = safe_query(
            "SELECT * FROM tasks WHERE status='queued' AND (retry_at IS NULL OR retry_at <= ?) "
            "ORDER BY created_at LIMIT 1", [now],
        )
        if not rows:
            return None
        task = rows[0]
        safe_exec("UPDATE tasks SET status='running', started_at=? WHERE id=?", [now, task['id']])
        return task

    def mark_completed(self, task_id: str, result: dict):
        now = time.time()
        result_json = json.dumps(result, ensure_ascii=False)
        safe_exec(
            "UPDATE tasks SET status='completed', result_json=?, completed_at=? WHERE id=?",
            [result_json, now, task_id],
        )

    def mark_failed(self, task_id: str, error: str):
        now = time.time()
        rows = safe_query("SELECT * FROM tasks WHERE id=?", [task_id])
        if not rows:
            return
        task = rows[0]
        retry_count = task.get("retry_count") or 0
        max_retries = task.get("max_retries") or DEFAULT_MAX_RETRIES
        if retry_count < max_retries:
            delay = min(1.0 * (2 ** retry_count), 60.0)
            delay += random.uniform(0, delay * 0.3)
            retry_at = now + delay
            error_msg = f"[retry {retry_count + 1}/{max_retries}] {error}"
            safe_exec(
                "UPDATE tasks SET status='queued', error_msg=?, retry_count=?, retry_at=?, completed_at=? WHERE id=?",
                [error_msg, retry_count + 1, retry_at, now, task_id],
            )
            logger.info("task_retry_queued", task_id=task_id,
                        retry=f"{retry_count + 1}/{max_retries}", backoff_s=round(delay, 1))
            return
        error_msg = f"[exhausted after {retry_count} retries] {error}"
        safe_exec(
            "UPDATE tasks SET status='failed', error_msg=?, completed_at=? WHERE id=?",
            [error_msg, now, task_id],
        )
        logger.error("task_exhausted", task_id=task_id, retries=retry_count)

    def mark_failed_no_retry(self, task_id: str, error: str):
        now = time.time()
        safe_exec(
            "UPDATE tasks SET status='failed', error_msg=?, completed_at=? WHERE id=?",
            [error, now, task_id],
        )

    def recover_stale_tasks(self) -> int:
        cutoff = time.time() - STALE_TASK_TIMEOUT_S
        now = time.time()
        safe_exec(
            "UPDATE tasks SET status='failed', error_msg='stale task — timed out after 30min', "
            "completed_at=? WHERE status='running' AND started_at < ?",
            [now, cutoff],
        )
        rows = safe_query(
            "SELECT COUNT(*) as cnt FROM tasks WHERE status='failed' "
            "AND error_msg='stale task — timed out after 30min'",
        )
        recovered = rows[0]["cnt"] if rows else 0
        if recovered:
            logger.warning("stale_tasks_recovered", count=recovered)
        return recovered

    def retry_failed(self, task_id: str) -> bool:
        rows = safe_query("SELECT * FROM tasks WHERE id=? AND status='failed'", [task_id])
        if not rows:
            return False
        safe_exec(
            "UPDATE tasks SET status='queued', error_msg='', started_at=NULL, completed_at=NULL WHERE id=?",
            [task_id],
        )
        return True

    def get(self, task_id: str) -> Optional[dict]:
        rows = safe_query("SELECT * FROM tasks WHERE id=?", [task_id])
        if not rows:
            return None
        task = rows[0]
        if task.get("result_json"):
            try:
                task["result"] = json.loads(task["result_json"])
            except json.JSONDecodeError:
                task["result"] = {}
        return task

    def list_tasks(self, status: str = None, limit: int = 20) -> list[dict]:
        if status:
            return safe_query("SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC LIMIT ?",
                              [status, limit])
        return safe_query("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", [limit])

    def count_by_status(self) -> dict:
        rows = safe_query("SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status")
        counts = {r["status"]: r["cnt"] for r in rows}
        counts["pending"] = counts.get("queued", 0) + counts.get("running", 0)
        return counts

    def cleanup(self, older_than_hours: int = 24):
        cutoff = time.time() - (older_than_hours * 3600)
        safe_exec(
            "DELETE FROM tasks WHERE completed_at < ? AND status IN ('completed', 'failed')",
            [cutoff],
        )
        return 0


class TaskRunner:
    def __init__(self, queue: TaskQueue = None, poll_interval: float = 2.0,
                 executor=None):
        self.queue = queue or TaskQueue()
        self.poll_interval = poll_interval
        self._executor = executor  # Optional[Callable[[dict], dict]] — injected by platform
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stale_check_count = 0

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self):
        while self._running:
            self._stale_check_count += 1
            if self._stale_check_count % 30 == 0:
                try:
                    self.queue.recover_stale_tasks()
                except Exception:
                    pass
            task = self.queue.dequeue()
            if task:
                try:
                    self._execute(task)
                except Exception as e:
                    error_str = str(e)
                    if any(kw in error_str.lower() for kw in ("fatal", "context_length", "permission", "denied", "auth")):
                        self.queue.mark_failed_no_retry(task["id"], error_str)
                    else:
                        self.queue.mark_failed(task["id"], error_str)
            else:
                time.sleep(self.poll_interval)

    def _execute(self, task: dict):
        if self._executor is None:
            raise RuntimeError("TaskRunner has no executor — call set_executor() or pass executor= at init")
        result = self._executor(task)
        self.queue.mark_completed(task["id"], result)


_queue = TaskQueue()
_runner = TaskRunner(_queue)

def get_queue() -> TaskQueue:
    return _queue

def get_runner() -> TaskRunner:
    return _runner
