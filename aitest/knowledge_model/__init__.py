"""Re-export from alice_discovery.schema — 保持向后兼容。

Canonical import: from alice_discovery.schema import ...
"""
from alice_discovery.schema import (  # noqa: F401
    Source, Confidence, Provenance, FieldValue,
    serialize_field, deserialize_field,
    serialize_optional, deserialize_optional,
    RouteMetadata, ElementInfo, PageElements,
    ComponentMetadata, ComponentRef,
    ApiMetadata, PermissionMetadata,
    PageMetadata, ProjectKnowledge,
    FrameworkType, FrameworkInfo,
    BackendFramework, BuildSystem, BackendLanguage, BackendInfo,
)
