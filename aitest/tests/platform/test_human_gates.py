"""Integration coverage for human gate wait, timeout, REST and WebSocket flow."""
import json
import threading
import time

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import aitest.platform.human_gates as gates
from aitest.server.api.human_gates import human_gates_router


@pytest.fixture(autouse=True)
def isolated_gate_db(tmp_path, monkeypatch):
    monkeypatch.setattr(gates, "_path", tmp_path / "human_gates.db")
    gates._waiters.clear()


def test_wait_unblocks_after_resolution():
    gate = gates.create_gate("run-1", "review", "Review", {}, ["approve", "reject"])
    result = {}
    worker = threading.Thread(
        target=lambda: result.update(gates.wait_for_gate(gate["id"], 2, "reject"))
    )
    worker.start()
    time.sleep(0.05)
    gates.resolve_gate("run-1", gate["id"], "approve", "LGTM")
    worker.join(timeout=1)

    assert not worker.is_alive()
    assert result == {
        "success": True,
        "action": "approved",
        "comment": "LGTM",
        "gate_id": gate["id"],
    }


def test_timeout_uses_fallback_action():
    gate = gates.create_gate("run-2", "review", "Review", {}, ["approve", "reject"])
    result = gates.wait_for_gate(gate["id"], 0, "reject")

    assert result["timed_out"] is True
    assert result["action"] == "reject"


def test_rest_resolution_is_pushed_to_websocket_stream():
    app = FastAPI()
    app.include_router(human_gates_router)
    client = TestClient(app)
    gate = gates.create_gate("run-3", "review", "Review", {"risk": "high"}, ["approve", "reject"])

    with client.websocket_connect("/api/v1/runs/run-3/human-gates/ws") as ws:
        initial = json.loads(ws.receive_text())
        assert initial["gates"][0]["status"] == "pending"
        response = client.post(
            f"/api/v1/runs/run-3/human-gates/{gate['id']}/resolve",
            json={"action": "approve", "comment": "Reviewed"},
        )
        assert response.status_code == 200
        updated = json.loads(ws.receive_text())
        assert updated["gates"][0]["status"] == "approved"
        assert updated["gates"][0]["resolution"]["comment"] == "Reviewed"
