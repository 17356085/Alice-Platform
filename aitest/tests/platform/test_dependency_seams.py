from types import SimpleNamespace

from aitest.platform.capability_router.providers.codegen import (
    PageObjectGenProvider,
)
from aitest.platform.capability_router.router import ToolCall


def test_codegen_provider_uses_injected_skill_runner():
    calls = []

    def runner(**kwargs):
        calls.append(kwargs)
        return SimpleNamespace(finish_reason="stop", content="generated page object")

    result = PageObjectGenProvider().execute(
        ToolCall(
            id="codegen-1",
            name="codegen__page_object",
            arguments={"module": "demo", "page": "home"},
        ),
        {"skill_runner": runner, "provider": "mock"},
    )

    assert result.success is True
    assert calls[0]["skill_id"] == "automation/page-object-generator"
    assert "模块:demo" in calls[0]["user_input"]


def test_dependency_graph_keeps_platform_seams_one_way():
    from tools.check_dependency_graph import build_dependency_report

    report = build_dependency_report()
    edges = {(edge["source"], edge["target"]) for edge in report["edges"]}

    assert ("aitest.platform", "aitest.agents") not in edges
    assert ("aitest.platform", "aitest.adapters") not in edges
    assert ("aitest.runtime", "aitest.platform") not in edges
    assert ("aitest.runtime", "aitest.infra") not in edges
    assert ("aitest.discovery", "aitest.platform") not in edges
    assert ("aitest.testing", "aitest.llm") not in edges
    assert ("aitest.testing", "aitest.audit_engine") not in edges
    assert ("aitest.mcp", "aitest.platform") not in edges
    assert ("aitest.platform", "aitest.llm") not in edges
    assert report["summary"]["largest_scc_size"] == 2


def test_runtime_contract_is_composed_by_platform_without_reverse_imports():
    from aitest.platform.runtime import BrowserRuntime, Runtime
    from aitest.runtime.base import Runtime as RuntimeContract

    assert Runtime is RuntimeContract
    runtime = BrowserRuntime(driver_factory=lambda: None)
    assert runtime.capabilities is not None


def test_discovery_artifacts_use_injected_store_port(monkeypatch):
    from aitest.discovery import base

    calls = []

    class Store:
        def write_discovery_pages(self, pages):
            calls.append(("pages", pages))

        def write_discovery_menu(self, menu):
            calls.append(("menu", menu))

    monkeypatch.setattr(base, "_artifact_store_factory", lambda project_id: Store())

    base.write_discovery_artifacts(
        "demo",
        [base.PageRecord(id="home", title="Home", route="/home")],
        [base.MenuNode(label="Home", route="/home", type="page")],
    )

    assert calls[0][0] == "pages"
    assert calls[0][1][0]["id"] == "home"
    assert calls[1] == ("menu", [{"label": "Home", "route": "/home", "type": "page"}])


def test_testing_ports_are_registered_at_package_composition_root():
    from aitest.audit_engine.event_bus import emit
    from aitest.llm.provider import get_provider
    from aitest.testing import evaluator_judge, regression

    assert evaluator_judge._provider_factory is get_provider
    assert regression._event_sink is emit


def test_mcp_resolvers_are_registered_by_platform_facade():
    from aitest.mcp import database
    from aitest.platform.mcp_server_store import _resolve_environment, _resolve_secret

    assert database._secret_resolver is _resolve_secret
    assert database._environment_resolver is _resolve_environment


def test_complexity_provider_is_registered_at_package_composition_root():
    from aitest.llm.provider import get_provider
    from aitest.platform.complexity import classifier

    assert classifier._provider_factory is get_provider
