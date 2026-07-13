from types import SimpleNamespace

import pytest

from aitest.server.api import kanban


def _request(payload):
    async def json():
        return payload

    return SimpleNamespace(
        json=json,
        state=SimpleNamespace(user_id="tester", org_id="org-test"),
        headers={},
    )


@pytest.mark.asyncio
async def test_sop_start_requires_module():
    result = await kanban.sop_start(_request({}))

    assert result == {"error": "module is required"}


@pytest.mark.asyncio
async def test_sop_start_queues_execution_service(monkeypatch):
    calls = []

    class Service:
        def execute(self, **kwargs):
            calls.append(kwargs)

    monkeypatch.setattr(kanban, "get_execution_service", lambda _request: Service())

    result = await kanban.sop_start(_request({
        "module": "equipment", "pages": ["alarm-config"], "mode": "full", "provider": "mock",
    }))
    await kanban.asyncio.sleep(0.05)

    assert result["status"] == "started"
    assert calls and calls[0]["module"] == "equipment"
    assert calls[0]["pages"] == ["alarm-config"]
    assert calls[0]["provider"] == "mock"
