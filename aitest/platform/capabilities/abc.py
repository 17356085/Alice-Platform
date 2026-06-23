"""
Capability ABCs — the stable interfaces for runtime capabilities.

These are the platform's extension points. Adding a new Runtime means
implementing these 4 interfaces. Agent code NEVER depends on a specific
runtime type — it requests capabilities by name.

Design:
  - Each Capability is a single-responsibility interface.
  - CapabilityRegistry maps Capability type → implementation instance.
  - Runtime.capabilities returns the registry.
"""

from abc import ABC, abstractmethod
from typing import Any, Type, TypeVar
from dataclasses import dataclass, field

from aitest.platform.runtime import PageStructure

T = TypeVar("T", bound="Capability")


# ══════════════════════════════════════════════════════════════════════════
#  Capability ABCs
# ══════════════════════════════════════════════════════════════════════════

class Capability(ABC):
    """Marker base class for all capabilities."""
    pass


class Navigator(Capability):
    """Navigate to targets: URLs, hash routes, pages."""

    @abstractmethod
    async def goto(self, target: str) -> None:
        """Navigate to a URL or hash route."""
        ...

    @abstractmethod
    async def back(self) -> None:
        """Go back to previous page."""
        ...

    @abstractmethod
    async def refresh(self) -> None:
        """Refresh current page."""
        ...

    @abstractmethod
    async def current_url(self) -> str:
        """Return current page URL."""
        ...


class Observer(Capability):
    """Observe page state: structure, screenshots, DOM, network."""

    @abstractmethod
    async def snapshot(self) -> PageStructure:
        """Capture structured page observation."""
        ...

    @abstractmethod
    async def screenshot(self) -> bytes:
        """Capture full-page screenshot."""
        ...

    @abstractmethod
    async def dom(self) -> str:
        """Return current DOM HTML."""
        ...

    @abstractmethod
    async def console_logs(self) -> list[str]:
        """Return recent browser console logs."""
        ...

    @abstractmethod
    async def network_trace(self) -> list[dict]:
        """Return recent network requests."""
        ...


class Interactor(Capability):
    """Interact with page elements using natural language descriptions."""

    @abstractmethod
    async def click(self, description: str) -> bool:
        """Click element matching natural language description. Returns success."""
        ...

    @abstractmethod
    async def type(self, field: str, value: str) -> bool:
        """Type into field matching description. Returns success."""
        ...

    @abstractmethod
    async def select(self, field: str, value: str) -> bool:
        """Select option in dropdown/select matching description. Returns success."""
        ...

    @abstractmethod
    async def wait(self, condition: str) -> None:
        """Wait for a condition described in natural language."""
        ...

    @abstractmethod
    async def execute(self, action: str) -> Any:
        """Execute arbitrary natural-language action. Returns result."""
        ...


class Authenticator(Capability):
    """Handle authentication flows."""

    @abstractmethod
    async def login(self, credentials: dict) -> bool:
        """Perform login with given credentials. Returns success."""
        ...

    @abstractmethod
    async def logout(self) -> None:
        """Log out current session."""
        ...

    @abstractmethod
    async def is_authenticated(self) -> bool:
        """Check if currently authenticated."""
        ...


# ══════════════════════════════════════════════════════════════════════════
#  Capability Registry
# ══════════════════════════════════════════════════════════════════════════

class CapabilityRegistry:
    """
    Maps Capability type → implementation instance.

    Runtime registers its capabilities. Agent requests by type.

    Usage:
        registry = CapabilityRegistry()
        registry.register(Navigator, BrowserNavigatorAdapter(runtime))
        registry.register(Observer, BrowserObserverAdapter(runtime))

        nav = registry.get(Navigator)
        await nav.goto("#/system/user")
    """

    def __init__(self):
        self._capabilities: dict[Type[Capability], Capability] = {}

    def register(self, capability_type: Type[T], instance: T):
        """Register a capability implementation."""
        if not issubclass(capability_type, Capability):
            raise TypeError(f"{capability_type} must be a Capability subclass")
        self._capabilities[capability_type] = instance

    def get(self, capability_type: Type[T]) -> T:
        """Get a capability by type. Raises KeyError if not registered."""
        if capability_type not in self._capabilities:
            raise KeyError(f"Capability {capability_type.__name__} not registered for this runtime")
        return self._capabilities[capability_type]

    def has(self, capability_type: Type[Capability]) -> bool:
        """Check if a capability is registered."""
        return capability_type in self._capabilities

    def list(self) -> list[str]:
        """List registered capability names."""
        return [t.__name__ for t in self._capabilities]

    def __getitem__(self, capability_type: Type[T]) -> T:
        return self.get(capability_type)

    def __contains__(self, capability_type: Type[Capability]) -> bool:
        return self.has(capability_type)
