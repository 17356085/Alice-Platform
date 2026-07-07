"""Tests for scheduler.py — frozen job / lease / retry model.

This module is loaded directly from its file path so the test stays isolated
from the heavier `aitest` package import chain.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


SCHEDULER_PATH = Path(__file__).resolve().parents[2] / "platform" / "scheduler.py"
SPEC = importlib.util.spec_from_file_location("aitest_platform_scheduler", SCHEDULER_PATH)
assert SPEC is not None and SPEC.loader is not None
SCHEDULER = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = SCHEDULER
SPEC.loader.exec_module(SCHEDULER)

ACTIVE_JOB_STATUSES = SCHEDULER.ACTIVE_JOB_STATUSES
TERMINAL_JOB_STATUSES = SCHEDULER.TERMINAL_JOB_STATUSES
JobStatus = SCHEDULER.JobStatus
QueueLease = SCHEDULER.QueueLease
RetryPolicy = SCHEDULER.RetryPolicy
SchedulerJob = SCHEDULER.SchedulerJob


def _make_job(**overrides) -> SchedulerJob:
    defaults = {
        "job_id": "job-1",
        "request_id": "req-1",
        "workspace_id": "ws-1",
        "org_id": "org-1",
    }
    defaults.update(overrides)
    return SchedulerJob(**defaults)


class TestJobStatus:
    def test_status_constants(self):
        assert JobStatus.QUEUED == "queued"
        assert JobStatus.RUNNING == "running"
        assert JobStatus.RETRYING == "retrying"


class TestStatusSets:
    def test_active_statuses(self):
        assert JobStatus.CREATED in ACTIVE_JOB_STATUSES
        assert JobStatus.RUNNING in ACTIVE_JOB_STATUSES

    def test_terminal_statuses(self):
        assert JobStatus.COMPLETED in TERMINAL_JOB_STATUSES
        assert JobStatus.CANCELLED in TERMINAL_JOB_STATUSES


class TestRetryPolicy:
    def test_delay_for_attempt(self):
        policy = RetryPolicy()
        assert policy.delay_for_attempt(0) == 1.0
        assert policy.delay_for_attempt(1) == 2.0

    def test_can_retry(self):
        policy = RetryPolicy(max_attempts=2)
        assert policy.can_retry(0, "failed") is True
        assert policy.can_retry(2, "failed") is False
        assert policy.can_retry(0, "completed") is False


class TestQueueLease:
    def test_acquire(self):
        lease = QueueLease.acquire("lease-1", "worker-1")
        assert lease.lease_id == "lease-1"
        assert lease.worker_id == "worker-1"
        assert lease.acquired_at
        assert lease.heartbeat_at

    def test_heartbeat(self):
        lease = QueueLease.acquire("lease-1", "worker-1")
        first = lease.heartbeat_at
        lease.heartbeat()
        assert lease.heartbeat_at != first


class TestSchedulerJob:
    def test_defaults(self):
        job = _make_job()
        assert job.status == JobStatus.CREATED
        assert job.is_active is True
        assert job.is_terminal is False
        assert job.attempt_count == 0

    def test_queue(self):
        job = _make_job()
        job.queue()
        assert job.status == JobStatus.QUEUED
        assert job.queued_at is not None

    def test_dispatch_and_start(self):
        job = _make_job()
        lease = QueueLease.acquire("lease-1", "worker-1")
        job.dispatch(lease)
        assert job.status == JobStatus.DISPATCHED
        assert job.attempt_count == 1
        assert job.lease is lease
        job.start(lease)
        assert job.status == JobStatus.RUNNING
        assert job.started_at is not None

    def test_complete(self):
        job = _make_job(status=JobStatus.RUNNING)
        job.complete({"ok": True})
        assert job.status == JobStatus.COMPLETED
        assert job.result == {"ok": True}
        assert job.is_terminal is True

    def test_fail_retrying(self):
        job = _make_job(status=JobStatus.RUNNING)
        job.dispatch()
        job.fail("temporary error", retryable=True)
        assert job.status == JobStatus.RETRYING
        assert job.next_retry_at is not None

    def test_fail_terminal(self):
        job = _make_job(status=JobStatus.RUNNING)
        job.retry_policy = RetryPolicy(max_attempts=0)
        job.fail("fatal error", retryable=True)
        assert job.status == JobStatus.FAILED

    def test_to_dict(self):
        job = _make_job()
        d = job.to_dict()
        assert d["job_id"] == "job-1"
        assert d["request_id"] == "req-1"
        assert d["status"] == JobStatus.CREATED
