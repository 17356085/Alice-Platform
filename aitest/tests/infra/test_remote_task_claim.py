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


def test_task_claim_is_organization_scoped(tmp_path):
    queue = TaskQueue(tmp_path / "tasks.db")
    queue.enqueue("agent-a", "module-a", org_id="org-a")
    assert queue.claim_for_worker("worker-b", org_id="org-b") is None
    task = queue.claim_for_worker("worker-a", org_id="org-a")
    assert task["org_id"] == "org-a"


def test_disconnected_worker_tasks_are_requeued(tmp_path):
    queue = TaskQueue(tmp_path / "tasks.db")
    task_id = queue.enqueue("agent", "module")
    queue.claim_for_worker("worker-lost")

    assert queue.recover_worker_tasks("worker-lost") == 1
    recovered = queue.get(task_id)
    assert recovered["status"] == "queued"
    assert recovered["claimed_by"] == ""


def test_disconnected_worker_exhausted_task_is_failed(tmp_path):
    queue = TaskQueue(tmp_path / "tasks.db")
    task_id = queue.enqueue("agent", "module", max_retries=0)
    queue.claim_for_worker("worker-lost")

    assert queue.recover_worker_tasks("worker-lost") == 1
    assert queue.get(task_id)["status"] == "failed"
