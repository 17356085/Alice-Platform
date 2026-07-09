"""Server composition-root wiring for shared platform services."""

from __future__ import annotations


def install_shared_services(app_state, log) -> None:
    """Populate app.state with shared service instances."""
    from aitest.platform.execution_service import ExecutionService
    from aitest.platform.run_store import get_run_store
    from aitest.platform.audit_log import get_audit_logger
    from aitest.platform.hooks.report_consumer import get_report_consumer
    from aitest.platform.hooks.metrics_consumer import get_metrics_consumer
    from aitest.platform.hooks.billing_hook import get_billing_hook
    from aitest.platform.hooks.quota_usage import get_quota_usage
    from aitest.platform.hooks.webhook import get_webhook_registry

    app_state.execution_service = ExecutionService()
    log.info("execution_service_created")

    app_state.run_store = get_run_store()
    app_state.audit_logger = get_audit_logger()
    app_state.report_consumer = get_report_consumer()
    app_state.metrics_consumer = get_metrics_consumer()
    app_state.billing_hook = get_billing_hook()
    app_state.quota_usage = get_quota_usage()
    app_state.webhook_registry = get_webhook_registry()
    log.info("di_instances_stored_in_app_state")
