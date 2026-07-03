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


def query_events_by_run(run_id: str, store=None, audit=None) -> dict:
    """Find all events, audit entries, and lineage records for a given run.

    Args:
        run_id: The run to query.
        store: RunStore instance. If None, uses get_run_store() singleton.
        audit: AuditLogger instance. If None, uses get_audit_logger() singleton.
    """
    store = store or get_run_store()
    audit = audit or get_audit_logger()

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


def query_events_by_module(module: str, limit: int = 50, store=None) -> dict:
    """Find recent runs and events for a module.

    Args:
        module: Module name to filter by.
        limit: Max runs to return.
        store: RunStore instance. If None, uses get_run_store() singleton.
    """
    store = store or get_run_store()
    all_runs = store.list_runs(limit=limit)
    runs = [r for r in all_runs if r.module == module]
    return {
        "module": module,
        "runs": [r.to_dict() for r in runs],
        "run_count": len(runs),
    }
