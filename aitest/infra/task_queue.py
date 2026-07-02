"""Task Queue — PostgreSQL persistent task queue with retry + stale recovery. v3.0
Uses docker exec psql as transport (Windows workaround).
"""

import json
import time
import uuid
import random
import threading
from typing import Optional
from aitest.infra.database import pg_exec, pg_query
from aitest.infra.logging import get_logger

logger = get_logger("task_queue")
DEFAULT_MAX_RETRIES = 3
STALE_TASK_TIMEOUT_S = 1800

def _escape(val):
    if val is None: return "NULL"
    return "'" + str(val).replace("'", "''") + "'"

class TaskQueue:
    def enqueue(self, agent: str, module: str, page: str = "", provider: str = "claude", max_retries: int = DEFAULT_MAX_RETRIES) -> str:
        task_id = f"task-{uuid.uuid4().hex[:12]}"
        now = time.time()
        pg_exec(f"INSERT INTO tasks (id, agent, module, page, provider, status, max_retries, created_at) VALUES ({_escape(task_id)}, {_escape(agent)}, {_escape(module)}, {_escape(page)}, {_escape(provider)}, 'queued', {max_retries}, {now})")
        return task_id

    def dequeue(self) -> Optional[dict]:
        now = time.time()
        rows = pg_query(f"SELECT * FROM tasks WHERE status='queued' AND (retry_at IS NULL OR retry_at <= {now}) ORDER BY created_at LIMIT 1")
        if not rows: return None
        task = rows[0]
        pg_exec(f"UPDATE tasks SET status='running', started_at={now} WHERE id={_escape(task['id'])}")
        return task

    def mark_completed(self, task_id: str, result: dict):
        now = time.time()
        result_json = json.dumps(result, ensure_ascii=False).replace("'", "''")
        pg_exec(f"UPDATE tasks SET status='completed', result_json='{result_json}', completed_at={now} WHERE id={_escape(task_id)}")

    def mark_failed(self, task_id: str, error: str):
        now = time.time()
        rows = pg_query(f"SELECT * FROM tasks WHERE id={_escape(task_id)}")
        if not rows: return
        task = rows[0]
        retry_count = task.get("retry_count") or 0
        max_retries = task.get("max_retries") or DEFAULT_MAX_RETRIES
        if retry_count < max_retries:
            delay = min(1.0 * (2 ** retry_count), 60.0)
            delay += random.uniform(0, delay * 0.3)
            retry_at = now + delay
            error_msg = f"[retry {retry_count + 1}/{max_retries}] {error}".replace("'", "''")
            pg_exec(f"UPDATE tasks SET status='queued', error_msg='{error_msg}', retry_count={retry_count + 1}, retry_at={retry_at}, completed_at={now} WHERE id={_escape(task_id)}")
            logger.info("task_retry_queued", task_id=task_id, retry=f"{retry_count + 1}/{max_retries}", backoff_s=round(delay, 1))
            return
        error_msg = f"[exhausted after {retry_count} retries] {error}".replace("'", "''")
        pg_exec(f"UPDATE tasks SET status='failed', error_msg='{error_msg}', completed_at={now} WHERE id={_escape(task_id)}")
        logger.error("task_exhausted", task_id=task_id, retries=retry_count)

    def mark_failed_no_retry(self, task_id: str, error: str):
        now = time.time()
        error_msg = error.replace("'", "''")
        pg_exec(f"UPDATE tasks SET status='failed', error_msg='{error_msg}', completed_at={now} WHERE id={_escape(task_id)}")

    def recover_stale_tasks(self) -> int:
        cutoff = time.time() - STALE_TASK_TIMEOUT_S
        now = time.time()
        pg_exec(f"UPDATE tasks SET status='failed', error_msg='stale task — timed out after 30min', completed_at={now} WHERE status='running' AND started_at < {cutoff}")
        rows = pg_query("SELECT COUNT(*) as cnt FROM tasks WHERE status='failed' AND error_msg='stale task — timed out after 30min'")
        recovered = rows[0]["cnt"] if rows else 0
        if recovered: logger.warning("stale_tasks_recovered", count=recovered)
        return recovered

    def retry_failed(self, task_id: str) -> bool:
        rows = pg_query(f"SELECT * FROM tasks WHERE id={_escape(task_id)} AND status='failed'")
        if not rows: return False
        pg_exec(f"UPDATE tasks SET status='queued', error_msg='', started_at=NULL, completed_at=NULL WHERE id={_escape(task_id)}")
        return True

    def get(self, task_id: str) -> Optional[dict]:
        rows = pg_query(f"SELECT * FROM tasks WHERE id={_escape(task_id)}")
        if not rows: return None
        task = rows[0]
        if task.get("result_json"):
            try: task["result"] = json.loads(task["result_json"])
            except json.JSONDecodeError: task["result"] = {}
        return task

    def list_tasks(self, status: str = None, limit: int = 20) -> list[dict]:
        where = f"WHERE status={_escape(status)}" if status else ""
        return pg_query(f"SELECT * FROM tasks {where} ORDER BY created_at DESC LIMIT {limit}")

    def count_by_status(self) -> dict:
        rows = pg_query("SELECT status, COUNT(*) as cnt FROM tasks GROUP BY status")
        counts = {r["status"]: r["cnt"] for r in rows}
        counts["pending"] = counts.get("queued", 0) + counts.get("running", 0)
        return counts

    def cleanup(self, older_than_hours: int = 24):
        cutoff = time.time() - (older_than_hours * 3600)
        pg_exec(f"DELETE FROM tasks WHERE completed_at < {cutoff} AND status IN ('completed', 'failed')")
        return 0

class TaskRunner:
    def __init__(self, queue: TaskQueue = None, poll_interval: float = 2.0):
        self.queue = queue or TaskQueue()
        self.poll_interval = poll_interval
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._stale_check_count = 0

    def start(self):
        if self._running: return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread: self._thread.join(timeout=5)

    def _loop(self):
        while self._running:
            self._stale_check_count += 1
            if self._stale_check_count % 30 == 0:
                try: self.queue.recover_stale_tasks()
                except Exception: pass
            task = self.queue.dequeue()
            if task:
                try: self._execute(task)
                except Exception as e:
                    error_str = str(e)
                    if any(kw in error_str.lower() for kw in ("fatal", "context_length", "permission", "denied", "auth")):
                        self.queue.mark_failed_no_retry(task["id"], error_str)
                    else:
                        self.queue.mark_failed(task["id"], error_str)
            else:
                time.sleep(self.poll_interval)

    def _execute(self, task: dict):
        from aitest.agents.agent_runner import run_agent
        result = run_agent(agent_name=task["agent"], provider=task.get("provider", "claude"), module=task["module"], page=task.get("page", ""), verbose=False)
        self.queue.mark_completed(task["id"], result)

_queue = TaskQueue()
_runner = TaskRunner(_queue)
def get_queue() -> TaskQueue: return _queue
def get_runner() -> TaskRunner: return _runner
