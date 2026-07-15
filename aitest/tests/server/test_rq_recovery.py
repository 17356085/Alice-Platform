import asyncio

import pytest

from aitest.server.core.rq_recovery import rq_recovery_loop


@pytest.mark.asyncio
async def test_rq_recovery_loop_recovers_stale_jobs_and_stops():
    calls: list[float] = []
    stop_event = asyncio.Event()

    class Queue:
        def recover_stale_tasks(self, *, stale_after_seconds: float) -> int:
            calls.append(stale_after_seconds)
            stop_event.set()
            return 1

    await asyncio.wait_for(
        rq_recovery_loop(
            Queue(),
            stop_event,
            interval_seconds=0.01,
            stale_after_seconds=7.5,
        ),
        timeout=2,
    )

    assert calls == [7.5]
