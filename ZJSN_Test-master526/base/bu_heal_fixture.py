# -*- coding: utf-8 -*-
"""bu_heal fixture — BrowserUse self-healing for selector failures.

ARCH_REVIEW B1: Does NOT embed in BasePage.click(). Runs as independent
pytest fixture in teardown phase. Zero changes to base_page.py.

ARCH_REVIEW B3: Logs healing suggestions to artifacts/heal_log.jsonl.
Does NOT auto-modify Page Object source files.

ARCH_REVIEW B4: No Event Bus integration. File-based logging only.

Usage (conftest.py):
    from base.bu_heal_fixture import enable_bu_heal
    enable_bu_heal(globals())

Usage (test):
    import pytest
    @pytest.mark.bu_heal
    def test_something(hazard_item_page):
        ...

Lifecycle:
    test runs → fails with NoSuchElementException / TimeoutException
    → teardown phase detects failure
    → if @pytest.mark.bu_heal is set + ENV=dev
    → BrowserUseSkillAdapter.heal_locator() attempts NL-based recovery
    → result logged to artifacts/heal_log.jsonl
"""

import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import pytest

logger = logging.getLogger(__name__)

# ── Config ────────────────────────────────────────────────────────
HEAL_LOG_DIR = Path(__file__).resolve().parent.parent / "artifacts"
HEAL_LOG_FILE = HEAL_LOG_DIR / "heal_log.jsonl"
MAX_HEALS_PER_SESSION = 3

# Global state (reset per session)
_heal_count = 0
_heal_pending: list[dict] = []


def enable_bu_heal(module_globals: dict):
    """Call in conftest.py to register the bu_heal fixture and hooks.

    Usage:
        from base.bu_heal_fixture import enable_bu_heal
        enable_bu_heal(globals())
    """
    # Register the fixture
    module_globals.setdefault("bu_heal", bu_heal)

    # Register hooks
    module_globals.setdefault("pytest_runtest_makereport", pytest_runtest_makereport)


# ── Hook: detect selector failures ─────────────────────────────────

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Detect selector-related failures during test teardown."""
    outcome = yield
    report = outcome.get_result()

    # Only trigger on test call failures (not setup/teardown)
    if report.when != "call" or report.passed:
        return

    # Only if the test has the bu_heal marker
    if not _has_bu_heal_marker(item):
        return

    # Only in dev environment
    if os.getenv("ENV", "test") != "dev":
        return

    # Only for selector-related failures
    if not _is_locator_failure(report):
        return

    # Only if under heal limit
    global _heal_count
    if _heal_count >= MAX_HEALS_PER_SESSION:
        return

    # Queue healing
    _heal_pending.append({
        "nodeid": item.nodeid,
        "exception": str(report.longrepr) if report.longrepr else "",
        "timestamp": datetime.now().isoformat(),
    })


# ── Fixture: runs in teardown ──────────────────────────────────────

@pytest.fixture
def bu_heal(request):
    """Self-healing fixture — yields during test, heals in teardown."""
    yield  # test runs here

    # Process pending heals from this test
    node_id = request.node.nodeid
    pending = [h for h in _heal_pending if h["nodeid"] == node_id]

    if not pending:
        return

    global _heal_count
    for entry in pending:
        if _heal_count >= MAX_HEALS_PER_SESSION:
            break

        _heal_count += 1
        _do_heal(entry)
        _heal_pending.remove(entry)


# ── Healing logic ──────────────────────────────────────────────────

def _do_heal(entry: dict):
    """Execute BrowserUse healing attempt and log result."""
    logger.info("bu_heal: attempting recovery for %s", entry["nodeid"])

    try:
        # Extract element description from the exception
        description = _extract_element_description(entry["exception"])
        page_url = _extract_page_url(entry["nodeid"])

        if not description:
            logger.warning("bu_heal: could not extract element description from failure")
            _log_heal(entry, found=False, note="could not extract element description")
            return

        # Run BrowserUse healing (async in sync context)
        import asyncio
        result = asyncio.run(_run_heal_async(description, page_url))

        _log_heal(
            entry,
            found=result.get("found", False),
            css_selector=result.get("css_selector"),
            xpath=result.get("xpath"),
            confidence=result.get("confidence", 0),
            note=result.get("note", ""),
        )

    except Exception as e:
        logger.error("bu_heal: healing crashed: %s", e)
        _log_heal(entry, found=False, note=str(e)[:200])


async def _run_heal_async(description: str, page_url: str) -> dict:
    """Run BrowserUse heal_locator asynchronously."""
    from aitest.bu_adapter import BrowserUseSkillAdapter

    adapter = BrowserUseSkillAdapter(headless=True, use_vision=True, max_steps=8)
    return await adapter.heal_locator(description, page_url)


def _log_heal(entry: dict, found: bool, **kwargs):
    """Append healing result to JSONL log file."""
    HEAL_LOG_DIR.mkdir(parents=True, exist_ok=True)

    record = {
        **entry,
        "found": found,
        **kwargs,
        "healed_at": datetime.now().isoformat(),
    }

    with open(HEAL_LOG_FILE, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")

    status = "RECOVERED" if found else "FAILED"
    logger.info("bu_heal: %s — %s", status, HEAL_LOG_FILE)


# ── Helpers ────────────────────────────────────────────────────────

def _has_bu_heal_marker(item) -> bool:
    """Check if test has @pytest.mark.bu_heal."""
    return any(m.name == "bu_heal" for m in item.iter_markers())


def _is_locator_failure(report) -> bool:
    """Check if failure is selector-related."""
    longrepr = str(report.longrepr) if report.longrepr else ""

    # Selenium / Playwright selector-related exceptions
    locator_keywords = [
        "NoSuchElementException",
        "ElementClickInterceptedException",
        "StaleElementReferenceException",
        "TimeoutException",
        "element_not_found",
        "not clickable",
        "not found",
    ]
    return any(kw in longrepr for kw in locator_keywords)


def _extract_element_description(exception_text: str) -> str | None:
    """Extract human-readable element description from exception.

    Tries to extract:
    1. Locator tuple text: (By.CSS_SELECTOR, '.search-btn')
    2. Element description from assertion message
    """
    import re

    # Try to find CSS/XPath selector in the exception
    m = re.search(r"selector[=:]\s*['\"]([^'\"]+)", exception_text)
    if m:
        return f"element with selector '{m.group(1)}'"

    # Try to find locator tuple
    m = re.search(r"By\.\w+,\s*['\"]([^'\"]+)", exception_text)
    if m:
        return f"element with selector '{m.group(1)}'"

    # Fallback: use the first line of the exception
    first_line = exception_text.split("\n")[0].strip()
    if len(first_line) > 10:
        return f"element that caused: {first_line[:200]}"

    return None


def _extract_page_url(nodeid: str) -> str:
    """Extract page info from test nodeid."""
    # nodeid format: script/warehouse/test_hazard_item.py::TestClass::test_method
    parts = nodeid.replace("\\", "/").split("::")
    # Return the module path as the page context
    if parts:
        return parts[0]
    return "unknown"


# ── pytest marker registration ─────────────────────────────────────

def pytest_configure(config):
    """Register bu_heal marker."""
    config.addinivalue_line("markers", "bu_heal: enable BrowserUse self-healing on test failure")
