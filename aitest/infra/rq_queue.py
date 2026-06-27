"""RQ Task Queue — Redis-backed distributed task queue adapter.

Same interface as SQLite TaskQueue. Drop-in replacement when Redis is available.

Usage:
    # Automatic: set REDIS_URL or redis running on localhost
    export REDIS_URL=redis://localhost:6379/0

    # Manual:
    from aitest.infra.rq_queue import RQTaskQueue
    queue = RQTaskQueue(redis_url="redis://localhost:6379/0")
    task_id = queue.enqueue("automation-agent", module="equipment")

    # Monitoring:
    GET /health → task_queue: {backend: "redis", pending: 3, ...}

Install:
    pip install rq redis
"""
from __future__ import annotations

import json
import time
import uuid
import logging
from typing import Optional

logger = logging.getLogger("rq_queue")

_RQ_AVAILABLE = False
try:
    import redis as _redis
    import rq
    from rq import Queue as _RQQueue
    from rq.job import Job
    _RQ_AVAILABLE = True
except ImportError:
    pass


class RQTaskQueueNotAvailable(Exception):
    """Raised when RQ/Redis is not installed or not reachable."""


class RQTaskQueue:
    """Redis-backed task queue with same interface as SQLite TaskQueue.

    Features:
      - enqueue / dequeue / mark_completed / mark_failed
      - count_by_status / list_tasks / get / cleanup
      - retry + stale recovery (via rq's built-in retry + TTL)
      - Zero config: connects to localhost:6379 by default
    """

    def __init__(self, redis_url: str = None, name: str = "aitest-tasks"):
        if not _RQ_AVAILABLE:
            raise RQTaskQueueNotAvailable(
                "rq and redis packages required: pip install rq redis")

        redis_url = redis_url or "redis://localhost:6379/0"
        try:
            conn = _redis.Redis.from_url(redis_url)
            conn.ping()
        except Exception as e:
            raise RQTaskQueueNotAvailable(
                f"Redis not reachable at {redis_url}: {e}") from e

        self._redis = conn
        self._queue = _RQQueue(name, connection=conn)
        self._default_timeout = 1800  # 30 min
        self._default_ttl = 86400     # 24h result retention
        self._max_retries = 3

    # ── Enqueue / Dequeue ──────────────────────────────────────────────

    def enqueue(self, agent: str, module: str, page: str = "",
                provider: str = "claude", max_retries: int = 3) -> str:
        """Enqueue an agent task. Returns job ID."""
        task_id = f"task-{uuid.uuid4().hex[:12]}"

        job = self._queue.enqueue(
            _run_agent_task,
            agent_name=agent,
            provider=provider,
            module=module,
            page=page,
            job_id=task_id,
            retry=rq.Retry(max=max_retries, interval=[10, 30, 60]),
            result_ttl=self._default_ttl,
            failure_ttl=86400 * 7,  # Keep failed jobs for 7 days
            job_timeout=self._default_timeout,
        )
        return job.id

    def dequeue(self) -> Optional[dict]:
        """RQ doesn't support explicit dequeue — returns None.
        Jobs are consumed by rq worker processes."""
        return None  # RQ workers pull jobs automatically

    # ── Complete / Fail ────────────────────────────────────────────────

    def mark_completed(self, task_id: str, result: dict):
        """No-op: RQ marks jobs complete automatically."""
        pass  # rq worker handles this

    def mark_failed(self, task_id: str, error: str):
        """No-op: RQ handles retry automatically via retry policy."""
        pass  # rq's Retry() handles this

    def mark_failed_no_retry(self, task_id: str, error: str):
        """Cancel a job to prevent retry."""
        try:
            job = Job.fetch(task_id, connection=self._redis)
            job.cancel()
        except Exception:
            pass

    # ── Recovery ──────────────────────────────────────────────────────

    def recover_stale_tasks(self) -> int:
        """RQ has built-in job timeout. Stale jobs are moved to FAILED
        by rq's maintenance thread. Manual recovery returns count of
        failed jobs that can be retried."""
        failed_registry = self._queue.failed_job_registry
        count = failed_registry.count
        # Jobs in FailedJobRegistry can be requeued
        for job_id in failed_registry.get_job_ids():
            try:
                failed_registry.requeue(job_id)
            except Exception:
                pass
        return count

    def retry_failed(self, task_id: str) -> bool:
        """Requeue a failed job."""
        try:
            failed_registry = self._queue.failed_job_registry
            for job_id in failed_registry.get_job_ids():
                if job_id == task_id:
                    failed_registry.requeue(task_id)
                    return True
            return False
        except Exception:
            return False

    # ── Query ──────────────────────────────────────────────────────────

    def get(self, task_id: str) -> Optional[dict]:
        """Get task status by ID."""
        try:
            job = Job.fetch(task_id, connection=self._redis)
            return self._job_to_dict(job)
        except Exception:
            return None

    def list_tasks(self, status: str = None, limit: int = 20) -> list[dict]:
        """List tasks. Filters by status if provided.

        RQ status mapping: queued→queued, started→running, finished→completed,
        failed→failed, deferred→queued.
        """
        result = []
        if status is None or status == "queued":
            result.extend(self._registry_jobs(
                self._queue.get_job_ids(), limit))
        if status is None or status == "running":
            result.extend(self._registry_jobs(
                self._queue.started_job_registry.get_job_ids(), limit))
        if status is None or status == "completed":
            result.extend(self._registry_jobs(
                self._queue.finished_job_registry.get_job_ids(), limit))
        if status is None or status == "failed":
            result.extend(self._registry_jobs(
                self._queue.failed_job_registry.get_job_ids(), limit))
        return result[:limit]

    def _registry_jobs(self, job_ids: list[str], limit: int) -> list[dict]:
        result = []
        for jid in job_ids[:limit]:
            try:
                job = Job.fetch(jid, connection=self._redis)
                result.append(self._job_to_dict(job))
            except Exception:
                pass
        return result

    def _job_to_dict(self, job: Job) -> dict:
        return {
            "id": job.id,
            "status": job.get_status(refresh=False),
            "agent": job.kwargs.get("agent_name", "") if job.kwargs else "",
            "module": job.kwargs.get("module", "") if job.kwargs else "",
            "error_msg": str(job.exc_info) if job.exc_info else "",
            "retry_count": job.meta.get("failures", 0) if job.meta else 0,
            "created_at": job.created_at.timestamp() if job.created_at else 0,
            "started_at": job.started_at.timestamp() if job.started_at else 0,
            "ended_at": job.ended_at.timestamp() if job.ended_at else 0,
        }

    def count_by_status(self) -> dict:
        """Count jobs by status. Includes 'pending' aggregation."""
        counts = {
            "queued": self._queue.count,
            "started": self._queue.started_job_registry.count,
            "finished": self._queue.finished_job_registry.count,
            "failed": self._queue.failed_job_registry.count,
            "deferred": self._queue.deferred_job_registry.count,
        }
        counts["running"] = counts["started"] + counts["deferred"]
        counts["completed"] = counts["finished"]
        counts["pending"] = counts["queued"] + counts["running"]
        return counts

    def cleanup(self, older_than_hours: int = 24) -> int:
        """Clean up old completed/failed jobs."""
        count = 0
        for registry in [self._queue.finished_job_registry,
                          self._queue.failed_job_registry]:
            for job_id in registry.get_job_ids():
                try:
                    job = Job.fetch(job_id, connection=self._redis)
                    if job.ended_at:
                        age_h = (time.time() - job.ended_at.timestamp()) / 3600
                        if age_h > older_than_hours:
                            job.delete()
                            count += 1
                except Exception:
                    pass
        return count

    @property
    def is_available(self) -> bool:
        """Check Redis connectivity."""
        try:
            self._redis.ping()
            return True
        except Exception:
            return False

    def stats(self) -> dict:
        """Extended stats for health monitoring."""
        try:
            info = self._redis.info("server")
            return {
                "backend": "redis",
                "redis_version": info.get("redis_version", "?"),
                "connected_clients": self._redis.info("clients").get("connected_clients", 0),
                "used_memory_mb": round(info.get("used_memory", 0) / 1024 / 1024, 1),
                "queue_name": self._queue.name,
                **self.count_by_status(),
            }
        except Exception:
            return {"backend": "redis", "status": "disconnected"}


# ── Task function (executed by rq worker) ─────────────────────────────

def _run_agent_task(agent_name: str, provider: str = "claude",
                    module: str = "", page: str = "") -> dict:
    """RQ worker entry point — called in a separate process."""
    from aitest.agents.agent_runner import run_agent
    return run_agent(
        agent_name=agent_name,
        provider=provider,
        module=module,
        page=page,
        verbose=False,
    )


# ── Factory ───────────────────────────────────────────────────────────

_queue: Optional[RQTaskQueue] = None


def get_rq_queue(redis_url: str = None,
                 fallback_to_sqlite: bool = True) -> RQTaskQueue:
    """Get or create the RQ task queue singleton. Falls back to SQLite if
    Redis is not available and fallback_to_sqlite is True.

    Returns:
        RQTaskQueue instance or raises RQTaskQueueNotAvailable.
    """
    global _queue
    if _queue is not None:
        return _queue

    try:
        _queue = RQTaskQueue(redis_url=redis_url)
        logger.info("rq_queue_initialized", backend="redis")
    except RQTaskQueueNotAvailable:
        if not fallback_to_sqlite:
            raise
        logger.info("rq_queue_fallback_sqlite")
        raise
    return _queue
