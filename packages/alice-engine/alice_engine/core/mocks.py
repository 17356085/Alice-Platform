"""
Standalone Engine Mock 模块。

替换 Platform 层的重型依赖:
  - EventBus (audit_engine/event_bus.py) → NoopEventBus
  - ErrorLogger (infra/error_logger.py) → 标准 logging
"""

import logging

logger = logging.getLogger(__name__)


class NoopEventBus:
    """空事件总线 — 丢弃所有事件。"""

    def emit(self, event_type: str, **kwargs) -> None:
        logger.debug("Event (noop): %s %s", event_type, kwargs)


def noop__log_error(area: str, action: str, error: Exception,
                   context: dict = None) -> None:
    """简化的错误日志 — 直接使用标准 logging。"""
    logger.error("[%s.%s] %s %s", area, action, error, context or {})
