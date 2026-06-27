"""
Worker Pool — concurrent agent execution with per-tenant limits.

Replaces single-threaded sequential execution with a bounded thread pool.
Integrates with tenant.py for per-project concurrency limits and metrics.py
for observability.

Usage:
    from aitest.infra.worker_pool import WorkerPool, get_worker_pool

    pool = get_worker_pool(max_workers=4)
    future = pool.submit(
        tenant_id="web-automation",
        task_type="agent_execution",
        fn=run_agent,
        agent_name="automation-agent",
        module="equipment",
    )
    result = future.result(timeout=600)

Design:
  - ThreadPoolExecutor for IO-bound agent tasks (LLM calls are IO)
  - Per-tenant semaphore limits via TenantManager.check_capacity()
  - Metrics: active_workers gauge, task_duration histogram
  - Graceful shutdown on SIGTERM
"""

import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from typing import Callable, Optional
import functools


@dataclass
class PoolStats:
    """Worker pool statistics snapshot. P4: + oldest_active_s, timed_out_tasks."""
    active_tasks: int = 0
    queued_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    timed_out_tasks: int = 0
    max_workers: int = 4
    per_tenant: dict = field(default_factory=dict)
    oldest_active_s: float = 0.0
    total_submitted: int = 0


class WorkerPool:
    """Bounded thread pool with per-tenant concurrency control."""

    _MAX_FUTURES = 10_000  # Safety cap: evict oldest if exceeded

    def __init__(self, max_workers: int = 4, default_timeout: float = 1800):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._max_workers = max_workers
        self._default_timeout = default_timeout  # P4: 30min default
        self._lock = threading.Lock()
        self._stats = PoolStats(max_workers=max_workers)
        self._tenant_active: dict[str, int] = {}
        self._futures: dict[str, Future] = {}
        self._task_started: dict[str, float] = {}  # P4: task_id → start_time
        self._task_timeouts: dict[str, float] = {}  # P4: task_id → timeout_s
        self._submit_counter: int = 0  # monotonic, for unique task IDs

    def submit(
        self,
        tenant_id: str,
        task_type: str,
        fn: Callable,
        *args,
        timeout: float = None,
        **kwargs,
    ) -> Future:
        """Submit a task for execution.

        Args:
            tenant_id: Project ID for per-tenant limiting
            task_type: "agent_execution" | "sop_run" | "skill_execution"
            fn: Callable to execute
            timeout: Max execution time in seconds (None = no limit)
            *args, **kwargs: Passed to fn

        Returns:
            Future representing the task result

        Raises:
            TenantCapacityError: If tenant exceeds concurrent limit
        """
        # Check tenant capacity
        try:
            from aitest.platform.tenant import get_tenant
            tenant = get_tenant(tenant_id)
            tenant.check_capacity("agent_execution")
        except ImportError:
            pass  # tenant module not available

        with self._lock:
            self._tenant_active[tenant_id] = self._tenant_active.get(tenant_id, 0) + 1
            self._stats.queued_tasks += 1

        # Wrap fn with metrics + cleanup
        @functools.wraps(fn)
        def _wrapped():
            start = time.monotonic()
            try:
                with self._lock:
                    self._stats.active_tasks += 1
                    self._stats.queued_tasks -= 1

                # Record metrics
                try:
                    from aitest.infra.metrics import agent_active
                    agent_active.labels(agent_name=kwargs.get("agent_name", task_type)).inc()
                except Exception:
                    pass

                result = fn(*args, **kwargs)

                with self._lock:
                    self._stats.completed_tasks += 1
                return result

            except Exception:
                with self._lock:
                    self._stats.failed_tasks += 1
                raise

            finally:
                with self._lock:
                    self._stats.active_tasks -= 1
                    self._tenant_active[tenant_id] = max(0, self._tenant_active.get(tenant_id, 1) - 1)

                # Release tenant capacity
                try:
                    from aitest.platform.tenant import get_tenant
                    tenant = get_tenant(tenant_id)
                    tenant.release("agent_execution")
                except ImportError:
                    pass

                # Record metrics
                try:
                    from aitest.infra.metrics import agent_active, agent_execution_duration
                    agent_active.labels(agent_name=kwargs.get("agent_name", task_type)).dec()
                    agent_execution_duration.labels(
                        agent_name=kwargs.get("agent_name", task_type)
                    ).observe(time.monotonic() - start)
                except Exception:
                    pass

        future = self._executor.submit(_wrapped)
        with self._lock:
            self._submit_counter += 1
        task_id = f"{tenant_id}-{task_type}-{self._submit_counter}"
        actual_timeout = timeout or self._default_timeout
        with self._lock:
            self._task_started[task_id] = time.monotonic()
            self._task_timeouts[task_id] = actual_timeout
            self._stats.total_submitted += 1
            # Safety cap: if futures dict grows past limit, evict oldest entries
            # (done callbacks normally prevent this — this is defense-in-depth)
            while len(self._futures) >= self._MAX_FUTURES:
                oldest = next(iter(self._futures))
                old_future = self._futures.pop(oldest)
                if not old_future.done():
                    old_future.cancel()
            self._futures[task_id] = future

        # Auto-cleanup on completion: remove Future reference to prevent
        # unbounded growth of result/exception/traceback references.
        def _cleanup(_f: Future):
            with self._lock:
                self._futures.pop(task_id, None)
                self._task_started.pop(task_id, None)
                self._task_timeouts.pop(task_id, None)

        future.add_done_callback(_cleanup)
        return future

    # ── P4: Timeout enforcement ───────────────────────────────────────

    def cleanup_stale(self) -> int:
        """P4: Cancel tasks that have exceeded their timeout. Returns count cancelled."""
        now = time.monotonic()
        cancelled = 0
        with self._lock:
            stale_ids = []
            for task_id, started in list(self._task_started.items()):
                timeout = self._task_timeouts.get(task_id, self._default_timeout)
                if now - started > timeout:
                    stale_ids.append(task_id)
            for task_id in stale_ids:
                future = self._futures.pop(task_id, None)
                self._task_started.pop(task_id, None)
                self._task_timeouts.pop(task_id, None)
                if future and not future.done():
                    future.cancel()
                    self._stats.timed_out_tasks += 1
                    self._stats.active_tasks = max(0, self._stats.active_tasks - 1)
                    cancelled += 1
        if cancelled:
            import logging
            logging.getLogger("worker_pool").warning(
                "stale_tasks_cancelled", count=cancelled)
        return cancelled

    def stats(self) -> PoolStats:
        """P4: includes oldest_active_s and timed_out_tasks."""
        with self._lock:
            oldest = 0.0
            if self._task_started:
                now = time.monotonic()
                oldest = max(0.0, now - min(self._task_started.values()))
            return PoolStats(
                active_tasks=self._stats.active_tasks,
                queued_tasks=self._stats.queued_tasks,
                completed_tasks=self._stats.completed_tasks,
                failed_tasks=self._stats.failed_tasks,
                timed_out_tasks=self._stats.timed_out_tasks,
                max_workers=self._max_workers,
                per_tenant=dict(self._tenant_active),
                oldest_active_s=round(oldest, 1),
                total_submitted=self._stats.total_submitted,
            )

    def shutdown(self, wait: bool = True):
        """Graceful shutdown. Cancels pending tasks if wait=False."""
        self._executor.shutdown(wait=wait, cancel_futures=not wait)


# ── Singleton ──────────────────────────────────────────────────────────

_worker_pool: Optional[WorkerPool] = None
_wp_lock = threading.Lock()


def get_worker_pool(max_workers: int = None) -> WorkerPool:
    """Get or create the global WorkerPool singleton."""
    global _worker_pool
    with _wp_lock:
        if _worker_pool is None:
            workers = max_workers or 4
            _worker_pool = WorkerPool(max_workers=workers)
        return _worker_pool
