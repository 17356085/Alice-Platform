"""
WebhookDispatcher + WebhookRegistry. v2.4

Consumer: subscribes to RunEvent types, POSTs to registered endpoints.
Registry: CRUD for webhook registrations. Persisted to JSON.

Pure consumer. No effect on execution. No new abstractions.

Usage:
    from aitest.platform.webhook import WebhookDispatcher, WebhookRegistry

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

from .consumer import RunEventConsumer
from .run_event import RunEvent, EventType
from .event_bus import get_bus


# ── Registry Data ────────────────────────────────────────────────────────

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


# ── Registry ─────────────────────────────────────────────────────────────

def _registry_path() -> Path:
    base = Path(__file__).resolve().parent.parent.parent
    return base / "governance" / ".data" / "webhooks.json"


class WebhookRegistry:
    """CRUD for webhook registrations. JSON-file backed."""

    def __init__(self):
        self._path = _registry_path()
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._registrations: dict[str, WebhookRegistration] = {}
        self._load()

    def _load(self):
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                self._registrations = {
                    k: WebhookRegistration(**v) for k, v in data.items()
                }
            except Exception:
                pass

    def _save(self):
        data = {k: v.__dict__ for k, v in self._registrations.items()}
        with self._lock:
            self._path.write_text(
                json.dumps(data, ensure_ascii=False, indent=2, default=str),
                encoding="utf-8",
            )

    def register(
        self,
        *,
        workspace_id: str,
        url: str,
        events: list[str],
        secret: str = "",
    ) -> WebhookRegistration:
        import uuid
        wid = str(uuid.uuid4())[:12]
        reg = WebhookRegistration(
            id=wid,
            workspace_id=workspace_id,
            url=url,
            events=events,
            secret=secret,
        )
        with self._lock:
            self._registrations[wid] = reg
        self._save()
        return reg

    def get(self, webhook_id: str) -> Optional[WebhookRegistration]:
        with self._lock:
            return self._registrations.get(webhook_id)

    def list(self, workspace_id: str = "") -> list[WebhookRegistration]:
        with self._lock:
            if workspace_id:
                return [r for r in self._registrations.values()
                        if r.workspace_id == workspace_id]
            return list(self._registrations.values())

    def delete(self, webhook_id: str) -> bool:
        with self._lock:
            if webhook_id in self._registrations:
                del self._registrations[webhook_id]
                self._save()
                return True
        return False

    def find_by_event(self, event_type: str) -> list[WebhookRegistration]:
        """Find all enabled webhooks subscribed to a given event type."""
        with self._lock:
            return [
                r for r in self._registrations.values()
                if r.enabled and event_type in r.events
            ]


# ── Dispatcher ───────────────────────────────────────────────────────────

class WebhookDispatcher:
    """Subscribes to EventBus, delivers matching events to registered webhooks.

    Delivery is best-effort, synchronous, with HMAC-SHA256 signature.
    Future: background thread pool for async delivery.
    """

    def __init__(self, registry: WebhookRegistry | None = None):
        self._registry = registry or WebhookRegistry()
        self._active = False
        self._lock = threading.Lock()

    def start(self):
        """Subscribe to all webhook-relevant event types."""
        if self._active:
            return
        bus = get_bus()
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
            bus.subscribe(t, self._on_event)
        self._active = True

    def stop(self):
        if not self._active:
            return
        bus = get_bus()
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
            with urllib.request.urlopen(req, timeout=10) as resp:
                # 2xx = success
                target.delivery_count += 1
                target.last_delivery_at = datetime.now(timezone.utc).isoformat()
        except Exception:
            target.failure_count += 1
            # Best-effort. Future: retry with backoff.

    @staticmethod
    def _sign(body: bytes, secret: str) -> str:
        if not secret:
            return ""
        mac = hmac.new(secret.encode(), body, hashlib.sha256)
        return f"sha256={mac.hexdigest()}"


# ── Singletons ───────────────────────────────────────────────────────────

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


def get_webhook_dispatcher() -> WebhookDispatcher:
    global _dispatcher
    with _dispatcher_lock:
        if _dispatcher is None:
            _dispatcher = WebhookDispatcher()
        return _dispatcher
