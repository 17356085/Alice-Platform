"""Cross-system event query — given a run_id, find all related data.

Phase 2: unified correlation via run_id as the causal root.

Usage:
    from aitest.platform.event_query import query_events_by_run
    result = query_events_by_run("run-abc123")
    # result = { "run_events": [...], "audit_entries": [...], "lineage": [...] }
"""

from aitest.platform.run_store import get_run_store
from aitest.platform.audit_log import get_audit_logger
from aitest.platform.artifact_lineage import get_lineage_by_run


def query_events_by_run(run_id: str) -> dict:
    """Find all events, audit entries, and lineage records for a given run."""
    store = get_run_store()
    audit = get_audit_logger()

    run_events = store.list_events(run_id=run_id, limit=500)
    audit_entries = audit.query(run_id=run_id, limit=500)
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


def query_events_by_module(module: str, limit: int = 50) -> dict:
    """Find recent runs and events for a module."""
    store = get_run_store()
    all_runs = store.list_runs(limit=limit)
    runs = [r for r in all_runs if r.module == module]
    return {
        "module": module,
        "runs": [r.to_dict() for r in runs],
        "run_count": len(runs),
    }
