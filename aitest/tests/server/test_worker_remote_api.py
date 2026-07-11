"""Remote Worker registration and heartbeat API contract tests."""

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_remote_worker_register_and_heartbeat(monkeypatch):
    import aitest.server.api.workers_v1 as workers_api

    lease = SimpleNamespace(
        to_dict=lambda: {
            "worker_id": "remote-1", "hostname": "node-a", "pid": 1,
            "status": "running", "started_at": "2026-07-11T00:00:00+00:00",
            "last_heartbeat_at": "2026-07-11T00:00:00+00:00",
            "heartbeat_interval_seconds": 30, "claimed_requests": [],
            "stats": {}, "metadata": {}, "org_id": "org-a",
        }
    )
    calls = []

    class Store:
        def register(self, *args, **kwargs):
            calls.append(("register", args, kwargs))
            return lease

        def heartbeat(self, *args, **kwargs):
            calls.append(("heartbeat", args, kwargs))
            return True

    monkeypatch.setattr(workers_api, "WorkerLeaseStore", lambda _: Store())
    app = FastAPI()
    app.include_router(workers_api.workers_router)
    client = TestClient(app)

    registered = client.post("/api/v1/workers/register", json={"worker_id": "remote-1", "org_id": "org-a"})
    heartbeat = client.post(
        "/api/v1/workers/remote-1/heartbeat",
        json={"org_id": "org-a", "stats": {"completed": 1}},
    )

    assert registered.status_code == 200
    assert heartbeat.status_code == 200
    assert calls[0][2]["org_id"] == "org-a"
    assert calls[1][2]["org_id"] == "org-a"


def test_worker_api_rejects_missing_token_when_auth_is_required(monkeypatch):
    import aitest.server.api.workers_v1 as workers_api

    monkeypatch.setenv("AITEST_WORKER_AUTH_REQUIRED", "1")
    monkeypatch.setenv("AITEST_WORKER_AUTH_SECRET", "server-secret")
    app = FastAPI()
    app.include_router(workers_api.workers_router)
    response = TestClient(app).post(
        "/api/v1/workers/remote-1/heartbeat",
        json={"org_id": "org-a"},
    )
    assert response.status_code == 401
