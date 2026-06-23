"""Source Discovery — parse project files without browser."""

from .framework_detector import FrameworkDetector, TechStackDetector, TechStack
from .file_indexer import FileIndexer, FileIndex
from .pipeline import SourceDiscoveryPipeline
from .backend_detector import BackendDetector

__all__ = [
    "FrameworkDetector",
    "TechStackDetector",
    "TechStack",
    "FileIndexer",
    "FileIndex",
    "SourceDiscoveryPipeline",
    "BackendDetector",
]
