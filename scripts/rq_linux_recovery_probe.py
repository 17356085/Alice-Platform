"""Exercise Linux RQ worker kill/recovery and same-queue concurrency.

The probe starts the production image's default ``rq worker`` command.  It
uses local deterministic functions by default. Set ``RQ_REAL_AGENTLOOP=1`` to
run the production ``_run_agent_task`` -> AgentLoop entry point with the local
mock provider before the kill/requeue assertion. No repository skill text is
sent to a third-party provider by this probe.

Run from the repository root after Redis and the staging image are available::

    python scripts/rq_linux_recovery_probe.py
"""

from __future__ import annotations

import json
import os
import subprocess
import time
import uuid
from pathlib import Path

from redis import Redis
from rq import Queue
from rq.job import Job

from aitest.infra.rq_queue import RQTaskQueue, _run_agent_task, agent_checkpoint_key
from rq_staging_functions import stage_long_task


REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
IMAGE = os.environ.get("AITEST_RQ_STAGING_IMAGE", "alice-aitest-worker-staging:local")
REAL_AGENTLOOP = os.environ.get("RQ_REAL_AGENTLOOP") == "1"

try:
    from dotenv import load_dotenv

    load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
except Exception:
    pass


def _docker(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["docker", *args], check=check, text=True, capture_output=True)


def _start_worker(name: str, queue_name: str, repo: Path) -> None:
    args = [
        "run", "-d", "--rm", "--name", name,
        "--network", "bridge",
        "--add-host", "host.docker.internal:host-gateway",
        # Reuse the already-built staging image's dependencies while mounting
        # the current source read-only. This keeps the probe runnable when a
        # registry is temporarily unavailable during an image rebuild.
        "-v", f"{repo}:/app:ro",
        "-e", "PYTHONPATH=/app:/app/scripts:/app/packages/alice-engine:/app/packages/alice-governance:/app/packages/alice-discovery",
    ]
    if REAL_AGENTLOOP:
        # Pass host variables by name so the secret is not copied into the
        # command string or printed by this probe.
        args.extend([
            "-e", "MOCK_LLM=1",
            "-e", "AITEST_AGENTLOOP_CHECKPOINT_PAUSE_SECONDS=15",
        ])
    args.extend([
        IMAGE,
        "rq", "worker", queue_name,
        "--url", "redis://host.docker.internal:6379/0",
    ])
    _docker(*args)


def _wait_status(job: Job, desired: set[str], timeout: float = 60) -> str:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        job.refresh()
        status = job.get_status(refresh=False)
        if status in desired:
            return status
        time.sleep(0.5)
    job.refresh()
    return job.get_status(refresh=False)


def _executions(job: Job) -> list[dict]:
    try:
        return [
            {
                "id": getattr(item, "id", ""),
                "worker": getattr(item, "worker_name", ""),
                "ended": bool(getattr(item, "ended_at", None)),
            }
            for item in job.get_executions()
        ]
    except Exception:
        return []


def main() -> None:
    repo = Path(__file__).resolve().parents[1]
    queue_name = f"aitest-rq-recovery-{uuid.uuid4().hex[:10]}"
    first_worker = f"aitest-rq-recovery-{uuid.uuid4().hex[:8]}"
    second_workers = [
        f"aitest-rq-recovery-{uuid.uuid4().hex[:8]}",
        f"aitest-rq-recovery-{uuid.uuid4().hex[:8]}",
    ]
    names = [first_worker, *second_workers]
    redis = Redis.from_url(REDIS_URL)
    redis.ping()
    queue = Queue(queue_name, connection=redis)
    recovery_task = _run_agent_task if REAL_AGENTLOOP else stage_long_task

    try:
        _start_worker(first_worker, queue_name, repo)
        if REAL_AGENTLOOP:
            killed_job = queue.enqueue(
                recovery_task,
                agent_name="automation-agent",
                provider="mock",
                module="rq-recovery",
                page="checkpoint-continuation",
                mode="full",
                job_timeout=300,
            )
        else:
            killed_job = queue.enqueue(
                recovery_task,
                seconds=10,
                marker="linux-worker-kill-recovery",
                job_timeout=300,
            )
        started_status = _wait_status(killed_job, {"started", "failed"}, timeout=30)
        if started_status != "started":
            raise RuntimeError(f"long task did not start: {started_status}")
        started_worker = getattr(killed_job, "worker_name", "")

        checkpoint_key = agent_checkpoint_key(killed_job.id) if REAL_AGENTLOOP else ""
        if REAL_AGENTLOOP:
            checkpoint_deadline = time.monotonic() + 90
            while time.monotonic() < checkpoint_deadline:
                if redis.exists(checkpoint_key):
                    break
                killed_job.refresh()
                if killed_job.get_status(refresh=False) != "started":
                    break
                time.sleep(0.5)
            if not redis.exists(checkpoint_key):
                raise RuntimeError("production AgentLoop did not persist a checkpoint before kill")

        _docker("kill", first_worker)
        time.sleep(2)
        killed_job.refresh()
        before = killed_job.get_status(refresh=True)
        rq_queue = RQTaskQueue(redis_url=REDIS_URL, name=queue_name)
        started_entries = (
            rq_queue._queue.started_job_registry.get_job_and_execution_ids(cleanup=False)
            if hasattr(rq_queue._queue.started_job_registry, "get_job_and_execution_ids")
            else rq_queue._queue.started_job_registry.get_job_ids(cleanup=False)
        )
        recovered = rq_queue.recover_stale_tasks(stale_after_seconds=0)
        killed_job.refresh()
        after_requeue = killed_job.get_status(refresh=True)
        print(json.dumps({
            "queue": queue_name,
            "task_kind": "real-agentloop-mimo" if REAL_AGENTLOOP else "deterministic-stub",
            "before_recovery": before,
            "started_entries": started_entries,
            "recovered": recovered,
            "after_requeue": after_requeue,
        }), flush=True)

        for name in second_workers:
            _start_worker(name, queue_name, repo)
        final_status = _wait_status(
            killed_job,
            {"finished", "failed"},
            timeout=240 if REAL_AGENTLOOP else 120,
        )
        killed_job.refresh()
        if final_status != "finished":
            raise RuntimeError(f"recovered long task did not finish: {final_status}")
        recovered_result = killed_job.result if isinstance(killed_job.result, dict) else {}
        if REAL_AGENTLOOP and not recovered_result.get("memory", {}).get("resumed_from_checkpoint"):
            raise RuntimeError("recovered AgentLoop did not report checkpoint continuation")

        # Multiple long jobs make concurrent consumption observable through
        # RQ's execution records and the two live worker names.
        concurrent_jobs = [
            queue.enqueue(stage_long_task, seconds=8, marker=f"parallel-{index}", job_timeout=60)
            for index in range(4)
        ]
        parallel_deadline = time.monotonic() + 40
        while time.monotonic() < parallel_deadline:
            if all(job.get_status(refresh=True) == "finished" for job in concurrent_jobs):
                break
            time.sleep(0.5)
        parallel_statuses = [job.get_status(refresh=True) for job in concurrent_jobs]
        if any(status != "finished" for status in parallel_statuses):
            raise RuntimeError(f"parallel jobs did not finish: {parallel_statuses}")

        result = {
            "status": "validated",
            "queue": queue_name,
            "started_worker": started_worker,
            "before_recovery": before,
            "recovered": recovered,
            "after_requeue": after_requeue,
            "replayed_status": final_status,
            "parallel_statuses": parallel_statuses,
            "parallel_executions": [_executions(job) for job in concurrent_jobs],
            "checkpoint_continuation": (
                recovered_result.get("memory", {}).get("resumed_from_checkpoint")
                if REAL_AGENTLOOP else False
            ),
        }
        print(json.dumps(result, ensure_ascii=False))
    except Exception:
        for name in names:
            logs = _docker("logs", name, check=False)
            if logs.stdout or logs.stderr:
                print(f"--- {name} logs ---", flush=True)
                print((logs.stdout + logs.stderr)[-4000:], flush=True)
        raise
    finally:
        for name in names:
            _docker("rm", "-f", name, check=False)


if __name__ == "__main__":
    main()
