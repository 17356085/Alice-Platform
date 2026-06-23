"""
Capability Interface Layer — thin ABCs for runtime capabilities.

Design:
  - Agent requests capability by name: runtime.capabilities[Navigator]
  - Runtime registers capabilities, not types.
  - Adapters wrap existing runtimes (BrowserUse, Playwright, Selenium).
  - Zero business logic in interfaces.

Usage:
    rt = ctx.runtime()
    nav = rt.capabilities[Navigator]
    await nav.goto("#/system/user")

    obs = rt.capabilities[Observer]
    structure = await obs.snapshot()

    interact = rt.capabilities[Interactor]
    await interact.click("新增按钮")
"""

from .abc import (
    Navigator, Observer, Interactor, Authenticator,
    Capability, CapabilityRegistry,
)
from .browser_adapter import (
    BrowserNavigatorAdapter,
    BrowserObserverAdapter,
    BrowserInteractorAdapter,
    BrowserAuthenticatorAdapter,
)

__all__ = [
    # ABCs
    "Navigator", "Observer", "Interactor", "Authenticator",
    "Capability", "CapabilityRegistry",
    # Browser adapters
    "BrowserNavigatorAdapter", "BrowserObserverAdapter",
    "BrowserInteractorAdapter", "BrowserAuthenticatorAdapter",
]
