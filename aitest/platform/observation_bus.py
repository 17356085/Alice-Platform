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


def get_bus() -> ObservationBus:
    global _bus
    if _bus is None:
        _bus = ObservationBus()
    return _bus


# ══════════════════════════════════════════════════════════════════════════
#  预置 Consumer: Memory Sync
# ══════════════════════════════════════════════════════════════════════════

def register_memory_consumer(store=None):
    """注册 Memory 消费者：自动将观测事件写入 TestingMemoryStore。"""
    from aitest.platform.testing_memory import (
        LocatorHistoryMemory, KnownBugMemory, HistoricalFailureMemory, MemoryType,
    )
    from aitest.platform.testing_memory_store import TestingMemoryStore

    if store is None:
        try:
            store = TestingMemoryStore()
        except Exception:
            return

    bus = get_bus()

    def on_test_failed(event: ObservationEvent):
        """测试失败 → 记录 HistoricalFailure。"""
        mem = HistoricalFailureMemory(
            content=f"Test failed: {event.data.get('test_name', 'unknown')} | "
                    f"error: {str(event.data.get('error', ''))[:300]}",
            failure_pattern=event.data.get("failure_pattern", ""),
            root_cause=event.data.get("root_cause", ""),
            fix_strategy=event.data.get("fix_strategy", ""),
            failure_count=1,
            module=event.module,
            page=event.page,
        )
        store.add(mem)

    def on_tool_call_failed(event: ObservationEvent):
        """Tool Call 失败 → 记录 KnownBug。"""
        mem = KnownBugMemory(
            content=f"Tool failed: {event.data.get('tool_name', 'unknown')} | "
                    f"error: {str(event.data.get('error', ''))[:300]}",
            bug_description=str(event.data.get('error', ''))[:500],
            workaround=event.data.get("workaround", ""),
            module=event.module,
            page=event.page,
        )
        store.add(mem)

    def on_locator_change(event: ObservationEvent):
        """定位器变更 → 记录 LocatorHistory。"""
        mem = LocatorHistoryMemory(
            element=event.data.get("element", ""),
            stable_locator=event.data.get("new_locator", ""),
            failed_locators=[event.data.get("old_locator", "")] if event.data.get("old_locator") else [],
            module=event.module,
            page=event.page,
        )
        store.add(mem)

    bus.subscribe(EventType.TEST_FAILED, on_test_failed)
    bus.subscribe(EventType.TOOL_CALL_FAILED, on_tool_call_failed)
    logger.info("Memory consumer registered on ObservationBus")
