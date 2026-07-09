"""Engine EventBus — bridges to platform EventBus.

v2.5: Unified with platform EventBus via adapter. Engine-level emit() calls
are translated to platform RunEvent objects and published on the same bus
that AuditLogger, BillingHook, MetricsConsumer etc. subscribe to.

The old alice_engine.events.EventBus is still available as _LegacyEventBus
for backward compatibility.
"""

from __future__ import annotations

import threading
from typing import Callable

from aitest.platform.event_bus import get_bus as get_platform_bus
from aitest.platform.runtime_contracts import runtime_event_from_payload, runtime_event_to_run_event


class EngineEventBusAdapter:
    """Adapt engine-level emit(event_type, data) to the RuntimeEventEnvelope projection path.

    This bridges the two EventBus systems:
      Engine:  emit("skill_start", {"skill_id": "foo"})
      Platform: RuntimeEventEnvelope -> RunEvent -> publish(...)
    """

    def __init__(self):
        self._platform_bus = get_platform_bus()
        self._handlers: dict[str, list[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to engine-level events (local handlers, not platform bus)."""
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """Unsubscribe from engine-level events."""
        with self._lock:
            if event_type in self._handlers:
                self._handlers[event_type] = [
                    h for h in self._handlers[event_type] if h != handler
                ]

    def emit(self, event_type: str, data: dict | None = None) -> None:
        """Publish event to both local handlers and platform EventBus.

        Local handlers fire first (for backward compatibility), then the
        event is published to the platform bus as a RunEvent so that
        AuditLogger, BillingHook, etc. can observe engine-level events.
        """
        data = data or {}

        # 1. Fire local handlers (backward compat)
        with self._lock:
            handlers = list(self._handlers.get(event_type, []))

        for handler in handlers:
            try:
                handler(data)
            except Exception:
                pass

        # 2. Publish to platform EventBus as RunEvent
        envelope = runtime_event_from_payload(
            event_type=f"engine.{event_type}",
            run_id=data.get("run_id", ""),
            request_id=data.get("request_id", ""),
            module=str(data.get("module", "")),
            pages=list(data.get("pages", [])) if isinstance(data.get("pages", []), list) else [],
            agent=str(data.get("agent", data.get("agent_name", ""))),
            phase=str(data.get("phase", "")),
            status=str(data.get("status", "")),
            metadata=dict(data),
        )
        run_event = runtime_event_to_run_event(envelope)
        self._platform_bus.publish(run_event)

    def clear(self) -> None:
        """Clear all local handlers."""
        with self._lock:
            self._handlers.clear()


# ── Singleton ────────────────────────────────────────────────────────────

_adapter: EngineEventBusAdapter | None = None
_adapter_lock = threading.Lock()


def get_event_bus() -> EngineEventBusAdapter:
    """Get the global engine EventBus adapter (bridges to platform bus)."""
    global _adapter
    with _adapter_lock:
        if _adapter is None:
            _adapter = EngineEventBusAdapter()
        return _adapter


# Alias — executor.py uses get_bus()
get_bus = get_event_bus

# Backward compat: expose as EventBus for imports like `from aitest.engine.event_bus import EventBus`
EventBus = EngineEventBusAdapter

# Backward compat: expose old EventType enum
from alice_engine.events import EventType  # noqa: F401, E402
