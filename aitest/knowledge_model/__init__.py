"""
Unified Project Knowledge Model — the most stable contract in TLO Platform.

All Discovery plugins output this schema.
All Agents consume this schema.

Usage:
    from aitest.knowledge_model import (
        PageMetadata, RouteMetadata, ComponentMetadata,
        ApiMetadata, PermissionMetadata, ProjectKnowledge,
        Source, Confidence, Provenance, FieldValue,
        FrameworkType, FrameworkInfo, ElementInfo,
    )

    # Create a page from browser observation
    page = PageMetadata(
        page_id="user-list",
        title=FieldValue.observed("用户管理", "sidebar scan"),
        route=FieldValue.observed("#/system/user", "sidebar scan"),
        ...
    )

    # Create a page from source code
    page = PageMetadata(
        page_id="user-list",
        title=FieldValue.certain("用户管理", Source.VUE_ROUTER, "router/index.ts:42"),
        route=FieldValue.certain("/system/user", Source.VUE_ROUTER, "router/index.ts:42"),
        component_file=FieldValue.certain("src/views/system/user/index.vue", Source.VUE_ROUTER),
        ...
    )

    # Migrate legacy PageRecord
    metadata = PageMetadata.from_legacy_page_record(old_record)

    # Serialize
    json_dict = page.to_dict()
"""

from .provenance import (
    Source, Confidence, Provenance, FieldValue,
    serialize_field, deserialize_field,
)
from .schema import (
    RouteMetadata,
    ElementInfo,
    PageElements,
    ComponentMetadata,
    ComponentRef,
    ApiMetadata,
    PermissionMetadata,
    PageMetadata,
    ProjectKnowledge,
    FrameworkType,
    FrameworkInfo,
)

__all__ = [
    # Provenance
    "Source", "Confidence", "Provenance", "FieldValue",
    "serialize_field", "deserialize_field",
    # Schema
    "RouteMetadata", "ElementInfo", "PageElements",
    "ComponentMetadata", "ComponentRef",
    "ApiMetadata", "PermissionMetadata",
    "PageMetadata", "ProjectKnowledge",
    "FrameworkType", "FrameworkInfo",
]
