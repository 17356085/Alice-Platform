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
import os
import time
import uuid
import logging
from typing import Optional

logger = logging.getLogger("rq_queue")

AGENT_CHECKPOINT_PREFIX = "aitest:agentloop:checkpoint:"
AGENT_CHECKPOINT_TTL = 7 * 24 * 3600


def agent_checkpoint_key(job_id: str) -> str:
    """Return the Redis key used for a job's durable AgentLoop checkpoint."""
    return f"{AGENT_CHECKPOINT_PREFIX}{job_id}"

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
                provider: str = "claude", max_retries: int = 3,
                org_id: str = "default-org", mode: str = "full") -> str:
        """Enqueue an agent task. Returns job ID."""
        task_id = f"task-{uuid.uuid4().hex[:12]}"

        retry_policy = (
            rq.Retry(max=max_retries, interval=[10, 30, 60])
            if max_retries > 0 else None
        )
        job = self._queue.enqueue(
            _run_agent_task,
            agent_name=agent,
            provider=provider,
            module=module,
            page=page,
            mode=mode,
            job_id=task_id,
            retry=retry_policy,
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

    def _prepare_recovery_job(self, job) -> bool:
        """Mark a requeued job for AgentLoop resume and record its source."""
        has_checkpoint = bool(self._redis.exists(agent_checkpoint_key(job.id)))
        job.kwargs = dict(job.kwargs or {})
        job.kwargs["mode"] = "resume"
        job.meta = dict(job.meta or {})
        job.meta["recovery_mode"] = (
            "checkpoint_continuation" if has_checkpoint else "entrypoint_restart_no_checkpoint"
        )
        job.meta["recovery_count"] = int(job.meta.get("recovery_count", 0) or 0) + 1
        job.save()
        return has_checkpoint

    def recover_stale_tasks(self, stale_after_seconds: float = 3600) -> int:
        """Requeue failed jobs and abandoned started jobs.

        RQ's maintenance thread eventually moves an abandoned worker job to
        ``FailedJobRegistry``.  A killed worker can nevertheless leave a job
        in ``StartedJobRegistry`` until that timeout expires, so production
        recovery needs an explicit, conservative stale threshold.  Active
        jobs are never touched when their age is below the threshold.
        """
        recovered = 0
        failed_registry = self._queue.failed_job_registry
        # Jobs in FailedJobRegistry can be requeued
        for job_id in failed_registry.get_job_ids(cleanup=False):
            try:
                job = Job.fetch(job_id, connection=self._redis)
                self._prepare_recovery_job(job)
                failed_registry.requeue(job_id)
                recovered += 1
            except Exception:
                pass

        started_registry = self._queue.started_job_registry
        now = time.time()
        if hasattr(started_registry, "get_job_and_execution_ids"):
            # RQ 2.x stores ``job_id:execution_id`` composite members in the
            # started sorted set.  Keep the raw member so requeue can remove
            # the exact entry (StartedJobRegistry.requeue(job_id) otherwise
            # misses the composite key and silently leaves the job stuck).
            from rq.registry import parse_composite_key

            raw_entries = self._redis.zrange(started_registry.key, 0, -1)
            started_entries = [
                (raw, parse_composite_key(raw.decode() if isinstance(raw, bytes) else raw))
                for raw in raw_entries
            ]
        else:
            started_entries = [
                (job_id, (job_id, ""))
                for job_id in started_registry.get_job_ids(cleanup=False)
            ]
        for raw_key, (job_id, _execution_id) in started_entries:
            try:
                job = Job.fetch(job_id, connection=self._redis)
                started_at = job.started_at.timestamp() if job.started_at else 0
                if started_at and (now - started_at) >= max(0, stale_after_seconds):
                    self._requeue_started_job(started_registry, raw_key, job)
                    recovered += 1
            except Exception:
                # A worker may complete/delete the job between the registry
                # scan and the requeue call; that race is intentionally benign.
                pass
        return recovered

    def _requeue_started_job(self, started_registry, raw_key, job) -> None:
        """Requeue a job using the exact RQ started-registry member."""
        queue = _RQQueue(
            job.origin,
            connection=self._redis,
            job_class=job.__class__,
            serializer=getattr(job, "serializer", None),
        )
        with self._redis.pipeline() as pipeline:
            pipeline.zrem(started_registry.key, raw_key)
            job.started_at = None
            job.ended_at = None
            job._exc_info = ""
            self._prepare_recovery_job(job)
            job.save()
            queue._enqueue_job(job, pipeline=pipeline)
            pipeline.execute()

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
        raw_status = job.get_status(refresh=False)
        status = {
            "queued": "queued",
            "started": "running",
            "deferred": "queued",
            "scheduled": "queued",
            "finished": "completed",
            "failed": "failed",
            "canceled": "failed",
        }.get(raw_status, raw_status)
        return {
            "id": job.id,
            "status": status,
            "agent": job.kwargs.get("agent_name", "") if job.kwargs else "",
            "module": job.kwargs.get("module", "") if job.kwargs else "",
            "result": job.result,
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


# ── Task function (executed by rq worker in separate process) ─────────
# NOTE: This is a lazy import by design — RQ workers run in separate
# processes and won't hit the circular dependency. The import only
# triggers in the worker process, not in the main server process.

def _run_agent_task(agent_name: str, provider: str = "claude",
                    module: str = "", page: str = "", mode: str = "full") -> dict:
    """RQ worker entry point — called in a separate process."""
    from alice_engine.core.executor import run_agent  # noqa: E402
    job = rq.get_current_job() if _RQ_AVAILABLE else None
    resume_state = None
    checkpoint_callback = None
    run_id = None
    if job is not None:
        run_id = f"rq-agent-{job.id}"
        key = agent_checkpoint_key(job.id)
        if mode == "resume":
            raw = job.connection.get(key)
            if raw:
                try:
                    resume_state = json.loads(raw)
                except (TypeError, ValueError, json.JSONDecodeError):
                    logger.warning("invalid_agent_checkpoint", extra={"job_id": job.id})

        checkpoint_pause_used = False

        def save_checkpoint(snapshot: dict) -> None:
            nonlocal checkpoint_pause_used
            try:
                job.connection.set(
                    key,
                    json.dumps(snapshot, ensure_ascii=False, separators=(",", ":")),
                    ex=AGENT_CHECKPOINT_TTL,
                )
                # Staging-only hook: keep the worker alive after a durable
                # checkpoint so a kill/recovery probe can terminate between
                # Skills. It is disabled by default and has no production
                # latency impact.
                pause = float(os.environ.get("AITEST_AGENTLOOP_CHECKPOINT_PAUSE_SECONDS", "0") or 0)
                if pause > 0 and not checkpoint_pause_used:
                    checkpoint_pause_used = True
                    time.sleep(pause)
            except Exception as exc:
                logger.warning("agent_checkpoint_write_failed", extra={"error": str(exc)[:200]})

        checkpoint_callback = save_checkpoint

    result = run_agent(
        agent_name=agent_name,
        provider=provider,
        module=module,
        page=page,
        mode=mode,
        verbose=False,
        **({"run_id": run_id} if run_id else {}),
        **({"resume_state": resume_state} if resume_state is not None else {}),
        **({"checkpoint_callback": checkpoint_callback} if checkpoint_callback else {}),
    )
    if job is not None and isinstance(result, dict) and result.get("success"):
        try:
            job.connection.delete(agent_checkpoint_key(job.id))
        except Exception:
            pass
    return result


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
