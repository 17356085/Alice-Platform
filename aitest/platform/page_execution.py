"""Deterministic execution of persisted page action plans.

The page DSL is deliberately provider-neutral.  When a runtime exposes its
underlying Playwright-compatible page (including the CDP runtime), actions
are executed directly against locators; no LLM is involved in the action
semantics.  A runtime without a direct page falls back to its legacy Runtime
methods for the actions those methods can safely represent.
"""

from __future__ import annotations

import asyncio
import inspect
import time
from dataclasses import dataclass, field
from typing import Any

from .page_config import PageAction, PageConfig


class PageExecutionError(RuntimeError):
    """Raised when a page action cannot be completed."""


@dataclass
class PageExecutionResult:
    page_id: str
    attempts: int = 0
    actions: list[dict[str, Any]] = field(default_factory=list)
    screenshots: list[bytes] = field(default_factory=list)

    @property
    def completed(self) -> int:
        return sum(item.get("status") == "completed" for item in self.actions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "page_id": self.page_id,
            "attempts": self.attempts,
            "completed": self.completed,
            "actions": list(self.actions),
            "screenshot_count": len(self.screenshots),
        }


class _BrowserUseLocator:
    """Small locator facade over browser-use's CDP Element API."""

    def __init__(
        self,
        page: Any,
        css: str,
        text: str | None = None,
        xpath: str | None = None,
    ):
        self._page = page
        self._css = css
        self._text = text
        self._xpath = xpath

    async def _element(self, timeout: int | None = None) -> Any:
        deadline = time.monotonic() + (timeout or 30000) / 1000
        while True:
            if self._xpath:
                await self._page.evaluate(
                    """(xpath) => {
                        const marker = 'data-aitest-runtime-target';
                        document.querySelectorAll(`[${marker}]`).forEach((node) => node.removeAttribute(marker));
                        const result = document.evaluate(
                            xpath, document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null
                        ).singleNodeValue;
                        if (result && result.nodeType === Node.ELEMENT_NODE) {
                            result.setAttribute(marker, '1');
                            return true;
                        }
                        return false;
                    }""",
                    self._xpath,
                )
                elements = await self._page.get_elements_by_css_selector(
                    "[data-aitest-runtime-target='1']"
                )
            elif self._text:
                await self._page.evaluate(
                    """(args) => {
                        const [selector, text] = args;
                        const marker = 'data-aitest-runtime-target';
                        const nodes = Array.from(document.querySelectorAll(selector));
                        nodes.forEach((node) => node.removeAttribute(marker));
                        const match = nodes.find((node) => (node.textContent || '').trim() === text);
                        if (match) match.setAttribute(marker, '1');
                        return Boolean(match);
                    }""",
                    [self._css, self._text],
                )
                # The source selector may be a comma-separated list; append
                # no suffix to it because that would filter only its final
                # branch. The marker is unique for this short-lived lookup.
                elements = await self._page.get_elements_by_css_selector(
                    "[data-aitest-runtime-target='1']"
                )
            else:
                elements = await self._page.get_elements_by_css_selector(self._css)
            if elements:
                return elements[0]
            if time.monotonic() >= deadline:
                raise PageExecutionError(f"locator not found: {self._css}")
            await asyncio.sleep(0.1)

    async def wait_for(self, state: str = "visible", timeout: int | None = None, **_: Any) -> None:
        if state not in {"visible", "attached"}:
            raise PageExecutionError(f"browser-use runtime does not support wait state {state!r}")
        await self._element(timeout)

    async def click(self, timeout: int | None = None, **_: Any) -> None:
        await (await self._element(timeout)).click()

    async def fill(self, value: str, timeout: int | None = None, **_: Any) -> None:
        await (await self._element(timeout)).fill(value)

    async def select_option(self, value: str, timeout: int | None = None, **_: Any) -> None:
        await (await self._element(timeout)).select_option(value)

    async def press(self, key: str, timeout: int | None = None, **_: Any) -> None:
        element = await self._element(timeout)
        if hasattr(element, "focus"):
            await element.focus()
        await self._page.press(key)


async def execute_page_config(
    runtime: Any,
    page_config: PageConfig | dict[str, Any],
) -> PageExecutionResult:
    """Execute one persisted page config against a BrowserRuntime-like object.

    ``retry`` retries the whole declarative plan because the DSL does not
    promise transactionality for side-effecting browser actions.  Callers
    should therefore use idempotent setup actions when enabling retries.
    """
    config = page_config if isinstance(page_config, PageConfig) else PageConfig.model_validate(page_config)
    result = PageExecutionResult(page_id=config.page_id)
    retries = config.execution.retry
    for attempt in range(retries + 1):
        result.attempts = attempt + 1
        result.actions.clear()
        result.screenshots.clear()
        try:
            page = await _get_direct_page(runtime)
            if config.url and not any(action.action == "goto" for action in config.execution.actions):
                await _navigate(runtime, page, config.url, config.execution.navigation_timeout_ms)
            for locator_name in config.execution.wait_for:
                await _wait_for(runtime, page, _resolve_locator(config, locator_name), config.execution.action_timeout_ms)
                result.actions.append({"action": "wait_for", "target": locator_name, "status": "completed"})
            for action in config.execution.actions:
                await _execute_action(runtime, page, config, action, result)
            return result
        except Exception as exc:
            if attempt >= retries:
                raise PageExecutionError(
                    f"page '{config.page_id}' failed on attempt {attempt + 1}: {exc}"
                ) from exc
            await asyncio.sleep(min(1.0, 0.1 * (attempt + 1)))
    raise AssertionError("unreachable")


async def _get_direct_page(runtime: Any) -> Any | None:
    """Get the Playwright-compatible page from Remote/BrowserRuntime."""
    page = getattr(runtime, "_page", None)
    if page is not None:
        return page

    ensure_connected = getattr(runtime, "_ensure_connected", None)
    if callable(ensure_connected):
        await ensure_connected()
        page = getattr(runtime, "_page", None)
        if page is not None:
            return page

    ensure_driver = getattr(runtime, "_ensure_driver", None)
    if callable(ensure_driver):
        ensure_driver()
        driver = getattr(runtime, "_driver", None)
        if driver is not None:
            start = getattr(driver, "start", None)
            if callable(start):
                await start()
            browser = getattr(driver, "_browser", None)
            get_page = getattr(browser, "get_current_page", None)
            if callable(get_page):
                return await get_page()
    return None


def _resolve_locator(config: PageConfig, target: str | None) -> str | dict[str, Any]:
    if not target:
        raise PageExecutionError("action target is required")
    return config.locators.get(target, target)


def _locator(page: Any, target: str | dict[str, Any]) -> Any:
    if hasattr(page, "get_elements_by_css_selector") and not hasattr(page, "locator"):
        if isinstance(target, str):
            return _BrowserUseLocator(page, target)
        strategy = target.get("strategy", "css")
        value = target.get("value", "")
        css_by_strategy = {
            "css": value,
            "id": f"#{value}",
            "name": f"[name='{value}']",
            "testid": f"[data-testid='{value}']",
            "role": f"[role='{value}']",
            "link_text": f"a[href]",  # browser-use CDP has no text locator; use explicit CSS when needed
        }
        if strategy == "xpath":
            return _BrowserUseLocator(page, "", xpath=value)
        if strategy in {"text", "link_text"}:
            selector = "button, a, [role='button'], [role='link']"
            return _BrowserUseLocator(page, selector, text=value)
        if strategy not in css_by_strategy or not css_by_strategy[strategy]:
            raise PageExecutionError(f"unsupported browser-use locator strategy: {strategy}")
        return _BrowserUseLocator(page, css_by_strategy[strategy])
    if not hasattr(page, "locator"):
        raise PageExecutionError("runtime page does not expose locator()")
    if isinstance(target, str):
        return page.locator(target)
    strategy = target.get("strategy", "css")
    value = target.get("value", "")
    if strategy == "css":
        return page.locator(value)
    if strategy == "xpath":
        return page.locator(f"xpath={value}")
    if strategy == "text":
        return page.get_by_text(value) if hasattr(page, "get_by_text") else page.locator(f"text={value}")
    if strategy == "role":
        return page.get_by_role(value) if hasattr(page, "get_by_role") else page.locator(f"[role='{value}']")
    if strategy == "testid":
        return page.get_by_test_id(value) if hasattr(page, "get_by_test_id") else page.locator(f"[data-testid='{value}']")
    if strategy == "id":
        return page.locator(f"#{value}")
    if strategy == "name":
        return page.locator(f"[name='{value}']")
    if strategy == "link_text":
        return page.get_by_role("link", name=value) if hasattr(page, "get_by_role") else page.locator(f"a:has-text('{value}')")
    raise PageExecutionError(f"unsupported locator strategy: {strategy}")


async def _call(method: Any, *args: Any, timeout_ms: int | None = None, **kwargs: Any) -> Any:
    if timeout_ms is not None:
        try:
            value = method(*args, timeout=timeout_ms, **kwargs)
        except TypeError:
            value = method(*args, **kwargs)
    else:
        value = method(*args, **kwargs)
    return await value if inspect.isawaitable(value) else value


async def _navigate(runtime: Any, page: Any | None, target: str, timeout_ms: int) -> None:
    if page is not None and hasattr(page, "goto"):
        try:
            await page.goto(target, timeout=timeout_ms, wait_until="domcontentloaded")
        except TypeError:
            # browser-use's CDP Page.goto intentionally only accepts the URL.
            await page.goto(target)
        return
    navigate = getattr(runtime, "navigate", None)
    if not callable(navigate):
        raise PageExecutionError("runtime does not support navigation")
    try:
        await _call(navigate, target, timeout_ms=timeout_ms)
    except TypeError:
        await _call(navigate, target)


async def _wait_for(runtime: Any, page: Any | None, target: str | dict[str, Any], timeout_ms: int) -> None:
    if page is not None:
        locator = _locator(page, target)
        if hasattr(locator, "wait_for"):
            await _call(locator.wait_for, state="visible", timeout_ms=timeout_ms)
            return
    raise PageExecutionError(f"runtime cannot deterministically wait for locator {target!r}")


async def _execute_action(
    runtime: Any,
    page: Any | None,
    config: PageConfig,
    action: PageAction,
    result: PageExecutionResult,
) -> None:
    target = _resolve_locator(config, action.target) if action.target else None
    if action.action == "goto":
        await _navigate(runtime, page, action.value or "", action.timeout_ms)
    elif page is not None and target is not None:
        locator = _locator(page, target)
        if action.action == "click":
            await _call(locator.click, timeout_ms=action.timeout_ms)
        elif action.action == "fill":
            await _call(locator.fill, action.value or "", timeout_ms=action.timeout_ms)
        elif action.action == "select":
            if not hasattr(locator, "select_option"):
                raise PageExecutionError("locator does not support select_option")
            await _call(locator.select_option, action.value or "", timeout_ms=action.timeout_ms)
        elif action.action == "press":
            await _call(locator.press, action.value or "", timeout_ms=action.timeout_ms)
        elif action.action == "wait_for":
            await _wait_for(runtime, page, target, action.timeout_ms)
        else:
            raise PageExecutionError(f"unsupported page action: {action.action}")
    elif action.action == "wait":
        await asyncio.sleep(max(0.0, float(action.value or action.timeout_ms / 1000)))
    elif action.action == "screenshot":
        screenshot = await runtime.screenshot()
        if screenshot:
            result.screenshots.append(screenshot)
    else:
        raise PageExecutionError(
            f"runtime has no direct browser page for action '{action.action}'"
        )

    result.actions.append({
        "action": action.action,
        "target": action.target or "",
        "status": "completed",
    })


__all__ = ["PageExecutionError", "PageExecutionResult", "execute_page_config"]
