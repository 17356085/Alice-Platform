"""Run a real local Redis/RQ infrastructure staging probe.

This probe deliberately replaces the AgentLoop entrypoint with local
success/failure functions. It verifies RQ transport, worker consumption,
resume-mode serialization, timeout configuration, and failed-job recovery
without calling an external provider or changing unrelated Redis keys.

Run from the repository root with the optional RQ dependencies available:
    python -m scripts.rq_staging_probe
"""

from __future__ import annotations

import json
import uuid

from rq import SimpleWorker
from rq.job import Job

import aitest.infra.rq_queue as rq_module
from scripts.rq_staging_functions import stage_failure, stage_success


def main() -> None:
    queue_name = f"aitest-staging-{uuid.uuid4().hex[:10]}"
    queue = rq_module.RQTaskQueue(
        redis_url="redis://127.0.0.1:6379/0",
        name=queue_name,
    )

    rq_module._run_agent_task = stage_success
    job_id = queue.enqueue(
        "automation-agent",
        "rq-staging",
        page="resume-probe",
        provider="mock",
        max_retries=0,
        mode="resume",
    )
    job = Job.fetch(job_id, connection=queue._redis)
    assert job.kwargs["mode"] == "resume"
    assert job.timeout == 1800

    SimpleWorker([queue._queue], connection=queue._redis).work(
        burst=True,
        with_scheduler=False,
    )
    completed = queue.get(job_id)
    assert completed and completed["status"] == "completed"
    assert completed["result"]["mode"] == "resume"

    rq_module._run_agent_task = stage_failure
    failed_id = queue.enqueue(
        "automation-agent",
        "rq-staging",
        page="failure-probe",
        provider="mock",
        max_retries=0,
        mode="resume",
    )
    SimpleWorker([queue._queue], connection=queue._redis).work(
        burst=True,
        with_scheduler=False,
    )
    failed = queue.get(failed_id)
    assert failed and failed["status"] == "failed"

    recovered = queue.recover_stale_tasks()
    requeued = queue.get(failed_id)
    assert recovered >= 1
    assert requeued and requeued["status"] == "queued"

    print(json.dumps({
        "queue": queue_name,
        "completed_status": completed["status"],
        "completed_mode": completed["result"]["mode"],
        "timeout": job.timeout,
        "failed_before_recovery": failed["status"],
        "recovered": recovered,
        "failed_after_recovery": requeued["status"],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
