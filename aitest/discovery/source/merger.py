"""
Metadata Merge Engine — merge Browser + Source discovery into unified PageMetadata.

Strategy:
  1. Normalize routes for matching (#/system/user ↔ /system/user)
  2. Merge by route matching (exact → fuzzy → one-way)
  3. Browser-only pages: confidence=0.7, flagged "browser_only"
  4. Source-only pages (hidden routes): confidence=0.85, flagged "hidden_routes"
  5. Both-matched pages: confidence=1.0, fields merged with best-source wins
  6. Every field tracks provenance — consumers know "how do we know this?"

Usage:
    merger = MetadataMergeEngine()

    # From existing discovery runs:
    merged = merger.merge(
        browser_pages=browser_pages,     # list[PageRecord] from BrowserUseDiscovery
        source_routes=source_routes,     # list[RouteMetadata] from VueRouterExtractor
        source_components=components,    # list[ComponentMetadata] from VueComponentExtractor
        source_apis=apis,               # list[ApiMetadata] from ApiExtractor
    )

    # All output pages are PageMetadata with provenance
"""

import logging
import re
from datetime import datetime
from typing import Optional

from aitest.discovery.base import PageRecord
from aitest.knowledge_model.schema import (
    PageMetadata, RouteMetadata, ComponentMetadata, ApiMetadata,
    ComponentRef, PageElements, ElementInfo, PermissionMetadata,
)
from aitest.knowledge_model.provenance import (
    FieldValue, Provenance, Source, Confidence,
)

logger = logging.getLogger(__name__)


# ── Route normalization ──────────────────────────────────────────────────

def normalize_route(route: str) -> str:
    """Normalize route for matching: strip #, lowercase, strip trailing /."""
    r = route.strip().lower()
    r = r.lstrip("#")  # #/system/user → /system/user
    r = r.rstrip("/")
    if not r.startswith("/"):
        r = "/" + r
    return r


def routes_match(browser_route: str, source_route: str) -> bool:
    """Check if two routes refer to the same page."""
    return normalize_route(browser_route) == normalize_route(source_route)


def route_fuzzy_match(browser_route: str, source_route: str) -> bool:
    """Fuzzy match: last 2 path segments match."""
    b_parts = normalize_route(browser_route).strip("/").split("/")
    s_parts = normalize_route(source_route).strip("/").split("/")
    # Match last 2 segments
    if len(b_parts) >= 2 and len(s_parts) >= 2:
        return b_parts[-2:] == s_parts[-2:]
    # Match last segment
    if b_parts and s_parts:
        return b_parts[-1] == s_parts[-1]
    return False


# ══════════════════════════════════════════════════════════════════════════
#  Merge Engine
# ══════════════════════════════════════════════════════════════════════════

class MetadataMergeEngine:
    """
    Merge Browser + Source discovery outputs into unified PageMetadata.

    Browser provides: page structure, observed elements, menu path
    Source provides: routes, component files, permissions, API endpoints

    Merge produces PageMetadata with per-field provenance tracking.
    """

    def merge(
        self,
        browser_pages: list[PageRecord] = None,
        source_routes: list[RouteMetadata] = None,
        source_components: list[ComponentMetadata] = None,
        source_apis: list[ApiMetadata] = None,
    ) -> list[PageMetadata]:
        """
        Merge browser and source discovery results.

        Returns unified PageMetadata list, one per unique page.
        """
        browser_pages = browser_pages or []
        source_routes = source_routes or []
        source_components = source_components or []
        source_apis = source_apis or []

        result: list[PageMetadata] = []
        matched_browser_ids: set[str] = set()
        matched_source_routes: set[str] = set()

        # Phase 1: Match browser pages to source routes
        for bp in browser_pages:
            best_match = None
            match_type = "none"

            for sr in source_routes:
                sr_path = sr.path.value
                # Exact match
                if routes_match(bp.route, sr_path):
                    best_match = sr
                    match_type = "exact"
                    break
                # Fuzzy match
                if route_fuzzy_match(bp.route, sr_path):
                    if best_match is None:
                        best_match = sr
                        match_type = "fuzzy"

            if best_match:
                merged = self._merge_pair(bp, best_match, source_components, source_apis, match_type)
                matched_browser_ids.add(bp.id)
                matched_source_routes.add(best_match.path.value)
            else:
                # Browser-only page
                merged = self._browser_only_page(bp)

            result.append(merged)

        # Phase 2: Source-only routes (routes not found in browser menu)
        for sr in source_routes:
            if sr.path.value not in matched_source_routes:
                # Add source-only routes (including hidden ones — they may be important)
                result.append(self._source_only_page(sr, source_components, source_apis))
                # Also add children
                for child in sr.children:
                    if child.path.value not in matched_source_routes:
                        result.append(self._source_only_page(child, source_components, source_apis, parent=sr))

        # Sort by menu_path for consistent ordering
        result.sort(key=lambda p: (p.menu_path[0] if p.menu_path else "zzz", p.title.value))

        logger.info(
            f"Merge complete: {len(result)} pages "
            f"({len(matched_browser_ids)} browser+source, "
            f"{len(browser_pages) - len(matched_browser_ids)} browser-only, "
            f"{len(source_routes) - len(matched_source_routes)} source-only)"
        )
        return result

    # ── Merge helpers ────────────────────────────────────────────────────

    def _merge_pair(
        self,
        bp: PageRecord,
        sr: RouteMetadata,
        components: list[ComponentMetadata],
        apis: list[ApiMetadata],
        match_type: str,
    ) -> PageMetadata:
        """Merge a browser page with its matching source route."""
        now = datetime.now().isoformat()
        sources = [Source.BROWSER_USE, Source.VUE_ROUTER]
        detail = f"merge:{match_type}"

        # ── Title: source meta.title > browser page title ──
        if sr.meta.get("title"):
            title = FieldValue(
                value=sr.meta["title"],
                provenance=[
                    Provenance(Source.VUE_ROUTER, Confidence.CERTAIN, "route.meta.title"),
                    Provenance(Source.BROWSER_USE, Confidence.MEDIUM, f"observed: {bp.title}"),
                ]
            )
        else:
            title = FieldValue(
                value=sr.title.value or bp.title,
                provenance=[
                    Provenance(Source.VUE_ROUTER, Confidence.HIGH, "route.name"),
                    Provenance(Source.BROWSER_USE, Confidence.MEDIUM, f"observed: {bp.title}"),
                ]
            )

        # ── Route: source path ──
        route = FieldValue(
            value=sr.path.value or bp.route,
            provenance=[
                Provenance(Source.VUE_ROUTER, Confidence.CERTAIN, "route.path"),
                Provenance(Source.BROWSER_USE, Confidence.MEDIUM, f"observed: {bp.route}"),
            ]
        )

        # ── Component file: source only ──
        comp_file = sr.component_file
        if not comp_file.value:
            # Try to find via component name matching
            found = self._find_component_for_route(sr, components)
            if found:
                comp_file = found.file_path

        # ── Elements: browser observation + source template analysis ──
        elements = self._merge_elements(bp, sr, components)

        # ── API endpoints: source only ──
        page_apis = self._find_apis_for_page(sr, apis)

        # ── Permissions: source route meta ──
        permissions = self._extract_permissions(sr)

        # ── Child components: from component imports ──
        child_comps = self._find_child_components(sr, components)

        confidence = 1.0 if match_type == "exact" else 0.90

        return PageMetadata(
            page_id=bp.id,
            title=title,
            route=route,
            route_name=sr.name if sr.name.value else FieldValue.inferred(sr.path.value.strip("/").replace("/", "-")),
            route_meta=sr.meta,
            menu_path=bp.menu_path,
            menu_icon=sr.icon if sr.icon.value else FieldValue.inferred(""),
            menu_hidden=sr.hidden,
            component_file=comp_file,
            component_name=sr.component_name if sr.component_name.value else FieldValue.inferred(""),
            child_components=child_comps,
            elements=elements,
            api_endpoints=page_apis,
            permissions=permissions,
            discovered_from=sources,
            primary_source=Source.VUE_ROUTER,
            confidence=confidence,
            discovered_at=bp.discovered_at or now,
            updated_at=now,
            raw_dom_snapshot=bp.raw_dom_snapshot,
            page_object=bp.page_object,
        )

    def _browser_only_page(self, bp: PageRecord) -> PageMetadata:
        """Create PageMetadata from browser-only observation."""
        return PageMetadata.from_legacy_page_record(bp)

    def _source_only_page(
        self,
        sr: RouteMetadata,
        components: list[ComponentMetadata],
        apis: list[ApiMetadata],
        parent: RouteMetadata = None,
    ) -> PageMetadata:
        """Create PageMetadata from source-only route (hidden page)."""
        now = datetime.now().isoformat()
        page_id = (sr.name.value or sr.path.value).strip("/").replace("/", "-")

        # Menu path from parent + self
        menu_path = []
        if parent:
            menu_path.append(parent.meta.get("title", parent.title.value or ""))
        menu_path.append(sr.meta.get("title", sr.title.value or page_id))

        elements = PageElements()
        comp_file = sr.component_file if sr.component_file.value else FieldValue.inferred("")
        comp_name = sr.component_name if sr.component_name.value else FieldValue.inferred("")

        # Enrich from component metadata
        comp = self._find_component_for_route(sr, components)
        if comp:
            comp_file = comp.file_path
            comp_name = comp.component_name
            # Extract elements from component
            for elem in comp.template_elements:
                elements.template_elements = comp.template_elements

        return PageMetadata(
            page_id=page_id,
            title=sr.title if sr.title.value else FieldValue.certain(sr.meta.get("title", page_id), Source.VUE_ROUTER),
            route=sr.path,
            route_name=sr.name if sr.name.value else FieldValue.inferred(""),
            route_meta=sr.meta,
            menu_path=menu_path,
            menu_icon=sr.icon if sr.icon.value else FieldValue.inferred(""),
            menu_hidden=FieldValue.certain(True, Source.VUE_ROUTER, "not in browser menu"),
            component_file=comp_file,
            component_name=comp_name,
            child_components=[],
            elements=elements,
            api_endpoints=self._find_apis_for_page(sr, apis),
            permissions=self._extract_permissions(sr),
            discovered_from=[Source.VUE_ROUTER],
            primary_source=Source.VUE_ROUTER,
            confidence=0.85,
            discovered_at=now,
            updated_at=now,
        )

    # ── Element merging ──────────────────────────────────────────────────

    def _merge_elements(
        self, bp: PageRecord, sr: RouteMetadata, components: list[ComponentMetadata]
    ) -> PageElements:
        """Merge browser-observed elements with source-analyzed template elements."""
        elements = PageElements()

        # Browser elements → ElementInfo
        be = bp.elements
        for sf in be.get("search_fields", []):
            elements.search_fields.append(ElementInfo(
                label=sf.get("label", ""), type=sf.get("type", ""),
                html_hint=sf.get("html_hint", ""), source=Source.BROWSER_USE, confidence=0.7
            ))
        for btn in be.get("action_buttons", []):
            elements.action_buttons.append(ElementInfo(
                label=btn.get("label", ""), css_selector=btn.get("css_hint", ""),
                source=Source.BROWSER_USE, confidence=0.7
            ))
        elements.table_columns = be.get("table_columns", [])
        elements.has_pagination = FieldValue.observed(be.get("has_pagination", False))
        elements.has_checkbox_column = FieldValue.observed(be.get("has_checkbox_column", False))
        elements.raw_dom_snapshot = bp.raw_dom_snapshot

        # Source elements — add if not already covered by browser
        comp = self._find_component_for_route(sr, components)
        if comp:
            browser_labels = {e.label for e in elements.search_fields + elements.action_buttons}
            for elem in comp.template_elements:
                if elem.label not in browser_labels:
                    if elem.type in ("button",):
                        elements.action_buttons.append(elem)
                    elif elem.type in ("input", "select", "date_picker", "cascader"):
                        elements.search_fields.append(elem)
                    elif elem.type == "table" and not elements.table_columns:
                        elements.table_columns = ["(from source analysis)"]
                    elif elem.type == "pagination":
                        elements.has_pagination = FieldValue(
                            value=True,
                            provenance=[Provenance(Source.VUE_COMPONENT, Confidence.HIGH, f"template: {sr.component_file.value}")]
                        )
                    elif elem.type in ("dialog", "drawer"):
                        elements.dialogs.append(elem)
                    elif elem.type == "tabs":
                        elements.has_tabs = FieldValue.certain(True, Source.VUE_COMPONENT)

        return elements

    # ── Finding helpers ──────────────────────────────────────────────────

    def _find_component_for_route(
        self, sr: RouteMetadata, components: list[ComponentMetadata]
    ) -> Optional[ComponentMetadata]:
        """Find component metadata matching a route."""
        comp_file = sr.component_file.value
        if not comp_file:
            return None
        for c in components:
            cf = c.file_path.value
            if cf and (comp_file in cf or cf.endswith(comp_file) or comp_file.endswith(cf)):
                return c
        return None

    def _find_apis_for_page(
        self, sr: RouteMetadata, apis: list[ApiMetadata]
    ) -> list[ApiMetadata]:
        """Find API endpoints called by this page's component."""
        comp_file = sr.component_file.value
        comp_name = sr.component_name.value
        page_id = (sr.name.value or sr.path.value).strip("/").replace("/", "-")

        result = []
        for api in apis:
            # Match by component name or page_id
            if comp_name and comp_name in api.called_by_components:
                result.append(api)
            elif page_id in api.called_by_pages:
                result.append(api)
            # Match by source file containing page route
            elif comp_file and any(comp_file in sf for sf in [api.source_file] if api.source_file):
                result.append(api)
        return result

    def _find_child_components(
        self, sr: RouteMetadata, components: list[ComponentMetadata]
    ) -> list[ComponentRef]:
        """Find child components imported by this page."""
        comp = self._find_component_for_route(sr, components)
        if comp:
            return comp.imports
        return []

    def _extract_permissions(self, sr: RouteMetadata) -> list[PermissionMetadata]:
        """Extract permissions from route meta."""
        perms = []
        perm = sr.meta.get("permission")
        if perm:
            perms.append(PermissionMetadata(
                code=FieldValue.certain(perm, Source.VUE_ROUTER, "route.meta.permission"),
                label=FieldValue.inferred(perm),
                type=FieldValue.certain("page", Source.VUE_ROUTER),
            ))
        perms_list = sr.meta.get("permissions", [])
        for p in perms_list:
            perms.append(PermissionMetadata(
                code=FieldValue.certain(p, Source.VUE_ROUTER, "route.meta.permissions"),
                label=FieldValue.inferred(p),
                type=FieldValue.certain("page", Source.VUE_ROUTER),
            ))
        return perms


# ── Top-level convenience ────────────────────────────────────────────────

def merge_discovery_results(
    browser_pages: list[PageRecord] = None,
    source_knowledge = None,  # ProjectKnowledge
) -> list[PageMetadata]:
    """
    Convenience: merge browser pages with source ProjectKnowledge.

    Usage:
        from aitest.discovery.source.merger import merge_discovery_results
        pages = merge_discovery_results(
            browser_pages=browser_discovery.pages,
            source_knowledge=source_pipeline.build_knowledge(),
        )
    """
    merger = MetadataMergeEngine()
    if source_knowledge:
        return merger.merge(
            browser_pages=browser_pages,
            source_routes=getattr(source_knowledge, 'routes', []),
            source_components=getattr(source_knowledge, 'components', []),
            source_apis=getattr(source_knowledge, 'apis', []),
        )
    return merger.merge(browser_pages=browser_pages)
