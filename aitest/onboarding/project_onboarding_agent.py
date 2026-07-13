"""
Onboarding Agent — orchestrates project auto-discovery from URL to ready-to-test.

Flow:
  1. User provides URL + credentials + project name
  2. Validate login
  3. BrowserUseDiscovery.scan_menu() → menu_tree.json
  4. [HITL] User reviews/edits menu tree
  5. BrowserUseDiscovery.discover_pages() → pages.json
  6. Observe each page → PAGE_CONTEXT.md
  7. Generate project.yaml
  8. Index into KnowledgeStore
  9. Project ready

Usage:
    agent = ProjectOnboardingAgent()
    result = await agent.onboard(
        project_id="my-app",
        base_url="https://example.com",
        credentials={"username": "admin", "password": "pass"},
        app_type="vue-hash-router",
    )
"""
import asyncio
import json
import logging
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional, Callable

from aitest.platform.context import get_project, ProjectContext
from aitest.discovery.browser_use import BrowserUseDiscovery
from aitest.discovery.base import PageRecord, MenuNode, _serialize_menu

logger = logging.getLogger(__name__)


# ── Onboarding State ─────────────────────────────────────────────────────

class OnboardingStep(str, Enum):
    INIT = "init"
    VALIDATING = "validating"
    SCANNING_MENU = "scanning_menu"
    CONFIRM_MENU = "confirm_menu"      # HITL pause
    DISCOVERING_PAGES = "discovering_pages"
    OBSERVING_PAGES = "observing_pages"
    GENERATING_CONFIG = "generating_config"
    INDEXING = "indexing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class OnboardingState:
    """Tracks onboarding progress across steps."""
    session_id: str
    project_id: str
    base_url: str
    app_type: str = "vue-hash-router"
    step: OnboardingStep = OnboardingStep.INIT
    progress: float = 0.0          # 0.0 - 1.0
    current_page: str = ""
    total_pages: int = 0
    completed_pages: int = 0
    menu_tree: list[dict] = field(default_factory=list)
    pages: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    result: dict = field(default_factory=dict)
    started_at: str = ""
    completed_at: str = ""

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "base_url": self.base_url,
            "step": self.step.value,
            "progress": self.progress,
            "current_page": self.current_page,
            "total_pages": self.total_pages,
            "completed_pages": self.completed_pages,
            "menu_tree": self.menu_tree,
            "pages": self.pages,
            "errors": self.errors[-5:],  # last 5 errors
            "result": self.result,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


# ── In-memory session store ──────────────────────────────────────────────
# ★ v2.9: OwnedDict — values auto-registered in LifecycleRegistry,
# auto-disposed on pop/delete, OwnershipChecker-verifiable.

from aitest.platform.ownership import OwnedDict
from aitest.platform.paths import get_workstudy
_sessions: OwnedDict[str, OnboardingState] = OwnedDict(
    "onboarding-sessions", owner="onboarding:module", ttl_s=7200, max_size=200,
)
_SESSION_MAX_AGE_S = 7200  # 2 hours — sessions older than this are cleaned


def get_session(session_id: str) -> Optional[OnboardingState]:
    return _sessions.get(session_id)


def cleanup_stale_sessions(max_age_s: float = _SESSION_MAX_AGE_S) -> int:
    """Remove sessions older than max_age_s. Returns number cleaned.

    Terminal sessions (completed/failed/cancelled) are cleaned immediately.
    Non-terminal sessions are cleaned if they exceed max_age_s.
    OwnedDict.__delitem__ triggers lifecycle dispose chain automatically.
    """
    import time as _time
    now = _time.time()
    stale = []
    for sid, state in list(_sessions.items()):
        is_terminal = state.step.value in ("completed", "failed", "cancelled")
        try:
            started = _time.mktime(_time.strptime(
                state.started_at[:19], "%Y-%m-%dT%H:%M:%S"
            )) if state.started_at else 0
        except Exception:
            started = 0
        age = now - started if started else 0
        if is_terminal or (started and age > max_age_s):
            stale.append(sid)
    for sid in stale:
        try:
            del _sessions[sid]  # OwnedDict triggers lifecycle.dispose()
        except Exception:
            pass
    return len(stale)


# ── Onboarding Agent ─────────────────────────────────────────────────────

class ProjectOnboardingAgent:
    """
    Orchestrates full project onboarding.

    Usage:
        agent = ProjectOnboardingAgent()
        state = await agent.start("my-app", "https://example.com", {"username": "admin", "password": "pass"})
        # ... poll state or subscribe to WebSocket
        result = await agent.wait()
    """

    def __init__(self, headless: bool = True, provider: str = None):
        self.headless = headless
        self.provider = provider
        self._state: Optional[OnboardingState] = None
        self._discovery: Optional[BrowserUseDiscovery] = None
        self._on_step: Optional[Callable] = None  # progress callback
        self._pause_event: Optional[asyncio.Event] = None  # HITL pause
        self._confirm_result: Optional[list[dict]] = None    # HITL menu edits
        self._cancelled: bool = False
        self._output_path: str = ""
        self._checkpoint_dir: Optional[Path] = None

    # ── Public API ───────────────────────────────────────────────────────

    async def start(
        self,
        project_id: str,
        base_url: str,
        credentials: dict = None,
        app_type: str = "vue-hash-router",
        source_type: str = "url",
        project_path: str = "",
        output_path: str = "",
        observe_pages: bool = True,
        generate_page_objects: bool = False,
        resume: bool = False,
    ) -> OnboardingState:
        """
        Start onboarding. Returns immediately with initial state.

        Args:
            source_type: "url" (browser discovery) | "local" (source discovery) | "both" (merge)
            project_path: Local project path (for source_type=local/both)
            output_path: Test project output directory.
            resume: If True, load checkpoint and skip completed steps.
        """
        # Resolve output_path
        if not output_path and source_type == "local" and project_path:
            output_path = str(Path(project_path) / "tests")
        self._output_path = output_path

        # Auto-create output directory
        if output_path:
            try:
                Path(output_path).mkdir(parents=True, exist_ok=True)
            except OSError:
                pass

        # Load checkpoint if resuming
        checkpoint = None
        if resume and output_path:
            checkpoint = self.load_checkpoint(output_path)

        safe_project_id = re.sub(r"[^a-zA-Z0-9_-]+", "-", project_id).strip("-")[:80] or "project"
        session_id = f"onboard-{safe_project_id}-{uuid.uuid4().hex[:8]}"
        initial_step = OnboardingStep.INIT
        initial_progress = 0.0

        if checkpoint:
            initial_step = OnboardingStep(checkpoint.get("step", "init"))
            initial_progress = checkpoint.get("progress", 0.0)
            logger.info(f"Resuming onboarding for {project_id} from step={initial_step.value} progress={initial_progress}")

        state = OnboardingState(
            session_id=session_id,
            project_id=project_id,
            base_url=base_url or project_path,
            app_type=app_type,
            step=initial_step if resume else OnboardingStep.INIT,
            progress=initial_progress if resume else 0.0,
            started_at=datetime.now().isoformat(),
        )
        # Restore checkpoint data
        if checkpoint:
            state.menu_tree = checkpoint.get("menu_tree", [])
            state.pages = checkpoint.get("pages", [])

        self._state = state
        _sessions[session_id] = state

        # Start background processing
        from aitest.platform.ownership import get_task_guard
        get_task_guard().create_task(
            self._run(
                project_id, base_url, credentials, app_type,
                source_type, project_path,
                observe_pages, generate_page_objects,
                checkpoint=checkpoint if resume else None,
            ),
            owner=f"onboarding:start:{project_id}",
            lifecycle_id=f"onboarding-task:{session_id}",
            ttl_s=7200,  # 2h — cancel if onboarding hangs
        )
        return state

    async def _run(
        self,
        project_id: str,
        base_url: str,
        credentials: dict,
        app_type: str,
        source_type: str,
        project_path: str,
        observe_pages: bool,
        generate_page_objects: bool,
        checkpoint: dict = None,
    ):
        """Background onboarding execution. Supports url, local, or both.

        Cancel-safe: checks self._cancelled after each major step.
        Checkpoint: saves partial results after key milestones for recovery.
        Resume: if checkpoint provided, skips completed steps.
        """
        state = self._state
        browser_pages = []
        source_routes = []
        source_components = []
        source_apis = []
        confirmed_menu = []

        # Resume: restore already-discovered data
        observed_offset = 0
        if checkpoint:
            confirmed_menu = checkpoint.get("menu_tree", [])
            observed_offset = checkpoint.get("observed_index", 0)
            logger.info(f"Resume checkpoint: step={checkpoint.get('step')}, "
                        f"menu={len(confirmed_menu)} items, observed_offset={observed_offset}")

        def _cancelled_check() -> bool:
            if self._cancelled:
                logger.info(f"Onboarding cancelled by user: {project_id}")
                return True
            return False

        try:
            # ── Source Discovery (local project) ──
            if source_type in ("local", "both") and project_path:
                self._set_step(OnboardingStep.VALIDATING, 0.03)
                if _cancelled_check(): return
                try:
                    from alice_discovery import FrameworkDetector, SourceDiscoveryPipeline
                    detector = FrameworkDetector()
                    # Resolve actual frontend root (may be subdir for multi-module projects)
                    self._set_step(OnboardingStep.VALIDATING, 0.06)
                    pkg_path = FrameworkDetector.find_package_json(project_path)
                    actual_project_path = str(pkg_path.parent) if pkg_path else project_path
                    framework = detector.detect(actual_project_path)
                    if framework:
                        self._set_step(OnboardingStep.SCANNING_MENU, 0.12)
                        pipeline = SourceDiscoveryPipeline(project_id, project_path=actual_project_path, framework=framework)
                        pipeline._run_extractors()
                        self._set_step(OnboardingStep.SCANNING_MENU, 0.18)
                        knowledge = pipeline.build_knowledge()
                        source_routes = knowledge.routes
                        source_components = knowledge.components
                        source_apis = knowledge.apis

                        # Build menu from source routes
                        source_menu = pipeline._routes_to_menu(source_routes)
                        state.menu_tree = _serialize_menu(source_menu)

                        # Build pages from source (already in knowledge.pages)
                        source_pages = knowledge.pages
                        logger.info(f"Source discovery: {len(source_routes)} routes, {len(source_components)} components, {len(source_apis)} APIs, {len(source_pages)} pages")
                    else:
                        hint = (
                            f"No package.json found at {project_path} (root or 1-level subdirs). "
                            "Source code analysis skipped. "
                            "Provide a valid frontend project path (e.g., D:/Projects/my-vue-app), "
                            "or use source_type='url' for browser-based discovery."
                        )
                        logger.warning(hint)
                        state.errors.append(hint)
                except Exception as e:
                    logger.exception(f"Source discovery failed: {e}")
                    state.errors.append(f"Source discovery: {e}")

            # ── Browser Discovery (URL) ──
            if source_type in ("url", "both") and base_url:
                self._set_step(OnboardingStep.VALIDATING, 0.08)
                if _cancelled_check(): return
                self._discovery = BrowserUseDiscovery(
                    project_id=project_id,
                    base_url=base_url,
                    credentials=credentials,
                    headless=self.headless,
                    provider=self.provider,
                )
                self._set_step(OnboardingStep.VALIDATING, 0.12)
                if credentials:
                    logged_in = await self._discovery.runtime.login(credentials)
                    if not logged_in:
                        logger.warning(f"Login may have failed for {project_id} — continuing anyway")

                self._set_step(OnboardingStep.SCANNING_MENU, 0.18)
                if _cancelled_check(): return
                menu = await self._discovery.discover_menu()

                # Merge with source menu if available
                if source_routes:
                    source_menu_nodes = self._source_routes_to_menu_nodes(source_routes)
                    state.menu_tree = _serialize_menu(menu) if menu else _serialize_menu(source_menu_nodes)
                else:
                    state.menu_tree = _serialize_menu(menu)

                # ── Save checkpoint: menu discovered ──
                self._save_checkpoint({
                    "project_id": project_id,
                    "step": "confirm_menu",
                    "menu_tree": state.menu_tree,
                    "progress": 0.30,
                })

                # HITL
                self._set_step(OnboardingStep.CONFIRM_MENU, 0.30)
                if self._on_step:
                    self._on_step(state)
                confirmed_menu = await self._wait_for_confirm(state.menu_tree)
                if _cancelled_check(): return

                # Discover pages from browser
                self._set_step(OnboardingStep.DISCOVERING_PAGES, 0.40)
                if _cancelled_check(): return
                pages = await self._discovery.discover_pages(
                    self._discovery._dicts_to_menu_nodes(confirmed_menu or state.menu_tree)
                )

                # ── Save checkpoint: pages discovered ──
                raw_pages = [
                    {"id": p.id, "title": p.title, "route": p.route,
                     "menu_path": p.menu_path, "elements": p.elements}
                    for p in pages
                ] if pages else []
                self._save_checkpoint({
                    "project_id": project_id,
                    "step": "observing_pages",
                    "menu_tree": confirmed_menu or state.menu_tree,
                    "pages": raw_pages,
                    "progress": 0.50,
                })

                # Observe pages
                if observe_pages and pages:
                    self._set_step(OnboardingStep.OBSERVING_PAGES, 0.50)
                    state.total_pages = len(pages)
                    for i, page in enumerate(pages):
                        if _cancelled_check():
                            # Save progress so we can resume from this page
                            self._save_checkpoint({
                                "project_id": project_id,
                                "step": "observing_pages",
                                "menu_tree": confirmed_menu or state.menu_tree,
                                "pages": raw_pages,
                                "observed_index": i,
                                "progress": 0.50 + 0.35 * (i / len(pages)),
                            })
                            return
                        state.current_page = page.title
                        state.completed_pages = i
                        state.progress = 0.50 + 0.35 * (i / len(pages))
                        try:
                            await self._discovery.observe_page(page)
                        except Exception as e:
                            state.errors.append(f"Observe {page.route}: {e}")
                        pages[i] = page
                    state.completed_pages = len(pages)

                browser_pages = pages

            # ── Merge browser + source ──
            if source_routes and browser_pages:
                self._set_step(OnboardingStep.GENERATING_CONFIG, 0.85)
                if _cancelled_check(): return
                from alice_discovery import MetadataMergeEngine
                merger = MetadataMergeEngine()
                merged = merger.merge(
                    browser_pages=browser_pages,
                    source_routes=source_routes,
                    source_components=source_components,
                    source_apis=source_apis,
                )
                final_pages = []
                for mp in merged:
                    final_pages.append({
                        "id": mp.page_id,
                        "title": mp.title.value,
                        "route": mp.route.value,
                        "menu_path": mp.menu_path,
                        "elements": {
                            "search_fields": [{"label": e.label, "type": e.type} for e in mp.elements.search_fields],
                            "action_buttons": [{"label": e.label} for e in mp.elements.action_buttons],
                            "table_columns": mp.elements.table_columns,
                            "has_pagination": mp.elements.has_pagination.value,
                            "has_checkbox_column": mp.elements.has_checkbox_column.value,
                        },
                        "component_file": mp.component_file.value,
                        "permissions": [p.code.value for p in mp.permissions],
                        "api_count": len(mp.api_endpoints),
                        "confidence": mp.confidence,
                        "discovered_from": [s.value for s in mp.discovered_from],
                    })
                state.pages = final_pages
                logger.info(f"Merged: {len(final_pages)} pages (browser+source)")
            elif browser_pages:
                state.pages = [
                    {"id": p.id, "title": p.title, "route": p.route, "menu_path": p.menu_path, "elements": p.elements}
                    for p in browser_pages
                ]
            elif source_routes:
                final_pages = []
                for sr in source_routes:
                    final_pages.append({
                        "id": (sr.name.value or sr.path.value).strip("/").replace("/", "-"),
                        "title": sr.title.value or sr.meta.get("title", ""),
                        "route": sr.path.value,
                        "menu_path": [sr.meta.get("title", sr.title.value or "")],
                        "elements": {},
                        "component_file": sr.component_file.value,
                        "permissions": [sr.meta.get("permission", "")] if sr.meta.get("permission") else [],
                        "confidence": 0.85,
                        "discovered_from": ["vue-router"],
                    })
                state.pages = final_pages

            # Step 6: Write .discovery/ + project.yaml
            self._set_step(OnboardingStep.GENERATING_CONFIG, 0.90)
            if _cancelled_check(): return
            self._write_project_files(project_id, base_url or project_path, app_type, confirmed_menu or state.menu_tree, state.pages)

            # Step 7: Index into KnowledgeStore
            self._set_step(OnboardingStep.INDEXING, 0.95)
            if _cancelled_check(): return
            self._index_to_knowledge(project_id, state.pages)

            # Done
            final_pages_list = state.pages or []
            final_menu = confirmed_menu or state.menu_tree or []
            state.step = OnboardingStep.COMPLETED
            state.progress = 1.0
            state.completed_at = datetime.now().isoformat()

            # Clear checkpoint on success
            self.clear_checkpoint(self._output_path)

            # ── Build diagnostics ──
            # BrowserRuntime delegates login to driver; check driver's state
            login_ok = None
            if self._discovery and self._discovery.runtime._driver:
                login_ok = getattr(self._discovery.runtime._driver, '_logged_in', None)

            diagnostics = {
                "login_attempted": bool(credentials),
                "login_succeeded": login_ok,
                "browser_pages": len(browser_pages) if browser_pages else 0,
                "source_routes": len(source_routes) if source_routes else 0,
                "total_pages": len(final_pages_list),
                "menu_groups": len(final_menu),
                "source_type": source_type,
                "discovery_method": (
                    "merged" if (source_routes and browser_pages) else
                    "browser" if browser_pages else
                    "source" if source_routes else
                    "none"
                ),
            }

            state.result = {
                "project_id": project_id,
                "pages_discovered": len(final_pages_list),
                "menu_groups": len(final_menu),
                "source_type": source_type,
                "project_yaml_path": str(self._project_yaml_path(project_id)),
                "diagnostics": diagnostics,
            }

            # Add diagnostic warnings when 0 pages discovered
            if len(final_pages_list) == 0 and source_type in ("url", "both"):
                if not diagnostics["login_succeeded"] and credentials:
                    state.errors.append(
                        f"⚠️ 登录可能失败 — 未检测到导航菜单。"
                        f"请检查用户名/密码是否正确，或手动输入页面列表。"
                    )
                else:
                    state.errors.append(
                        f"⚠️ 未发现任何页面 — URL 可能不是有效的 Web 应用，"
                        f"或需要特定的登录方式。请尝试手动输入页面路由。"
                    )

        except Exception as e:
            logger.exception(f"Onboarding failed for {project_id}")
            state.step = OnboardingStep.FAILED
            state.errors.append(str(e))

        finally:
            await self._release_resources()

    # ── HITL: Menu Confirmation ──────────────────────────────────────────

    async def confirm_menu(self, session_id: str, edited_menu: list[dict] = None):
        """User confirms or edits the discovered menu tree."""
        state = _sessions.get(session_id)
        if not state:
            raise ValueError(f"Session {session_id} not found")
        self._confirm_result = edited_menu or state.menu_tree
        if self._pause_event:
            self._pause_event.set()

    async def cancel(self, session_id: str):
        """Cancel onboarding — stop background work, save checkpoint, release resources."""
        self._cancelled = True
        state = _sessions.get(session_id)
        if state:
            state.step = OnboardingStep.CANCELLED
            # Save checkpoint with current state for potential recovery
            self._save_checkpoint({
                "project_id": state.project_id,
                "step": state.step.value,
                "menu_tree": state.menu_tree,
                "pages": state.pages,
                "progress": state.progress,
                "cancelled_at": datetime.now().isoformat(),
            })
            if self._pause_event:
                self._pause_event.set()
        # Release browser immediately — don't wait for _run() to finish
        await self._release_resources()

    async def _wait_for_confirm(self, menu_tree: list[dict]) -> list[dict]:
        """Wait for user confirmation (HITL). Auto-continue after timeout if no callback."""
        if self._on_step is None:
            # No UI callback — auto-continue
            return menu_tree
        self._pause_event = asyncio.Event()
        try:
            await asyncio.wait_for(self._pause_event.wait(), timeout=300)  # 5 min timeout
        except asyncio.TimeoutError:
            logger.info("Menu confirmation timeout — auto-continuing")
        finally:
            self._pause_event = None
        return self._confirm_result or menu_tree

    # ── File generation ──────────────────────────────────────────────────

    def _write_project_files(
        self, project_id: str, base_url: str, app_type: str,
        menu: list[dict], pages: list,
    ):
        """Write project.yaml + MODULE_INDEX.md + PAGE_CONTEXT.md per page.
        Handles both PageRecord objects and plain dicts.
        """
        ctx = get_project(project_id)
        arts = ctx.artifacts()

        # Helper: get attribute from PageRecord or dict
        def _get(p, key, default=""):
            if isinstance(p, dict):
                return p.get(key, default)
            return getattr(p, key, default)

        def _get_elements(p):
            if isinstance(p, dict):
                return p.get("elements", {})
            return getattr(p, "elements", {})

        def _get_discovered(p):
            if isinstance(p, dict):
                return p.get("discovered_at", "")
            return getattr(p, "discovered_at", "")

        def _get_route(p):
            if isinstance(p, dict):
                return p.get("route", "")
            return getattr(p, "route", "")

        # project.yaml
        yaml_content = f"""# TLO Project — {project_id}
project:
  id: "{project_id}"
  name: "{project_id}"

application:
  type: "web"
  runtime: "browser"

connection:
  base_url: "{base_url}"
  login_required: true
  login_method: "form"

discovery:
  strategy: "browser-use"

knowledge:
  chroma_namespace: "{project_id}"

test_project:
  code_path: "{self._output_path}"
  type: "pytest-selenium"
  categories:
    - smoke
    - functional
"""
        arts.write_project(yaml_content, "project.yaml")

        # MODULE_INDEX.md
        module_lines = ["# Module Index\n", f"\nDiscovered: {datetime.now().isoformat()}\n"]
        by_module = {}
        for p in pages:
            menu_path = _get(p, "menu_path", [])
            mod = menu_path[0] if menu_path else "Unknown"
            by_module.setdefault(mod, []).append(p)
        for mod, mod_pages in by_module.items():
            module_lines.append(f"\n## {mod}\n")
            for p in mod_pages:
                title = _get(p, "title")
                route = _get_route(p)
                pid = _get(p, "id")
                module_lines.append(f"- [{title}]({route}) — `{pid}`\n")
        arts.write_project("\n".join(module_lines), "MODULE_INDEX.md")

        # Initial SOP_STATUS per module → kanban shows discovered modules
        for mod, mod_pages in by_module.items():
            page_ids = [_get(p, "id") for p in mod_pages]
            arts.write_sop_status(mod, {
                "status": "discovered",
                "completed_phases": [],
                "failed_phases": [],
                "pages_processed": page_ids,
                "artifact_count": len(mod_pages),
                "run_id": "",
                "updated_at": datetime.now().isoformat(),
                "note": f"Onboarded — {len(mod_pages)} pages discovered",
            })

        # PAGE_CONTEXT.md per page
        for p in pages:
            menu_path = _get(p, "menu_path", [])
            module = menu_path[0] if menu_path else "pages"
            page_slug = _get(p, "id")
            title = _get(p, "title")
            route = _get_route(p)
            discovered = _get_discovered(p)
            elements = _get_elements(p)

            ctx_md = f"""# {title}

> Route: `{route}` | Module: {module} | Discovered: {discovered}

## Search Fields
"""
            for sf in elements.get("search_fields", []):
                ctx_md += f"- **{sf.get('label', '?')}** ({sf.get('type', 'input')}): {sf.get('html_hint', '')}\n"

            ctx_md += "\n## Action Buttons\n"
            for btn in elements.get("action_buttons", []):
                ctx_md += f"- **{btn.get('label', '?')}** — `{btn.get('css_hint', '')}`\n"

            ctx_md += "\n## Table Columns\n"
            for col in elements.get("table_columns", []):
                ctx_md += f"- {col}\n"

            ctx_md += f"\n- **Pagination**: {'Yes' if elements.get('has_pagination') else 'No'}\n"
            ctx_md += f"- **Checkbox Column**: {'Yes' if elements.get('has_checkbox_column') else 'No'}\n"

            arts.write(ctx_md, module, "pages", page_slug, "PAGE_CONTEXT.md")

    def _index_to_knowledge(self, project_id: str, pages: list):
        """Index discovered pages into KnowledgeStore. Handles dicts and PageRecords."""
        ctx = get_project(project_id)
        store = ctx.knowledge()

        for p in pages:
            if isinstance(p, dict):
                pid, title, route = p.get("id",""), p.get("title",""), p.get("route","")
                menu = p.get("menu_path", [])
                elements = p.get("elements", {})
            else:
                pid, title, route = p.id, p.title, p.route
                menu = p.menu_path
                elements = p.elements

            elements_text = json.dumps(elements, ensure_ascii=False)
            store.index_page(
                f"{project_id}_{pid}",
                f"Page: {title}\nRoute: {route}\nPath: {' > '.join(menu)}\nElements: {elements_text}",
                {"project_id": project_id, "page_id": pid, "route": route, "title": title}
            )

    def _source_routes_to_menu_nodes(self, routes: list) -> list:
        """Convert RouteMetadata list to menu tree dicts (for state serialization)."""
        nodes = []
        for r in routes:
            node = {
                "label": r.meta.get("title", r.title.value) if hasattr(r, 'meta') else str(r),
                "route": r.path.value if hasattr(r, 'path') else "",
                "type": "menu_group" if (hasattr(r, 'children') and r.children) else "page",
            }
            if hasattr(r, 'children') and r.children:
                node["children"] = self._source_routes_to_menu_nodes(r.children)
            nodes.append(node)
        return nodes

    def _project_yaml_path(self, project_id: str) -> Path:
        return (
            get_workstudy()
            / "governance" / "context" / "projects" / project_id / "project.yaml"
        )

    # ── Helpers ──────────────────────────────────────────────────────────

    async def _release_resources(self):
        """Release BrowserUseDiscovery, browser, and internal state.

        Called on terminal states (completed/failed/cancelled) and from
        external cancel. Idempotent — safe to call multiple times.
        Lifecycle unregistration handled by OwnedDict — not here.
        """
        # 1. Close BrowserUseDiscovery (closes Browser + Playwright)
        discovery = self._discovery
        self._discovery = None
        if discovery:
            try:
                await discovery.close()
            except Exception as e:
                logger.debug("Discovery close error (ignored): %s", e)

        # 2. Clear HITL state
        self._pause_event = None
        self._confirm_result = None
        self._on_step = None

    def _set_step(self, step: OnboardingStep, progress: float):
        if self._state:
            self._state.step = step
            self._state.progress = progress

    def _checkpoint_path(self) -> Optional[Path]:
        """Directory for partial results during onboarding. Created on first write."""
        if self._checkpoint_dir:
            return self._checkpoint_dir
        if not self._output_path:
            return None
        cp = Path(self._output_path) / ".tlo" / "onboarding_checkpoint"
        cp.mkdir(parents=True, exist_ok=True)
        self._checkpoint_dir = cp
        return cp

    def _save_checkpoint(self, checkpoint_data: dict) -> None:
        """Save partial onboarding results so we can resume after cancel."""
        cp = self._checkpoint_path()
        if not cp:
            return
        try:
            cp_file = cp / "checkpoint.json"
            cp_file.write_text(json.dumps(checkpoint_data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError as e:
            logger.debug("Checkpoint save failed (non-fatal): %s", e)

    @staticmethod
    def load_checkpoint(output_path: str) -> Optional[dict]:
        """Load partial onboarding results from a previous cancelled session. Returns None if not found."""
        cp_file = Path(output_path) / ".tlo" / "onboarding_checkpoint" / "checkpoint.json"
        if not cp_file.exists():
            return None
        try:
            return json.loads(cp_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def clear_checkpoint(output_path: str) -> None:
        """Remove checkpoint after successful completion."""
        cp_file = Path(output_path) / ".tlo" / "onboarding_checkpoint" / "checkpoint.json"
        try:
            cp_file.unlink(missing_ok=True)
        except OSError:
            pass

    def on_progress(self, callback: Callable):
        """Register progress callback for UI updates."""
        self._on_step = callback
