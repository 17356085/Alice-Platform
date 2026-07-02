"""Adapters — 外部系统适配器接口。

SDK 定义接口，平台层实现。
"""

from alice_engine.adapters.interfaces import (
    AuditAdapter,
    EventAdapter,
)

__all__ = [
    "AuditAdapter",
    "EventAdapter",
]
