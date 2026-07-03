"""Cross-system event query — given a run_id, find all related data.

Phase 2: unified correlation via run_id as the causal root.

Usage:
    from aitest.platform.event_query import EventQueryService

    service = EventQueryService(store=..., audit=...)
    result = service.query_by_run("run-abc123")
"""

from aitest.platform.run_store import get_run_store
from aitest.platform.audit_log import get_audit_logger
from aitest.platform.artifact_lineage import get_lineage_by_run


class EventQueryService:
    """Unified event query service. Dependencies injected via constructor.

    v3.2: No lazy singleton fallback — all dependencies resolved at construction.
    """

    def __init__(self, store=None, audit=None):
        self._store = store or get_run_store()
        self._audit = audit or get_audit_logger()

    def query_by_run(self, run_id: str) -> dict:
        """Find all events, audit entries, and lineage records for a given run."""
        run_events = self._store.list_events(run_id=run_id, limit=500)
        audit_entries = self._audit.query(run_id=run_id, limit=500)
        lineage = get_lineage_by_run(run_id)

        return {
            "run_id": run_id,
            "run_events": [e.to_dict() for e in run_events],
            "audit_entries": audit_entries,
            "lineage": lineage,
            "counts": {
                "run_events": len(run_events),
                "audit_entries": len(audit_entries),
                "lineage": len(lineage),
            },
        }

    def query_by_module(self, module: str, limit: int = 50) -> dict:
        """Find recent runs and events for a module."""
        all_runs = self._store.list_runs(limit=limit)
        runs = [r for r in all_runs if r.module == module]
        return {
            "module": module,
            "runs": [r.to_dict() for r in runs],
            "run_count": len(runs),
        }


# ── Legacy API (backward compatibility) ─────────────────────────────

_service: EventQueryService | None = None


def _get_service() -> EventQueryService:
    global _service
    if _service is None:
        _service = EventQueryService()
    return _service


def query_events_by_run(run_id: str, store=None, audit=None) -> dict:
    """Legacy API. Prefer EventQueryService for new code."""
    if store is not None or audit is not None:
        service = EventQueryService(store=store, audit=audit)
    else:
        service = _get_service()
    return service.query_by_run(run_id)


def query_events_by_module(module: str, limit: int = 50, store=None) -> dict:
    """Legacy API. Prefer EventQueryService for new code."""
    if store is not None:
        service = EventQueryService(store=store)
    else:
        service = _get_service()
    return service.query_by_module(module, limit)
