"""DiffExtractor — Diff 提取。"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_diff(file_path: str | Path, old_content: str = "", new_content: str = "") -> str:
    if old_content and new_content:
        import difflib
        diff = difflib.unified_diff(
            old_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile="old", tofile="new",
        )
        return "".join(diff)
    return ""
