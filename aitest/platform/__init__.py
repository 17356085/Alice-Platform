"""
TLO Platform Kernel — 4 abstractions that define TLO as a platform, not a test framework.

Layers:
  ProjectContext  — unified access to project config, paths, artifacts
  Runtime         — abstract browser/api/miniapp execution (Skills never know what's underneath)
  KnowledgeStore  — vector DB abstraction (project-scoped ChromaDB)
  ArtifactStore   — file-based artifact read/write (SOP_STATUS, page contexts, reports)

Skills NEVER know project directory structure. They call:
  ctx.artifacts().read("pages", page_id, "PAGE_CONTEXT.md")
  ctx.runtime().click("新增")
  ctx.knowledge().search_issues("element not found")

Not:
  GOVERNANCE / "context" / "projects" / "web-automation" / "modules" / module / ...
"""

from .context import ProjectContext, get_project, set_active_project, list_projects
from .runtime import Runtime, BrowserRuntime
from .knowledge import KnowledgeStore
from .artifacts import ArtifactStore

# ★ v2.2 Platform Runtime Foundation
from .run import Run
from .run_event import RunEvent, EventType, make_event
from .event_bus import EventBus, get_bus
from .run_store import RunStore, get_run_store
from .execution_request import ExecutionRequest, RequestStatus
from .execution_service import ExecutionService, ExecutionResult

# ★ v2.3 Platform Observability
from .timeline import build_timeline, timeline_summary
from .audit_log import AuditLogger, get_audit_logger

# ★ v2.4 Platform Governance
from .consumer import RunEventConsumer
from .webhook import WebhookDispatcher, WebhookRegistry, WebhookRegistration, get_webhook_registry, get_webhook_dispatcher
from .metrics_consumer import MetricsConsumer, get_metrics_consumer
from .billing_hook import BillingHookConsumer, get_billing_hook
from .quota_usage import QuotaUsageConsumer, get_quota_usage

# ★ v2.0 Platform Foundation
from .organization import Organization, OrganizationManager, get_org_manager
from .workspace import Workspace, WorkspaceManager, ExecutionContext, get_ws_manager

__all__ = [
    # v1.x
    "ProjectContext",
    "get_project",
    "set_active_project",
    "list_projects",
    "Runtime",
    "BrowserRuntime",
    "KnowledgeStore",
    "ArtifactStore",
    # v2.0
    "Organization",
    "OrganizationManager",
    "get_org_manager",
    "Workspace",
    "WorkspaceManager",
    "ExecutionContext",
    "get_ws_manager",
    # v2.2
    "Run",
    "RunEvent",
    "EventType",
    "make_event",
    "EventBus",
    "get_bus",
    "RunStore",
    "get_run_store",
    "ExecutionRequest",
    "RequestStatus",
    "ExecutionService",
    "ExecutionResult",
    # v2.3
    "build_timeline",
    "timeline_summary",
    "AuditLogger",
    "get_audit_logger",
    # v2.4
    "RunEventConsumer",
    "WebhookDispatcher",
    "WebhookRegistry",
    "WebhookRegistration",
    "get_webhook_registry",
    "get_webhook_dispatcher",
    "MetricsConsumer",
    "get_metrics_consumer",
    "BillingHookConsumer",
    "get_billing_hook",
    "QuotaUsageConsumer",
    "get_quota_usage",
]
