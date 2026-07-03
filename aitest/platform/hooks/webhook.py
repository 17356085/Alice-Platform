"""
WebhookDispatcher + WebhookRegistry. v3.1

v3.1: WebhookRegistry uses PG instead of JSON file. Multi-process safe.

Consumer: subscribes to RunEvent types, POSTs to registered endpoints.
Registry: CRUD for webhook registrations. Persisted to PG.

Pure consumer. No effect on execution. No new abstractions.

Usage:
    from aitest.platform.hooks.webhook import WebhookDispatcher, WebhookRegistry

    registry = WebhookRegistry()
    registry.register(workspace_id="ws-1", url="https://hooks.example.com/",
                      events=["run.completed", "run.failed"], secret="whsec_...")

    dispatcher = WebhookDispatcher()
    dispatcher.start()   # subscribes to EventBus
"""

from __future__ import annotations

import json
import hashlib
import hmac
import threading
import urllib.request
import urllib.error
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from ..consumer import RunEventConsumer
from ..run_event import RunEvent, EventType
from ..event_bus import get_bus
from ..config_registry import cfg


# ── Registry Data ──────────────────────────────────────────────────────

@dataclass
class WebhookRegistration:
    id: str
    workspace_id: str
    url: str
    events: list[str]                    # EventType values to subscribe to
    secret: str = ""                     # HMAC-SHA256 secret
    enabled: bool = True
    created_at: str = ""
    updated_at: str = ""
    last_delivery_at: str = ""
    delivery_count: int = 0
    failure_count: int = 0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()


# ── Registry (v3.1: PG-backed) ────────────────────────────────────────

class WebhookRegistry:
    """CRUD for webhook registrations. PG-backed. Multi-process safe."""

    def __init__(self):
        self._lock = threading.Lock()

    def register(
        self,
        *,
        workspace_id: str,
        url: str,
        events: list[str],
        secret: str = "",
    ) -> WebhookRegistration:
        import uuid
        from aitest.infra.sql import safe_exec

        wid = str(uuid.uuid4())[:12]
        now = datetime.now(timezone.utc).isoformat()
        reg = WebhookRegistration(
            id=wid, workspace_id=workspace_id, url=url,
            events=events, secret=secret, created_at=now,
        )
        safe_exec(
            "INSERT INTO webhook_registrations "
            "(id, workspace_id, url, events, secret, enabled, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, 1, ?, ?)",
            [wid, workspace_id, url, json.dumps(events, ensure_ascii=False),
             secret, now, now],
        )
        return reg

    def get(self, webhook_id: str) -> Optional[WebhookRegistration]:
        from aitest.infra.sql import safe_query
        rows = safe_query(
            "SELECT * FROM webhook_registrations WHERE id=?", [webhook_id],
        )
        return self._row_to_reg(rows[0]) if rows else None

    def list(self, workspace_id: str = "") -> list[WebhookRegistration]:
        from aitest.infra.sql import safe_query
        if workspace_id:
            rows = safe_query(
                "SELECT * FROM webhook_registrations WHERE workspace_id=? ORDER BY created_at DESC",
                [workspace_id],
            )
        else:
            rows = safe_query(
                "SELECT * FROM webhook_registrations ORDER BY created_at DESC",
            )
        return [self._row_to_reg(r) for r in rows]

    def delete(self, webhook_id: str) -> bool:
        from aitest.infra.sql import safe_exec, safe_query
        rows = safe_query("SELECT id FROM webhook_registrations WHERE id=?", [webhook_id])
        if not rows:
            return False
        safe_exec("DELETE FROM webhook_registrations WHERE id=?", [webhook_id])
        return True

    def find_by_event(self, event_type: str) -> list[WebhookRegistration]:
        """Find all enabled webhooks subscribed to a given event type."""
        from aitest.infra.sql import safe_query
        rows = safe_query(
            "SELECT * FROM webhook_registrations WHERE enabled=1",
        )
        result = []
        for r in rows:
            events = json.loads(r.get("events", "[]"))
            if event_type in events:
                result.append(self._row_to_reg(r))
        return result

    def update_delivery_stats(self, webhook_id: str, success: bool):
        """Update delivery count and last delivery time."""
        from aitest.infra.sql import safe_exec
        now = datetime.now(timezone.utc).isoformat()
        if success:
            safe_exec(
                "UPDATE webhook_registrations SET delivery_count=delivery_count+1, "
                "last_delivery_at=?, updated_at=? WHERE id=?",
                [now, now, webhook_id],
            )
        else:
            safe_exec(
                "UPDATE webhook_registrations SET failure_count=failure_count+1, "
                "last_delivery_at=?, updated_at=? WHERE id=?",
                [now, now, webhook_id],
            )

    @staticmethod
    def _row_to_reg(r: dict) -> WebhookRegistration:
        return WebhookRegistration(
            id=r["id"],
            workspace_id=r["workspace_id"],
            url=r["url"],
            events=json.loads(r.get("events", "[]")),
            secret=r.get("secret", ""),
            enabled=bool(r.get("enabled", 1)),
            created_at=r.get("created_at", ""),
            updated_at=r.get("updated_at", ""),
            last_delivery_at=r.get("last_delivery_at", ""),
            delivery_count=r.get("delivery_count", 0),
            failure_count=r.get("failure_count", 0),
        )


# ── Dispatcher ─────────────────────────────────────────────────────────

class WebhookDispatcher:
    """Subscribes to EventBus, delivers matching events to registered webhooks.

    Delivery is best-effort, synchronous, with HMAC-SHA256 signature.
    v3.1: async via ThreadPoolExecutor (priority=30 >= ASYNC_THRESHOLD).

    Args:
        registry: WebhookRegistry instance. If None, creates a default one.
        bus: EventBus instance. If None, uses get_bus() singleton.
    """

    def __init__(self, registry: WebhookRegistry | None = None, bus=None):
        self._registry = registry or WebhookRegistry()
        self._active = False
        self._lock = threading.Lock()
        self._bus = bus  # injected EventBus (None = lazy singleton)

    def start(self):
        """Subscribe to all webhook-relevant event types."""
        if self._active:
            return
        bus = self._bus or get_bus()
        types = [
            EventType.EXECUTION_REQUESTED,
            EventType.EXECUTION_QUEUED,
            EventType.EXECUTION_STARTED,
            EventType.PHASE_STARTED,
            EventType.PHASE_COMPLETED,
            EventType.ARTIFACT_CREATED,
            EventType.RUN_COMPLETED,
            EventType.RUN_FAILED,
            EventType.RUN_CANCELLED,
            EventType.COST_RECORDED,
        ]
        for t in types:
            bus.subscribe(t, self._on_event, priority=30)  # LOW: external delivery, slow HTTP
        self._active = True

    def stop(self):
        if not self._active:
            return
        bus = self._bus or get_bus()
        types = [
            EventType.EXECUTION_REQUESTED, EventType.EXECUTION_QUEUED,
            EventType.EXECUTION_STARTED, EventType.PHASE_STARTED,
            EventType.PHASE_COMPLETED, EventType.ARTIFACT_CREATED,
            EventType.RUN_COMPLETED, EventType.RUN_FAILED,
            EventType.RUN_CANCELLED, EventType.COST_RECORDED,
        ]
        for t in types:
            bus.unsubscribe(t, self._on_event)
        self._active = False

    @property
    def is_active(self) -> bool:
        return self._active

    def _on_event(self, event: RunEvent):
        """Deliver event to all matching webhooks. Best-effort."""
        targets = self._registry.find_by_event(event.event_type)
        for target in targets:
            self._deliver(target, event)

    def _deliver(self, target: WebhookRegistration, event: RunEvent):
        """POST the event to the webhook endpoint with HMAC signature."""
        body = json.dumps(event.to_dict(), ensure_ascii=False, default=str).encode("utf-8")

        req = urllib.request.Request(
            target.url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Id": target.id,
                "X-Event-Type": event.event_type,
                "X-Webhook-Signature": self._sign(body, target.secret),
            },
        )

        try:
            with urllib.request.urlopen(req, timeout=cfg.webhook_timeout_s) as resp:
                # 2xx = success
                self._registry.update_delivery_stats(target.id, success=True)
        except Exception:
            self._registry.update_delivery_stats(target.id, success=False)

    @staticmethod
    def _sign(body: bytes, secret: str) -> str:
        if not secret:
            return ""
        mac = hmac.new(secret.encode(), body, hashlib.sha256)
        return f"sha256={mac.hexdigest()}"


# ── Singletons ─────────────────────────────────────────────────────────

_registry: WebhookRegistry | None = None
_registry_lock = threading.Lock()


def get_webhook_registry() -> WebhookRegistry:
    global _registry
    with _registry_lock:
        if _registry is None:
            _registry = WebhookRegistry()
        return _registry


_dispatcher: WebhookDispatcher | None = None
_dispatcher_lock = threading.Lock()


def get_webhook_dispatcher(bus=None) -> WebhookDispatcher:
    """Get the global WebhookDispatcher singleton. Creates one on first call."""
    global _dispatcher
    with _dispatcher_lock:
        if _dispatcher is None:
            _dispatcher = WebhookDispatcher(bus=bus)
        return _dispatcher
