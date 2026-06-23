"""
SourceDiscoveryPipeline — orchestrates all source extractors.

Implements BaseDiscovery interface → drop-in replacement for BrowserUseDiscovery.

Flow:
  1. FrameworkDetector → FrameworkInfo
  2. FileIndexer → FileIndex
  3. VueRouterExtractor → list[RouteMetadata]
  4. VueComponentExtractor → list[ComponentMetadata]
  5. ApiExtractor → list[ApiMetadata]
  6. Convert to MenuNode + PageRecord for BaseDiscovery contract
  7. Output to .discovery/ via ProjectContext artifacts

No browser needed. Purely source code analysis.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from aitest.discovery.base import BaseDiscovery, PageRecord, MenuNode, DiscoveryIndex
from aitest.knowledge_model.schema import (
    PageMetadata, RouteMetadata, ComponentMetadata, ApiMetadata,
    FrameworkInfo, FrameworkType, ProjectKnowledge,
)
from aitest.knowledge_model.provenance import FieldValue, Provenance, Source, Confidence

from .framework_detector import FrameworkDetector
from .file_indexer import FileIndexer, FileIndex
from .extractors import VueRouterExtractor, VueComponentExtractor, ApiExtractor

logger = logging.getLogger(__name__)


class SourceDiscoveryPipeline(BaseDiscovery):
    """
    Source code discovery pipeline — parses project files without browser.

    Implements BaseDiscovery → can be used wherever BrowserUseDiscovery is used.

    Usage:
        pipeline = SourceDiscoveryPipeline("my-project", project_path="/path/to/vue-app")
        index = await pipeline.run_full_discovery()
        # or step by step:
        menu = await pipeline.discover_menu()
        pages = await pipeline.discover_pages(menu)
    """

    def __init__(
        self,
        project_id: str,
        project_path: str | Path = "",
        framework: Optional[FrameworkInfo] = None,
    ):
        super().__init__(project_id)
        self.project_path = Path(project_path).resolve() if project_path else None
        self._framework: Optional[FrameworkInfo] = framework
        self._file_index: Optional[FileIndex] = None
        self._routes: list[RouteMetadata] = []
        self._components: list[ComponentMetadata] = []
        self._apis: list[ApiMetadata] = []

    # ── BaseDiscovery interface ──────────────────────────────────────────

    async def discover_menu(self) -> list[MenuNode]:
        """Build menu tree from route metadata (no browser needed)."""
        if not self._routes:
            self._run_extractors()

        return self._routes_to_menu(self._routes)

    async def discover_pages(self, menu: list[MenuNode] = None) -> list[PageRecord]:
        """
        Convert routes to PageRecords.
        If menu not provided, builds from routes.
        """
        if not self._routes:
            self._run_extractors()

        if menu is None:
            menu = self._routes_to_menu(self._routes)

        pages = []
        for route in self._routes:
            # Skip hidden routes unless explicitly included
            if route.hidden.value and not route.children:
                continue

            # Build menu_path from route hierarchy
            menu_path = self._infer_menu_path(route, menu)

            # Determine page_id from route name or path
            page_id = (route.name.value or route.path.value).strip("/").replace("/", "-")

            pages.append(PageRecord(
                id=page_id,
                title=route.title.value or page_id,
                route=route.path.value,
                menu_path=menu_path,
                discovered_at=datetime.now().isoformat(),
                elements={
                    "search_fields": [],
                    "action_buttons": [],
                    "table_columns": [],
                    "has_pagination": False,
                    "has_checkbox_column": False,
                },
            ))

            # Add children as separate pages
            for child in route.children:
                child_id = (child.name.value or child.path.value).strip("/").replace("/", "-")
                child_menu = menu_path + [route.title.value]
                pages.append(PageRecord(
                    id=child_id,
                    title=child.title.value or child_id,
                    route=child.path.value,
                    menu_path=child_menu,
                    discovered_at=datetime.now().isoformat(),
                ))

        return pages

    async def observe_page(self, page: PageRecord) -> PageRecord:
        """
        For source discovery: parse component template for elements.
        No browser — AST analysis of .vue SFC files.
        """
        # Find the component file for this page
        comp = self._find_component_for_page(page)
        if comp:
            # Extract elements from component metadata
            for elem in comp.template_elements:
                if elem.type in ("button",):
                    page.elements.setdefault("action_buttons", []).append({
                        "label": elem.label, "css_hint": "", "source": "vue-component"
                    })
                elif elem.type in ("input", "select", "date_picker", "cascader"):
                    page.elements.setdefault("search_fields", []).append({
                        "label": elem.label, "type": elem.type,
                        "html_hint": "", "source": "vue-component"
                    })
                elif elem.type == "table":
                    page.elements["has_table"] = True
                elif elem.type == "pagination":
                    page.elements["has_pagination"] = True
                elif elem.type == "dialog":
                    page.elements["has_dialog"] = True
        return page

    # ── Core extraction ──────────────────────────────────────────────────

    def _run_extractors(self):
        """Run all extractors. Populates _routes, _components, _apis."""
        if not self.project_path or not self.project_path.exists():
            logger.warning(f"Project path not set or missing: {self.project_path}")
            return

        # 1. Detect framework
        if not self._framework:
            detector = FrameworkDetector()
            self._framework = detector.detect(self.project_path)
            if not self._framework:
                logger.warning(f"Could not detect framework in {self.project_path}")
                return
            logger.info(f"Detected: {self._framework.framework.value} {self._framework.version}")

        # 2. Index files
        indexer = FileIndexer()
        self._file_index = indexer.scan(self.project_path, self._framework)
        if not self._file_index.has_router:
            logger.warning("No router files found — source discovery limited")

        # 3. Extract routes
        if self._file_index.has_router:
            try:
                router_ext = VueRouterExtractor(self.project_path, self._framework, self._file_index)
                if router_ext.can_extract():
                    self._routes = router_ext.extract()
                    logger.info(f"Extracted {len(self._routes)} routes")
            except Exception as e:
                logger.warning(f"Router extraction failed: {e}")

        # 4. Extract components
        try:
            comp_ext = VueComponentExtractor(self.project_path, self._framework, self._file_index)
            if comp_ext.can_extract():
                self._components = comp_ext.extract()
                logger.info(f"Extracted {len(self._components)} components")
        except Exception as e:
            logger.warning(f"Component extraction failed: {e}")

        # 5. Extract APIs
        try:
            api_ext = ApiExtractor(self.project_path, self._framework, self._file_index)
            if api_ext.can_extract():
                self._apis = api_ext.extract()
                logger.info(f"Extracted {len(self._apis)} API endpoints")
        except Exception as e:
            logger.warning(f"API extraction failed: {e}")

    def build_knowledge(self) -> ProjectKnowledge:
        """
        Build complete ProjectKnowledge from source extraction.
        Converts RouteMetadata + ComponentMetadata + ApiMetadata → PageMetadata.
        """
        if not self._routes:
            self._run_extractors()

        pages = []
        for route in self._routes:
            page = self._route_to_page_metadata(route)
            if page:
                pages.append(page)
            for child in route.children:
                child_page = self._route_to_page_metadata(child, parent=route)
                if child_page:
                    pages.append(child_page)

        knowledge = ProjectKnowledge(
            project_id=self.project_id,
            pages=pages,
            routes=self._routes,
            components=self._components,
            apis=self._apis,
            menu_tree=[],  # Will be set during merge
            generated_at=datetime.now().isoformat(),
            discovery_sources=["source-code"],
        )
        return knowledge

    # ── Helpers ──────────────────────────────────────────────────────────

    def _routes_to_menu(self, routes: list[RouteMetadata]) -> list[MenuNode]:
        """Convert route tree to MenuNode tree."""
        nodes = []
        for route in routes:
            if route.hidden.value:
                continue
            children = self._routes_to_menu(route.children)
            # Determine type
            node_type = "menu_group" if children else "page"
            nodes.append(MenuNode(
                label=route.meta.get("title", route.title.value or route.path.value.strip("/")),
                route=route.path.value if not children else "",
                children=children,
                icon=route.icon.value or "",
                type=node_type,
            ))
        return nodes

    def _infer_menu_path(self, route: RouteMetadata, menu: list[MenuNode]) -> list[str]:
        """Infer menu breadcrumb path from route position in menu tree."""
        for node in menu:
            if node.route == route.path.value:
                return [node.label]
            for child_path in self._find_node_path(node, route.path.value):
                if child_path:
                    return child_path
        # Fallback: route path segments
        return route.path.value.strip("/").split("/")

    def _find_node_path(self, node: MenuNode, target_route: str, prefix: list[str] = None) -> list[list[str]]:
        """Recursively find all paths to a route in menu tree."""
        if prefix is None:
            prefix = []
        paths = []
        current = prefix + [node.label]
        if node.route == target_route:
            paths.append(current)
        for child in node.children:
            paths.extend(self._find_node_path(child, target_route, current))
        return paths

    def _find_component_for_page(self, page: PageRecord) -> Optional[ComponentMetadata]:
        """Match page record to component metadata by route/path."""
        for comp in self._components:
            comp_path = comp.file_path.value
            # Try fuzzy match: page id in component path
            if page.id.replace("-", "") in comp_path.replace("-", "").lower():
                return comp
        return None

    def _route_to_page_metadata(
        self, route: RouteMetadata, parent: RouteMetadata = None
    ) -> Optional[PageMetadata]:
        """Convert RouteMetadata → PageMetadata."""
        if route.hidden.value and not route.children:
            return None

        # Find matching component
        comp = None
        comp_file = route.component_file.value
        for c in self._components:
            if comp_file and comp_file in c.file_path.value:
                comp = c
                break

        # Find APIs called by this page
        page_apis = []
        page_id = (route.name.value or route.path.value).strip("/").replace("/", "-")
        for api in self._apis:
            if page_id in api.called_by_pages or route.component_name.value in api.called_by_components:
                page_apis.append(api)

        # Build menu path
        menu_path = []
        if parent:
            menu_path = [parent.meta.get("title", parent.title.value or "")]
        menu_path.append(route.meta.get("title", route.title.value or ""))

        return PageMetadata(
            page_id=page_id,
            title=route.title,
            route=route.path,
            route_name=route.name,
            route_meta=route.meta,
            menu_path=menu_path,
            menu_icon=route.icon,
            menu_hidden=route.hidden,
            component_file=route.component_file,
            component_name=route.component_name,
            child_components=[ComponentRef(name=i.name, path=i.path, source=Source.VUE_COMPONENT)
                            for i in (comp.imports if comp else [])],
            api_endpoints=page_apis,
            permissions=[
                # Extract permission from route.meta.permission / permissions
                # (simplified; full implementation can parse permission config)
            ],
            discovered_from=[Source.VUE_ROUTER],
            primary_source=Source.VUE_ROUTER,
            confidence=0.85,
            discovered_at=datetime.now().isoformat(),
        )
