"""
ArtifactStore — project-scoped file artifact read/write.

Handles SOP_STATUS, page contexts, test cases, reports.
Callers don't construct paths manually.

ADR-001: Supports .tlo/ dual-write strategy.
  - Prefer .tlo/ when project has it
  - Fall back to governance/context/projects/<id>/ for legacy
  - Write to BOTH locations during migration (P1-P2)

Usage:
    store = ctx.artifacts()
    content = store.read("pages", "user_list", "PAGE_CONTEXT.md")
    store.write("## Page Context\n...", "pages", "user_list", "PAGE_CONTEXT.md")
    status = store.sop_status("equipment")
    store.write_sop_status("equipment", status_data)
"""

import json
from pathlib import Path
from typing import Optional


class ArtifactStore:
    """
    Project-scoped file artifact access with .tlo/ support.

    ADR-001 dual-path strategy:
      - Read: .tlo/ → legacy governance/ → None
      - Write: .tlo/ + legacy (dual-write during migration)
    """

    def __init__(self, project_id: str = "web-automation"):
        self._project_id = project_id
        self._root = Path(__file__).resolve().parent.parent.parent

        # TLO directory (may be None if project has no .tlo/)
        self._tlo_dir: Optional[Path] = self._resolve_tlo_dir()

        # Legacy project directories
        self._project_dir = self._root / "governance" / "context" / "projects" / project_id
        self._modules_dir = self._project_dir / "modules"

        # Legacy governance directories
        self._artifacts_dir = self._root / "governance" / "artifacts"
        self._sop_status_dir = self._artifacts_dir / "sop-status" / project_id
        self._sop_status_dir_legacy = self._artifacts_dir / "sop-status"

    def _resolve_tlo_dir(self) -> Optional[Path]:
        """Resolve .tlo/ directory from project.yaml code_path."""
        try:
            from aitest.platform.paths import get_test_project_root
            root = get_test_project_root(self._project_id)
            if root:
                tlo = root / ".tlo"
                if tlo.exists():
                    return tlo
                # If project root exists but .tlo/ doesn't, we can create it
                if root.exists():
                    return None  # Not created yet — will create on first write
        except Exception:
            pass
        return None

    def _ensure_tlo_dir(self) -> Optional[Path]:
        """Get or create .tlo/ directory."""
        try:
            from aitest.platform.paths import get_test_project_root
            root = get_test_project_root(self._project_id)
            if root and root.exists():
                tlo = root / ".tlo"
                tlo.mkdir(parents=True, exist_ok=True)
                self._tlo_dir = tlo
                return tlo
        except Exception:
            pass
        return None

    @property
    def project_id(self) -> str:
        return self._project_id

    # ── Low-level path resolution ────────────────────────────────────────

    def path(self, *parts: str) -> Path:
        """Resolve path relative to modules directory.
        Prefers .tlo/knowledge/modules/ if .tlo/ exists."""
        if self._tlo_dir:
            return self._tlo_dir / "knowledge" / "modules" / Path(*parts)
        return self._modules_dir.joinpath(*parts)

    def project_path(self, *parts: str) -> Path:
        """Resolve path relative to project directory.
        Prefers .tlo/ if it exists."""
        if self._tlo_dir:
            return self._tlo_dir / Path(*parts)
        return self._project_dir.joinpath(*parts)

    def discovery_path(self, *parts: str) -> Path:
        """Resolve path relative to cache/discovery/ (or .discovery/ legacy)."""
        if self._tlo_dir:
            return self._tlo_dir / "cache" / "discovery" / Path(*parts)
        return self._project_dir / ".discovery" / Path(*parts)

    # ── Read/Write ───────────────────────────────────────────────────────

    def read(self, *parts: str) -> Optional[str]:
        """Read file content relative to modules dir. Returns None if missing."""
        p = self.path(*parts)
        try:
            return p.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            # Fallback: try legacy path if .tlo/ was preferred but file not there
            if self._tlo_dir:
                p_legacy = self._modules_dir.joinpath(*parts)
                try:
                    return p_legacy.read_text(encoding="utf-8")
                except (FileNotFoundError, OSError):
                    pass
            return None

    def read_project(self, *parts: str) -> Optional[str]:
        """Read file content relative to project dir."""
        p = self.project_path(*parts)
        try:
            return p.read_text(encoding="utf-8")
        except (FileNotFoundError, OSError):
            if self._tlo_dir:
                p_legacy = self._project_dir.joinpath(*parts)
                try:
                    return p_legacy.read_text(encoding="utf-8")
                except (FileNotFoundError, OSError):
                    pass
            return None

    def write(self, content: str, *parts: str):
        """Write file content relative to modules dir.
        During migration (P1-P2): dual-write to .tlo/ and legacy."""
        # Primary: .tlo/ or legacy modules dir
        p = self.path(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

        # Dual-write to legacy if .tlo/ is active
        if self._tlo_dir:
            p_legacy = self._modules_dir.joinpath(*parts)
            p_legacy.parent.mkdir(parents=True, exist_ok=True)
            p_legacy.write_text(content, encoding="utf-8")

    def write_project(self, content: str, *parts: str):
        """Write file content relative to project dir.
        During migration: dual-write to .tlo/ and legacy."""
        p = self.project_path(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

        # Dual-write to legacy
        if self._tlo_dir:
            p_legacy = self._project_dir.joinpath(*parts)
            p_legacy.parent.mkdir(parents=True, exist_ok=True)
            p_legacy.write_text(content, encoding="utf-8")

    def exists(self, *parts: str) -> bool:
        """Check if file exists relative to modules dir."""
        if self.path(*parts).exists():
            return True
        if self._tlo_dir:
            return self._modules_dir.joinpath(*parts).exists()
        return False

    def glob(self, pattern: str) -> list[Path]:
        """Glob pattern relative to modules dir. Merges .tlo/ + legacy."""
        results = list(self._modules_dir.glob(pattern))
        if self._tlo_dir:
            tlo_mods = self._tlo_dir / "knowledge" / "modules"
            if tlo_mods.exists():
                results.extend(tlo_mods.glob(pattern))
        return sorted(set(results))

    # ── Module/Page discovery ────────────────────────────────────────────

    def list_modules(self) -> list[str]:
        """Discover modules from directory structure."""
        pages_data = self._load_discovery_pages()
        if pages_data:
            menus = set()
            for p in pages_data:
                if p.get("menu_path"):
                    menus.add(p["menu_path"][0])
            if menus:
                return sorted(menus)

        # Scan .tlo/knowledge/modules/ first, then legacy
        modules = set()
        for mod_dir in self._get_module_search_dirs():
            if mod_dir.exists():
                for d in mod_dir.iterdir():
                    if d.is_dir() and not d.name.startswith(".") and not d.name.startswith("_"):
                        modules.add(d.name)
        return sorted(modules)

    def list_pages(self, module: str) -> list[str]:
        """Discover pages for a module."""
        pages_data = self._load_discovery_pages()
        if pages_data:
            result = []
            for p in pages_data:
                menu = p.get("menu_path", [])
                if menu and menu[0] == module:
                    result.append(p.get("id", ""))
            return result

        # Scan pages/ subdirectories
        pages = set()
        for mod_dir in self._get_module_search_dirs():
            pages_dir = mod_dir / module / "pages"
            if pages_dir.exists():
                for d in pages_dir.iterdir():
                    if d.is_dir() and not d.name.startswith("."):
                        pages.add(d.name)
        return sorted(pages)

    def _get_module_search_dirs(self) -> list[Path]:
        """Return all directories to scan for modules (TLO first)."""
        dirs = []
        if self._tlo_dir:
            dirs.append(self._tlo_dir / "knowledge" / "modules")
        dirs.append(self._modules_dir)
        return dirs

    def _load_discovery_pages(self) -> Optional[list]:
        """Load discovery pages.json (TLO cache first, then legacy)."""
        for p in [self.discovery_path("pages.json"),
                  self._project_dir / ".discovery" / "pages.json"]:
            if p.exists():
                try:
                    return json.loads(p.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    pass
        return None

    # ── SOP Status ───────────────────────────────────────────────────────

    def sop_status(self, module: str) -> Optional[dict]:
        """Read SOP_STATUS file. Tries .tlo/runtime/ first, then per-project, then legacy."""
        search_paths = []
        if self._tlo_dir:
            search_paths.append(self._tlo_dir / "runtime" / "sop-status")
        search_paths.append(self._sop_status_dir)
        search_paths.append(self._sop_status_dir_legacy)

        for d in search_paths:
            p = d / f"SOP_STATUS_{module}.json"
            if p.exists():
                try:
                    return json.loads(p.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    pass
        return None

    def write_sop_status(self, module: str, data: dict):
        """Write SOP_STATUS. Dual-write: .tlo/runtime/ + legacy per-project dir."""
        # Primary: .tlo/runtime/sop-status/ (or legacy per-project)
        if self._tlo_dir or self._ensure_tlo_dir():
            tlo_runtime = self._tlo_dir / "runtime" / "sop-status"
            tlo_runtime.mkdir(parents=True, exist_ok=True)
            p = tlo_runtime / f"SOP_STATUS_{module}.json"
            p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

        # Dual-write: legacy per-project location
        self._sop_status_dir.mkdir(parents=True, exist_ok=True)
        p_legacy = self._sop_status_dir / f"SOP_STATUS_{module}.json"
        p_legacy.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def all_sop_statuses(self) -> dict[str, dict]:
        """Read all SOP_STATUS files. Merges .tlo/ + per-project + legacy."""
        result = {}
        search_dirs = []
        if self._tlo_dir:
            search_dirs.append(self._tlo_dir / "runtime" / "sop-status")
        search_dirs.append(self._sop_status_dir)
        search_dirs.append(self._sop_status_dir_legacy)

        for d in search_dirs:
            if d.exists():
                for f in sorted(d.glob("SOP_STATUS_*.json")):
                    mod = f.stem.replace("SOP_STATUS_", "")
                    if mod not in result:
                        try:
                            result[mod] = json.loads(f.read_text(encoding="utf-8"))
                        except (json.JSONDecodeError, OSError):
                            pass
        return result

    # ── Discovery output ─────────────────────────────────────────────────

    def write_discovery_pages(self, pages: list[dict]):
        """Write cache/discovery/pages.json (dual-write)."""
        p = self.discovery_path("pages.json")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")

        # Dual-write legacy
        if self._tlo_dir:
            p_legacy = self._project_dir / ".discovery" / "pages.json"
            p_legacy.parent.mkdir(parents=True, exist_ok=True)
            p_legacy.write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")

    def read_discovery_pages(self) -> Optional[list]:
        """Read discovery pages."""
        return self._load_discovery_pages()

    def write_discovery_menu(self, menu: list[dict]):
        """Write cache/discovery/menu_tree.json (dual-write)."""
        p = self.discovery_path("menu_tree.json")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(menu, ensure_ascii=False, indent=2), encoding="utf-8")

        if self._tlo_dir:
            p_legacy = self._project_dir / ".discovery" / "menu_tree.json"
            p_legacy.parent.mkdir(parents=True, exist_ok=True)
            p_legacy.write_text(json.dumps(menu, ensure_ascii=False, indent=2), encoding="utf-8")

    def read_discovery_menu(self) -> Optional[list]:
        """Read discovery menu."""
        for p in [self.discovery_path("menu_tree.json"),
                  self._project_dir / ".discovery" / "menu_tree.json"]:
            if p.exists():
                try:
                    return json.loads(p.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    pass
        return None
