"""Run the persisted page DSL against the local web UI with Playwright."""

from __future__ import annotations

import asyncio
import json
import os

from playwright.async_api import async_playwright

from aitest.platform.page_config import PageConfig
from aitest.platform.page_execution import execute_page_config
from aitest.platform.runtime import BrowserRuntime


class _PlaywrightRuntime:
    def __init__(self, page):
        self._page = page

    async def screenshot(self):
        return await self._page.screenshot()


async def _run() -> None:
    if os.environ.get("PAGE_EXECUTION_RUNTIME", "playwright").lower() == "browseruse":
        await _run_browser_runtime()
        return

    browser_path = os.environ.get(
        "E2E_BROWSER_PATH",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    )
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True, executable_path=browser_path)
        page = await browser.new_page()
        config = PageConfig.from_payload(
            "local-alice-workflow",
            {
                "url": "http://127.0.0.1:15173/",
                "locators": {
                    "workflow": {
                        "strategy": "xpath",
                        "value": "//button[.//*[normalize-space()='工作流']]",
                    },
                    "name": {"strategy": "xpath", "value": "//input[@placeholder='工作流名称']"},
                },
                "execution": {
                    "wait_for": ["workflow"],
                    "actions": [
                        {"action": "click", "target": "workflow"},
                        {"action": "fill", "target": "name", "value": "DSL staging"},
                        {"action": "screenshot"},
                    ],
                },
            },
        )
        result = await execute_page_config(_PlaywrightRuntime(page), config)
        name_value = await page.locator("input[placeholder='工作流名称']").input_value()
        print(json.dumps({
            "status": "validated",
            "url": page.url,
            "name_value": name_value,
            **result.to_dict(),
        }, ensure_ascii=False))
        await browser.close()


def _config() -> PageConfig:
    return PageConfig.from_payload(
        "local-alice-workflow",
        {
            "url": "http://127.0.0.1:15173/",
            "locators": {
                "workflow": {
                    "strategy": "xpath",
                    "value": "//button[normalize-space()='工作流']",
                },
                "name": {"strategy": "css", "value": "input[placeholder='工作流名称']"},
            },
            "execution": {
                "wait_for": ["workflow"],
                "actions": [
                    {"action": "click", "target": "workflow"},
                    {"action": "fill", "target": "name", "value": "DSL BrowserUse staging"},
                    {"action": "screenshot"},
                ],
            },
        },
    )


async def _run_browser_runtime() -> None:
    """Exercise the same DSL through the real BrowserUseDriver-backed runtime."""
    runtime = BrowserRuntime(
        base_url="http://127.0.0.1:15173/",
        headless=True,
        use_vision=False,
        provider="mimo",
        model=os.environ.get("MIMO_MODEL", "mimo-v2.5"),
    )
    try:
        result = await execute_page_config(runtime, _config())
        page = await runtime._driver._browser.get_current_page()
        if hasattr(page, "locator"):
            name_value = await page.locator("input[placeholder='工作流名称']").input_value()
        else:
            name_value = await page.evaluate(
                "() => document.querySelector(\"input[placeholder='工作流名称']\")?.value || ''"
            )
        current_url = await page.get_url() if hasattr(page, "get_url") else page.url
        print(json.dumps({
            "status": "validated",
            "runtime": "BrowserRuntime/BrowserUseDriver",
            "url": current_url,
            "name_value": name_value,
            **result.to_dict(),
        }, ensure_ascii=False))
    finally:
        await runtime.close()


if __name__ == "__main__":
    asyncio.run(_run())
