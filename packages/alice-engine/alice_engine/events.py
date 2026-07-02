"""EventBus — 发布/订阅事件系统。"""

import logging
import threading
from enum import Enum
from typing import Any, Callable

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """观测事件类型（SDK 内最小集）。"""
    SKILL_START = "skill_start"
    SKILL_COMPLETE = "skill_complete"
    SKILL_FAILED = "skill_failed"
    SKILL_RETRY = "skill_retry"
    AGENT_START = "agent_start"
    AGENT_COMPLETE = "agent_complete"


class EventBus:
    """线程安全的发布/订阅事件总线。

    用法:
        bus = EventBus()
        bus.subscribe("phase_start", lambda data: print(data))
        bus.emit("phase_start", {"phase": "observe"})
    """

    def __init__(self):
        self._handlers: dict[str, list[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, handler: Callable) -> None:
        """订阅事件。"""
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: Callable) -> None:
        """取消订阅。"""
        with self._lock:
            if event_type in self._handlers:
                self._handlers[event_type] = [
                    h for h in self._handlers[event_type] if h != handler
                ]

    def emit(self, event_type: str, data: dict | None = None) -> None:
        """发布事件（同步调用所有 handler）。"""
        with self._lock:
            handlers = list(self._handlers.get(event_type, []))

        for handler in handlers:
            try:
                handler(data or {})
            except Exception as e:
                logger.warning("EventBus handler error [%s]: %s", event_type, e)

    def clear(self) -> None:
        """清除所有订阅。"""
        with self._lock:
            self._handlers.clear()


# 全局单例
_global_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """获取全局 EventBus 单例。"""
    global _global_bus
    if _global_bus is None:
        _global_bus = EventBus()
    return _global_bus


# 别名 — executor.py 使用 get_bus()
get_bus = get_event_bus
