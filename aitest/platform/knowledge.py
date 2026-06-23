"""
KnowledgeStore — project-scoped vector DB abstraction.

Collections are auto-prefixed with project chroma_namespace.
Callers never construct collection names manually.

Usage:
    store = ctx.knowledge()
    results = store.search_issues("element not found")
    store.index_page("user_list", content, metadata)
    store.switch_project("my-other-app")  # switches to different namespace
"""

from pathlib import Path
from typing import Optional

import chromadb
from chromadb.config import Settings

# ── ChromaDB path ────────────────────────────────────────────────────────
_CHROMA_DIR = Path(__file__).resolve().parent.parent.parent / "governance" / ".chroma"

# ── Base collection names (without namespace prefix) ─────────────────────
KNOWN_ISSUES = "known_issues"
PROJECT_CONTEXT = "project_context"
TECH_ANALYSIS = "tech_analysis"
PAGE_CONTEXT = "page_context"
PAGE_OBJECTS = "page_objects"

ALL_COLLECTIONS = [KNOWN_ISSUES, PROJECT_CONTEXT, TECH_ANALYSIS, PAGE_CONTEXT, PAGE_OBJECTS]

# ── Distance threshold for relevance ─────────────────────────────────────
RAG_DISTANCE_THRESHOLD = 1.5


def _get_client() -> chromadb.PersistentClient:
    """Get shared ChromaDB persistent client."""
    _CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(
        path=str(_CHROMA_DIR),
        settings=Settings(anonymized_telemetry=False)
    )


class KnowledgeStore:
    """
    Project-scoped knowledge base backed by ChromaDB.

    Collection names are prefixed: <namespace>_<base_name>
    e.g. web-automation_known_issues, dev-platform_tech_analysis
    """

    def __init__(self, namespace: str = "web-automation"):
        self._namespace = namespace
        self._client = _get_client()

    @property
    def namespace(self) -> str:
        return self._namespace

    # ── Collection name helpers ──────────────────────────────────────────

    def _col(self, base_name: str) -> str:
        """Prefix collection name with namespace."""
        return f"{self._namespace}_{base_name}"

    def _get_or_create(self, base_name: str):
        """Get or create a namespaced collection."""
        col_name = self._col(base_name)
        try:
            return self._client.get_collection(col_name)
        except Exception:
            return self._client.create_collection(name=col_name)

    def _get_fallback(self, base_name: str):
        """
        Get collection with namespace prefix.
        Fall back to bare name for legacy web-automation data.
        """
        col_name = self._col(base_name)
        try:
            return self._client.get_collection(col_name)
        except Exception:
            # Fallback: try bare name (legacy data before scoping)
            try:
                return self._client.get_collection(base_name)
            except Exception:
                return self._client.create_collection(name=col_name)

    # ── Search API ───────────────────────────────────────────────────────

    def search_issues(self, query: str, k: int = 5) -> list[dict]:
        """Search known issues."""
        return self._search(KNOWN_ISSUES, query, k)

    def search_context(self, query: str, k: int = 5) -> list[dict]:
        """Search project context docs."""
        return self._search(PROJECT_CONTEXT, query, k)

    def search_tech(self, query: str, k: int = 5) -> list[dict]:
        """Search technical analysis docs."""
        return self._search(TECH_ANALYSIS, query, k)

    def search_pages(self, query: str, k: int = 5) -> list[dict]:
        """Search page context docs."""
        return self._search(PAGE_CONTEXT, query, k)

    def search_objects(self, query: str, k: int = 5) -> list[dict]:
        """Search page object patterns."""
        return self._search(PAGE_OBJECTS, query, k)

    def _search(self, base_name: str, query: str, k: int) -> list[dict]:
        """Internal search with fallback."""
        try:
            collection = self._get_fallback(base_name)
            results = collection.query(query_texts=[query], n_results=k)
            docs = []
            if results.get("documents") and results["documents"][0]:
                for i, doc in enumerate(results["documents"][0]):
                    meta = results.get("metadatas", [[]])[0]
                    dist = results.get("distances", [[]])[0]
                    if dist and i < len(dist) and dist[i] <= RAG_DISTANCE_THRESHOLD:
                        docs.append({
                            "content": doc,
                            "metadata": meta[i] if meta and i < len(meta) else {},
                            "distance": dist[i] if dist and i < len(dist) else None,
                        })
            return docs
        except Exception:
            return []

    # ── Index API ────────────────────────────────────────────────────────

    def index_issue(self, issue_id: str, content: str, metadata: dict = None):
        """Index a known issue."""
        col = self._get_or_create(KNOWN_ISSUES)
        col.add(ids=[issue_id], documents=[content], metadatas=[metadata or {}])

    def index_context(self, doc_id: str, content: str, metadata: dict = None):
        """Index project context document."""
        col = self._get_or_create(PROJECT_CONTEXT)
        col.add(ids=[doc_id], documents=[content], metadatas=[metadata or {}])

    def index_tech(self, doc_id: str, content: str, metadata: dict = None):
        """Index technical analysis document."""
        col = self._get_or_create(TECH_ANALYSIS)
        col.add(ids=[doc_id], documents=[content], metadatas=[metadata or {}])

    def index_page(self, doc_id: str, content: str, metadata: dict = None):
        """Index page context document."""
        col = self._get_or_create(PAGE_CONTEXT)
        col.add(ids=[doc_id], documents=[content], metadatas=[metadata or {}])

    def index_object(self, obj_id: str, content: str, metadata: dict = None):
        """Index page object pattern."""
        col = self._get_or_create(PAGE_OBJECTS)
        col.add(ids=[obj_id], documents=[content], metadatas=[metadata or {}])

    # ── Utility ──────────────────────────────────────────────────────────

    def switch_project(self, namespace: str):
        """Switch to a different project namespace."""
        self._namespace = namespace

    def collection_stats(self) -> dict:
        """Return document counts per collection."""
        stats = {}
        for base_name in ALL_COLLECTIONS:
            try:
                col = self._get_fallback(base_name)
                stats[base_name] = col.count()
            except Exception:
                stats[base_name] = 0
        return stats

    def rebuild_namespace(self):
        """Ensure all namespaced collections exist (used during migration)."""
        for base_name in ALL_COLLECTIONS:
            self._get_or_create(base_name)
