"""Discovery — 页面发现接口。

SDK 定义接口，平台层实现具体发现逻辑 (Selenium/BrowserUse/Vue 解析)。
"""

from alice_engine.discovery.interfaces import (
    PageDiscoverer,
    PageStructure,
    ComponentInfo,
    RouteInfo,
)

__all__ = [
    "PageDiscoverer",
    "PageStructure",
    "ComponentInfo",
    "RouteInfo",
]
