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
    Browser runtime with injectable driver factory.

    Default: BrowserUseDriver (lazy-imported from aitest.integrations.bu_driver).
    Inject alternative: BrowserRuntime(driver_factory=lambda: PlaywrightDriver(...))
    """

    def __init__(
        self,
        base_url: str = "",
        headless: bool = True,
        use_vision: bool = True,
        max_steps: int = 15,
        provider: str = None,
        model: str = None,
        driver_factory: callable = None,  # ★ v1.0: dependency injection
    ):
        self._base_url = base_url
        self._headless = headless
        self._use_vision = use_vision
        self._max_steps = max_steps
        self._provider = provider
        self._model = model
        self._driver_factory = driver_factory  # None = use default BrowserUseDriver
        self._driver = None
        self._logged_in = False

    def _build_capabilities(self):
        """Register all 4 Browser capability adapters."""
        from .capabilities.browser_adapter import register_browser_capabilities
        return register_browser_capabilities(self)

    def _ensure_driver(self):
        """Lazy-load driver — uses injected factory or default BrowserUseDriver."""
        if self._driver is None:
            if self._driver_factory is not None:
                self._driver = self._driver_factory()
            else:
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


class RemoteBrowserRuntime(Runtime):
    """
    Remote browser runtime — connects to a browser via CDP WebSocket.

    Supports:
      - chrome-devtools:// (local Chrome DevTools)
      - ws://host:port/cdp (remote Chrome/Chromium)
      - wss://host:port/cdp (TLS-secured remote browser)
      - Browserbase / Browserless / custom CDP endpoints

    Env vars:
      BROWSER_WS_URL — CDP WebSocket endpoint (required)
      BROWSER_API_KEY — optional API key for cloud services

    Usage:
        rt = RemoteBrowserRuntime("wss://browser.example.com/cdp")
        await rt.navigate("#/system/user")
        await rt.click("新增按钮")
    """

    def __init__(
        self,
        ws_url: str = None,
        api_key: str = None,
        base_url: str = "",
    ):
        from aitest.config import config
        self._ws_url = ws_url or config.browser_ws_url
        self._api_key = api_key or config.browser_api_key
        self._base_url = base_url or config.base_url
        self._browser = None
        self._page = None

    def _build_capabilities(self):
        from .capabilities.browser_adapter import register_browser_capabilities
        return register_browser_capabilities(self)

    async def _ensure_connected(self):
        """Lazy-connect to remote browser via CDP."""
        if self._page is not None:
            return
        if not self._ws_url:
            raise RuntimeError(
                "BROWSER_WS_URL not set. Set env var or pass ws_url to RemoteBrowserRuntime."
            )
        try:
            from playwright.async_api import async_playwright

            pw = await async_playwright().start()
            headers = {}
            if self._api_key:
                headers["x-api-key"] = self._api_key

            self._browser = await pw.chromium.connect_over_cdp(
                self._ws_url,
                headers=headers if headers else None,
            )
            context = self._browser.contexts[0] if self._browser.contexts else await self._browser.new_context()
            self._page = context.pages[0] if context.pages else await context.new_page()

        except ImportError:
            raise RuntimeError(
                "playwright not installed. Install with: pip install playwright"
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to connect to remote browser at {self._ws_url}: {e}"
            )

    async def navigate(self, target: str, wait_until: str = "domcontentloaded", timeout: float = 30_000) -> None:
        """Navigate to a page via CDP.

        Default wait_until="domcontentloaded" because:
        - SUT apps often have persistent WebSocket/SSE connections
        - "networkidle" never fires on such pages → RESULT_CODE_HUNG
        - "domcontentloaded" is reliable: DOM ready, visual elements present

        Pass wait_until="networkidle" only for static pages that need full asset load.
        """
        await self._ensure_connected()
        url = target if target.startswith("http") else f"{self._base_url.rstrip('/')}/#{target.lstrip('#')}"
        try:
            await self._page.goto(url, wait_until=wait_until, timeout=timeout)
        except Exception as e:
            err_msg = str(e)
            # RESULT_CODE_HUNG: browser tab froze or navigation hung.
            # Common on pages with persistent connections (WS/SSE/polling).
            # Fall back to domcontentloaded if we were using a stricter strategy.
            if "RESULT_CODE_HUNG" in err_msg or "timeout" in err_msg.lower():
                if wait_until != "domcontentloaded":
                    from aitest.infra.error_logger import log_error
                    log_error("runtime.navigate", "hung_fallback",
                        RuntimeError(f"Navigation hung with wait_until={wait_until}. "
                                     f"Falling back to domcontentloaded. URL={url}"),
                        severity="warning")
                    await self._page.goto(url, wait_until="domcontentloaded", timeout=timeout)
                else:
                    raise  # Already at minimum wait_until — re-raise
            else:
                raise

    async def observe(self) -> PageStructure:
        await self._ensure_connected()
        title = await self._page.title()
        try:
            search_fields = await self._page.eval_on_selector_all(
                'input[placeholder], .el-input__inner',
                'els => els.map(e => ({placeholder: e.placeholder, type: e.type}))'
            )
        except Exception:
            search_fields = []
        try:
            buttons = await self._page.eval_on_selector_all(
                'button:not([disabled]), .el-button:not(.is-disabled)',
                'els => els.map(e => ({text: e.textContent?.trim() || ""}))'
            )
        except Exception:
            buttons = []
        try:
            columns = await self._page.eval_on_selector_all(
                '.el-table__header th, table th',
                'els => els.map(e => e.textContent?.trim() || "")'
            )
        except Exception:
            columns = []

        return PageStructure(
            page_title=title,
            search_fields=search_fields,
            action_buttons=buttons,
            table_columns=columns,
            has_pagination=False,
            has_checkbox_column=False,
        )

    async def click(self, description: str) -> bool:
        await self._ensure_connected()
        try:
            await self._page.click(f"text={description}")
            return True
        except Exception:
            try:
                await self._page.click(f"[aria-label*='{description}']")
                return True
            except Exception:
                return False

    async def type(self, field_description: str, value: str) -> bool:
        await self._ensure_connected()
        try:
            await self._page.fill(f"[placeholder*='{field_description}']", value)
            return True
        except Exception:
            try:
                await self._page.fill(f"[aria-label*='{field_description}']", value)
                return True
            except Exception:
                return False

    async def screenshot(self) -> bytes:
        await self._ensure_connected()
        return await self._page.screenshot()

    async def execute(self, action: str) -> Any:
        await self._ensure_connected()
        return await self._page.evaluate(action)

    async def login(self, credentials: dict) -> bool:
        await self._ensure_connected()
        try:
            username = credentials.get("username", "")
            password = credentials.get("password", "")
            if username:
                await self._page.fill('input[placeholder*="用户名"], input[placeholder*="账号"]', username)
            if password:
                await self._page.fill('input[type="password"]', password)
            await self._page.click('button:has-text("登录"), button:has-text("登 录")')
            await self._page.wait_for_load_state("networkidle")
            return True
        except Exception:
            return False

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._page = None

    @property
    def total_tokens(self) -> int:
        return 0  # Remote browser doesn't use LLM tokens

    @property
    def estimated_cost(self) -> float:
        return 0.0
