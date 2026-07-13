"""Worker selection and organization isolation tests."""

from types import SimpleNamespace

from aitest.platform.worker_scheduler import WorkerScheduler


def test_scheduler_selects_least_loaded_worker_with_capability():
    workers = [
        SimpleNamespace(worker_id="worker-b", org_id="org-a", status="running", claimed_requests=["x"], stats={}, metadata={"capabilities": ["browser"]}),
        SimpleNamespace(worker_id="worker-a", org_id="org-a", status="running", claimed_requests=[], stats={}, metadata={"capabilities": ["browser"]}),
        SimpleNamespace(worker_id="worker-c", org_id="org-b", status="running", claimed_requests=[], stats={}, metadata={"capabilities": ["browser"]}),
    ]
    store = SimpleNamespace(list_alive=lambda **kwargs: [w for w in workers if w.org_id == kwargs["org_id"]])
    selected = WorkerScheduler(store).select("org-a", capability="browser")
    assert selected.worker_id == "worker-a"
    assert selected.org_id == "org-a"


def test_scheduler_returns_none_when_capability_is_missing():
    worker = SimpleNamespace(worker_id="worker-a", org_id="org-a", status="running", claimed_requests=[], stats={}, metadata={"capabilities": ["api"]})
    store = SimpleNamespace(list_alive=lambda **_: [worker])
    assert WorkerScheduler(store).select("org-a", capability="browser") is None


def test_scheduler_dispatches_through_selected_worker():
    worker = SimpleNamespace(worker_id="worker-a", org_id="org-a", status="running", claimed_requests=[], stats={}, metadata={})
    store = SimpleNamespace(list_alive=lambda **_: [worker])
    queue = SimpleNamespace(claim_for_worker=lambda worker_id, org_id: {"id": "task-1", "claimed_by": worker_id, "org_id": org_id})
    result = WorkerScheduler(store, queue).dispatch_once("org-a")
    assert result["worker_id"] == "worker-a"
    assert result["task"]["claimed_by"] == "worker-a"


def test_recover_dead_workers_survives_missing_task_queue(monkeypatch):
    class Store:
        def mark_dead_workers(self, timeout_seconds):
            return ["dead-1"]

    import builtins
    real_import = builtins.__import__

    def blocked_import(name, *args, **kwargs):
        if name == "aitest.infra.task_queue":
            raise OSError("task db unavailable")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", blocked_import)

    assert WorkerScheduler(Store()).recover_dead_workers(timeout_seconds=60) == ["dead-1"]
