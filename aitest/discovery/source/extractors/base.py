"""
BaseExtractor — abstract base for all source code extractors.

Each extractor produces a specific type of metadata from source files.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from aitest.knowledge_model.schema import FrameworkInfo
from aitest.discovery.source.file_indexer import FileIndex


class BaseExtractor(ABC):
    """Abstract source code extractor."""

    def __init__(self, project_root: Path, framework: FrameworkInfo, file_index: FileIndex):
        self.project_root = Path(project_root)
        self.framework = framework
        self.file_index = file_index

    @abstractmethod
    def extract(self) -> list:
        """Extract metadata from source files. Returns list of metadata objects."""
        ...

    @abstractmethod
    def can_extract(self) -> bool:
        """Check if this extractor can run on the current project."""
        ...

    @staticmethod
    def read_file(path: Path) -> Optional[str]:
        """Safely read a source file."""
        try:
            return path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None

    @staticmethod
    def resolve_import(import_path: str, current_file: Path) -> Optional[Path]:
        """
        Resolve a relative import to absolute file path.

        Handles: @/ alias, ./ relative, ../ relative
        """
        if import_path.startswith("@"):
            # @/ → src/
            import_path = import_path[1:]  # Remove @
            if import_path.startswith("/"):
                import_path = import_path[1:]
        elif import_path.startswith("."):
            # Relative import
            resolved = (current_file.parent / import_path).resolve()
            # Try with extensions
            for ext in [".vue", ".ts", ".tsx", ".js", ".jsx", "/index.vue", "/index.ts"]:
                candidate = resolved.with_suffix("") if ext.startswith("/") else Path(str(resolved) + ext)
                if candidate.exists():
                    return candidate
            return None

        # Absolute from project root
        candidates = [
            current_file.parent.parent.parent / import_path,
            current_file.parent.parent / import_path,
            current_file.parent / import_path,
        ]
        for c in candidates:
            if c.exists():
                return c
            for ext in [".vue", ".ts", ".tsx", ".js"]:
                c2 = Path(str(c) + ext)
                if c2.exists():
                    return c2
                c3 = c / "index.vue"
                if c3.exists():
                    return c3
        return None
