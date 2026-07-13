"""Read API coverage for the global Studio resource pages."""

from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_list_runs_returns_persisted_resources(monkeypatch):
    from aitest.server.api.runs import runs_router
    import aitest.platform.run_store as run_store

    run = SimpleNamespace(to_dict=lambda: {"run_id": "run-1", "status": "completed"})
    monkeypatch.setattr(run_store, "get_run_store", lambda: SimpleNamespace(list_runs=lambda **_: [run]))
    app = FastAPI(); app.include_router(runs_router)

    response = TestClient(app).get("/api/v1/runs?status=completed")

    assert response.status_code == 200
    assert response.json() == {"runs": [{"run_id": "run-1", "status": "completed"}], "total": 1}


def test_list_runs_returns_store_total_for_pagination(monkeypatch):
    from aitest.server.api.runs import runs_router
    import aitest.platform.run_store as run_store

    run = SimpleNamespace(to_dict=lambda: {"run_id": "run-11", "status": "completed"})
    store = SimpleNamespace(list_runs=lambda **_: [run], count_runs=lambda **kwargs: 11)
    monkeypatch.setattr(run_store, "get_run_store", lambda: store)
    app = FastAPI(); app.include_router(runs_router)

    response = TestClient(app).get("/api/v1/runs?limit=1&offset=10")

    assert response.status_code == 200
    assert response.json()["total"] == 11


def test_list_evaluations_returns_quality_resources(monkeypatch):
    from aitest.server.api.quality import quality_router
    import aitest.platform.quality_store as quality_store

    evaluation = SimpleNamespace(to_dict=lambda: {"evaluation_id": "eval-1", "status": "completed"})
    store = SimpleNamespace(list_evaluations=lambda **_: [evaluation])
    monkeypatch.setattr(quality_store, "get_quality_store", lambda: store)
    app = FastAPI(); app.include_router(quality_router)

    response = TestClient(app).get("/api/v1/evaluations?status=completed")

    assert response.status_code == 200
    assert response.json() == {"evaluations": [{"evaluation_id": "eval-1", "status": "completed"}], "total": 1}


def test_registry_snapshot_aggregates_existing_resources(monkeypatch):
    from aitest.server.api.registry_v1 import registry_router
    import alice_engine.core.executor as executor
    import aitest.platform.environment_store as environment_store
    import aitest.platform.model_provider_store as provider_store
    import aitest.platform.plugin as plugin
    import aitest.platform.workflow_store as workflow_store

    resource = lambda **data: SimpleNamespace(to_dict=lambda: data)
    monkeypatch.setattr(executor, "AGENT_SKILL_MAP", {"automation-agent": ["automation/page-observe"]})
    monkeypatch.setattr(workflow_store, "get_workflow_store", lambda: SimpleNamespace(list_workflows=lambda **_: [resource(workflow_id="wf-1")]))
    monkeypatch.setattr(provider_store, "get_model_provider_store", lambda: SimpleNamespace(list_providers=lambda **_: [resource(provider_id="provider-1")]))
    monkeypatch.setattr(environment_store, "get_environment_store", lambda: SimpleNamespace(list_environments=lambda **_: [resource(environment_id="env-1")]))
    monkeypatch.setattr(plugin, "get_plugin_manager", lambda: SimpleNamespace(load_all=lambda: {}, get_skills=lambda: {"plugin/skill": "x"}, list_plugins=lambda: []))
    app = FastAPI(); app.include_router(registry_router)

    response = TestClient(app).get("/api/v1/registry")

    assert response.status_code == 200
    payload = response.json()
    assert payload["agents"] == [{"id": "automation-agent", "skills": ["automation/page-observe"]}]
    assert payload["skills"] == ["automation/page-observe", "plugin/skill"]
    assert payload["workflows"] == [{"workflow_id": "wf-1"}]


def test_list_mcp_servers_redacts_environment_values(monkeypatch):
    from aitest.platform.mcp_server_store import MCPServer
    import aitest.server.api.mcp_servers_v1 as mcp_api

    server = MCPServer(
        mcp_server_id="mcp-1", name="Browser", transport_type="stdio",
        command="node", env={"API_KEY": "secret:browser-key"}, tools=["navigate"],
    )
    store = SimpleNamespace(list_mcp_servers=lambda **_: [server])
    monkeypatch.setattr(mcp_api, "_store", lambda: store)
    app = FastAPI(); app.include_router(mcp_api.mcp_servers_router)

    response = TestClient(app).get("/api/v1/mcp-servers")

    assert response.status_code == 200
    payload = response.json()
    assert payload["servers"][0]["env_keys"] == ["API_KEY"]
    assert "env" not in payload["servers"][0]
