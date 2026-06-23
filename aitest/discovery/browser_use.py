"""
BrowserUseDiscovery — AI-driven application structure discovery.

Uses BrowserUse to:
  1. Scan sidebar/menu → menu_tree.json
  2. Expand menu to pages → navigate each → observe elements → pages.json
  3. Optionally generate Page Objects from observations

Supports: Vue hash-router, standard URL, React SPA.
Handles: collapsed menus, dynamic menus, permission-hidden items.

This consolidates what was previously scattered across:
  - page-observe skill
  - sidebar_navigator.py
  - bu_adapter.py page scanning
  - page-object-generator skill (browser-use mode)
"""

import json
import logging
import re
from datetime import datetime
from typing import Optional

from .base import BaseDiscovery, PageRecord, MenuNode, DiscoveryIndex
from aitest.platform.runtime import BrowserRuntime, PageStructure

logger = logging.getLogger(__name__)

# ── LLM Prompts ──────────────────────────────────────────────────────────

MENU_SCAN_PROMPT = """
You are on a web application. Your task is to scan the ENTIRE sidebar/navigation menu.

Steps:
1. Look at the sidebar. Find all top-level menu items.
2. For each item that has children (sub-menu), expand it by clicking.
3. For each sub-item, note the label AND the href/route (e.g. #/system/user or /users).
4. If there are nested sub-menus, expand those too and note all children.
5. Return a COMPLETE JSON array of all menu items.

Return format — ONLY this JSON, nothing else:
[
  {
    "label": "系统管理",
    "type": "menu_group",
    "children": [
      {"label": "用户管理", "route": "#/system/user", "type": "page"},
      {"label": "角色管理", "route": "#/system/role", "type": "page"}
    ]
  }
]

Rules:
- Every leaf item MUST have a "route" field.
- Menu groups (items with children) have type "menu_group".
- Individual page items have type "page".
- If a top-level item has no children and is itself a page, give it type "page" with its route.
- Include ALL visible items. If some are hidden behind scroll, scroll down to find them.
- If the sidebar uses icons without text labels, describe the icon in the label.
"""

PAGE_OBSERVE_PROMPT = """
Navigate to the page with route: {route}

Wait for the page to fully render. Then observe and extract:

1. Page title (breadcrumb text or main heading)
2. All search/filter fields:
   - label (human-readable)
   - type (input | select | date | cascader)
   - html_hint (placeholder text, CSS class, or distinguishing attribute)
3. All action buttons:
   - label (button text)
   - css_hint (CSS class or distinguishing attribute)
4. All table column headers (if a table exists)
5. Whether pagination controls exist (true/false)
6. Whether a checkbox/selection column exists (true/false)

Return ONLY this JSON, nothing else:
{{
  "page_title": "...",
  "search_fields": [{{"label": "...", "type": "...", "html_hint": "..."}}],
  "action_buttons": [{{"label": "...", "css_hint": "..."}}],
  "table_columns": ["col1", "col2"],
  "has_pagination": true,
  "has_checkbox_column": false
}}
"""


class BrowserUseDiscovery(BaseDiscovery):
    """
    BrowserUse-based application discovery.

    Uses LLM-driven browser automation to scan menus and observe pages.
    Requires: BrowserUseDriver available (from ZJSN_Test-master526 or aitest/browser/).

    Usage:
        discovery = BrowserUseDiscovery("my-app", base_url="https://example.com")
        index = await discovery.run_full_discovery()
        print(f"Found {index.total_pages} pages")
    """

    def __init__(
        self,
        project_id: str,
        base_url: str = "",
        credentials: dict = None,
        headless: bool = True,
        provider: str = None,
    ):
        super().__init__(project_id)
        self.base_url = base_url
        self.credentials = credentials or {}
        self.headless = headless
        self.provider = provider
        self._runtime: Optional[BrowserRuntime] = None

    @property
    def runtime(self) -> BrowserRuntime:
        if self._runtime is None:
            self._runtime = BrowserRuntime(
                base_url=self.base_url,
                headless=self.headless,
                provider=self.provider,
            )
        return self._runtime

    # ── Menu Discovery ───────────────────────────────────────────────────

    async def discover_menu(self) -> list[MenuNode]:
        """
        Scan sidebar via BrowserUse → return menu tree.

        1. Navigate to base URL
        2. Login if credentials provided
        3. Execute MENU_SCAN_PROMPT via BrowserUse
        4. Parse JSON result → list[MenuNode]
        """
        rt = self.runtime

        # Login if needed
        if self.credentials:
            logged_in = await rt.login(self.credentials)
            if not logged_in:
                logger.warning(f"Login failed for {self.project_id}")

        # Navigate to base URL
        await rt.navigate(self.base_url)

        # Scan menu via BrowserUse
        result = await rt.execute(MENU_SCAN_PROMPT)
        menu_data = self._parse_menu_json(result)

        return self._dicts_to_menu_nodes(menu_data)

    async def discover_pages(self, menu: list[MenuNode] = None) -> list[PageRecord]:
        """
        Expand menu tree to flat page list.
        If menu not provided, discovers it first.
        """
        if menu is None:
            menu = await self.discover_menu()

        pages = []
        self._flatten_menu(menu, [], pages)
        return pages

    def _flatten_menu(
        self,
        nodes: list[MenuNode],
        path: list[str],
        result: list[PageRecord],
    ):
        """Recursively flatten menu tree to page records."""
        for node in nodes:
            current_path = path + [node.label]
            if node.type == "page" and node.route:
                page_id = self._slugify(node.label)
                result.append(PageRecord(
                    id=page_id,
                    title=node.label,
                    route=node.route,
                    menu_path=current_path,
                    discovered_at=datetime.now().isoformat(),
                ))
            if node.children:
                self._flatten_menu(node.children, current_path, result)

    # ── Page Observation ─────────────────────────────────────────────────

    async def observe_page(self, page: PageRecord) -> PageRecord:
        """
        Navigate to a page and observe its structure.
        Returns enriched PageRecord with elements populated.
        """
        rt = self.runtime

        # Navigate to the page
        target = page.route if page.route.startswith("#") or page.route.startswith("http") else f"{self.base_url}{page.route}"
        await rt.navigate(target)

        # Observe
        prompt = PAGE_OBSERVE_PROMPT.format(route=page.route)
        result = await rt.execute(prompt)
        structure = self._parse_page_json(result)

        page.elements = {
            "search_fields": structure.search_fields,
            "action_buttons": structure.action_buttons,
            "table_columns": structure.table_columns,
            "has_pagination": structure.has_pagination,
            "has_checkbox_column": structure.has_checkbox_column,
        }
        page.raw_dom_snapshot = structure.raw_html_snapshot

        return page

    async def observe_all_pages(self, pages: list[PageRecord]) -> list[PageRecord]:
        """Observe all pages in sequence."""
        results = []
        for i, page in enumerate(pages):
            logger.info(f"Observing page {i+1}/{len(pages)}: {page.title} ({page.route})")
            try:
                observed = await self.observe_page(page)
                results.append(observed)
            except Exception as e:
                logger.error(f"Failed to observe {page.route}: {e}")
                results.append(page)  # Return un-enriched page
        return results

    # ── Full Discovery ───────────────────────────────────────────────────

    async def run_full_discovery(self, observe: bool = True) -> DiscoveryIndex:
        """
        Full discovery: menu → pages → (optional) observe all pages.
        Writes .discovery/pages.json and .discovery/menu_tree.json.
        """
        # 1. Menu
        menu = await self.discover_menu()
        logger.info(f"Discovered menu: {len(menu)} top-level groups")

        # 2. Pages
        pages = await self.discover_pages(menu)
        logger.info(f"Expanded to {len(pages)} pages")

        # 3. Observe (optional — can be expensive in LLM tokens)
        if observe:
            pages = await self.observe_all_pages(pages)

        # 4. Build index and write files
        index = DiscoveryIndex(
            pages=pages,
            menu_tree=menu,
            discovered_at=datetime.now().isoformat(),
            strategy="browser-use",
            total_pages=len(pages),
        )

        # Write to .discovery/
        self._write_discovery_files(pages, menu)

        return index

    def _write_discovery_files(self, pages: list[PageRecord], menu: list[MenuNode]):
        """Write .discovery/ output files via ArtifactStore."""
        from aitest.platform.context import get_project
        ctx = get_project(self.project_id)
        artifacts = ctx.artifacts()

        # pages.json
        pages_data = []
        for p in pages:
            pages_data.append({
                "id": p.id,
                "title": p.title,
                "route": p.route,
                "menu_path": p.menu_path,
                "page_object": p.page_object,
                "discovered_at": p.discovered_at,
                "elements": p.elements,
            })
        artifacts.write_discovery_pages(pages_data)

        # menu_tree.json
        from .base import _serialize_menu
        menu_data = _serialize_menu(menu)
        artifacts.write_discovery_menu(menu_data)

        logger.info(f"Wrote .discovery/ for {self.project_id}: {len(pages_data)} pages, {len(menu_data)} menu groups")

    # ── Cleanup ──────────────────────────────────────────────────────────

    async def close(self):
        if self._runtime:
            await self._runtime.close()
            self._runtime = None

    # ── JSON Parsing ─────────────────────────────────────────────────────

    @staticmethod
    def _parse_menu_json(result) -> list[dict]:
        """Extract menu JSON from BrowserUse result (handles markdown fences, raw JSON, etc.)."""
        text = str(result)
        # Try ```json fence
        match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
        if match:
            text = match.group(1)
        # Try JSON array
        match = re.search(r'\[[\s\S]*\]', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.warning(f"Could not parse menu JSON from result: {text[:200]}")
        return []

    @staticmethod
    def _parse_page_json(result) -> PageStructure:
        """Extract page observation JSON from BrowserUse result."""
        text = str(result)
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                data = json.loads(match.group())
                return PageStructure(
                    page_title=data.get("page_title", ""),
                    search_fields=data.get("search_fields", []),
                    action_buttons=data.get("action_buttons", []),
                    table_columns=data.get("table_columns", []),
                    has_pagination=data.get("has_pagination", False),
                    has_checkbox_column=data.get("has_checkbox_column", False),
                )
            except json.JSONDecodeError:
                pass
        return PageStructure()

    @staticmethod
    def _dicts_to_menu_nodes(data: list[dict]) -> list[MenuNode]:
        """Convert parsed JSON dicts to MenuNode tree."""
        nodes = []
        for item in data:
            children = []
            if item.get("children"):
                children = BrowserUseDiscovery._dicts_to_menu_nodes(item["children"])
            nodes.append(MenuNode(
                label=item.get("label", ""),
                route=item.get("route", ""),
                children=children,
                icon=item.get("icon", ""),
                type=item.get("type", "menu_item"),
            ))
        return nodes

    @staticmethod
    def _slugify(name: str) -> str:
        """Convert Chinese/English label to URL-safe slug."""
        # Simple: lowercase, replace spaces/special chars with hyphens
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[-\s]+', '-', slug)
        return slug.strip('-') or name
