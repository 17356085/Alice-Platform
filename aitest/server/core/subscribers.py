"""Platform subscriber activation — called from lifespan.
Extracted from main.py (P0-2 split, 2026-06-25).
"""
from __future__ import annotations


async def activate_subscribers(log) -> dict:
    """Activate all platform subscribers. Returns dict of active objects for lifecycle registration."""
    activated: dict[str, object] = {}

    # Resolve shared dependencies for injection
    from aitest.platform.run_store import get_run_store
    from aitest.platform.event_bus import get_bus
    store = get_run_store()
    bus = get_bus()

    # P1-ACTIVATION: KnowledgeAgentSubscriber
    try:
        from aitest.audit_engine.event_bus import KnowledgeAgentSubscriber
        sub = KnowledgeAgentSubscriber(auto_process=True)  # provider auto-resolved
        sub.activate()
        activated["knowledge-agent-subscriber"] = sub
        log.info("governance_subscriber_activated")
    except Exception as e:
        import traceback
        log.error("governance_subscriber_failed", error=str(e), traceback=traceback.format_exc()[:300])

    # v2.3: AuditLogger
    try:
        from aitest.platform.audit_log import get_audit_logger
        obj = get_audit_logger(bus=bus)
        obj.start()
        activated["audit-logger"] = obj
        log.info("audit_logger_started")
    except Exception as e:
        log.error("audit_logger_failed", error=str(e))

    # v2.4: WebhookDispatcher
    try:
        from aitest.platform.hooks.webhook import get_webhook_dispatcher
        obj = get_webhook_dispatcher(bus=bus)
        obj.start()
        activated["webhook-dispatcher"] = obj
        log.info("webhook_dispatcher_started")
    except Exception as e:
        log.error("webhook_dispatcher_failed", error=str(e))

    # v2.4: MetricsConsumer
    try:
        from aitest.platform.hooks.metrics_consumer import get_metrics_consumer
        obj = get_metrics_consumer(bus=bus)
        obj.start()
        activated["metrics-consumer"] = obj
        log.info("metrics_consumer_started")
    except Exception as e:
        log.error("metrics_consumer_failed", error=str(e))

    # v2.5: BillingHook
    try:
        from aitest.platform.hooks.billing_hook import get_billing_hook
        obj = get_billing_hook(bus=bus)
        obj.start()
        activated["billing-hook"] = obj
        log.info("billing_hook_started")
    except Exception as e:
        log.error("billing_hook_failed", error=str(e))

    # v2.5: QuotaUsage — v3.1: pure event-driven, no store dependency
    try:
        from aitest.platform.hooks.quota_usage import get_quota_usage
        obj = get_quota_usage(bus=bus)
        obj.start()
        activated["quota-usage"] = obj
        log.info("quota_usage_started")
    except Exception as e:
        log.error("quota_usage_failed", error=str(e))

    # v3: ReportConsumer — AI execution summary
    try:
        from aitest.platform.hooks.report_consumer import get_report_consumer
        obj = get_report_consumer(store=store, bus=bus)
        obj.start()
        activated["report-consumer"] = obj
        log.info("report_consumer_started")
    except Exception as e:
        log.error("report_consumer_failed", error=str(e))

    # v3.1: GovernanceBridge — forward governance events to platform EventBus
    try:
        from aitest.adapters.event.interface import EVENT_ACTIONS, subscribe
        from aitest.platform.governance_bridge import (
            get_governance_bridge,
            register_governance_source,
        )
        register_governance_source(EVENT_ACTIONS, subscribe)
        obj = get_governance_bridge()
        obj.start()
        activated["governance-bridge"] = obj
        log.info("governance_bridge_started")
    except Exception as e:
        log.error("governance_bridge_failed", error=str(e))

    # Register the agent skill runner through the composition root so the
    # platform capability providers do not import the agents layer.
    try:
        from aitest.agents.skill_executor import run_skill
        from aitest.platform.capability_router.providers.codegen import register_skill_runner
        register_skill_runner(run_skill)
        log.info("codegen_skill_runner_registered")
    except Exception as e:
        log.error("codegen_skill_runner_registration_failed", error=str(e))

    # v3.0: PlatformBridge — forward ObservationBus events to platform EventBus
    try:
        from aitest.platform.observation_bus import get_platform_bridge
        obj = get_platform_bridge()
        obj.start()
        activated["platform-bridge"] = obj
        log.info("platform_bridge_started")
    except Exception as e:
        log.error("platform_bridge_failed", error=str(e))

    return activated


async def deactivate_subscribers(activated: dict, log) -> int:
    """Deactivate all platform subscribers. Returns count of stopped objects.

    Calls .stop() / .deactivate() on each active subscriber.
    Best-effort — a failure in one does not prevent the rest from stopping.
    """
    count = 0
    for name, obj in list(activated.items()):
        try:
            if hasattr(obj, "stop"):
                obj.stop()
            elif hasattr(obj, "deactivate"):
                obj.deactivate()
            count += 1
            log.info("subscriber_stopped", name=name)
        except Exception as e:
            log.error("subscriber_stop_failed", name=name, error=str(e))
    return count
