"""Platform subscriber activation — called from lifespan.
Extracted from main.py (P0-2 split, 2026-06-25).
"""
from __future__ import annotations


async def activate_subscribers(log) -> dict:
    """Activate all platform subscribers. Returns dict of active objects for lifecycle registration."""
    activated: dict[str, object] = {}

    # P1-ACTIVATION: KnowledgeAgentSubscriber
    try:
        from aitest.audit_engine.event_bus import KnowledgeAgentSubscriber
        sub = KnowledgeAgentSubscriber(provider="claude", auto_process=True)
        sub.activate()
        activated["knowledge-agent-subscriber"] = sub
        log.info("governance_subscriber_activated")
    except Exception as e:
        log.error("governance_subscriber_failed", error=str(e))

    # v2.3: AuditLogger
    try:
        from aitest.platform.audit_log import get_audit_logger
        obj = get_audit_logger()
        obj.start()
        activated["audit-logger"] = obj
        log.info("audit_logger_started")
    except Exception as e:
        log.error("audit_logger_failed", error=str(e))

    # v2.4: WebhookDispatcher
    try:
        from aitest.platform.webhook import get_webhook_dispatcher
        obj = get_webhook_dispatcher()
        obj.start()
        activated["webhook-dispatcher"] = obj
        log.info("webhook_dispatcher_started")
    except Exception as e:
        log.error("webhook_dispatcher_failed", error=str(e))

    # v2.4: MetricsConsumer
    try:
        from aitest.platform.metrics_consumer import get_metrics_consumer
        obj = get_metrics_consumer()
        obj.start()
        activated["metrics-consumer"] = obj
        log.info("metrics_consumer_started")
    except Exception as e:
        log.error("metrics_consumer_failed", error=str(e))

    # v2.5: BillingHook
    try:
        from aitest.platform.billing_hook import get_billing_hook
        obj = get_billing_hook()
        obj.start()
        activated["billing-hook"] = obj
        log.info("billing_hook_started")
    except Exception as e:
        log.error("billing_hook_failed", error=str(e))

    # v2.5: QuotaUsage
    try:
        from aitest.platform.quota_usage import get_quota_usage
        obj = get_quota_usage()
        obj.start()
        activated["quota-usage"] = obj
        log.info("quota_usage_started")
    except Exception as e:
        log.error("quota_usage_failed", error=str(e))

    return activated
