from types import SimpleNamespace

from aitest.server.core.composition import install_shared_services
from aitest.server.core.dependencies import get_execution_service, get_from_app_state


def _request_with_state(**state):
    return SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(**state)))


def test_get_from_app_state_prefers_shared_instance():
    shared = object()

    resolved = get_from_app_state(_request_with_state(example=shared), "example", object)

    assert resolved is shared


def test_get_execution_service_falls_back_to_factory(monkeypatch):
    created = object()

    monkeypatch.setattr(
        "aitest.platform.execution_service.ExecutionService",
        lambda: created,
    )

    resolved = get_execution_service(_request_with_state())

    assert resolved is created


def test_install_shared_services_populates_app_state(monkeypatch):
    app_state = SimpleNamespace()
    log_messages = []
    logger = SimpleNamespace(info=lambda event, **kwargs: log_messages.append(event))

    monkeypatch.setattr("aitest.platform.execution_service.ExecutionService", lambda: "svc")
    monkeypatch.setattr("aitest.platform.run_store.get_run_store", lambda: "run-store")
    monkeypatch.setattr("aitest.platform.audit_log.get_audit_logger", lambda: "audit")
    monkeypatch.setattr("aitest.platform.hooks.report_consumer.get_report_consumer", lambda: "report")
    monkeypatch.setattr("aitest.platform.hooks.metrics_consumer.get_metrics_consumer", lambda: "metrics")
    monkeypatch.setattr("aitest.platform.hooks.billing_hook.get_billing_hook", lambda: "billing")
    monkeypatch.setattr("aitest.platform.hooks.quota_usage.get_quota_usage", lambda: "quota")
    monkeypatch.setattr("aitest.platform.hooks.webhook.get_webhook_registry", lambda: "webhooks")

    install_shared_services(app_state, logger)

    assert app_state.execution_service == "svc"
    assert app_state.run_store == "run-store"
    assert app_state.audit_logger == "audit"
    assert app_state.report_consumer == "report"
    assert app_state.metrics_consumer == "metrics"
    assert app_state.billing_hook == "billing"
    assert app_state.quota_usage == "quota"
    assert app_state.webhook_registry == "webhooks"
    assert log_messages == ["execution_service_created", "di_instances_stored_in_app_state"]
