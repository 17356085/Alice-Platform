"""Tests for TaskQueue — SQLite async task queue with retry + stale recovery.

P2 (2026-06-27): Integration tests covering enqueue/dequeue/complete/fail/retry/recovery.
"""
from __future__ import annotations

import tempfile
import time
from pathlib import Path

import pytest

from aitest.infra.task_queue import TaskQueue, DEFAULT_MAX_RETRIES, STALE_TASK_TIMEOUT_S


@pytest.fixture
def queue():
    """Create a TaskQueue with a temporary database."""
    tmp = tempfile.mktemp(suffix=".db")
    q = TaskQueue(db_path=tmp)
    yield q
    # Cleanup
    Path(tmp).unlink(missing_ok=True)


# ══════════════════════════════════════════════════════════════════════════
#  Basic enqueue / dequeue / complete
# ══════════════════════════════════════════════════════════════════════════


def test_enqueue_returns_task_id(queue):
    tid = queue.enqueue("automation-agent", "equipment", page="alarm-config")
    assert tid.startswith("task-")
    assert len(tid) > 5


def test_enqueue_then_dequeue(queue):
    tid = queue.enqueue("automation-agent", "equipment")
    task = queue.dequeue()
    assert task is not None
    assert task["id"] == tid
    assert task["agent"] == "automation-agent"
    assert task["module"] == "equipment"
    # dequeue returns pre-update row; verify status change via get()
    assert queue.get(tid)["status"] == "running"


def test_dequeue_empty_returns_none(queue):
    assert queue.dequeue() is None


def test_dequeue_fifo_order(queue):
    tid1 = queue.enqueue("agent-a", "m1")
    time.sleep(0.01)  # ensure different created_at
    tid2 = queue.enqueue("agent-b", "m2")

    t1 = queue.dequeue()
    t2 = queue.dequeue()
    assert t1["id"] == tid1  # first in, first out
    assert t2["id"] == tid2


def test_mark_completed(queue):
    tid = queue.enqueue("agent-x", "m1")
    queue.dequeue()
    queue.mark_completed(tid, {"status": "ok", "artifacts": 3})

    task = queue.get(tid)
    assert task["status"] == "completed"
    assert '"status": "ok"' in task["result_json"]


# ══════════════════════════════════════════════════════════════════════════
#  P4: Retry logic
# ══════════════════════════════════════════════════════════════════════════


def test_mark_failed_auto_requeues_within_retry_limit(queue):
    """First failure should requeue (retry 1/3)."""
    tid = queue.enqueue("agent-x", "m1", max_retries=3)
    queue.dequeue()
    queue.mark_failed(tid, "Connection timeout")

    task = queue.get(tid)
    assert task["status"] == "queued"
    assert "retry 1/3" in task["error_msg"]


def test_mark_failed_tracks_retry_count(queue):
    tid = queue.enqueue("agent-x", "m1", max_retries=3)
    queue.dequeue()
    queue.mark_failed(tid, "err1")
    assert queue.get(tid)["retry_count"] == 1

    time.sleep(1.5)  # Wait for backoff (1s + 30% jitter)
    queue.dequeue()  # re-dequeue
    queue.mark_failed(tid, "err2")
    assert queue.get(tid)["retry_count"] == 2


def test_mark_failed_exhausts_retries(queue):
    """After max_retries failures, task should be permanently failed.

    v2.6 backoff note: mark_failed sets retry_at in the future.
    We bypass backoff via direct DB reset so the test stays fast.
    """
    def _clear_retry_at(tid):
        conn = queue._get_conn()
        conn.execute("UPDATE tasks SET retry_at=0 WHERE id=?", (tid,))
        conn.commit()
        conn.close()

    tid = queue.enqueue("agent-x", "m1", max_retries=2)

    queue.dequeue()
    queue.mark_failed(tid, "err1")  # retry 1/2 → queued
    _clear_retry_at(tid)

    task = queue.dequeue()  # re-dequeue
    assert task is not None
    queue.mark_failed(tid, "err2")  # retry 2/2 → queued
    _clear_retry_at(tid)

    task = queue.dequeue()  # 3rd attempt
    assert task is not None
    queue.mark_failed(tid, "err3")  # exhausted → failed

    task = queue.get(tid)
    assert task["status"] == "failed"
    assert "exhausted" in task["error_msg"]


def test_mark_failed_no_retry_immediate_failure(queue):
    """Unrecoverable errors skip retry entirely."""
    tid = queue.enqueue("agent-x", "m1", max_retries=3)
    queue.dequeue()
    queue.mark_failed_no_retry(tid, "Fatal: disk full")

    task = queue.get(tid)
    assert task["status"] == "failed"
    assert "Fatal" in task["error_msg"]
    assert task["retry_count"] == 0  # never retried


def test_default_max_retries(queue):
    tid = queue.enqueue("agent-x", "m1")
    task = queue.get(tid)
    assert task["max_retries"] == DEFAULT_MAX_RETRIES


# ══════════════════════════════════════════════════════════════════════════
#  P4: Stale recovery + manual retry
# ══════════════════════════════════════════════════════════════════════════


def test_recover_stale_tasks(queue):
    """Tasks stuck in 'running' for > STALE_TASK_TIMEOUT_S should be failed."""
    tid = queue.enqueue("agent-x", "m1")
    queue.dequeue()

    # Manually backdate started_at to simulate stale task
    conn = queue._get_conn()
    stale_time = time.time() - STALE_TASK_TIMEOUT_S - 60
    conn.execute("UPDATE tasks SET started_at=? WHERE id=?", (stale_time, tid))
    conn.commit()
    conn.close()

    recovered = queue.recover_stale_tasks()
    assert recovered >= 1

    task = queue.get(tid)
    assert task["status"] == "failed"
    assert "timed out" in task["error_msg"]


def test_recover_stale_tasks_ignores_recent_tasks(queue):
    """Recently started tasks should NOT be recovered."""
    tid = queue.enqueue("agent-x", "m1")
    queue.dequeue()  # just started → started_at is now

    recovered = queue.recover_stale_tasks()
    assert recovered == 0

    task = queue.get(tid)
    assert task["status"] == "running"


def test_retry_failed_manually_requeues(queue):
    """Manual retry of a failed task should put it back in queue."""
    tid = queue.enqueue("agent-x", "m1")
    queue.dequeue()
    queue.mark_failed_no_retry(tid, "some error")

    assert queue.get(tid)["status"] == "failed"

    ok = queue.retry_failed(tid)
    assert ok is True

    task = queue.get(tid)
    assert task["status"] == "queued"
    assert task["error_msg"] == ""


def test_retry_failed_returns_false_for_nonexistent(queue):
    assert queue.retry_failed("nonexistent-id") is False


def test_retry_failed_returns_false_for_non_failed(queue):
    """Can only retry tasks in 'failed' status."""
    tid = queue.enqueue("agent-x", "m1")
    assert queue.retry_failed(tid) is False  # status is 'queued', not 'failed'


# ══════════════════════════════════════════════════════════════════════════
#  Query helpers
# ══════════════════════════════════════════════════════════════════════════


def test_get_returns_none_for_missing(queue):
    assert queue.get("no-such-task") is None


def test_list_tasks_by_status(queue):
    queue.enqueue("a1", "m1")
    queue.enqueue("a2", "m2")
    tid3 = queue.enqueue("a3", "m3")
    queue.dequeue()  # a1 → running
    queue.mark_completed(tid3, {})  # a3 → completed... wait, need to dequeue first

    queued = queue.list_tasks(status="queued")
    assert len(queued) == 1  # only a2 left in queued


def test_count_by_status(queue):
    queue.enqueue("a1", "m1")
    queue.enqueue("a2", "m2")
    queue.dequeue()  # a1 → running

    counts = queue.count_by_status()
    assert counts.get("queued", 0) == 1
    assert counts.get("running", 0) == 1
    assert counts.get("completed", 0) == 0
    assert counts.get("failed", 0) == 0


def test_full_lifecycle(queue):
    """End-to-end: enqueue → dequeue → complete."""
    tid = queue.enqueue("test-agent", "test-module", page="test-page")
    task = queue.dequeue()
    assert task["page"] == "test-page"
    assert task["provider"] == "claude"

    queue.mark_completed(tid, {"passed": True})
    final = queue.get(tid)
    assert final["status"] == "completed"
    assert final["completed_at"] is not None


# ══════════════════════════════════════════════════════════════════════════
#  Concurrent access safety
# ══════════════════════════════════════════════════════════════════════════


def test_concurrent_enqueue_unique_ids(queue):
    """Multiple enqueues should produce unique IDs."""
    ids = set()
    for i in range(100):
        tid = queue.enqueue(f"agent-{i % 5}", f"module-{i % 10}")
        ids.add(tid)
    assert len(ids) == 100


def test_dequeue_atomic(queue):
    """Dequeue should atomically claim a task."""
    tids = [queue.enqueue("a", "m") for _ in range(5)]
    dequeued = []
    for _ in range(5):
        t = queue.dequeue()
        if t:
            dequeued.append(t["id"])
    assert len(dequeued) == 5
    # All unique
    assert len(set(dequeued)) == 5
    # All were enqueued
    assert set(dequeued).issubset(set(tids))
