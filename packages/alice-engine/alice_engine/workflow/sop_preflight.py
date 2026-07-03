"""SOP Preflight — preflight cache and mtime scanning.

Extracted from sop_graph.py for single-responsibility.
"""

import threading
from dataclasses import dataclass, field
from pathlib import Path

from alice_engine.workflow.state import get_module_dir, get_test_project_root

WORKSTUDY = Path(".")


def _get_max_mtime(module: str) -> float:
    """获取模块关键目录的最新 mtime，用于 preflight 缓存失效。"""
    max_mtime = 0.0
    dirs_to_check = [get_module_dir(module), WORKSTUDY]
    zjsn = get_test_project_root()
    code_dirs = [
        zjsn / "page" / f"{module}_page",
        zjsn / "script" / module,
    ] if zjsn else []

    for d in dirs_to_check + code_dirs:
        if not d.exists():
            continue
        try:
            for fpath in d.rglob("*"):
                if fpath.is_file() and not fpath.name.startswith("."):
                    try:
                        mtime = fpath.stat().st_mtime
                        if mtime > max_mtime:
                            max_mtime = mtime
                    except OSError:
                        pass
        except OSError:
            pass
    return max_mtime


@dataclass
class PreflightCache:
    """Thread-safe preflight result cache with mtime-based TTL."""
    results: dict[str, dict] = field(default_factory=dict)
    mtimes: dict[str, float] = field(default_factory=dict)
    hits: int = 0
    total: int = 0
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def get(self, cache_key: str, module: str) -> dict | None:
        with self._lock:
            self.total += 1
            if cache_key not in self.results:
                return None
            cached_mtime = self.mtimes.get(cache_key, 0.0)
            current_mtime = _get_max_mtime(module)
            if current_mtime <= cached_mtime:
                self.hits += 1
                return self.results[cache_key]
            del self.results[cache_key]
            self.mtimes.pop(cache_key, None)
            return None

    def put(self, cache_key: str, result: dict, module: str) -> None:
        with self._lock:
            self.results[cache_key] = result
            self.mtimes[cache_key] = _get_max_mtime(module)


_preflight_cache = PreflightCache()
