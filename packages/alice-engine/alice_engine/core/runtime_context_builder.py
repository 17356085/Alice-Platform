"""Internal runtime context collaborator for AgentLoop-like orchestrators."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from alice_engine.core.path_utils import (
    _CONTEXT_MODULES,
    _get_project_dir,
    get_test_project_root,
    page_slug_to_underscore,
    slug_to_page_name,
)


class RuntimeContextBuilder:
    """Build runtime context and prompt context variables outside AgentLoop."""

    def __init__(
        self,
        *,
        state,
        module: str,
        page: str,
        goal: str,
        focused_context: str | None,
        token_budget: int,
        log_fn: Callable[[str], None],
        context_modules: Path | None = None,
        get_test_project_root_fn: Callable[[], Path | None] = get_test_project_root,
        get_project_dir_fn: Callable[[], Path] = _get_project_dir,
        create_testing_memory_store_fn: Callable[[], Any] | None = None,
        get_knowledge_service_fn: Callable[[], Any] | None = None,
        build_context_fn: Callable[..., Any] | None = None,
    ) -> None:
        self.state = state
        self.module = module
        self.page = page
        self.goal = goal
        self.focused_context = focused_context
        self.token_budget = token_budget
        self._log = log_fn
        self._context_modules = context_modules or _CONTEXT_MODULES
        self._get_test_project_root = get_test_project_root_fn
        self._get_project_dir = get_project_dir_fn
        self._create_testing_memory_store = create_testing_memory_store_fn
        self._get_knowledge_service = get_knowledge_service_fn
        self._build_context_fn = build_context_fn

    def build_runtime_context(self) -> dict:
        """Assemble memory / knowledge context and cache it in agent memory."""
        runtime_context = self.state.memory.setdefault("runtime_context", {})
        if runtime_context:
            return runtime_context

        module = self.module or ""
        page = self.page or ""
        query = " ".join(part for part in [module, page, self.goal] if part).strip() or module or page
        assembled = {
            "memory_context": {},
            "knowledge_context": {},
            "context_sources": [],
        }

        try:
            create_store = self._create_testing_memory_store
            if create_store is None:
                from alice_engine.platform_bridge import create_testing_memory_store

                create_store = create_testing_memory_store
            store = create_store()
            if store.available():
                memory_queries = []
                if query:
                    memory_queries = [
                        {"collection": "known_bugs", "query": query},
                        {"collection": "historical_failures", "query": query},
                        {"collection": "workflow_recipes", "query": query},
                    ]
                if memory_queries:
                    memory_context = store.search_multi(memory_queries, top_k=3)
                    if memory_context:
                        assembled["memory_context"] = memory_context
                        assembled["context_sources"].append("memory")
        except Exception as exc:
            self._log(f"[warn] memory context skipped: {exc}")

        try:
            get_knowledge = self._get_knowledge_service
            if get_knowledge is None:
                from alice_engine.platform_bridge import get_knowledge_service

                get_knowledge = get_knowledge_service
            knowledge = get_knowledge()
            if getattr(knowledge, "available", lambda: False)():
                knowledge_context = knowledge.search(
                    query=query or module or page or self.goal,
                    collection="all",
                    top_k=5,
                )
                if knowledge_context:
                    assembled["knowledge_context"] = {"results": knowledge_context}
                    assembled["context_sources"].append("knowledge")
        except Exception as exc:
            self._log(f"[warn] knowledge context skipped: {exc}")

        runtime_context.update(assembled)
        return runtime_context

    def build_context_vars(self, extra: dict | None = None) -> dict:
        """Construct context variables passed to skill execution."""
        vars_: dict[str, Any] = {
            "module": self.module,
            "page": self.page,
        }
        if self.state.memory.get("prev_output"):
            vars_["prev_output"] = str(self.state.memory["prev_output"])[:3000]
        if self.state.memory.get("tech_analysis_summary"):
            vars_["tech_analysis_summary"] = self.state.memory["tech_analysis_summary"]

        runtime_context = self.build_runtime_context()
        if runtime_context.get("memory_context"):
            vars_["memory_context"] = runtime_context["memory_context"]
        if runtime_context.get("knowledge_context"):
            vars_["knowledge_context"] = runtime_context["knowledge_context"]
        if runtime_context.get("context_sources"):
            vars_["context_sources"] = runtime_context["context_sources"]

        if self.module:
            page_name = slug_to_page_name(self.page) if self.page else ""
            page_underscore = page_slug_to_underscore(self.page) if self.page else ""
            test_project_root = self._get_test_project_root()

            project_ctx = self._get_project_dir() / "PROJECT_CONTEXT.md"
            if project_ctx.exists():
                vars_["project_context_path"] = str(project_ctx)

            if test_project_root:
                po_path = test_project_root / "page" / f"{self.module}_page" / f"{page_name}Page.py"
                if page_name and po_path.exists():
                    vars_["po_path"] = str(po_path)

                test_path = test_project_root / "script" / self.module / f"test_{page_underscore}.py"
                if page_underscore and test_path.exists():
                    vars_["test_path"] = str(test_path)

                po_dir = test_project_root / "page" / f"{self.module}_page"
                if po_dir.exists():
                    vars_["po_dir"] = str(po_dir)

                test_dir = test_project_root / "script" / self.module
                if test_dir.exists():
                    vars_["test_dir"] = str(test_dir)

            page_dir = self._context_modules / self.module / "pages" / self.page
            if self.page:
                vars_["page_dir"] = str(page_dir)

            if test_project_root and not vars_.get("builder_context"):
                try:
                    build_context = self._build_context_fn
                    if build_context is None:
                        from alice_engine.core.context_builder import build_context

                    else:
                        build_context = self._build_context_fn
                    builder_ctx = build_context(
                        module=self.module,
                        project_root=test_project_root,
                        page=self.page,
                        task_description=self.goal,
                    )
                    vars_["builder_context"] = builder_ctx
                    self._log(
                        f"  ContextBuilder: {builder_ctx.source_count} files, "
                        f"{len(builder_ctx.patterns)} patterns, "
                        f"memory={'yes' if builder_ctx.memory_hints else 'no'}"
                    )
                except Exception as exc:
                    self._log(f"[warn] context discovery skipped: {exc}")

        if self.focused_context:
            vars_["focused_context"] = self.focused_context

        estimated_used = self.state.step * 2000
        vars_["token_budget_remaining"] = max(1000, self.token_budget - estimated_used)

        if extra:
            vars_.update(extra)
        return vars_
