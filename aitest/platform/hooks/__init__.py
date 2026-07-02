"""Platform business policy hooks — v2.4 Governance layer.

These consumers react to RunEvents and enforce business rules:
  - BillingHook:   Token usage → cost computation
  - QuotaUsage:    Track and enforce per-tenant quotas
  - MetricsConsumer: Aggregate operational metrics
  - WebhookDispatcher: Outgoing webhook notifications

Design: Each hook is a RunEventConsumer. They are activated via
server/core/subscribers.py and registered in the health endpoint.

Extracted from aitest/platform/ (P3 boundary cleanup, 2026-06-27).
"""

from aitest.platform.hooks.billing_hook import BillingHookConsumer, get_billing_hook
from aitest.platform.hooks.metrics_consumer import MetricsConsumer, get_metrics_consumer
from aitest.platform.hooks.quota_usage import QuotaUsageConsumer, get_quota_usage
from aitest.platform.hooks.webhook import WebhookDispatcher, WebhookRegistry, get_webhook_dispatcher, get_webhook_registry

__all__ = [
    "BillingHookConsumer", "get_billing_hook",
    "MetricsConsumer", "get_metrics_consumer",
    "QuotaUsageConsumer", "get_quota_usage",
    "WebhookDispatcher", "WebhookRegistry",
    "get_webhook_dispatcher", "get_webhook_registry",
]
