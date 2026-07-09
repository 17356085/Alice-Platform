"""ExecutionWorker — consumes queued ExecutionRequest records.

This is the execution plane for async platform jobs. The control plane only
creates and persists requests; the worker claims queued requests and runs the
execution flow independently.
"""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass
from typing import Optional

from alice_engine.contracts import ExecutionContext

from aitest.infra.metrics import (
    record_execution_retry,
    record_execution_worker_throttle,
)
from .execution_service import ExecutionService
from .tenant import get_tenant_manager
from .run_store import get_run_store


@dataclass
class ExecutionWorkerStats:
    worker_id: str
    running: bool = False
    claimed: int = 0
    completed: int = 0
    failed: int = 0
    retried: int = 0
    throttled: int = 0
    last_claimed_request_id: str = ""
    last_claimed_at: str = ""
    last_error: str = ""


class ExecutionWorker:
    """Polls execution_requests and processes queued jobs."""

    def __init__(
        self,
        service: ExecutionService | None = None,
        store=None,
        *,
        worker_id: str = "",
        poll_interval: float = 1.0,
        tenant_manager=None,
    ):
        self._service = service or ExecutionService()
        self._store = store or get_run_store()
        self._worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self._poll_interval = max(0.2, float(poll_interval))
        self._tenant_manager = tenant_manager or get_tenant_manager()
        self._running = False
        self._stop_event = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._stats = ExecutionWorkerStats(worker_id=self._worker_id)

    @property
    def worker_id(self) -> str:
        return self._worker_id

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._stats.running = True
        self._thread = threading.Thread(target=self._loop, name=self._worker_id, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._running = False
        self._stop_event.set()
        self._stats.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)

    def run_once(self) -> bool:
        request = self._store.claim_next_request()
        if request is None:
            return False
        self._handle_request(request)
        return True

    def stats(self) -> ExecutionWorkerStats:
        with self._lock:
            return ExecutionWorkerStats(
                worker_id=self._stats.worker_id,
                running=self._stats.running,
                claimed=self._stats.claimed,
                completed=self._stats.completed,
                failed=self._stats.failed,
                retried=self._stats.retried,
                throttled=self._stats.throttled,
                last_claimed_request_id=self._stats.last_claimed_request_id,
                last_claimed_at=self._stats.last_claimed_at,
                last_error=self._stats.last_error,
            )

    def _loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                ran = self.run_once()
                if not ran:
                    self._stop_event.wait(self._poll_interval)
            except Exception as exc:
                with self._lock:
                    self._stats.failed += 1
                    self._stats.last_error = str(exc)[:200]
                self._stop_event.wait(self._poll_interval)

    def _handle_request(self, request) -> None:
        agent = request.agent or "automation-agent"
        ctx = ExecutionContext(
            workspace_id=request.workspace_id,
            user_id=request.triggered_by,
            scopes=["read", "execute"],
            org_id=request.org_id,
            module=request.module,
            pages=list(request.pages),
            agent=agent,
            mode=request.mode,
            provider=request.provider or "",
            priority=request.priority,
            metadata={
                "entrypoint": "worker.execution",
                "trigger_type": request.trigger_type,
            },
        )

        tenant = None
        capacity_acquired = False
        with self._lock:
            self._stats.claimed += 1
            self._stats.last_claimed_request_id = request.request_id
            self._stats.last_claimed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

        try:
            if self._tenant_manager is not None:
                tenant = self._tenant_manager.get(request.workspace_id)
                tenant.check_capacity("agent_execution")
                capacity_acquired = True
            self._service._run_request_flow(
                ctx,
                request,
                agent=agent,
                t0=time.perf_counter(),
                verbose=False,
                checkpoint_thread_id=request.request_id,
                allow_retry=True,
            )
            loaded = self._store.load_request(request.request_id)
            with self._lock:
                if loaded is not None and loaded.status == "queued":
                    self._stats.retried += 1
                else:
                    self._stats.completed += 1
        except Exception as exc:
            is_capacity_issue = "capacity" in str(exc).lower() or exc.__class__.__name__.endswith("CapacityError")
            if is_capacity_issue:
                with self._lock:
                    self._stats.throttled += 1
                record_execution_worker_throttle(self._worker_id)
            if self._service._can_retry_request(request, exc):
                try:
                    delay_s = self._service._retry_delay_for_request(request)
                    request.schedule_retry(delay_s)
                    self._store.save_request(request)
                    record_execution_retry(request.agent or agent, request.module)
                    with self._lock:
                        self._stats.retried += 1
                    return
                except Exception:
                    pass
            try:
                request.fail()
                self._store.save_request(request)
            except Exception:
                pass
            with self._lock:
                self._stats.failed += 0 if is_capacity_issue else 1
                self._stats.last_error = str(exc)[:200]
        finally:
            if tenant is not None and capacity_acquired:
                try:
                    tenant.release("agent_execution")
                except Exception:
                    pass


_worker: ExecutionWorker | None = None
_worker_lock = threading.Lock()


def get_execution_worker(
    *,
    service: ExecutionService | None = None,
    worker_id: str = "",
    poll_interval: float = 1.0,
) -> ExecutionWorker:
    global _worker
    with _worker_lock:
        if _worker is None:
            _worker = ExecutionWorker(
                service=service,
                worker_id=worker_id,
                poll_interval=poll_interval,
            )
        elif service is not None:
            _worker._service = service
        return _worker
