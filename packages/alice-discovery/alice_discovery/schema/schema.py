"""
Unified Project Knowledge Model — the most stable contract in the platform.

All Discovery plugins output this schema.
All Agents, Planners, Test Generators, and Runtimes consume this schema.

This file should change SLOWLY and DELIBERATELY.
Adding fields: fine. Removing/renaming: breaking change → migration required.

Design principles:
  1. Every field has provenance (which source provided it)
  2. Confidence per field, not per page
  3. Extensible: new sources add fields without breaking consumers
  4. Backward compat: legacy PageRecord → PageMetadata migration path
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import StrEnum

from .provenance import (
    FieldValue, Provenance, Source, Confidence,
    serialize_field, deserialize_field,
    serialize_optional, deserialize_optional,
)


# ══════════════════════════════════════════════════════════════════════════
#  Metadata Types — the unified knowledge model
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class RouteMetadata:
    """
    Route definition extracted from application source code or browser observation.

    Source priority: vue-router > react-router > browser-use > manual
    """
    path: FieldValue                     # "/system/user" or "#/system/user"
    name: FieldValue                     # "UserList"
    title: FieldValue                    # "用户管理" — from route.meta.title or page <title>
    component_file: FieldValue           # "src/views/system/user/index.vue"
    component_name: FieldValue           # "UserList" — the Vue component name
    icon: FieldValue                     # "user" — Lucide/Element icon name
    hidden: FieldValue                   # True if route is hidden from navigation
    keep_alive: FieldValue               # True if route is cached
    redirect: FieldValue                 # Redirect target path, if any
    meta: dict                           # Raw route.meta — all custom fields preserved
    children: list["RouteMetadata"] = field(default_factory=list)

    @classmethod
    def empty(cls) -> "RouteMetadata":
        """Empty route (all fields inferred with low confidence)."""
        return cls(
            path=FieldValue.inferred(""),
            name=FieldValue.inferred(""),
            title=FieldValue.inferred(""),
            component_file=FieldValue.inferred(""),
            component_name=FieldValue.inferred(""),
            icon=FieldValue.inferred(""),
            hidden=FieldValue.inferred(False),
            keep_alive=FieldValue.inferred(False),
            redirect=FieldValue.inferred(""),
            meta={},
        )


@dataclass
class ElementInfo:
    """Single UI element on a page."""
    label: str                           # "新增按钮"
    type: str = ""                       # "button" | "input" | "select" | "table" | "dialog"
    css_selector: str = ""               # Best known CSS selector
    xpath: str = ""                      # Best known XPath
    html_hint: str = ""                  # Placeholder, CSS class, or distinguishing attr
    location: str = ""                   # "header", "search-bar", "table-toolbar", "footer"
    visible: bool = True
    interactive: bool = True
    source: Source = Source.INFERRED     # Which discovery found this element
    confidence: float = 0.5


@dataclass
class PageElements:
    """Structured page elements from browser observation."""
    search_fields: list[ElementInfo] = field(default_factory=list)
    action_buttons: list[ElementInfo] = field(default_factory=list)
    table_columns: list[str] = field(default_factory=list)
    form_fields: list[ElementInfo] = field(default_factory=list)
    dialogs: list[ElementInfo] = field(default_factory=list)
    has_pagination: FieldValue = field(default_factory=lambda: FieldValue.inferred(False))
    has_checkbox_column: FieldValue = field(default_factory=lambda: FieldValue.inferred(False))
    has_tabs: FieldValue = field(default_factory=lambda: FieldValue.inferred(False))
    raw_dom_snapshot: str = ""
    screenshot_base64: str = ""


@dataclass
class ComponentMetadata:
    """
    Component information extracted from source code (.vue / .tsx).

    Source priority: vue-component > react-component > inferred
    """
    file_path: FieldValue                # Absolute path to component file
    component_name: FieldValue           # "UserList"
    component_type: FieldValue           # "page" | "dialog" | "layout" | "widget"
    template_elements: list[ElementInfo] = field(default_factory=list)
    imports: list["ComponentRef"] = field(default_factory=list)  # Child components
    script_setup: bool = True            # Vue 3 <script setup>?
    props: list[str] = field(default_factory=list)
    emits: list[str] = field(default_factory=list)
    reactive_state: list[str] = field(default_factory=list)  # ref(), reactive() names
    computed_props: list[str] = field(default_factory=list)   # computed() names

    @classmethod
    def empty(cls) -> "ComponentMetadata":
        return cls(
            file_path=FieldValue.inferred(""),
            component_name=FieldValue.inferred(""),
            component_type=FieldValue.inferred("page"),
        )


@dataclass
class ComponentRef:
    """Reference to a child component imported by a page component."""
    name: str                            # "UserTable"
    path: str                            # "@/components/system/UserTable.vue"
    source: Source = Source.INFERRED


@dataclass
class ApiMetadata:
    """
    API endpoint discovered from source code or network trace.

    Source priority: source-code (axios/fetch) > openapi > network-trace
    """
    method: FieldValue                   # "GET" | "POST" | "PUT" | "DELETE"
    path: FieldValue                     # "/api/system/user/list"
    description: FieldValue              # "获取用户列表"
    request_body: dict = field(default_factory=dict)    # Schema or example
    response_body: dict = field(default_factory=dict)   # Schema or example
    called_by_pages: list[str] = field(default_factory=list)  # page_ids that use this API
    called_by_components: list[str] = field(default_factory=list)  # component names
    auth_required: FieldValue = field(default_factory=lambda: FieldValue.inferred(True))
    source_file: str = ""                # File where API call was found
    source_line: int = 0
    http_client: str = ""                # "axios" | "fetch" | "umi-request"

    @classmethod
    def empty(cls, method: str = "GET", path: str = "") -> "ApiMetadata":
        return cls(
            method=FieldValue.inferred(method),
            path=FieldValue.inferred(path),
            description=FieldValue.inferred(""),
            auth_required=FieldValue.inferred(True),
        )


@dataclass
class PermissionMetadata:
    """
    Permission/authority information for a page or action.

    Source priority: source-code (route.meta.permission) > browser > inferred
    """
    code: FieldValue                     # "system:user:list"
    label: FieldValue                    # "用户列表查看"
    type: FieldValue                     # "page" | "button" | "api" | "data"
    granted_to: list[str] = field(default_factory=list)  # Role names
    applies_to_pages: list[str] = field(default_factory=list)  # page_ids
    applies_to_apis: list[str] = field(default_factory=list)   # API paths
    source_file: str = ""                # File where permission was declared

    @classmethod
    def empty(cls) -> "PermissionMetadata":
        return cls(
            code=FieldValue.inferred(""),
            label=FieldValue.inferred(""),
            type=FieldValue.inferred("page"),
        )


# ══════════════════════════════════════════════════════════════════════════
#  Unified PageMetadata — the central entity
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class PageMetadata:
    """
    Unified page knowledge — merged from all discovery sources.

    This is the PRIMARY data structure consumed by:
      - AgentLoop (test planning)
      - Test Designer (test case generation)
      - Automation Developer (page object creation)
      - State Auditor (artifact checks)
      - Kanban/UI (display)

    Every field tracks provenance so consumers know "how do we know this?"
    """
    # ── Identity ──
    page_id: str                         # "user-list"
    title: FieldValue                    # "用户管理"

    # ── Route ──
    route: FieldValue                    # "/system/user"
    route_name: FieldValue               # "UserList"
    route_meta: dict = field(default_factory=dict)

    # ── Navigation ──
    menu_path: list[str] = field(default_factory=list)  # ["系统管理", "用户管理"]
    menu_icon: FieldValue = field(default_factory=lambda: FieldValue.inferred(""))
    menu_hidden: FieldValue = field(default_factory=lambda: FieldValue.inferred(False))
    breadcrumb: list[str] = field(default_factory=list)

    # ── Component ──
    component_file: FieldValue = field(default_factory=lambda: FieldValue.inferred(""))
    component_name: FieldValue = field(default_factory=lambda: FieldValue.inferred(""))
    child_components: list[ComponentRef] = field(default_factory=list)

    # ── UI Elements ──
    elements: PageElements = field(default_factory=PageElements)

    # ── APIs ──
    api_endpoints: list[ApiMetadata] = field(default_factory=list)

    # ── Permissions ──
    permissions: list[PermissionMetadata] = field(default_factory=list)

    # ── Page Object (optional, generated by Automation Developer) ──
    page_object_file: str = ""           # "po/user_list.py"
    page_object_class: str = ""          # "UserListPage"

    # ── Provenance & Quality ──
    discovered_from: list[Source] = field(default_factory=list)  # All sources that found this page
    primary_source: Source = Source.INFERRED
    confidence: float = 0.0              # Overall page confidence (max of all fields)
    discovered_at: str = ""              # ISO timestamp of first discovery
    updated_at: str = ""                 # ISO timestamp of last update

    # ── Legacy compat ──
    raw_dom_snapshot: str = ""           # Kept for locator healing
    page_object: str = ""                # Legacy field (use page_object_file instead)

    @property
    def is_browser_confirmed(self) -> bool:
        """Was this page actually observed in a browser?"""
        return Source.BROWSER_USE in self.discovered_from

    @property
    def is_source_confirmed(self) -> bool:
        """Was this page found in source code?"""
        return any(s in self.discovered_from for s in [
            Source.VUE_ROUTER, Source.VUE_COMPONENT,
            Source.REACT_ROUTER, Source.OPENAPI
        ])

    @property
    def is_high_confidence(self) -> bool:
        """Page confirmed by both browser AND source code."""
        return self.confidence >= 0.85

    @property
    def module_name(self) -> str:
        """Top-level menu group = module name."""
        return self.menu_path[0] if self.menu_path else "unknown"

    # ── Serialization ────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict (for .discovery/pages.json)."""
        return {
            "page_id": self.page_id,
            "title": self.title.to_dict(),
            "route": self.route.to_dict(),
            "route_name": self.route_name.to_dict(),
            "route_meta": self.route_meta,
            "menu_path": self.menu_path,
            "menu_icon": self.menu_icon.to_dict(),
            "menu_hidden": self.menu_hidden.to_dict(),
            "breadcrumb": self.breadcrumb,
            "component_file": self.component_file.to_dict(),
            "component_name": self.component_name.to_dict(),
            "child_components": [
                {"name": c.name, "path": c.path, "source": c.source.value}
                for c in self.child_components
            ],
            "elements": {
                "search_fields": [
                    {"label": e.label, "type": e.type, "css_selector": e.css_selector,
                     "html_hint": e.html_hint, "source": e.source.value, "confidence": e.confidence}
                    for e in self.elements.search_fields
                ],
                "action_buttons": [
                    {"label": e.label, "css_selector": e.css_selector,
                     "html_hint": e.html_hint, "source": e.source.value, "confidence": e.confidence}
                    for e in self.elements.action_buttons
                ],
                "table_columns": self.elements.table_columns,
                "form_fields": [
                    {"label": e.label, "type": e.type, "css_selector": e.css_selector}
                    for e in self.elements.form_fields
                ],
                "has_pagination": self.elements.has_pagination.to_dict(),
                "has_checkbox_column": self.elements.has_checkbox_column.to_dict(),
                "has_tabs": self.elements.has_tabs.to_dict(),
            },
            "api_endpoints": [
                {
                    "method": api.method.to_dict(),
                    "path": api.path.to_dict(),
                    "description": api.description.to_dict(),
                    "called_by_pages": api.called_by_pages,
                    "source_file": api.source_file,
                    "http_client": api.http_client,
                }
                for api in self.api_endpoints
            ],
            "permissions": [
                {
                    "code": perm.code.to_dict(),
                    "label": perm.label.to_dict(),
                    "type": perm.type.to_dict(),
                    "granted_to": perm.granted_to,
                    "applies_to_pages": perm.applies_to_pages,
                }
                for perm in self.permissions
            ],
            "page_object_file": self.page_object_file,
            "page_object_class": self.page_object_class,
            "discovered_from": [s.value for s in self.discovered_from],
            "primary_source": self.primary_source.value,
            "confidence": self.confidence,
            "discovered_at": self.discovered_at,
            "updated_at": self.updated_at,
            # Legacy compat
            "page_object": self.page_object_file or self.page_object,
            "raw_dom_snapshot": self.raw_dom_snapshot,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "PageMetadata":
        """Deserialize from JSON dict."""
        return cls(
            page_id=d["page_id"],
            title=deserialize_field(d["title"]),
            route=deserialize_field(d["route"]),
            route_name=deserialize_field(d.get("route_name", d.get("route", {}))),
            route_meta=d.get("route_meta", {}),
            menu_path=d.get("menu_path", []),
            menu_icon=deserialize_field(d.get("menu_icon", {"value": "", "provenance": []})),
            menu_hidden=deserialize_field(d.get("menu_hidden", {"value": False, "provenance": []})),
            breadcrumb=d.get("breadcrumb", []),
            component_file=deserialize_field(d.get("component_file", {"value": "", "provenance": []})),
            component_name=deserialize_field(d.get("component_name", {"value": "", "provenance": []})),
            child_components=[
                ComponentRef(name=c["name"], path=c["path"], source=Source(c.get("source", "inferred")))
                for c in d.get("child_components", [])
            ],
            elements=_parse_elements(d.get("elements", {})),
            api_endpoints=[_parse_api(a) for a in d.get("api_endpoints", [])],
            permissions=[_parse_permission(p) for p in d.get("permissions", [])],
            page_object_file=d.get("page_object_file", ""),
            page_object_class=d.get("page_object_class", ""),
            discovered_from=[Source(s) for s in d.get("discovered_from", [])],
            primary_source=Source(d.get("primary_source", "inferred")),
            confidence=d.get("confidence", 0.0),
            discovered_at=d.get("discovered_at", ""),
            updated_at=d.get("updated_at", ""),
            raw_dom_snapshot=d.get("raw_dom_snapshot", ""),
            page_object=d.get("page_object", ""),
        )

    @classmethod
    def from_legacy_page_record(cls, record) -> "PageMetadata":
        """
        Migrate from legacy PageRecord (discovery/base.py) to PageMetadata.
        All fields become browser-observed provenance.
        """
        from .provenance import FieldValue, Provenance, Source, Confidence

        obs = lambda v, d="": FieldValue(value=v, provenance=[
            Provenance(source=Source.BROWSER_USE, confidence=Confidence.MEDIUM, detail=d)
        ])

        return cls(
            page_id=record.id,
            title=obs(record.title),
            route=obs(record.route),
            route_name=obs(""),
            menu_path=record.menu_path,
            elements=PageElements(
                search_fields=[
                    ElementInfo(label=f.get("label", ""), type=f.get("type", ""),
                               html_hint=f.get("html_hint", ""), source=Source.BROWSER_USE, confidence=0.7)
                    for f in record.elements.get("search_fields", [])
                ],
                action_buttons=[
                    ElementInfo(label=b.get("label", ""), css_selector=b.get("css_hint", ""),
                               source=Source.BROWSER_USE, confidence=0.7)
                    for b in record.elements.get("action_buttons", [])
                ],
                table_columns=record.elements.get("table_columns", []),
                has_pagination=obs(record.elements.get("has_pagination", False)),
                has_checkbox_column=obs(record.elements.get("has_checkbox_column", False)),
                raw_dom_snapshot=record.raw_dom_snapshot,
            ),
            discovered_from=[Source.BROWSER_USE],
            primary_source=Source.BROWSER_USE,
            confidence=0.7,
            discovered_at=record.discovered_at,
            page_object=record.page_object,
            page_object_file=record.page_object,
            raw_dom_snapshot=record.raw_dom_snapshot,
        )


# ══════════════════════════════════════════════════════════════════════════
#  Project-level Knowledge Model
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ProjectKnowledge:
    """
    Complete knowledge model for a tested project.

    Lives at .discovery/knowledge.json (superset of pages.json).
    All Agents consume this. All Discovery plugins contribute to this.
    """
    project_id: str
    pages: list[PageMetadata] = field(default_factory=list)
    routes: list[RouteMetadata] = field(default_factory=list)
    components: list[ComponentMetadata] = field(default_factory=list)
    apis: list[ApiMetadata] = field(default_factory=list)
    permissions: list[PermissionMetadata] = field(default_factory=list)
    menu_tree: list[dict] = field(default_factory=list)  # Keep using MenuNode serialization
    generated_at: str = ""
    discovery_sources: list[str] = field(default_factory=list)  # Which sources contributed

    def to_dict(self) -> dict:
        return {
            "project_id": self.project_id,
            "pages": [p.to_dict() for p in self.pages],
            "routes": [_route_to_dict(r) for r in self.routes],
            "components": [_component_to_dict(c) for c in self.components],
            "apis": [_api_to_dict(a) for a in self.apis],
            "permissions": [_perm_to_dict(pm) for p in self.permissions],
            "menu_tree": self.menu_tree,
            "generated_at": self.generated_at,
            "discovery_sources": self.discovery_sources,
        }


# ══════════════════════════════════════════════════════════════════════════
#  Framework info (for source discovery)
# ══════════════════════════════════════════════════════════════════════════

class FrameworkType(StrEnum):
    VUE_3 = "vue-3"
    VUE_2 = "vue-2"
    REACT = "react"
    NEXT_JS = "next-js"
    NUXT = "nuxt"
    ANGULAR = "angular"
    UNKNOWN = "unknown"


@dataclass
class FrameworkInfo:
    """Detected framework metadata from package.json + project structure."""
    framework: FrameworkType
    version: str = ""
    router_package: str = ""             # "vue-router" | "react-router-dom" | "next/router"
    ui_library: str = ""                 # "element-plus" | "ant-design-vue" | "antd" | "mui"
    build_tool: str = ""                 # "vite" | "webpack" | "turbo"
    state_management: str = ""           # "pinia" | "vuex" | "redux" | "zustand"
    http_client: str = ""                # "axios" | "fetch" | "umi-request"
    typescript: bool = False
    project_root: str = ""               # Absolute path


# ══════════════════════════════════════════════════════════════════════════
#  Backend framework detection
# ══════════════════════════════════════════════════════════════════════════

class BackendFramework(StrEnum):
    SPRING_BOOT = "spring-boot"    # Java / Kotlin
    SPRING_CLOUD = "spring-cloud"  # Spring Cloud Gateway / Microservices
    FLASK = "flask"                # Python
    FASTAPI = "fastapi"            # Python
    DJANGO = "django"              # Python
    EXPRESS = "express"            # Node.js
    GIN = "gin"                    # Go
    LARAVEL = "laravel"            # PHP
    UNKNOWN = "unknown"


class BuildSystem(StrEnum):
    MAVEN = "maven"
    GRADLE = "gradle"
    PIP = "pip"
    POETRY = "poetry"
    GO_MOD = "go-mod"
    NPM = "npm"
    YARN = "yarn"
    PNPM = "pnpm"
    UNKNOWN = "unknown"


class BackendLanguage(StrEnum):
    JAVA = "java"
    KOTLIN = "kotlin"
    PYTHON = "python"
    GO = "go"
    NODE = "node"
    PHP = "php"
    UNKNOWN = "unknown"


@dataclass
class BackendInfo:
    """Detected backend stack from build files + config.

    One instance per backend module/service.
    """
    framework: BackendFramework = BackendFramework.UNKNOWN
    language: BackendLanguage = BackendLanguage.UNKNOWN
    language_version: str = ""          # "21", "3.12", "1.22"
    build_system: BuildSystem = BuildSystem.UNKNOWN
    build_file: str = ""                # path to pom.xml / build.gradle
    project_root: str = ""              # Absolute path to this module root
    service_name: str = ""              # module dir name: "end", "gateway"
    parent_pom: bool = False            # This module is a Maven parent
    modules: list[str] = field(default_factory=list)  # child module names
    db_type: str = ""                   # "mysql" | "postgresql" | "mongodb"
    orm: str = ""                       # "jpa" | "mybatis" | "hibernate"
    config_files: list[str] = field(default_factory=list)

    @property
    def has_db(self) -> bool:
        return bool(self.db_type)

    @property
    def is_spring_boot(self) -> bool:
        return self.framework in (BackendFramework.SPRING_BOOT, BackendFramework.SPRING_CLOUD)

    def to_dict(self) -> dict:
        return {
            "framework": self.framework.value,
            "language": self.language.value,
            "language_version": self.language_version,
            "build_system": self.build_system.value,
            "project_root": self.project_root,
            "service_name": self.service_name,
            "parent_pom": self.parent_pom,
            "modules": self.modules,
            "db_type": self.db_type,
            "orm": self.orm,
        }


# ══════════════════════════════════════════════════════════════════════════
#  Internal helpers (not exported)
# ══════════════════════════════════════════════════════════════════════════

def _parse_elements(d: dict) -> PageElements:
    if not d:
        return PageElements()
    return PageElements(
        search_fields=[ElementInfo(**{**e, "source": Source(e.get("source", "inferred")), "confidence": e.get("confidence", 0.5)}) for e in d.get("search_fields", [])],
        action_buttons=[ElementInfo(**{**e, "source": Source(e.get("source", "inferred")), "confidence": e.get("confidence", 0.5)}) for e in d.get("action_buttons", [])],
        table_columns=d.get("table_columns", []),
        form_fields=[ElementInfo(**{**e, "source": Source(e.get("source", "inferred")), "confidence": e.get("confidence", 0.5)}) for e in d.get("form_fields", [])],
        has_pagination=deserialize_field(d.get("has_pagination", {"value": False})),
        has_checkbox_column=deserialize_field(d.get("has_checkbox_column", {"value": False})),
        has_tabs=deserialize_field(d.get("has_tabs", {"value": False})),
    )

def _parse_api(d: dict) -> ApiMetadata:
    return ApiMetadata(
        method=deserialize_field(d.get("method", {})),
        path=deserialize_field(d.get("path", {})),
        description=deserialize_field(d.get("description", {})),
        called_by_pages=d.get("called_by_pages", []),
        source_file=d.get("source_file", ""),
        http_client=d.get("http_client", ""),
    )

def _parse_permission(d: dict) -> PermissionMetadata:
    return PermissionMetadata(
        code=deserialize_field(d.get("code", {})),
        label=deserialize_field(d.get("label", {})),
        type=deserialize_field(d.get("type", {})),
        granted_to=d.get("granted_to", []),
        applies_to_pages=d.get("applies_to_pages", []),
    )

def _route_to_dict(r: RouteMetadata) -> dict:
    return {
        "path": r.path.to_dict(),
        "name": r.name.to_dict(),
        "title": r.title.to_dict(),
        "component_file": r.component_file.to_dict(),
        "component_name": r.component_name.to_dict(),
        "icon": r.icon.to_dict(),
        "hidden": r.hidden.to_dict(),
        "keep_alive": r.keep_alive.to_dict(),
        "meta": r.meta,
        "children": [_route_to_dict(c) for c in r.children],
    }

def _component_to_dict(c: ComponentMetadata) -> dict:
    return {
        "file_path": c.file_path.to_dict(),
        "component_name": c.component_name.to_dict(),
        "component_type": c.component_type.to_dict(),
        "template_elements": [
            {"label": e.label, "type": e.type, "source": e.source.value}
            for e in c.template_elements
        ],
        "imports": [{"name": i.name, "path": i.path} for i in c.imports],
    }

def _api_to_dict(a: ApiMetadata) -> dict:
    return {
        "method": a.method.to_dict(), "path": a.path.to_dict(),
        "description": a.description.to_dict(),
        "called_by_pages": a.called_by_pages,
        "source_file": a.source_file, "http_client": a.http_client,
    }

def _perm_to_dict(pm: PermissionMetadata) -> dict:
    return {
        "code": pm.code.to_dict(), "label": pm.label.to_dict(),
        "type": pm.type.to_dict(),
        "granted_to": pm.granted_to, "applies_to_pages": pm.applies_to_pages,
    }
