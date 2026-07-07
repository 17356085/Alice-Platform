"""Unified Project Knowledge Model — 数据模型 + 溯源系统。"""

from .provenance import (
    Source, Confidence, Provenance, FieldValue,
    serialize_field, deserialize_field,
    serialize_optional, deserialize_optional,
)
from .schema import (
    RouteMetadata, ElementInfo, PageElements,
    ComponentMetadata, ComponentRef,
    ApiMetadata, PermissionMetadata,
    PageMetadata, ProjectKnowledge,
    FrameworkType, FrameworkInfo,
    BackendFramework, BuildSystem, BackendLanguage, BackendInfo,
)
