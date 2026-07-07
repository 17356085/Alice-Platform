"""Alice Discovery — 前端项目静态分析 SDK。

扫描 Vue/React 源码，提取路由、组件、API，输出结构化知识模型。

快速开始:
    from alice_discovery import (
        # 数据模型
        PageMetadata, RouteMetadata, ComponentMetadata, ApiMetadata,
        Source, Confidence, Provenance, FieldValue,
        # 源码分析
        SourceDiscoveryPipeline, MetadataMergeEngine,
        FrameworkDetector, TechStackDetector,
        VueRouterExtractor, VueComponentExtractor, ApiExtractor,
    )

    # 分析 Vue 项目
    detector = TechStackDetector()
    tech = detector.detect(Path("./my-vue-app"))
    print(tech.framework)  # FrameworkType.VUE_3

    pipeline = SourceDiscoveryPipeline()
    knowledge = pipeline.run(Path("./my-vue-app"))
    for page in knowledge.pages:
        print(f"{page.title.value} → {page.route.value}")
"""

# === Schema (from knowledge_model) ===
from .schema.provenance import (
    Source, Confidence, Provenance, FieldValue,
    serialize_field, deserialize_field,
    serialize_optional, deserialize_optional,
)
from .schema.schema import (
    RouteMetadata, ElementInfo, PageElements,
    ComponentMetadata, ComponentRef,
    ApiMetadata, PermissionMetadata,
    PageMetadata, ProjectKnowledge,
    FrameworkType, FrameworkInfo,
    BackendFramework, BuildSystem, BackendLanguage, BackendInfo,
)

# === Discovery Core ===
from .base import BaseDiscovery, PageRecord, MenuNode, DiscoveryIndex

# === Source Analysis ===
from .source.pipeline import SourceDiscoveryPipeline
from .source.merger import MetadataMergeEngine, merge_discovery_results
from .source.framework_detector import FrameworkDetector, TechStackDetector, TechStack
from .source.file_indexer import FileIndexer, FileIndex
from .source.backend_detector import BackendDetector
from .source.extractors.base import BaseExtractor
from .source.extractors.vue_router import VueRouterExtractor
from .source.extractors.vue_component import VueComponentExtractor
from .source.extractors.api_extractor import ApiExtractor

__version__ = "0.1.0"

__all__ = [
    # Schema
    "Source", "Confidence", "Provenance", "FieldValue",
    "serialize_field", "deserialize_field",
    "serialize_optional", "deserialize_optional",
    "RouteMetadata", "ElementInfo", "PageElements",
    "ComponentMetadata", "ComponentRef",
    "ApiMetadata", "PermissionMetadata",
    "PageMetadata", "ProjectKnowledge",
    "FrameworkType", "FrameworkInfo",
    "BackendFramework", "BuildSystem", "BackendLanguage", "BackendInfo",
    # Discovery
    "BaseDiscovery", "PageRecord", "MenuNode", "DiscoveryIndex",
    # Source Analysis
    "SourceDiscoveryPipeline", "MetadataMergeEngine", "merge_discovery_results",
    "FrameworkDetector", "TechStackDetector", "TechStack",
    "FileIndexer", "FileIndex", "BackendDetector",
    "BaseExtractor",
    "VueRouterExtractor", "VueComponentExtractor", "ApiExtractor",
]
