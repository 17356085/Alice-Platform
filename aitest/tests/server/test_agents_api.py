import pytest
from types import SimpleNamespace

from aitest.server.api.agents import AgentRunRequest, all_modules_status, trigger_agent_async


@pytest.mark.asyncio
async def test_all_modules_status_uses_static_route(monkeypatch, tmp_path):
    monkeypatch.setattr("aitest.platform.paths.get_project_dir", lambda: tmp_path / "missing-project")
    result = await all_modules_status()

    assert "modules" in result
    assert result["modules"]
    assert "status" not in result


@pytest.mark.asyncio
async def test_trigger_agent_returns_queue_contract(monkeypatch):
    calls = []

    class Queue:
        def enqueue(self, **kwargs):
            calls.append(kwargs)
            return "task-agent-1"

    monkeypatch.setattr("aitest.infra.task_queue.get_queue", lambda: Queue())

    result = await trigger_agent_async(AgentRunRequest(
        agent="automation-agent", module="equipment", provider="mock", mode="resume",
    ))

    assert result["status"] == "queued"
    assert result["task_id"] == "task-agent-1"
    assert calls == [{
        "agent": "automation-agent",
        "module": "equipment",
        "page": "",
        "provider": "mock",
        "org_id": "default-org",
        "mode": "resume",
    }]
