"""Discovery 接口 — 页面发现抽象。

SDK 定义接口，平台层实现具体发现逻辑。

用法:
    from alice_engine.discovery import PageDiscoverer, PageStructure

    class MyDiscoverer(PageDiscoverer):
        def discover(self, url: str) -> PageStructure:
            # 实现页面发现逻辑
            ...
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass
class ComponentInfo:
    """组件信息。"""
    name: str = ""
    selector: str = ""
    type: str = ""  # button, input, table, form, etc.
    text: str = ""
    attributes: dict = field(default_factory=dict)
    children: list["ComponentInfo"] = field(default_factory=list)


@dataclass
class RouteInfo:
    """路由信息。"""
    path: str = ""
    name: str = ""
    component: str = ""
    params: list[str] = field(default_factory=list)
    children: list["RouteInfo"] = field(default_factory=list)


@dataclass
class PageStructure:
    """页面结构。"""
    url: str = ""
    title: str = ""
    framework: str = ""  # vue, react, angular, etc.
    components: list[ComponentInfo] = field(default_factory=list)
    routes: list[RouteInfo] = field(default_factory=list)
    forms: list[dict] = field(default_factory=list)
    tables: list[dict] = field(default_factory=list)
    buttons: list[dict] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)


@runtime_checkable
class PageDiscoverer(Protocol):
    """页面发现接口。

    平台层实现此接口，提供页面结构发现能力。
    """

    def discover(self, url: str, **kwargs) -> PageStructure:
        """发现页面结构。

        Args:
            url: 页面 URL
            **kwargs: 额外参数

        Returns:
            PageStructure
        """
        ...

    def discover_routes(self, url: str, **kwargs) -> list[RouteInfo]:
        """发现路由结构。

        Args:
            url: 应用 URL
            **kwargs: 额外参数

        Returns:
            路由列表
        """
        ...

    def discover_components(self, url: str, **kwargs) -> list[ComponentInfo]:
        """发现页面组件。

        Args:
            url: 页面 URL
            **kwargs: 额外参数

        Returns:
            组件列表
        """
        ...
