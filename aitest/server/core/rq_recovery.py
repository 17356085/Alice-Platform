"""Background recovery loop for abandoned RQ jobs."""

from __future__ import annotations

import asyncio
from typing import Any


async def rq_recovery_loop(
    queue: Any,
    stop_event: asyncio.Event,
    *,
    interval_seconds: float = 60.0,
    stale_after_seconds: float = 3600.0,
    log: Any = None,
) -> None:
    """Requeue abandoned RQ jobs without blocking the event loop."""
    interval = max(1.0, float(interval_seconds))
    stale_after = max(0.0, float(stale_after_seconds))
    while not stop_event.is_set():
        try:
            recovered = await asyncio.to_thread(
                queue.recover_stale_tasks,
                stale_after_seconds=stale_after,
            )
            if recovered and log is not None:
                log.warning("rq_stale_jobs_recovered", recovered=recovered)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            if log is not None:
                log.warning("rq_stale_job_recovery_failed", error=str(exc)[:200])
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=interval)
        except asyncio.TimeoutError:
            pass
