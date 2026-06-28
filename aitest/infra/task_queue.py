"""Task Queue — SQLite persistent async task queue with retry + stale recovery.

Design:
  1. Zero external deps — pure Python + SQLite
  2. Single-machine / low-frequency scenarios
  3. P4 (2026-06-25): retry_count + max_retries + auto-requeue + stale recovery

Schema:
  tasks:
    - id: TEXT PRIMARY KEY
    - agent, module, page, provider
    - status: queued | running | completed | failed | retrying
    - result_json, error_msg
    - retry_count INTEGER DEFAULT 0
    - max_retries INTEGER DEFAULT 3
    - created_at, started_at, completed_at
"""
import json
import time
import uuid
import sqlite3
import threading
from typing import Optional

from aitest.platform.paths import get_workstudy
from aitest.infra.logging import get_logger

logger = get_logger("task_queue")

WORKSTUDY = get_workstudy()
DB_PATH = WORKSTUDY / "aitest" / "tasks.db"

DEFAULT_MAX_RETRIES = 3
STALE_TASK_TIMEOUT_S = 1800  # 30 min


class TaskQueue:
    """SQLite persistent async task queue. P4: retry + stale recovery."""

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
                    retry_count INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    retry_at REAL DEFAULT 0,
                    created_at REAL,
                    started_at REAL,
                    completed_at REAL
                )
            """)
            # P4: migrate old tables missing columns
            for col, col_type in [("retry_count", "INTEGER DEFAULT 0"),
                                   ("max_retries", "INTEGER DEFAULT 3"),
                                   ("retry_at", "REAL DEFAULT 0")]:
                try:
                    conn.execute(f"ALTER TABLE tasks ADD COLUMN {col} {col_type}")
                except sqlite3.OperationalError:
                    pass
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created ON tasks(created_at)")
            conn.commit()
            conn.close()

    # ── Enqueue / Dequeue ──────────────────────────────────────────────

    def enqueue(self, agent: str, module: str, page: str = "",
                provider: str = "claude", max_retries: int = DEFAULT_MAX_RETRIES) -> str:
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        now = time.time()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                """INSERT INTO tasks (id, agent, module, page, provider, status, max_retries, created_at)
                   VALUES (?, ?, ?, ?, ?, 'queued', ?, ?)""",
                (task_id, agent, module, page, provider, max_retries, now))
            conn.commit()
            conn.close()
        return task_id

    def dequeue(self) -> Optional[dict]:
        with self._lock:
            conn = self._get_conn()
            now = time.time()
            # v2.6: skip tasks whose retry backoff hasn't elapsed
            row = conn.execute(
                "SELECT * FROM tasks WHERE status='queued' AND (retry_at IS NULL OR retry_at <= ?) "
                "ORDER BY created_at LIMIT 1",
                (now,)
            ).fetchone()
            if not row:
                conn.close()
                return None
            conn.execute("UPDATE tasks SET status='running', started_at=? WHERE id=?",
                         (now, row["id"]))
            conn.commit()
            conn.close()
            return dict(row)

    # ── Complete / Fail ────────────────────────────────────────────────

    def mark_completed(self, task_id: str, result: dict):
        now = time.time()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "UPDATE tasks SET status='completed', result_json=?, completed_at=? WHERE id=?",
                (json.dumps(result, ensure_ascii=False), now, task_id))
            conn.commit()
            conn.close()

    def mark_failed(self, task_id: str, error: str):
        """P4: auto-requeue if retry_count < max_retries. Else final fail.

        v2.6: Exponential backoff with jitter between retries (1s-60s).
        """
        import random
        now = time.time()
        with self._lock:
            conn = self._get_conn()
            task = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
            if not task:
                conn.close()
                return
            retry_count = task["retry_count"] or 0
            max_retries = task["max_retries"] or DEFAULT_MAX_RETRIES

            if retry_count < max_retries:
                # Exponential backoff: 1s * 2^retry + jitter, capped at 60s
                delay = min(1.0 * (2 ** retry_count), 60.0)
                delay += random.uniform(0, delay * 0.3)  # 30% jitter
                retry_at = now + delay
                conn.execute(
                    "UPDATE tasks SET status='queued', error_msg=?, retry_count=?, retry_at=?, completed_at=? WHERE id=?",
                    (f"[retry {retry_count + 1}/{max_retries}] {error}",
                     retry_count + 1, retry_at, now, task_id))
                conn.commit()
                conn.close()
                logger.info("task_retry_queued", task_id=task_id,
                            retry=f"{retry_count + 1}/{max_retries}",
                            backoff_s=round(delay, 1))
                return

            conn.execute(
                "UPDATE tasks SET status='failed', error_msg=?, completed_at=? WHERE id=?",
                (f"[exhausted after {retry_count} retries] {error}", now, task_id))
            conn.commit()
            conn.close()
            logger.error("task_exhausted", task_id=task_id, retries=retry_count)

    def mark_failed_no_retry(self, task_id: str, error: str):
        """P4: fail immediately without retry (unrecoverable errors)."""
        now = time.time()
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "UPDATE tasks SET status='failed', error_msg=?, completed_at=? WHERE id=?",
                (error, now, task_id))
            conn.commit()
            conn.close()

    # ── P4: Recovery ───────────────────────────────────────────────────

    def recover_stale_tasks(self) -> int:
        """P4: mark running tasks stalled > STALE_TASK_TIMEOUT_S as failed."""
        cutoff = time.time() - STALE_TASK_TIMEOUT_S
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "UPDATE tasks SET status='failed', error_msg=?, completed_at=?"
                " WHERE status='running' AND started_at < ?",
                ("stale task — timed out after 30min", time.time(), cutoff))
            recovered = conn.total_changes
            conn.commit()
            conn.close()
        if recovered:
            logger.warning("stale_tasks_recovered", count=recovered)
        return recovered

    def retry_failed(self, task_id: str) -> bool:
        """P4: manually requeue a failed task."""
        with self._lock:
            conn = self._get_conn()
            task = conn.execute(
                "SELECT * FROM tasks WHERE id=? AND status='failed'", (task_id,)
            ).fetchone()
            if not task:
                conn.close()
                return False
            conn.execute(
                "UPDATE tasks SET status='queued', error_msg='', started_at=NULL, completed_at=NULL WHERE id=?",
                (task_id,))
            conn.commit()
            conn.close()
            return True

    # ── Query ──────────────────────────────────────────────────────────

    def get(self, task_id: str) -> Optional[dict]:
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
        conn = self._get_conn()
        if status:
            rows = conn.execute(
                "SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC LIMIT ?",
                (status, limit)).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?",
                (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def count_by_status(self) -> dict:
        """P4: includes 'pending' = queued + running."""
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status").fetchall()
        conn.close()
        result = {r["status"]: r["cnt"] for r in rows}
        result["pending"] = result.get("queued", 0) + result.get("running", 0)
        return result

    def cleanup(self, older_than_hours: int = 24):
        cutoff = time.time() - (older_than_hours * 3600)
        with self._lock:
            conn = self._get_conn()
            conn.execute(
                "DELETE FROM tasks WHERE completed_at < ? AND status IN ('completed', 'failed')",
                (cutoff,))
            deleted = conn.total_changes
            conn.commit()
            conn.close()
        return deleted


# ══════════════════════════════════════════════════════════════════════════
#  Task Runner — background consumer thread
# ══════════════════════════════════════════════════════════════════════════

class TaskRunner:
    """Background task consumer. P4: stale recovery + retry-aware error handling."""

    def __init__(self, queue: TaskQueue = None, poll_interval: float = 2.0):
        self.queue = queue or TaskQueue()
        self.poll_interval = poll_interval
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
            # P4: every 30 polls (~60s), recover stale tasks
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
                    if any(kw in error_str.lower() for kw in
                           ("fatal", "context_length", "permission", "denied", "auth")):
                        self.queue.mark_failed_no_retry(task["id"], error_str)
                    else:
                        self.queue.mark_failed(task["id"], error_str)
            else:
                time.sleep(self.poll_interval)

    def _execute(self, task: dict):
        from aitest.agents.agent_runner import run_agent
        result = run_agent(
            agent_name=task["agent"],
            provider=task.get("provider", "claude"),
            module=task["module"],
            page=task.get("page", ""),
            verbose=False,
        )
        self.queue.mark_completed(task["id"], result)


# ── Global singletons ───────────────────────────────────────────────────

_queue = TaskQueue()
_runner = TaskRunner(_queue)


def get_queue() -> TaskQueue:
    return _queue


def get_runner() -> TaskRunner:
    return _runner
