"""Runtime contract and composition-root service ports.

The runtime package owns the abstract execution contract. Platform-specific
page execution and capability adapters are registered by the platform
composition root, keeping this module independent from ``aitest.platform``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any

from aitest.runtime.types import PageStructure

_page_executor: Callable | None = None
_capability_factory: Callable | None = None


def register_page_executor(executor: Callable) -> None:
    """Register the platform-neutral page execution implementation."""
    global _page_executor
    _page_executor = executor


def register_capability_factory(factory: Callable) -> None:
    """Register platform capability adapters for concrete runtimes."""
    global _capability_factory
    _capability_factory = factory


class Runtime(ABC):
    """Abstract browser/API/miniapp execution runtime."""

    @property
    def capabilities(self):
        if not hasattr(self, "_capabilities"):
            self._capabilities = self._build_capabilities()
        return self._capabilities

    async def execute_page_config(self, page_config):
        if _page_executor is None:
            raise RuntimeError("page executor is not registered")
        return await _page_executor(self, page_config)

    def _build_capabilities(self):
        if _capability_factory is None:
            raise RuntimeError("runtime capability factory is not registered")
        return _capability_factory(self)

    @abstractmethod
    async def navigate(self, target: str) -> None:
        ...

    @abstractmethod
    async def observe(self) -> PageStructure:
        ...

    @abstractmethod
    async def click(self, description: str) -> bool:
        ...

    @abstractmethod
    async def type(self, field_description: str, value: str) -> bool:
        ...

    @abstractmethod
    async def screenshot(self) -> bytes:
        ...

    @abstractmethod
    async def execute(self, action: str) -> Any:
        ...

    @abstractmethod
    async def login(self, credentials: dict) -> bool:
        ...

    @abstractmethod
    async def close(self) -> None:
        ...

    @property
    @abstractmethod
    def total_tokens(self) -> int:
        ...

    @property
    @abstractmethod
    def estimated_cost(self) -> float:
        ...


__all__ = [
    "Runtime",
    "PageStructure",
    "register_page_executor",
    "register_capability_factory",
]
