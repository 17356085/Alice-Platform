"""Re-export from alice_discovery.source — 保持向后兼容。"""
from alice_discovery.source import (  # noqa: F401
    FrameworkDetector, TechStackDetector, TechStack,
    FileIndexer, FileIndex,
    SourceDiscoveryPipeline,
    MetadataMergeEngine, merge_discovery_results,
    BackendDetector,
)
