"""
Runtime abstraction — Skills never know if it's BrowserUse, Playwright, or API underneath.

Usage:
    rt = ctx.runtime()
    await rt.navigate("#/equipment/device")
    structure = await rt.observe()
    await rt.click("新增按钮")
    await rt.type("设备名称", "测试设备")
    screenshot = await rt.screenshot()
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any


@dataclass
class PageStructure:
    """Standardized page observation result — runtime-agnostic."""
    page_title: str = ""
    search_fields: list[dict] = field(default_factory=list)
    action_buttons: list[dict] = field(default_factory=list)
    table_columns: list[str] = field(default_factory=list)
    has_pagination: bool = False
    has_checkbox_column: bool = False
    raw_html_snapshot: str = ""
    screenshot_base64: str = ""


class Runtime(ABC):
    """
    Abstract execution runtime.

    Skills call runtime.click("新增"), never know if it's BrowserUse, Playwright, or MCP.
    Each project's application.type selects the runtime implementation.

    Capabilities (preferred): use runtime.capabilities[Navigator] for granular access.
    Legacy methods (navigate, observe, click, etc.) still work for backward compat.
    """

    @property
    def capabilities(self):
        """
        Capability registry — preferred way to access runtime features.
        Agent code uses capabilities, not runtime type.

        Usage:
            nav = rt.capabilities[Navigator]
            await nav.goto("#/system/user")
        """
        if not hasattr(self, '_capabilities'):
            self._capabilities = self._build_capabilities()
        return self._capabilities

    def _build_capabilities(self):
        """
        Override in subclasses to register capabilities.
        Default: no capabilities (abstract runtime).
        """
        from .capabilities.abc import CapabilityRegistry
        return CapabilityRegistry()

    @abstractmethod
    async def navigate(self, target: str) -> None:
        """Navigate to a page. target can be URL or hash route."""
        ...

    @abstractmethod
    async def observe(self) -> PageStructure:
        """Observe current page: extract elements, structure, screenshot."""
        ...

    @abstractmethod
    async def click(self, description: str) -> bool:
        """Click an element described in natural language. Returns success."""
        ...

    @abstractmethod
    async def type(self, field_description: str, value: str) -> bool:
        """Type into a field described in natural language. Returns success."""
        ...

    @abstractmethod
    async def screenshot(self) -> bytes:
        """Capture current page screenshot."""
        ...

    @abstractmethod
    async def execute(self, action: str) -> Any:
        """Execute an arbitrary natural-language action. Returns result."""
        ...

    @abstractmethod
    async def login(self, credentials: dict) -> bool:
        """Perform login with given credentials. Returns success."""
        ...

    @abstractmethod
    async def close(self) -> None:
        """Clean up runtime resources."""
        ...

    @property
    @abstractmethod
    def total_tokens(self) -> int: ...

    @property
    @abstractmethod
    def estimated_cost(self) -> float: ...


class BrowserRuntime(Runtime):
    """
    BrowserUse-backed browser runtime.
    Delegates to BrowserUseDriver under the hood.
    """

    def __init__(
        self,
        base_url: str = "",
        headless: bool = True,
        use_vision: bool = True,
        max_steps: int = 15,
        provider: str = None,
        model: str = None,
    ):
        self._base_url = base_url
        self._headless = headless
        self._use_vision = use_vision
        self._max_steps = max_steps
        self._provider = provider
        self._model = model
        self._driver = None
        self._logged_in = False

    def _build_capabilities(self):
        """Register all 4 Browser capability adapters."""
        from .capabilities.browser_adapter import register_browser_capabilities
        return register_browser_capabilities(self)

    def _ensure_driver(self):
        """Lazy-load BrowserUseDriver to avoid import if unused."""
        if self._driver is None:
            from aitest.integrations.bu_driver import BrowserUseDriver
            self._driver = BrowserUseDriver(
                headless=self._headless,
                max_steps=self._max_steps,
                provider=self._provider,
                model=self._model,
                use_vision=self._use_vision,
            )

    async def navigate(self, target: str) -> None:
        self._ensure_driver()
        await self._driver.start()
        if target.startswith("#"):
            await self._driver.navigate_and_observe(target)
        else:
            await self._driver.run_task(f"Navigate to {target}")

    async def observe(self) -> PageStructure:
        self._ensure_driver()
        result = await self._driver.run_task(
            """Observe the current page. Extract:
            1. Page title (breadcrumb or heading)
            2. Search/filter fields (label, type, placeholder)
            3. Action buttons (text, CSS hint)
            4. Table columns (all visible column headers)
            5. Whether pagination exists
            6. Whether checkbox column exists
            Return as JSON."""
        )
        return self._parse_observation(result)

    async def click(self, description: str) -> bool:
        self._ensure_driver()
        try:
            await self._driver.run_task(f"Click on: {description}")
            return True
        except Exception:
            return False

    async def type(self, field_description: str, value: str) -> bool:
        self._ensure_driver()
        try:
            await self._driver.run_task(
                f"Find the input field matching '{field_description}' and type '{value}'"
            )
            return True
        except Exception:
            return False

    async def screenshot(self) -> bytes:
        self._ensure_driver()
        return await self._driver.screenshot() if hasattr(self._driver, 'screenshot') else b""

    async def execute(self, action: str) -> Any:
        self._ensure_driver()
        result = await self._driver.run_task(action)
        return result

    async def login(self, credentials: dict) -> bool:
        self._ensure_driver()
        await self._driver.start()
        username = credentials.get("username", "")
        password = credentials.get("password", "")
        return await self._driver.login(username=username, password=password)

    async def close(self) -> None:
        if self._driver:
            await self._driver.close()
            self._driver = None

    @property
    def total_tokens(self) -> int:
        return self._driver.total_tokens if self._driver else 0

    @property
    def estimated_cost(self) -> float:
        return self._driver.estimated_cost if self._driver else 0.0

    @staticmethod
    def _parse_observation(result) -> PageStructure:
        """Parse BrowserUse result into standardized PageStructure."""
        import json
        import re
        try:
            text = str(result)
            # Try JSON extraction
            match = re.search(r'\{[\s\S]*\}', text)
            if match:
                data = json.loads(match.group())
                return PageStructure(
                    page_title=data.get("page_title", ""),
                    search_fields=data.get("search_fields", []),
                    action_buttons=data.get("action_buttons", []),
                    table_columns=data.get("table_columns", []),
                    has_pagination=data.get("has_pagination", False),
                    has_checkbox_column=data.get("has_checkbox_column", False),
                )
        except (json.JSONDecodeError, AttributeError):
            pass
        return PageStructure(page_title=str(result)[:200])
