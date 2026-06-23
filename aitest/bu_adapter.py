# -*- coding: utf-8 -*-
"""BrowserUse Skill Adapter — bridge between Skills/Fixtures and BrowserUseDriver.

Location: aitest/bu_adapter.py (peer to agent_runner.py per ARCH_REVIEW C2)
Depends: aitest/integrations/bu_driver.py (platform-owned, no ZJSN dependency)

Each public method maps to a Skill or Fixture scenario:
  observe_page_structure  → page-observe Skill (test-design-agent)
  generate_po_suggestions → page-object-generator Skill, browser-use mode
  heal_locator            → bu_heal fixture (conftest teardown hook)

Usage:
    import asyncio
    from aitest.bu_adapter import BrowserUseSkillAdapter

    adapter = BrowserUseSkillAdapter(headless=False)
    result = asyncio.run(adapter.observe_page_structure("#/warehouse/hazard/item"))
"""

import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Optional

from aitest.integrations.bu_driver import BrowserUseDriver

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════
#  Page Structure Schema (for observe_page_structure)
# ═══════════════════════════════════════════════════════════════════

PAGE_STRUCTURE_PROMPT = """
Navigate to #{hash_route}. Wait for the page to fully render.

IMPORTANT — when calling done(), put ONLY this JSON in the text field, nothing else:
{{
  "page_title": "breadcrumb or heading text",
  "search_fields": [
    {{"label": "human-readable label", "type": "input|select|date",
      "html_hint": "placeholder text or CSS class hint"}}
  ],
  "action_buttons": [
    {{"label": "button text", "css_hint": "CSS class or distinguishing attribute"}}
  ],
  "table_columns": ["col1", "col2", ...],
  "has_pagination": true,
  "has_checkbox_column": true
}}

The done() text MUST be exactly the JSON above. No markdown. No summary. No extra words. Just the JSON.
"""

# ═══════════════════════════════════════════════════════════════════
#  PO Suggestion Schema
# ═══════════════════════════════════════════════════════════════════

PO_SUGGESTION_PROMPT = """
Navigate to #{hash_route} and observe the fully rendered page.
This is a Vue 3 + Element Plus application.

For every interactive element (inputs, selects, buttons), find its CSS selector and XPath.
Prefer semantic selectors (input[placeholder*="..."]) over dynamic classes (el-xxx, data-v-xxx).

Output ONLY a JSON array:
[
  {{
    "element_name": "Python snake_case identifier",
    "type": "input|select|button|date_picker",
    "label_hint": "associated label text",
    "css": "recommended CSS selector",
    "xpath": "fallback XPath",
    "confidence": 0.0-1.0
  }}
]

Return ONLY valid JSON. No explanation, no code fences.
"""

# ═══════════════════════════════════════════════════════════════════
#  Heal Locator Prompt
# ═══════════════════════════════════════════════════════════════════

HEAL_LOCATOR_PROMPT = """
You are on page: {page_url}

The test automation script tried to find element "{description}" but the CSS/XPath selector failed.
The page UI may have changed.

Using vision and DOM observation:
1. Find an element that matches the description "{description}"
2. Record its current CSS selector and XPath
3. Click it (to verify it works)

Output ONLY a JSON object:
{{
  "found": true/false,
  "css_selector": "new CSS selector if found",
  "xpath": "new XPath if found",
  "confidence": 0.0-1.0,
  "note": "brief explanation"
}}
"""

# ═══════════════════════════════════════════════════════════════════
#  Adapter
# ═══════════════════════════════════════════════════════════════════


class BrowserUseSkillAdapter:
    """Bridge between governance Skills / pytest fixtures and BrowserUseDriver.

    Each method:
    1. Starts a BrowserUseDriver session (login + navigate)
    2. Runs a BrowserUse Agent with a structured prompt
    3. Parses the output into a typed dict
    4. Closes the browser
    """

    def __init__(
        self,
        headless: bool = True,
        use_vision: bool = True,
        max_steps: int = 15,
    ):
        self.headless = headless
        self.use_vision = use_vision
        self.max_steps = max_steps

    # ── Public API ──────────────────────────────────────────────

    async def observe_page_structure(self, hash_route: str) -> dict:
        """Observe a page and extract its structure.

        Used by: page-observe Skill (test-design-agent)

        Args:
            hash_route: Vue hash route, e.g. "#/warehouse/hazard/item"

        Returns:
            {search_fields, action_buttons, table_columns, has_pagination, error?}
        """
        task = PAGE_STRUCTURE_PROMPT.format(hash_route=hash_route)

        result = await self._run_task(task, hash_route)
        parsed = self._parse_json_output(result)

        if parsed:
            return {
                "search_fields": parsed.get("search_fields", []),
                "action_buttons": parsed.get("action_buttons", []),
                "table_columns": parsed.get("table_columns", []),
                "has_pagination": parsed.get("has_pagination", False),
                "has_checkbox_column": parsed.get("has_checkbox_column", False),
                "page_title": parsed.get("page_title", ""),
            }
        return {"error": "JSON parse failed", "raw": str(result)[:500]}

    async def generate_po_suggestions(self, hash_route: str) -> dict:
        """Generate Page Object locator suggestions for a page.

        Used by: page-object-generator Skill, mode=browser-use

        Args:
            hash_route: Vue hash route

        Returns:
            {class_name, locators: [{element_name, type, css, xpath, confidence}], error?}
        """
        task = PO_SUGGESTION_PROMPT.format(hash_route=hash_route)

        result = await self._run_task(task, hash_route)
        parsed = self._parse_json_output(result)

        if parsed and isinstance(parsed, list):
            # Filter low-confidence suggestions
            locators = [l for l in parsed if l.get("confidence", 0) > 0.6]
            class_name = self._derive_class_name(hash_route)
            return {
                "class_name": class_name,
                "locators": locators,
                "total_found": len(parsed),
                "high_confidence": len(locators),
            }
        return {"error": "JSON parse failed", "raw": str(result)[:500]}

    async def heal_locator(
        self,
        description: str,
        page_url: str,
    ) -> dict:
        """Try to find an element via NL when the CSS selector fails.

        Used by: bu_heal fixture (conftest teardown hook)

        Args:
            description: Human-readable element description, e.g. "the search button"
            page_url: Current page URL/hash

        Returns:
            {found, css_selector, xpath, confidence, note, error?}
        """
        task = HEAL_LOCATOR_PROMPT.format(
            description=description,
            page_url=page_url,
        )

        result = await self._run_task(task, page_url, max_steps_override=8)
        parsed = self._parse_json_output(result)

        if parsed:
            return {
                "found": parsed.get("found", False),
                "css_selector": parsed.get("css_selector"),
                "xpath": parsed.get("xpath"),
                "confidence": parsed.get("confidence", 0),
                "note": parsed.get("note", ""),
            }
        return {
            "found": False,
            "note": f"JSON parse failed: {str(result)[:200]}",
        }

    # ── Internal ────────────────────────────────────────────────

    async def _run_task(
        self,
        task: str,
        hash_route: str,
        max_steps_override: int = None,
    ):
        """Run a BrowserUse task with login + navigation.

        Returns the raw AgentHistoryList object (NOT str).
        Caller should use result.final_result() for output.
        """
        async with BrowserUseDriver(
            headless=self.headless,
            use_vision=self.use_vision,
            max_steps=max_steps_override or self.max_steps,
        ) as bu:
            await bu.login()

            t0 = time.perf_counter()
            result = await bu.run_task(task)
            elapsed = time.perf_counter() - t0

            logger.info(
                "Adapter task done: hash=%s elapsed=%.1fs provider=%s model=%s",
                hash_route, elapsed, bu._provider_name, bu.model,
            )
            return result  # AgentHistoryList, not str

    @staticmethod
    def _parse_json_output(result):
        """Extract JSON from AgentHistoryList result.

        Tries, in order:
        1. result.final_result() — the done() text
        2. result.extracted_content — accumulated content from all steps
        3. str(result) — full string representation
        """
        if result is None:
            return None

        # Path 1: final_result() returns the done() text directly
        try:
            fr = result.final_result()
            if fr and isinstance(fr, str) and fr.strip():
                parsed = BrowserUseSkillAdapter._try_parse_json(fr)
                if parsed:
                    return parsed
        except Exception:
            pass

        # Path 2: extracted_content (MiMo sometimes outputs JSON in step, not done)
        try:
            ec = result.extracted_content()
            if ec and isinstance(ec, str) and ec.strip():
                parsed = BrowserUseSkillAdapter._try_parse_json(ec)
                if parsed:
                    return parsed
        except Exception:
            pass

        # Path 3: full str(result)
        text = str(result)
        return BrowserUseSkillAdapter._try_parse_json(text)

    @staticmethod
    def _try_parse_json(text: str):
        """Try to extract JSON from a string (handles ``` fences, raw objects, raw arrays)."""
        if not text or not text.strip():
            return None

        # ```json ... ``` block
        if "```json" in text:
            try:
                return json.loads(text.split("```json")[1].split("```")[0])
            except (json.JSONDecodeError, IndexError):
                pass

        # ``` ... ``` block
        if "```" in text:
            try:
                return json.loads(text.split("```")[1].split("```")[0])
            except (json.JSONDecodeError, IndexError):
                pass

        # Raw { ... }
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            pass

        # Raw [ ... ]
        try:
            start = text.index("[")
            end = text.rindex("]") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError):
            pass

        # Try parsing entire text as JSON
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass

        return None

    @staticmethod
    def _derive_class_name(hash_route: str) -> str:
        """Derive Page Object class name from hash route.

        e.g. #/warehouse/hazard/item → HazardItemPage
        """
        parts = hash_route.strip("#/").split("/")
        # Take last meaningful segment, capitalize words
        name = parts[-1].replace("-", " ").title().replace(" ", "")
        if len(parts) >= 3:
            # Include module prefix for uniqueness
            module = parts[-2].replace("-", " ").title().replace(" ", "")
            name = module + name
        return name + "Page"
