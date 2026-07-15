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

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Optional

from .base import (
    BaseDiscovery,
    DiscoveryIndex,
    MenuNode,
    PageRecord,
    write_discovery_artifacts,
)
from aitest.runtime.browser import BrowserRuntime
from aitest.runtime.types import PageStructure

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

FALLBACK_SCAN_PROMPT = """
Observe the ENTIRE page and find ALL navigation elements.

Look for:
1. Sidebar with <nav>, <aside>, or sidebar CSS class
2. Top navigation bar
3. Dropdown menus or collapsible sections
4. Any links or buttons that look like navigation to different sections/pages
5. If the page is a login page or error page, report that.

For EACH navigation item found, extract the label and route/href.

Return ONLY this JSON:
{
  "page_type": "app|login|error|empty",
  "page_title": "...",
  "current_url": "...",
  "menu_items": [
    {"label": "...", "route": "...", "type": "menu_group|page"}
  ],
  "diagnostics": "what you see on the page"
}
"""


class BrowserUseDiscovery(BaseDiscovery):
    """
    BrowserUse-based application discovery.

    Uses LLM-driven browser automation to scan menus and observe pages.
    Requires: BrowserUseDriver available (from ZJSN_Test-master526 or aitest/browser/).

    Usage:
        discovery = BrowserUseDiscovery("my-app", base_url="https://example.com")
        index = await discovery.run_full_discovery()
        logger.info(f"Found {index.total_pages} pages")
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
        Extract sidebar menu tree using JavaScript DOM traversal.

        1. Navigate to base URL
        2. Login if credentials provided
        3. JavaScript: expand all collapsed menu groups + extract tree
        4. Parse JSON → list[MenuNode]
        5. Fallback: LLM-based MENU_SCAN_PROMPT if JS returns nothing
        """
        rt = self.runtime

        # Login if needed (respects _logged_in on driver to avoid re-login)
        if self.credentials and self._runtime and self._runtime._driver:
            if not getattr(self._runtime._driver, '_logged_in', False):
                logged_in = await rt.login(self.credentials)
                if not logged_in:
                    logger.warning(
                        f"Login failed for {self.project_id} — "
                        f"menu discovery will attempt to proceed but may return empty results"
                    )

        # Navigate to base URL
        await rt.navigate(self.base_url)
        await asyncio.sleep(2)  # let SPA render

        # ── Primary: JavaScript DOM extraction ──
        logger.info("Menu discovery: JS DOM extraction")
        js_menu = await self._extract_menu_via_js(rt)

        if js_menu:
            logger.info(f"JS menu extraction: found {len(js_menu)} top-level items")
            return self._dicts_to_menu_nodes(js_menu)

        # ── Fallback 1: LLM-based menu scan ──
        logger.warning("JS menu extraction returned empty — trying LLM MENU_SCAN_PROMPT")
        result = await rt.execute(MENU_SCAN_PROMPT)
        menu_data = self._parse_menu_json(result)
        if menu_data:
            logger.info(f"LLM menu scan: found {len(menu_data)} top-level items")
            return self._dicts_to_menu_nodes(menu_data)

        # ── Fallback 2: full navigation scan ──
        logger.warning("LLM menu scan also empty — trying full navigation scan...")
        fallback_result = await rt.execute(FALLBACK_SCAN_PROMPT)
        fallback_data = self._parse_fallback_json(str(fallback_result))

        if fallback_data:
            page_type = fallback_data.get("page_type", "unknown")
            menu_items = fallback_data.get("menu_items", [])
            logger.info(
                f"Fallback scan: page_type={page_type}, items={len(menu_items)}"
            )
            if page_type in ("login", "error"):
                logger.warning(
                    f"Menu discovery blocked: page is '{page_type}'. "
                    f"Credentials provided: {bool(self.credentials)}"
                )
            if menu_items:
                return self._dicts_to_menu_nodes(menu_items)

        # ── Fallback 3: last resort — extract any links ──
        logger.warning("All strategies failed — trying last resort link extraction...")
        last_result = await rt.execute(f"""
List EVERY clickable link or button on this page that looks like it leads to
another page or section. Ignore: external links, help links, footer links.

For each: note the label text and the URL/href.

Return ONLY this JSON:
{{"links": [{{"label": "...", "href": "..."}}]}}
""")
        last_data = self._parse_fallback_json(str(last_result))
        if last_data and last_data.get("links"):
            links = last_data["links"]
            logger.info(f"Last resort: found {len(links)} raw links")
            menu_nodes = []
            for link in links:
                label = link.get("label", "Unknown")
                href = link.get("href", "")
                if label and href:
                    menu_nodes.append({"label": label, "route": href, "type": "page"})
            return self._dicts_to_menu_nodes(menu_nodes)

        logger.error(
            f"Menu discovery COMPLETELY FAILED for {self.project_id}. "
            f"Base URL: {self.base_url}. Credentials: {bool(self.credentials)}."
        )
        return []

    async def _extract_menu_via_js(self, rt) -> list[dict] | None:
        """Extract menu tree using JavaScript DOM traversal. Returns parsed JSON or None.

        Strategy:
        1. Try Vue Router extraction (most reliable, 0 DOM dependency)
        2. Try synchronous DOM extraction (works if menus are already expanded)
        3. Try accordion-aware sequential expansion (expand one, extract, collapse, next)
        """
        import json as _json

        # ── Strategy 1: Vue Router extraction (best for Vue SPAs) ──
        router_js = """() => {
            try {
                const app = document.querySelector('#app');
                if (app && app.__vue_app__) {
                    const router = app.__vue_app__.config.globalProperties.$router;
                    if (router && router.getRoutes) {
                        const routes = router.getRoutes();
                        const menuRoutes = routes.filter(r => r.meta && (r.meta.title || r.meta.icon));
                        if (menuRoutes.length > 0) {
                            return JSON.stringify({source: 'vue_router', routes: menuRoutes.map(r => ({
                                path: r.path,
                                title: (r.meta && r.meta.title) || '',
                                parent: (r.meta && r.meta.parent) || '',
                                icon: (r.meta && r.meta.icon) || '',
                                hidden: (r.meta && r.meta.hidden) || false,
                            }))});
                        }
                    }
                }
            } catch(e) {}
            return JSON.stringify({source: 'none', routes: []});
        }"""
        try:
            raw = await rt.evaluate_js(router_js)
            data = _json.loads(raw)
            if data.get("source") == "vue_router" and data.get("routes"):
                logger.info("Vue Router extraction: found %d routes", len(data["routes"]))
                return self._vue_routes_to_menu_tree(data["routes"])
        except Exception as e:
            logger.debug("Vue Router extraction failed: %s", e)

        # ── Strategy 2: Synchronous DOM extraction (fast path) ──
        extract_js = """() => {
            function findMenu() {
                const el = document.querySelector('.el-menu, ul[role="menubar"], ul[role="menu"]');
                if (el) return el;
                const ant = document.querySelector('.ant-menu, .ant-menu-root');
                if (ant) return ant;
                const sidebar = document.querySelector('.sidebar, [class*=sidebar], aside, nav');
                if (sidebar) {
                    const menu = sidebar.querySelector('ul, [role=menu], [role=menubar]');
                    if (menu) return menu;
                    return sidebar;
                }
                const uls = document.querySelectorAll('ul');
                for (const ul of uls) {
                    if (ul.querySelectorAll('li').length >= 3) return ul;
                }
                return null;
            }

            const menuRoot = findMenu();
            if (!menuRoot) return JSON.stringify([]);

            // Expand all collapsed submenus (may not work for accordion)
            const subTitles = menuRoot.querySelectorAll('.el-submenu__title, .el-menu-item[aria-expanded="false"], [aria-expanded="false"], .ant-menu-submenu-title');
            for (const title of subTitles) {
                const parent = title.closest('.el-submenu, .ant-menu-submenu, [role=menuitem]');
                const isOpen = parent && (parent.classList.contains('is-opened') || parent.getAttribute('aria-expanded') === 'true');
                if (!isOpen) {
                    try { title.click(); } catch(e) {}
                }
            }

            function extract(parent, depth) {
                if (depth > 10) return [];
                const items = [];
                const children = [];
                for (const el of parent.children) {
                    if (el.tagName === 'LI' || el.getAttribute('role') === 'menuitem') {
                        children.push(el);
                    }
                }
                if (children.length === 0 && depth === 0) {
                    for (const el of parent.querySelectorAll(':scope > li, :scope > [role=menuitem]')) {
                        children.push(el);
                    }
                    if (children.length === 0) {
                        for (const el of parent.querySelectorAll('li[role=menuitem], .el-menu-item, .el-submenu, .ant-menu-item, .ant-menu-submenu')) {
                            children.push(el);
                        }
                    }
                }

                for (const li of children) {
                    let label = '';
                    const titleEl = li.querySelector('.el-submenu__title, .ant-menu-submenu-title, > span, > a > span');
                    if (titleEl) {
                        label = (titleEl.textContent || '').trim();
                    } else {
                        const clone = li.cloneNode(true);
                        const nestedUls = clone.querySelectorAll('ul, .el-menu--inline');
                        nestedUls.forEach(u => u.remove());
                        label = (clone.textContent || '').trim();
                    }
                    label = label.replace(/\\s+/g, ' ').slice(0, 80).trim();
                    if (!label) continue;

                    let route = '';
                    const link = li.querySelector('a[href]');
                    if (link) {
                        route = link.getAttribute('href') || '';
                        if (!route.startsWith('#') && !route.startsWith('/')) {
                            route = '';
                        }
                    }

                    const childUl = li.querySelector(':scope > ul, .el-menu--inline, .ant-menu-sub');
                    let children = [];
                    if (childUl && childUl.querySelectorAll('li').length > 0) {
                        children = extract(childUl, depth + 1);
                    }

                    const isGroup = children.length > 0;
                    items.push({
                        label: label,
                        route: route,
                        type: isGroup ? 'menu_group' : 'page',
                        children: children
                    });
                }
                return items;
            }

            const result = extract(menuRoot, 0);

            if (result.length === 0) {
                const links = menuRoot.querySelectorAll('a[href*="#/"]');
                const seen = new Set();
                for (const a of links) {
                    const href = a.getAttribute('href');
                    const text = (a.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 80);
                    if (href && text && !seen.has(href) && href.includes('#/')) {
                        seen.add(href);
                        result.push({label: text, route: href, type: 'page', children: []});
                    }
                }
            }

            return JSON.stringify(result);
        }"""

        try:
            raw = await rt.evaluate_js(extract_js)
            data = _json.loads(raw)
            if isinstance(data, list) and len(data) > 0:
                logger.info("DOM extraction: found %d top-level items", len(data))
                return data
            logger.info("JS menu extraction returned empty list")
        except Exception as e:
            logger.warning(f"JS menu extraction failed: {e}")

        # ── Strategy 3: Accordion-aware sequential expansion ──
        # Element Plus accordion mode: expanding one menu collapses others.
        # Solution: expand each top-level menu one at a time, extract children, record.
        logger.info("Trying accordion-aware sequential extraction")
        try:
            return await self._extract_accordion_menus(rt)
        except Exception as e:
            logger.warning(f"Accordion extraction failed: {e}")

        return None

    async def _extract_accordion_menus(self, rt) -> list[dict] | None:
        """Extract menu tree by expanding each top-level menu sequentially.

        Handles Element Plus accordion mode where only one submenu can be open.
        """
        import json as _json

        # Step 1: Get top-level menu labels
        top_level_js = """() => {
            const menu = document.querySelector('.el-menu, ul[role="menubar"], ul[role="menu"], .ant-menu');
            if (!menu) return JSON.stringify([]);
            const items = [];
            for (const li of menu.children) {
                if (li.tagName !== 'LI' && li.getAttribute('role') !== 'menuitem') continue;
                const titleEl = li.querySelector('.el-submenu__title, .ant-menu-submenu-title, > span, > a > span');
                const label = titleEl ? (titleEl.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 80) : '';
                if (label) items.push(label);
            }
            return JSON.stringify(items);
        }"""
        raw = await rt.evaluate_js(top_level_js)
        top_labels = _json.loads(raw)
        if not top_labels:
            return None

        logger.info("Accordion extraction: %d top-level menus found", len(top_labels))

        # Step 2: For each top-level menu, expand it and extract its children
        all_items = []
        for label in top_labels:
            expand_and_extract_js = f"""() => {{
                const menu = document.querySelector('.el-menu, ul[role="menubar"], ul[role="menu"], .ant-menu');
                if (!menu) return JSON.stringify({{error: 'no menu'}});

                // Find and click the target top-level menu
                let targetLi = null;
                for (const li of menu.children) {{
                    const titleEl = li.querySelector('.el-submenu__title, .ant-menu-submenu-title, > span, > a > span');
                    const l = titleEl ? (titleEl.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 80) : '';
                    if (l === {repr(label)}) {{
                        targetLi = li;
                        break;
                    }}
                }}
                if (!targetLi) return JSON.stringify({{error: 'not found', label: {repr(label)}}});

                // Click to expand
                const title = targetLi.querySelector('.el-submenu__title, .ant-menu-submenu-title, > span');
                if (title) title.click();

                // Extract children from expanded submenu
                const childUl = targetLi.querySelector(':scope > ul, .el-menu--inline, .ant-menu-sub');
                if (!childUl) {{
                    // No children — might be a direct link page
                    const link = targetLi.querySelector('a[href]');
                    const route = link ? link.getAttribute('href') : '';
                    return JSON.stringify({{
                        label: {repr(label)},
                        route: route,
                        type: 'page',
                        children: []
                    }});
                }}

                const children = [];
                for (const li of childUl.children) {{
                    if (li.tagName !== 'LI' && li.getAttribute('role') !== 'menuitem') continue;
                    const titleEl = li.querySelector('.el-submenu__title, .ant-menu-submenu-title, > span, > a > span');
                    let clabel = titleEl ? (titleEl.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 80) : '';
                    if (!clabel) continue;

                    const link = li.querySelector('a[href]');
                    let route = link ? (link.getAttribute('href') || '') : '';
                    if (route && !route.startsWith('#') && !route.startsWith('/')) route = '';

                    // Check for nested children (level 3)
                    const nestedUl = li.querySelector(':scope > ul, .el-menu--inline, .ant-menu-sub');
                    let nestedChildren = [];
                    if (nestedUl) {{
                        for (const nli of nestedUl.children) {{
                            if (nli.tagName !== 'LI' && nli.getAttribute('role') !== 'menuitem') continue;
                            const ntitle = nli.querySelector('.el-submenu__title, > span, > a > span');
                            const nlabel = ntitle ? (ntitle.textContent || '').trim().replace(/\\s+/g, ' ').slice(0, 80) : '';
                            if (!nlabel) continue;
                            const nlink = nli.querySelector('a[href]');
                            let nroute = nlink ? (nlink.getAttribute('href') || '') : '';
                            if (nroute && !nroute.startsWith('#') && !nroute.startsWith('/')) nroute = '';
                            nestedChildren.push({{label: nlabel, route: nroute, type: 'page', children: []}});
                        }}
                    }}

                    const isGroup = nestedChildren.length > 0;
                    children.push({{
                        label: clabel,
                        route: route,
                        type: isGroup ? 'menu_group' : 'page',
                        children: nestedChildren
                    }});
                }}

                return JSON.stringify({{
                    label: {repr(label)},
                    route: '',
                    type: 'menu_group',
                    children: children
                }});
            }}"""

            try:
                raw = await rt.evaluate_js(expand_and_extract_js)
                item = _json.loads(raw)
                if item.get("error"):
                    logger.debug("Accordion extraction for '%s': %s", label, item.get("error"))
                else:
                    all_items.append(item)
                    child_count = len(item.get("children", []))
                    logger.debug("Accordion extraction: '%s' → %d children", label, child_count)
            except Exception as e:
                logger.debug("Accordion extraction for '%s' failed: %s", label, e)

            # Small delay for DOM update
            await asyncio.sleep(0.3)

        if all_items:
            logger.info("Accordion extraction: %d menus with children", len(all_items))
        return all_items if all_items else None

    @staticmethod
    def _vue_routes_to_menu_tree(routes: list[dict]) -> list[dict]:
        """Convert Vue Router routes to menu tree structure.

        Filters out non-menu routes (login, 404, redirects, layout wrappers)
        and groups children under their parent.
        """
        # Skip patterns: routes that are NOT sidebar menu items
        _SKIP_PATTERNS = (
            "login", "signin", "auth", "register",
            "404", "403", "500", "error", "exception",
            "redirect", "index", "home", "welcome",
            "dashboard", "console",
        )

        # Build parent→children map
        by_parent: dict[str, list] = {}
        roots = []
        for r in routes:
            if r.get("hidden"):
                continue
            title = r.get("title", "").strip()
            if not title:
                continue
            path = r.get("path", "")

            # Skip utility/non-menu routes
            path_lower = path.lower().lstrip("/#")
            if any(skip in path_lower for skip in _SKIP_PATTERNS):
                continue

            # Skip root path or empty path
            if path in ("", "/", "/#/", "#/"):
                continue

            parent = r.get("parent", "")
            entry = {"label": title, "route": path, "type": "page", "children": []}
            if parent:
                by_parent.setdefault(parent, []).append(entry)
            else:
                roots.append(entry)

        # Attach children to parents
        for root in roots:
            label = root["label"]
            if label in by_parent:
                root["children"] = by_parent.pop(label)
                if root["children"]:
                    root["type"] = "menu_group"

        # Remaining orphan children → create menu groups
        for label, children in by_parent.items():
            if children:
                roots.append({"label": label, "route": "", "type": "menu_group", "children": children})

        return roots

    @staticmethod
    def _parse_fallback_json(text: str) -> dict | None:
        """Parse JSON from fallback/discovery responses."""
        import re as _re
        try:
            match = _re.search(r'\{[\s\S]*\}', text)
            if match:
                return json.loads(match.group())
        except (json.JSONDecodeError, AttributeError):
            pass
        return None

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
        base = self.base_url.rstrip("/")
        route = page.route
        if route.startswith("#") or route.startswith("http"):
            target = route
        else:
            target = f"{base}/{route.lstrip('/')}"
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
        """Write .discovery/ output through the injected artifact-store port."""
        write_discovery_artifacts(self.project_id, pages, menu)
        logger.info(
            "Wrote .discovery/ for %s: %d pages, %d menu groups",
            self.project_id,
            len(pages),
            len(menu),
        )

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
