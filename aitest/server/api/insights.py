"""Read-only query APIs for the Studio insight surfaces.

This module is deliberately an adapter layer: it exposes existing memory and
knowledge stores to the UI without changing their storage or execution paths.
"""

from __future__ import annotations

from fastapi import APIRouter, Query


insights_router = APIRouter(prefix="/api/v1", tags=["studio-insights"])


@insights_router.get("/kanban/overview")
async def kanban_overview(project_id: str = Query("")):
    """Aggregate the existing run-event phase read model for the Kanban UI."""
    try:
        from aitest.platform.artifacts import ArtifactStore
        from aitest.server.api.kanban import get_module_phase_progress

        store = ArtifactStore(project_id.strip() or "web-automation")
        modules = []
        for module in store.list_modules():
            progress = get_module_phase_progress(module)
            progress["pages"] = store.list_pages(module)
            progress["page_count"] = len(progress["pages"])
            modules.append(progress)
        return {"modules": modules}
    except Exception as exc:
        return {"modules": [], "error": str(exc)[:200]}


@insights_router.get("/memory/stats")
async def memory_stats():
    try:
        from aitest.platform.testing_memory_store import TestingMemoryStore

        store = TestingMemoryStore()
        return {"available": store.available(), "collections": store.stats()}
    except Exception as exc:
        return {"available": False, "collections": {}, "error": str(exc)[:200]}


@insights_router.get("/memory/search")
async def memory_search(
    query: str = Query("", min_length=0),
    collection: str = "",
    top_k: int = Query(12, ge=1, le=20),
):
    if not query.strip():
        return {"query": query, "collection": collection or "all", "results": []}
    try:
        from aitest.platform.testing_memory_store import COLLECTIONS, TestingMemoryStore

        store = TestingMemoryStore()
        collections = [collection] if collection in COLLECTIONS else list(COLLECTIONS)
        results = []
        for name in collections:
            for item in store.search(name, query.strip(), top_k=top_k):
                results.append({"collection": name, **item})
        results.sort(key=lambda item: item.get("score", 0), reverse=True)
        return {"query": query, "collection": collection or "all", "results": results[:top_k]}
    except Exception as exc:
        return {"query": query, "collection": collection or "all", "results": [], "error": str(exc)[:200]}


@insights_router.get("/knowledge/stats")
async def knowledge_stats(namespace: str = "web-automation"):
    try:
        from aitest.platform.knowledge import get_knowledge

        store = get_knowledge(namespace)
        return {
            "namespace": store.namespace,
            "available": store.available(),
            "collections": store.collection_stats(),
        }
    except Exception as exc:
        return {"namespace": namespace, "available": False, "collections": {}, "error": str(exc)[:200]}


@insights_router.get("/knowledge/search")
async def knowledge_search(
    query: str = Query("", min_length=0),
    collection: str = "all",
    top_k: int = Query(12, ge=1, le=20),
    namespace: str = "web-automation",
):
    if not query.strip():
        return {"query": query, "collection": collection, "results": []}
    try:
        from aitest.platform.knowledge import get_knowledge

        results = get_knowledge(namespace).search(query.strip(), collection=collection, top_k=top_k)
        return {"query": query, "collection": collection, "results": results}
    except Exception as exc:
        return {"query": query, "collection": collection, "results": [], "error": str(exc)[:200]}
