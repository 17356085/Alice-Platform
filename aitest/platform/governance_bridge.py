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
from collections.abc import Callable, Mapping

from aitest.infra.logging import get_logger

_log = get_logger(__name__)

# The composition root injects the governance event source. This keeps the
# platform layer independent from the adapter implementation.
_event_actions: Mapping[str, object] | None = None
_subscribe: Callable | None = None


def register_governance_source(
    event_actions: Mapping[str, object],
    subscribe: Callable,
) -> None:
    """Inject the file-backed governance bus before starting the bridge."""
    global _event_actions, _subscribe
    _event_actions = event_actions
    _subscribe = subscribe


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

        if _event_actions is None or _subscribe is None:
            raise RuntimeError("governance event source is not registered")
        from aitest.platform.event_bus import get_bus as get_platform_bus
        from aitest.platform.runtime_contracts import runtime_event_from_payload, runtime_event_to_run_event

        platform_bus = get_platform_bus()

        def _forward(event) -> None:
            """Forward a governance event to the platform EventBus."""
            try:
                if not self._active:
                    return
                envelope = runtime_event_from_payload(
                    event_type=f"governance.{event.type}",
                    run_id=event.data.get("run_id", ""),
                    request_id="",
                    module=str(event.data.get("module", "")),
                    metadata=dict(event.data),
                )
                run_event = runtime_event_to_run_event(envelope)
                platform_bus.publish(run_event)
            except Exception:
                _log.error(f"Failed to forward governance event {event.type} to platform bus")

        # Subscribe to all governance event types
        for event_type in _event_actions:
            try:
                _subscribe(event_type, _forward)
            except Exception:
                _log.error(f"Failed to subscribe to governance event {event_type}")

        self._active = True
        _log.info(f"GovernanceBridge started, forwarding {len(_event_actions)} event types")

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
