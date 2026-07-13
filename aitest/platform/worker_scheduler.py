"""Deterministic Worker selection for remote task dispatch."""

from __future__ import annotations

from dataclasses import dataclass

from aitest.platform.worker_lease import WorkerLease


@dataclass(frozen=True)
class WorkerSelection:
    worker_id: str
    org_id: str
    load: int


class WorkerScheduler:
    """Select the least-loaded healthy Worker within an organization."""

    def __init__(self, lease_store, task_queue=None):
        self.lease_store = lease_store
        self.task_queue = task_queue

    def select(self, org_id: str, capability: str | None = None) -> WorkerSelection | None:
        workers = [w for w in self.lease_store.list_alive(org_id=org_id) if w.status == "running"]
        if capability:
            workers = [w for w in workers if capability in (w.metadata.get("capabilities") or [])]
        if not workers:
            return None
        selected = min(workers, key=lambda worker: (self._load(worker), worker.worker_id))
        return WorkerSelection(selected.worker_id, selected.org_id, self._load(selected))

    def dispatch_once(self, org_id: str, capability: str | None = None) -> dict | None:
        """Central scheduler path: select a healthy Worker and claim one task."""
        queue = self.task_queue
        if queue is None:
            from aitest.infra.task_queue import get_queue
            queue = get_queue()
        selection = self.select(org_id, capability)
        if selection is None:
            return None
        task = queue.claim_for_worker(selection.worker_id, org_id=org_id)
        if task is None:
            return None
        return {"worker_id": selection.worker_id, "org_id": org_id, "task": task}

    def recover_dead_workers(self, *, timeout_seconds: int = 90, requeue: bool = True) -> list[str]:
        """Mark dead leases and release every task held by them."""
        dead_ids = self.lease_store.mark_dead_workers(timeout_seconds=timeout_seconds)
        queue = self.task_queue
        if queue is None:
            # Lease cleanup must remain available when the optional task DB is
            # not mounted (for example in an in-memory control-plane test).
            try:
                from aitest.infra.task_queue import get_queue
                queue = get_queue()
            except Exception:
                queue = None
        for worker_id in dead_ids:
            if queue is None:
                break
            try:
                queue.recover_worker_tasks(worker_id, requeue=requeue)
            except Exception:
                # Lease cleanup must remain available when the optional task DB
                # is not mounted in a standalone control-plane test/process.
                continue
        return dead_ids

    @staticmethod
    def _load(worker: WorkerLease) -> int:
        active = worker.stats.get("active", worker.stats.get("claimed", 0))
        return len(worker.claimed_requests) + int(active or 0)
