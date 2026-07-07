"""Source Discovery — 源码级前端项目分析。"""

from .pipeline import SourceDiscoveryPipeline
from .merger import MetadataMergeEngine, merge_discovery_results
from .framework_detector import FrameworkDetector, TechStackDetector, TechStack
from .file_indexer import FileIndexer, FileIndex
from .backend_detector import BackendDetector
