"""Remote Worker task claim ownership tests."""

from aitest.infra.task_queue import TaskQueue


def test_task_claim_and_completion_are_worker_owned(tmp_path):
    queue = TaskQueue(tmp_path / "tasks.db")
    task_id = queue.enqueue("agent", "module")

    task = queue.claim_for_worker("worker-1")
    assert task["id"] == task_id
    assert task["claimed_by"] == "worker-1"
    assert queue.complete_for_worker(task_id, "worker-2", {"ok": False}) is False
    assert queue.complete_for_worker(task_id, "worker-1", {"ok": True}) is True
    assert queue.get(task_id)["status"] == "completed"
