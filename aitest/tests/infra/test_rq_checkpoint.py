"""RQ/AgentLoop checkpoint bridge tests without a live Redis server."""

import json
from types import SimpleNamespace

from aitest.infra import rq_queue


class _FakeRedis:
    def __init__(self, raw=None):
        self.raw = raw
        self.saved = {}
        self.deleted = []

    def exists(self, key):
        return int(self.raw is not None)

    def get(self, key):
        return self.raw

    def set(self, key, value, ex=None):
        self.saved[key] = (value, ex)

    def delete(self, key):
        self.deleted.append(key)


def test_recovery_marks_job_for_checkpoint_continuation():
    connection = _FakeRedis(raw=b'{"step": 1}')
    queue = rq_queue.RQTaskQueue.__new__(rq_queue.RQTaskQueue)
    queue._redis = connection
    job = SimpleNamespace(
        id="job-1",
        kwargs={"mode": "full"},
        meta={},
        save=lambda: None,
    )

    assert queue._prepare_recovery_job(job) is True
    assert job.kwargs["mode"] == "resume"
    assert job.meta["recovery_mode"] == "checkpoint_continuation"
    assert job.meta["recovery_count"] == 1


def test_rq_agent_entrypoint_loads_and_persists_checkpoint(monkeypatch):
    snapshot = {"step": 1, "completed_skills": ["skill-one"]}
    connection = _FakeRedis(raw=json.dumps(snapshot).encode())
    job = SimpleNamespace(id="job-2", connection=connection)
    captured = {}

    def fake_run_agent(**kwargs):
        captured.update(kwargs)
        kwargs["checkpoint_callback"]({"step": 2, "completed_skills": ["skill-one", "skill-two"]})
        return {"success": True, "step": 2}

    monkeypatch.setattr(rq_queue.rq, "get_current_job", lambda: job)
    monkeypatch.setattr("alice_engine.core.executor.run_agent", fake_run_agent)

    result = rq_queue._run_agent_task(
        agent_name="automation-agent",
        provider="mock",
        module="checkout",
        page="cart",
        mode="resume",
    )

    assert result["success"] is True
    assert captured["resume_state"] == snapshot
    assert captured["run_id"] == "rq-agent-job-2"
    assert connection.saved[rq_queue.agent_checkpoint_key("job-2")][1] == rq_queue.AGENT_CHECKPOINT_TTL
    assert connection.deleted == [rq_queue.agent_checkpoint_key("job-2")]
