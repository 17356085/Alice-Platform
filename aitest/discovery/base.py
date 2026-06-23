"""
BaseDiscovery — abstract interface + standardized output types.

All discovery strategies output:
  .discovery/pages.json     — flat page list with elements
  .discovery/menu_tree.json — hierarchical menu structure

These become the single source of truth for "what pages exist."
Skills read pages.json, not MODULE_INDEX.md or directory structure.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PageRecord:
    """Single page record in pages.json."""
    id: str                              # slug: "user_list"
    title: str                           # display: "用户管理"
    route: str                           # "#/system/user" or "/users"
    menu_path: list[str] = field(default_factory=list)  # ["系统管理", "用户管理"]
    page_object: str = ""                # "po/user_list.py" (optional)
    discovered_at: str = ""              # ISO timestamp
    elements: dict = field(default_factory=lambda: {
        "search_fields": [],
        "action_buttons": [],
        "table_columns": [],
        "has_pagination": False,
        "has_checkbox_column": False,
    })
    raw_dom_snapshot: str = ""           # HTML at discovery time (for healing)


@dataclass
class MenuNode:
    """Single node in menu_tree.json (recursive)."""
    label: str                           # "系统管理"
    route: str = ""                      # "#/system/user" (empty for groups)
    children: list["MenuNode"] = field(default_factory=list)
    icon: str = ""                       # CSS class or icon name
    type: str = "menu_item"              # "menu_group" | "menu_item" | "page"


@dataclass
class DiscoveryIndex:
    """Complete discovery output for a project."""
    pages: list[PageRecord] = field(default_factory=list)
    menu_tree: list[MenuNode] = field(default_factory=list)
    discovered_at: str = ""
    strategy: str = ""                   # "browser-use" | "vue-source" | "manual"
    total_pages: int = 0


class BaseDiscovery(ABC):
    """
    Abstract discovery strategy.

    Each strategy (BrowserUse, source parse, manual) implements these methods.
    Output is always written to the project's .discovery/ directory.
    """

    def __init__(self, project_id: str):
        self.project_id = project_id

    @abstractmethod
    async def discover_menu(self) -> list[MenuNode]:
        """Discover application menu/sidebar structure."""
        ...

    @abstractmethod
    async def discover_pages(self, menu: list[MenuNode] = None) -> list[PageRecord]:
        """
        Discover all pages.
        If menu is provided, expand menu items to pages.
        """
        ...

    @abstractmethod
    async def observe_page(self, page: PageRecord) -> PageRecord:
        """
        Observe a single page: navigate, extract elements, screenshot.
        Returns enriched PageRecord with elements populated.
        """
        ...

    async def run_full_discovery(self) -> DiscoveryIndex:
        """
        Run complete discovery pipeline: menu → pages → observe.
        Writes .discovery/pages.json and .discovery/menu_tree.json.
        """
        import json
        from datetime import datetime
        from pathlib import Path

        # 1. Discover menu
        menu = await self.discover_menu()

        # 2. Expand menu to pages
        pages = await self.discover_pages(menu)

        # 3. Write to .discovery/
        discovery_dir = (
            Path(__file__).resolve().parent.parent.parent
            / "governance" / "context" / "projects"
            / self.project_id / ".discovery"
        )
        discovery_dir.mkdir(parents=True, exist_ok=True)

        # Write pages.json
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
        (discovery_dir / "pages.json").write_text(
            json.dumps(pages_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        # Write menu_tree.json
        menu_data = _serialize_menu(menu)
        (discovery_dir / "menu_tree.json").write_text(
            json.dumps(menu_data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

        now = datetime.now().isoformat()
        return DiscoveryIndex(
            pages=pages,
            menu_tree=menu,
            discovered_at=now,
            strategy=self.__class__.__name__,
            total_pages=len(pages),
        )


def _serialize_menu(nodes: list[MenuNode]) -> list[dict]:
    """Serialize MenuNode tree to JSON-compatible dicts."""
    result = []
    for node in nodes:
        d = {
            "label": node.label,
            "route": node.route,
            "type": node.type,
        }
        if node.icon:
            d["icon"] = node.icon
        if node.children:
            d["children"] = _serialize_menu(node.children)
        result.append(d)
    return result
