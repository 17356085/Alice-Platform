from types import SimpleNamespace

import pytest

from aitest.server.api import workflows_v1


class _WorkflowStore:
    def __init__(self):
        self.kwargs = None

    def create_workflow(self, **kwargs):
        self.kwargs = kwargs
        graph = kwargs["graph"]
        return SimpleNamespace(
            to_dict=lambda: {
                "workflow_id": kwargs["workflow_id"],
                "name": kwargs["name"],
                "graph": graph.to_dict(),
            }
        )


class _WorkflowMutationStore:
    def __init__(self, exists=True):
        self.exists = exists
        self.calls = []

    def update_workflow(self, **kwargs):
        self.calls.append(("update", kwargs))
        return self.exists

    def publish_workflow(self, workflow_id, version):
        self.calls.append(("publish", {"workflow_id": workflow_id, "version": version}))
        return self.exists

    def delete_workflow(self, workflow_id):
        self.calls.append(("delete", {"workflow_id": workflow_id}))
        return self.exists


@pytest.mark.asyncio
async def test_create_workflow_accepts_compact_web_graph(monkeypatch):
    store = _WorkflowStore()
    monkeypatch.setattr(workflows_v1, "get_workflow_store", lambda: store)

    result = await workflows_v1.create_workflow(
        workflows_v1.CreateWorkflowRequest(
            name="browser-created",
            description="created from the studio",
            graph={"nodes": [], "edges": []},
        )
    )

    assert result["workflow_id"].startswith("wf_")
    assert result["graph"]["workflow_id"] == result["workflow_id"]
    assert result["graph"]["name"] == "browser-created"
    assert store.kwargs["workflow_id"] == result["workflow_id"]


@pytest.mark.asyncio
async def test_update_workflow_preserves_api_contract(monkeypatch):
    store = _WorkflowMutationStore()
    monkeypatch.setattr(workflows_v1, "get_workflow_store", lambda: store)

    result = await workflows_v1.update_workflow(
        "wf_test",
        workflows_v1.UpdateWorkflowRequest(name="renamed", status="draft"),
    )

    assert result == {"workflow_id": "wf_test", "status": "updated"}
    assert store.calls == [("update", {
        "workflow_id": "wf_test",
        "name": "renamed",
        "description": None,
        "status": "draft",
        "graph": None,
    })]


@pytest.mark.asyncio
async def test_publish_workflow_calls_store_and_returns_published_status(monkeypatch):
    store = _WorkflowMutationStore()
    monkeypatch.setattr(workflows_v1, "get_workflow_store", lambda: store)

    result = await workflows_v1.publish_workflow(
        "wf_test",
        workflows_v1.PublishWorkflowRequest(version="1.0.0"),
    )

    assert result == {"workflow_id": "wf_test", "version": "1.0.0", "status": "published"}
    assert store.calls == [("publish", {"workflow_id": "wf_test", "version": "1.0.0"})]


@pytest.mark.asyncio
async def test_publish_workflow_returns_404_for_missing_workflow(monkeypatch):
    store = _WorkflowMutationStore(exists=False)
    monkeypatch.setattr(workflows_v1, "get_workflow_store", lambda: store)

    with pytest.raises(workflows_v1.HTTPException) as exc:
        await workflows_v1.publish_workflow(
            "wf_missing",
            workflows_v1.PublishWorkflowRequest(version="1.0.0"),
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_delete_workflow_calls_store_and_returns_deleted_status(monkeypatch):
    store = _WorkflowMutationStore()
    monkeypatch.setattr(workflows_v1, "get_workflow_store", lambda: store)

    result = await workflows_v1.delete_workflow("wf_test")

    assert result == {"workflow_id": "wf_test", "status": "deleted"}
    assert store.calls == [("delete", {"workflow_id": "wf_test"})]


@pytest.mark.asyncio
async def test_delete_workflow_returns_404_for_missing_workflow(monkeypatch):
    store = _WorkflowMutationStore(exists=False)
    monkeypatch.setattr(workflows_v1, "get_workflow_store", lambda: store)

    with pytest.raises(workflows_v1.HTTPException) as exc:
        await workflows_v1.delete_workflow("wf_missing")

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_validate_empty_workflow_returns_structured_validation_result(monkeypatch):
    workflow = SimpleNamespace(graph=None)
    monkeypatch.setattr(
        workflows_v1,
        "get_workflow_store",
        lambda: SimpleNamespace(get_workflow=lambda _workflow_id: workflow),
    )

    result = await workflows_v1.validate_workflow("wf_empty")

    assert result == {
        "workflow_id": "wf_empty",
        "valid": False,
        "errors": ["Workflow has no graph"],
        "warnings": [],
    }
