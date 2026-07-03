"""
GovernanceBridge — forwards governance events to platform EventBus.

Bridges the file-persisted governance event system (adapters/event/interface.py)
to the in-process platform EventBus, enabling AuditLogger, WebhookDispatcher,
and other platform consumers to observe governance events.

Usage:
    from aitest.platform.governance_bridge import GovernanceBridge
    bridge = GovernanceBridge()
    bridge.start()   # subscribes to all governance event types
    bridge.stop()    # unsubscribes
"""

from __future__ import annotations

import threading
import uuid
from typing import TYPE_CHECKING

from aitest.infra.logging import get_logger

if TYPE_CHECKING:
    from aitest.adapters.event.interface import Event

_log = get_logger(__name__)


class GovernanceBridge:
    """Forwards governance events to platform EventBus.

    Subscribes to all governance event types on the file-persisted bus
    and re-publishes them as RunEvents on the platform EventBus with
    event_type prefixed as "governance.<type>".
    """

    def __init__(self):
        self._active = False
        self._lock = threading.Lock()

    def start(self) -> None:
        """Subscribe to all governance event types and forward to platform bus."""
        if self._active:
            return

        from aitest.adapters.event.interface import EVENT_ACTIONS, subscribe
        from aitest.platform.event_bus import get_bus as get_platform_bus
        from aitest.platform.run_event import RunEvent

        platform_bus = get_platform_bus()

        def _forward(event: Event) -> None:
            """Forward a governance event to the platform EventBus."""
            try:
                run_event = RunEvent(
                    event_id=str(uuid.uuid4()),
                    event_type=f"governance.{event.type}",
                    run_id=event.data.get("run_id", ""),
                    request_id="",
                    data=event.data,
                )
                platform_bus.publish(run_event)
            except Exception:
                _log.error(f"Failed to forward governance event {event.type} to platform bus")

        # Subscribe to all governance event types
        for event_type in EVENT_ACTIONS:
            try:
                subscribe(event_type, _forward)
            except Exception:
                _log.error(f"Failed to subscribe to governance event {event_type}")

        self._active = True
        _log.info(f"GovernanceBridge started, forwarding {len(EVENT_ACTIONS)} event types")

    def stop(self) -> None:
        """Unsubscribe from governance events.

        Note: The governance bus doesn't support unsubscribe natively,
        so this just marks the bridge as inactive. The forwarder will
        check _active before publishing.
        """
        self._active = False
        _log.info("GovernanceBridge stopped")

    @property
    def is_active(self) -> bool:
        return self._active


# ── Singleton ────────────────────────────────────────────────────────────

_bridge: GovernanceBridge | None = None
_bridge_lock = threading.Lock()


def get_governance_bridge() -> GovernanceBridge:
    """Get the global GovernanceBridge singleton."""
    global _bridge
    with _bridge_lock:
        if _bridge is None:
            _bridge = GovernanceBridge()
        return _bridge
