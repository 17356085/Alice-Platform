"""RQ worker entrypoint contract tests without requiring Redis/RQ locally."""

from aitest.infra.rq_queue import _run_agent_task


def test_rq_worker_forwards_resume_mode(monkeypatch):
    captured = {}

    def fake_run_agent(**kwargs):
        captured.update(kwargs)
        return {"status": "ok"}

    monkeypatch.setattr("alice_engine.core.executor.run_agent", fake_run_agent)

    result = _run_agent_task(
        agent_name="automation-agent",
        provider="mimo",
        module="checkout",
        page="cart",
        mode="resume",
    )

    assert result == {"status": "ok"}
    assert captured == {
        "agent_name": "automation-agent",
        "provider": "mimo",
        "module": "checkout",
        "page": "cart",
        "mode": "resume",
        "verbose": False,
    }
