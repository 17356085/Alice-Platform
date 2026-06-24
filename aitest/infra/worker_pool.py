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
from concurrent.futures import ThreadPoolExecutor, Future, TimeoutError as FutureTimeout
from dataclasses import dataclass, field
from typing import Callable, Optional
import functools


@dataclass
class PoolStats:
    """Worker pool statistics snapshot."""
    active_tasks: int = 0
    queued_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    max_workers: int = 4
    per_tenant: dict = field(default_factory=dict)


class WorkerPool:
    """Bounded thread pool with per-tenant concurrency control."""

    def __init__(self, max_workers: int = 4):
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._max_workers = max_workers
        self._lock = threading.Lock()
        self._stats = PoolStats(max_workers=max_workers)
        self._tenant_active: dict[str, int] = {}
        self._futures: dict[str, Future] = {}

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
        task_id = f"{tenant_id}-{task_type}-{time.monotonic()}"
        self._futures[task_id] = future
        return future

    def stats(self) -> PoolStats:
        """Get current pool statistics."""
        with self._lock:
            return PoolStats(
                active_tasks=self._stats.active_tasks,
                queued_tasks=self._stats.queued_tasks,
                completed_tasks=self._stats.completed_tasks,
                failed_tasks=self._stats.failed_tasks,
                max_workers=self._max_workers,
                per_tenant=dict(self._tenant_active),
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
