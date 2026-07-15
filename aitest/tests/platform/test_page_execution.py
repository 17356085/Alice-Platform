"""Contract tests for deterministic persisted page action execution."""

import pytest

from aitest.platform.page_config import PageConfig
from aitest.platform.page_execution import PageExecutionError, execute_page_config


class _Locator:
    def __init__(self, page, selector):
        self.page = page
        self.selector = selector

    async def click(self, **kwargs):
        self.page.calls.append(("click", self.selector, kwargs))

    async def fill(self, value, **kwargs):
        self.page.calls.append(("fill", self.selector, value, kwargs))

    async def select_option(self, value, **kwargs):
        self.page.calls.append(("select", self.selector, value, kwargs))

    async def press(self, value, **kwargs):
        self.page.calls.append(("press", self.selector, value, kwargs))

    async def wait_for(self, **kwargs):
        self.page.calls.append(("wait_for", self.selector, kwargs))


class _Page:
    def __init__(self):
        self.calls = []

    def locator(self, selector):
        self.calls.append(("locator", selector))
        return _Locator(self, selector)

    async def goto(self, target, **kwargs):
        self.calls.append(("goto", target, kwargs))


class _Runtime:
    def __init__(self):
        self._page = _Page()

    async def screenshot(self):
        return b"png"


@pytest.mark.asyncio
async def test_page_execution_resolves_locators_and_runs_actions():
    runtime = _Runtime()
    config = PageConfig.from_payload(
        "login",
        {
            "locators": {
                "username": {"strategy": "id", "value": "username"},
                "submit": {"strategy": "text", "value": "Sign in"},
            },
            "execution": {
                "wait_for": ["username"],
                "actions": [
                    {"action": "fill", "target": "username", "value": "demo"},
                    {"action": "click", "target": "submit"},
                    {"action": "screenshot"},
                ],
            },
        },
    )

    result = await execute_page_config(runtime, config)

    assert result.completed == 4
    assert len(result.screenshots) == 1
    assert ("locator", "#username") in runtime._page.calls
    assert ("locator", "text=Sign in") in runtime._page.calls
    assert any(item[0] == "fill" and item[2] == "demo" for item in runtime._page.calls)


@pytest.mark.asyncio
async def test_page_execution_retries_transient_plan_failure():
    class FlakyLocator(_Locator):
        async def click(self, **kwargs):
            self.page.click_attempts += 1
            if self.page.click_attempts == 1:
                raise RuntimeError("transient")
            await super().click(**kwargs)

    class FlakyPage(_Page):
        def __init__(self):
            super().__init__()
            self.click_attempts = 0

        def locator(self, selector):
            self.calls.append(("locator", selector))
            return FlakyLocator(self, selector)

    runtime = _Runtime()
    runtime._page = FlakyPage()
    config = PageConfig.from_payload(
        "retry",
        {"execution": {"retry": 1, "actions": [{"action": "click", "target": "#submit"}]}},
    )

    result = await execute_page_config(runtime, config)

    assert result.attempts == 2
    assert result.completed == 1


@pytest.mark.asyncio
async def test_page_execution_requires_deterministic_page_for_locator_actions():
    class RuntimeWithoutPage:
        pass

    config = PageConfig.from_payload(
        "missing-runtime",
        {"execution": {"actions": [{"action": "click", "target": "#submit"}]}},
    )
    with pytest.raises(PageExecutionError, match="direct browser page"):
        await execute_page_config(RuntimeWithoutPage(), config)


@pytest.mark.asyncio
async def test_page_execution_supports_browser_use_cdp_page_facade():
    class Element:
        def __init__(self, page, name):
            self.page = page
            self.name = name

        async def click(self):
            self.page.form_visible = True

        async def fill(self, value):
            self.page.value = value

        async def focus(self):
            return None

    class BrowserUsePage:
        def __init__(self):
            self.form_visible = False
            self.value = ""

        async def goto(self, target):
            self.url = target

        async def evaluate(self, _script, _args):
            return "true"

        async def get_elements_by_css_selector(self, selector):
            if "data-aitest-runtime-target" in selector:
                return [Element(self, "workflow")]
            if selector == "input[placeholder='Workflow name']" and self.form_visible:
                return [Element(self, "name")]
            return []

        async def press(self, _key):
            return None

    class BrowserUseRuntime:
        def __init__(self):
            self._page = BrowserUsePage()

        async def screenshot(self):
            return b"png"

    runtime = BrowserUseRuntime()
    config = PageConfig.from_payload(
        "browser-use",
        {
            "locators": {
                "workflow": {"strategy": "xpath", "value": "//button[normalize-space()='Workflow']"},
                "name": {"strategy": "css", "value": "input[placeholder='Workflow name']"},
            },
            "execution": {
                "wait_for": ["workflow"],
                "actions": [
                    {"action": "click", "target": "workflow"},
                    {"action": "fill", "target": "name", "value": "staging"},
                    {"action": "screenshot"},
                ],
            },
        },
    )

    result = await execute_page_config(runtime, config)

    assert result.completed == 4
    assert result.screenshots == [b"png"]
    assert runtime._page.value == "staging"
