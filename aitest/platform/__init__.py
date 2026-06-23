"""
TLO Platform Kernel — 4 abstractions that define TLO as a platform, not a test framework.

Layers:
  ProjectContext  — unified access to project config, paths, artifacts
  Runtime         — abstract browser/api/miniapp execution (Skills never know what's underneath)
  KnowledgeStore  — vector DB abstraction (project-scoped ChromaDB)
  ArtifactStore   — file-based artifact read/write (SOP_STATUS, page contexts, reports)

Skills NEVER know project directory structure. They call:
  ctx.artifacts().read("pages", page_id, "PAGE_CONTEXT.md")
  ctx.runtime().click("新增")
  ctx.knowledge().search_issues("element not found")

Not:
  GOVERNANCE / "context" / "projects" / "web-automation" / "modules" / module / ...
"""

from .context import ProjectContext, get_project, set_active_project, list_projects
from .runtime import Runtime, BrowserRuntime
from .knowledge import KnowledgeStore
from .artifacts import ArtifactStore

__all__ = [
    "ProjectContext",
    "get_project",
    "set_active_project",
    "list_projects",
    "Runtime",
    "BrowserRuntime",
    "KnowledgeStore",
    "ArtifactStore",
]
