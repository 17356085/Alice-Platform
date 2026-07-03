"""Observation Bus — 轻量级事件总线。

Week 3 Day 3-4: 统一事件流，Memory/Knowledge/UI 等消费者订阅 Agent 观测结果。

用法:
    from aitest.platform.observation_bus import ObservationBus, EventType

    bus = ObservationBus()
    bus.subscribe(EventType.SKILL_COMPLETE, lambda e: memory_store.add(e.data))
    bus.emit(EventType.SKILL_COMPLETE, {"skill_id": "...", "output": "..."})
"""
import time
import logging
from dataclasses import dataclass, field
from typing import Any, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """观测事件类型。"""
    # Agent lifecycle
    SKILL_START = "skill_start"
    SKILL_COMPLETE = "skill_complete"
    SKILL_FAILED = "skill_failed"
    SKILL_RETRY = "skill_retry"
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"

    # Tool calling
    TOOL_CALL_START = "tool_call_start"
    TOOL_CALL_COMPLETE = "tool_call_complete"
    TOOL_CALL_FAILED = "tool_call_failed"

    # Execution
    TEST_PASSED = "test_passed"
    TEST_FAILED = "test_failed"
    EVIDENCE_CAPTURED = "evidence_captured"

    # Memory
    MEMORY_ADDED = "memory_added"
    MEMORY_VERIFIED = "memory_verified"
    MEMORY_DECAYED = "memory_decayed"

    # Security
    SECURITY_BLOCKED = "security_blocked"
    PROMPT_INJECTION_DETECTED = "prompt_injection_detected"

    # System
    CONTEXT_WINDOW_WARN = "context_window_warn"
    CONTEXT_WINDOW_CONTINUE = "context_window_continue"
    PROVIDER_FALLBACK = "provider_fallback"
    PROVIDER_RETRY = "provider_retry"


@dataclass
class ObservationEvent:
    """观测事件实体。"""
    type: EventType
    data: dict = field(default_factory=dict)
    agent_name: str = ""
    module: str = ""
    page: str = ""
    timestamp: float = field(default_factory=lambda: time.time())


class ObservationBus:
    """轻量级事件总线。

    - 内存中的发布-订阅模式
    - 每个 EventType 可以有多个订阅者
    - 同步执行（消费者不应阻塞太久）
    """

    def __init__(self):
        self._subscribers: dict[EventType, list[Callable]] = {}
        self._history: list[ObservationEvent] = []
        self._max_history = 1000

    def subscribe(self, event_type: EventType, callback: Callable[[ObservationEvent], None]) -> None:
        """订阅事件。"""
        self._subscribers.setdefault(event_type, []).append(callback)

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """取消订阅。"""
        subs = self._subscribers.get(event_type, [])
        if callback in subs:
            subs.remove(callback)

    def emit(
        self,
        event_type: EventType,
        data: dict = None,
        agent_name: str = "",
        module: str = "",
        page: str = "",
    ) -> None:
        """发射事件。同步通知所有订阅者。"""
        event = ObservationEvent(
            type=event_type,
            data=data or {},
            agent_name=agent_name,
            module=module,
            page=page,
        )

        # 记录历史
        self._history.append(event)
        if len(self._history) > self._max_history:
            self._history = self._history[-self._max_history:]

        # 通知订阅者
        subs = self._subscribers.get(event_type, [])
        for callback in subs:
            try:
                callback(event)
            except Exception as e:
                logger.warning(f"Event handler failed for {event_type.value}: {e}")

    def history(self, event_type: EventType = None, limit: int = 50) -> list[ObservationEvent]:
        """获取事件历史。"""
        events = self._history
        if event_type:
            events = [e for e in events if e.type == event_type]
        return events[-limit:]

    def clear_history(self) -> None:
        self._history.clear()

    def subscriber_count(self) -> int:
        return sum(len(v) for v in self._subscribers.values())


# ══════════════════════════════════════════════════════════════════════════
#  全局单例
# ══════════════════════════════════════════════════════════════════════════

_bus: ObservationBus = None
_bus_lock = __import__('threading').Lock()


def get_bus() -> ObservationBus:
    """Get the global ObservationBus singleton. Creates one on first call."""
    global _bus
    with _bus_lock:
        if _bus is None:
            _bus = ObservationBus()
        return _bus


def set_bus(bus: ObservationBus) -> None:
    """Inject a custom ObservationBus instance (for testing or plugin replacement)."""
    global _bus
    with _bus_lock:
        _bus = bus


def reset_bus() -> None:
    """Reset to default singleton (next get_bus() creates a fresh instance)."""
    global _bus
    with _bus_lock:
        _bus = None


# ══════════════════════════════════════════════════════════════════════════
#  预置 Consumer: Memory Sync (delegated to memory_consumer.py)
# ══════════════════════════════════════════════════════════════════════════

def register_memory_consumer(store=None):
    """注册 Memory 消费者：自动将观测事件写入 TestingMemoryStore。

    .. deprecated::
        Use ``from aitest.platform.memory_consumer import register_memory_consumer``
        directly. This wrapper exists for backward compatibility.
    """
    from aitest.platform.memory_consumer import register_memory_consumer as _register
    _register(store=store, bus=get_bus())

    logger.info("Memory consumer registered on ObservationBus")


# ══════════════════════════════════════════════════════════════════════════
#  PlatformBridge — forward ObservationEvents to platform EventBus (v3.0)
# ══════════════════════════════════════════════════════════════════════════

# Mapping: ObservationBus EventType → platform RunEvent event_type
_OBSERVATION_TO_PLATFORM: dict[EventType, str] = {
    EventType.SKILL_START: "observation.skill_start",
    EventType.SKILL_COMPLETE: "observation.skill_complete",
    EventType.SKILL_FAILED: "observation.skill_failed",
    EventType.SKILL_RETRY: "observation.skill_retry",
    EventType.AGENT_START: "observation.agent_start",
    EventType.AGENT_COMPLETE: "observation.agent_complete",
    EventType.TOOL_CALL_START: "observation.tool_call_start",
    EventType.TOOL_CALL_COMPLETE: "observation.tool_call_complete",
    EventType.TOOL_CALL_FAILED: "observation.tool_call_failed",
    EventType.TEST_PASSED: "observation.test_passed",
    EventType.TEST_FAILED: "observation.test_failed",
    EventType.EVIDENCE_CAPTURED: "observation.evidence_captured",
    EventType.MEMORY_ADDED: "observation.memory_added",
    EventType.MEMORY_VERIFIED: "observation.memory_verified",
    EventType.MEMORY_DECAYED: "observation.memory_decayed",
    EventType.SECURITY_BLOCKED: "observation.security_blocked",
    EventType.PROMPT_INJECTION_DETECTED: "observation.prompt_injection_detected",
    EventType.CONTEXT_WINDOW_WARN: "observation.context_window_warn",
    EventType.CONTEXT_WINDOW_CONTINUE: "observation.context_window_continue",
    EventType.PROVIDER_FALLBACK: "observation.provider_fallback",
    EventType.PROVIDER_RETRY: "observation.provider_retry",
}


class PlatformBridge:
    """Forwards ObservationEvents to the platform EventBus as RunEvents.

    This unifies the two event bus systems:
      - ObservationBus (Agent-level: skill_start, tool_call, test_failed)
      - EventBus (Platform-level: run.completed, billing, audit)

    After this bridge, platform consumers (AuditLogger, WebhookDispatcher,
    MetricsConsumer) can observe agent-level events without importing
    ObservationBus directly.

    Usage:
        bridge = PlatformBridge()
        bridge.start()   # subscribes to all ObservationEvent types
        bridge.stop()    # unsubscribes
    """

    def __init__(self, obs_bus=None, platform_bus=None):
        self._active = False
        self._obs_bus = obs_bus
        self._platform_bus = platform_bus

    def start(self) -> None:
        if self._active:
            return
        from aitest.platform.observation_bus import get_bus as get_obs_bus
        from aitest.platform.event_bus import get_bus as get_platform_bus

        obs = self._obs_bus or get_obs_bus()
        platform = self._platform_bus or get_platform_bus()

        for obs_type, platform_type in _OBSERVATION_TO_PLATFORM.items():
            obs.subscribe(obs_type, self._make_forwarder(platform, platform_type))

        self._active = True
        logger.info(f"PlatformBridge started, forwarding {len(_OBSERVATION_TO_PLATFORM)} event types")

    def stop(self) -> None:
        self._active = False
        logger.info("PlatformBridge stopped")

    @property
    def is_active(self) -> bool:
        return self._active

    @staticmethod
    def _make_forwarder(platform_bus, event_type: str):
        """Create a forwarder function for a specific event type."""
        import uuid as _uuid
        from aitest.platform.run_event import RunEvent

        def forwarder(obs_event):
            try:
                run_event = RunEvent(
                    event_id=str(_uuid.uuid4()),
                    event_type=event_type,
                    run_id=obs_event.data.get("run_id", ""),
                    request_id="",
                    data={
                        **obs_event.data,
                        "agent_name": obs_event.agent_name,
                        "module": obs_event.module,
                        "page": obs_event.page,
                        "_source": "observation_bus",
                    },
                )
                platform_bus.publish(run_event)
            except Exception as e:
                logger.warning(f"PlatformBridge forward failed for {event_type}: {e}")

        return forwarder


_bridge: PlatformBridge | None = None
_bridge_lock = __import__('threading').Lock()


def get_platform_bridge() -> PlatformBridge:
    """Get the global PlatformBridge singleton."""
    global _bridge
    with _bridge_lock:
        if _bridge is None:
            _bridge = PlatformBridge()
        return _bridge
