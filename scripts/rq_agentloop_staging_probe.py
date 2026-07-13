"""Run a real multi-process RQ -> AgentLoop staging probe.

The parent process enqueues the production ``_run_agent_task`` function and a
separate Windows spawn child runs an actual RQ ``SimpleWorker``.  The probe uses the
single-skill execution agent and the local mock provider, so the real
AgentLoop/RQ boundary is exercised without exporting private skill prompts.

Run from the repository root after Redis is available::

    python scripts/rq_agentloop_staging_probe.py
"""

from __future__ import annotations

import json
import multiprocessing as mp
import os
import time
import uuid
from typing import Any

from redis import Redis
from rq import Queue, SimpleWorker
from rq.job import Job

from aitest.infra.rq_queue import RQTaskQueue


REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")


def _run_worker(queue_name: str, redis_url: str) -> None:
    connection = Redis.from_url(redis_url)
    worker = SimpleWorker(
        [Queue(queue_name, connection=connection)],
        connection=connection,
    )
    worker.work(burst=True, with_scheduler=False)


def _summary(job: Job) -> dict[str, Any]:
    result = job.result if isinstance(job.result, dict) else {}
    return {
        "job_id": job.id,
        "status": job.get_status(refresh=True),
        "provider": job.kwargs.get("provider", "") if job.kwargs else "",
        "mode": job.kwargs.get("mode", "") if job.kwargs else "",
        "agent": job.kwargs.get("agent_name", "") if job.kwargs else "",
        "result_success": result.get("success"),
        "result_step": result.get("step"),
        "result_provider": result.get("provider"),
        "result_error": str(result.get("error", ""))[-1000:],
        "observations": [
            {
                "skill_id": item.get("skill_id"),
                "status": item.get("status"),
                "error": str(item.get("error", ""))[-300:],
            }
            for item in result.get("observations", [])
            if isinstance(item, dict)
        ],
        "error": str(job.exc_info or "")[-1000:],
    }


def main() -> None:
    queue_name = f"aitest-agentloop-staging-{uuid.uuid4().hex[:10]}"
    queue = RQTaskQueue(redis_url=REDIS_URL, name=queue_name)
    job_id = queue.enqueue(
        "automation-agent",
        "rq-agentloop-staging",
        page="local-mock-single-skill",
        provider="mock",
        max_retries=0,
        mode="resume",
    )

    context = mp.get_context("spawn")
    worker_process = context.Process(target=_run_worker, args=(queue_name, REDIS_URL))
    worker_process.start()
    deadline = time.monotonic() + 180
    job = Job.fetch(job_id, connection=queue._redis)
    while time.monotonic() < deadline:
        job.refresh()
        if job.get_status(refresh=False) in {"finished", "failed", "canceled"}:
            break
        time.sleep(1)

    if worker_process.is_alive():
        worker_process.join(timeout=10)
    if worker_process.is_alive():
        worker_process.terminate()
        worker_process.join(timeout=10)

    job.refresh()
    result = _summary(job)
    print(json.dumps(result, ensure_ascii=False))
    # The mock provider intentionally cannot satisfy every automation skill's
    # semantic evaluator.  Infrastructure success is a finished RQ job with a
    # serialized AgentState; semantic success requires a real provider and
    # project inputs, which this safe probe deliberately does not export.
    if result["status"] != "finished" or result["result_step"] is None:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
