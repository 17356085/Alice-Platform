"""Worker bearer-token and task ownership tests."""

import pytest

from aitest.platform.worker_auth import WorkerAuthError, issue_token, verify_token


def test_worker_token_is_scoped_and_signed(monkeypatch):
    monkeypatch.setenv("AITEST_WORKER_AUTH_SECRET", "test-secret")
    token = issue_token("worker-1", "org-a", ttl_seconds=300)
    assert verify_token(token, "worker-1", "org-a").worker_id == "worker-1"
    with pytest.raises(WorkerAuthError, match="scope"):
        verify_token(token, "worker-2", "org-a")


def test_worker_token_rejects_tampering(monkeypatch):
    monkeypatch.setenv("AITEST_WORKER_AUTH_SECRET", "test-secret")
    token = issue_token("worker-1", "org-a", ttl_seconds=300)
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(WorkerAuthError, match="signature"):
        verify_token(tampered, "worker-1", "org-a")
