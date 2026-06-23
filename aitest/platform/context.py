"""
ProjectContext — single entry point for everything project-specific.

Replaces 17 duplicated CONTEXT_MODULES constants across the codebase.
Skills NEVER see project directory structure. They access artifacts,
knowledge, and runtime through this context.

Usage:
    from aitest.platform import get_project

    ctx = get_project("web-automation")
    url = ctx.sut_url()
    pages = ctx.list_pages()
    content = ctx.artifacts().read("pages", "user_list", "PAGE_CONTEXT.md")
    results = ctx.knowledge().search_issues("element not found")
    rt = ctx.runtime()
    await rt.navigate("#/equipment/device")
"""

import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

from .artifacts import ArtifactStore
from .knowledge import KnowledgeStore
from .runtime import Runtime, BrowserRuntime


# ── Root discovery ───────────────────────────────────────────────────────
_ROOT = Path(__file__).resolve().parent.parent.parent
_PROJECTS_ROOT = _ROOT / "governance" / "context" / "projects"


# ── Project YAML helpers ─────────────────────────────────────────────────

def _load_project_yaml(project_id: str) -> Optional[dict]:
    """Load project.yaml from governance/context/projects/<id>/project.yaml."""
    yaml_path = _PROJECTS_ROOT / project_id / "project.yaml"
    if yaml_path.exists():
        try:
            return yaml.safe_load(yaml_path.read_text(encoding="utf-8"))
        except (yaml.YAMLError, OSError):
            pass
    return None


def _scan_projects() -> list[str]:
    """Scan governance/context/projects/ for directories containing project.yaml."""
    if not _PROJECTS_ROOT.exists():
        return []
    projects = []
    for d in _PROJECTS_ROOT.iterdir():
        if d.is_dir() and (d / "project.yaml").exists():
            projects.append(d.name)
    return sorted(projects)


# ── Global active project ────────────────────────────────────────────────
_active_project_id: Optional[str] = None


def get_active_project_id() -> str:
    """Return the currently active project ID."""
    global _active_project_id
    if _active_project_id:
        return _active_project_id
    # Check env var
    from aitest.config import config
    env_id = config.aitest_project
    if env_id:
        return env_id
    # Fall back: prefer web-automation if available, else first discovered project
    projects = _scan_projects()
    if "web-automation" in projects:
        return "web-automation"
    if projects:
        return projects[0]
    return "web-automation"


def set_active_project(project_id: str):
    """Set the active project globally."""
    global _active_project_id
    _active_project_id = project_id


def list_projects() -> list[str]:
    """List all available project IDs (have project.yaml)."""
    return _scan_projects()


# ── ProjectConfig (parsed project.yaml) ──────────────────────────────────

@dataclass
class ProjectConfig:
    """Parsed project.yaml values with safe defaults."""
    project_id: str = "web-automation"
    name: str = "Untitled Project"
    base_url: str = ""
    sut_type: str = "vue-hash-router"
    login_required: bool = False
    login_method: str = "form"
    discovery_strategy: str = "browser-use"
    chroma_namespace: str = "web-automation"
    test_project_code_path: str = ""
    test_project_type: str = ""

    @classmethod
    def from_yaml(cls, project_id: str, raw: Optional[dict] = None) -> "ProjectConfig":
        """Parse project.yaml dict into ProjectConfig."""
        if raw is None:
            raw = _load_project_yaml(project_id) or {}

        project = raw.get("project", {})
        application = raw.get("application", {})
        connection = raw.get("connection", {})
        discovery = raw.get("discovery", {})
        knowledge = raw.get("knowledge", {})
        test_project = raw.get("test_project", {})

        return cls(
            project_id=project.get("id", project_id),
            name=project.get("name", project_id),
            base_url=connection.get("base_url", ""),
            sut_type=application.get("type", "web"),
            login_required=connection.get("login_required", False),
            login_method=connection.get("login_method", "form"),
            discovery_strategy=discovery.get("strategy", "browser-use"),
            chroma_namespace=knowledge.get("chroma_namespace", project_id),
            test_project_code_path=test_project.get("code_path", ""),
            test_project_type=test_project.get("type", ""),
        )


# ── ProjectContext ───────────────────────────────────────────────────────

class ProjectContext:
    """
    Unified project context — the single entry point for project-specific access.

    Skills and agents should receive this from their caller, never construct it
    with hardcoded paths.

    Lifecycle:
      ctx = ProjectContext("web-automation")
      pages = ctx.list_pages()          # from .discovery/ or directory scan
      content = ctx.artifacts().read(...)  # file artifacts
      results = ctx.knowledge().search_issues(...)  # vector search
      rt = ctx.runtime()                # browser runtime
    """

    def __init__(self, project_id: str = None):
        self._project_id = project_id or get_active_project_id()
        self._config: Optional[ProjectConfig] = None
        self._artifacts: Optional[ArtifactStore] = None
        self._knowledge: Optional[KnowledgeStore] = None
        self._runtime: Optional[Runtime] = None

    # ── Identity ─────────────────────────────────────────────────────────

    @property
    def project_id(self) -> str:
        return self._project_id

    @property
    def config(self) -> ProjectConfig:
        if self._config is None:
            self._config = ProjectConfig.from_yaml(
                self._project_id,
                _load_project_yaml(self._project_id)
            )
        return self._config

    # ── Sub-stores (lazy) ────────────────────────────────────────────────

    def artifacts(self) -> ArtifactStore:
        if self._artifacts is None:
            self._artifacts = ArtifactStore(self._project_id)
        return self._artifacts

    def knowledge(self) -> KnowledgeStore:
        if self._knowledge is None:
            self._knowledge = KnowledgeStore(self.config.chroma_namespace)
        return self._knowledge

    def runtime(self, runtime_type: str = None) -> Runtime:
        """
        Get or create a runtime for this project.
        Currently only BrowserRuntime is implemented.
        """
        if self._runtime is None:
            cfg = self.config
            rt_type = runtime_type or cfg.sut_type or "browser"
            if rt_type in ("web", "browser", "vue-hash-router", "react-spa"):
                self._runtime = BrowserRuntime(base_url=cfg.base_url)
            else:
                # Future: APIRuntime, MiniAppRuntime, etc.
                self._runtime = BrowserRuntime(base_url=cfg.base_url)
        return self._runtime

    # ── Convenience: URL / type ──────────────────────────────────────────

    def sut_url(self) -> str:
        return self.config.base_url

    def sut_type(self) -> str:
        return self.config.sut_type

    # ── Convenience: page/module discovery ───────────────────────────────

    def list_modules(self) -> list[str]:
        return self.artifacts().list_modules()

    def list_pages(self, module: str = None) -> list[dict]:
        """
        List pages from .discovery/pages.json.
        If module specified, filter by top-level menu.
        Returns list of {id, title, route, menu_path, elements, ...}.
        """
        pages = self.artifacts().read_discovery_pages()
        if pages is None:
            # Fall back to directory-based discovery
            pages = self._discover_from_directories()
        if module:
            pages = [p for p in pages if p.get("menu_path", [None])[0] == module]
        return pages

    def _discover_from_directories(self) -> list[dict]:
        """Fallback: scan module/page directories for pages."""
        result = []
        for mod in self.artifacts().list_modules():
            for page_slug in self.artifacts().list_pages(mod):
                result.append({
                    "id": page_slug,
                    "title": page_slug.replace("-", " ").title(),
                    "route": "",
                    "menu_path": [mod, page_slug],
                    "discovered_at": "",
                })
        return result

    # ── Convenience: page context paths ──────────────────────────────────

    def page_dir(self, module: str, page: str) -> Path:
        """Get page directory path (for backward compat)."""
        return self.artifacts().path(module, "pages", page)

    def module_dir(self, module: str) -> Path:
        """Get module directory path (for backward compat)."""
        return self.artifacts().path(module)

    def project_dir(self) -> Path:
        """Get project directory path."""
        return _PROJECTS_ROOT / self._project_id

    def sop_status_path(self, module: str) -> Path:
        """Get SOP_STATUS file path for a module (for backward compat)."""
        return (
            self.artifacts()._sop_status_dir / f"SOP_STATUS_{module}.json"
        )


# ── Global accessor (cached for explicit IDs only) ──────────────────────

# Cache for explicitly-specified project IDs only.
# When project_id is None, the active project can change, so we bypass the cache.
_explicit_project_cache: dict[str, ProjectContext] = {}


def get_project(project_id: str = None) -> ProjectContext:
    """
    Get or create a ProjectContext. Cached for repeated access with explicit IDs.

    Usage:
        from aitest.platform import get_project
        ctx = get_project()              # active project (not cached — may change)
        ctx = get_project("web-automation")  # specific project (cached)
    """
    if project_id is not None:
        if project_id not in _explicit_project_cache:
            _explicit_project_cache[project_id] = ProjectContext(project_id)
        return _explicit_project_cache[project_id]
    return ProjectContext(project_id)
