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
from aitest.platform.replay import ReplayPlayer, list_replay_sessions
from aitest.platform.versioning import select_versioning_payload


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
        trace_events = []
        trace_summary = {}
        try:
            from aitest.infra.trace import query_trace_events, get_trace_summary

            trace_events = query_trace_events(run_id=run_id, limit=500)
            trace_summary = get_trace_summary(run_id)
        except Exception:
            trace_events = []
            trace_summary = {}
        versioning = select_versioning_payload([e.to_dict() for e in run_events])
        if not versioning:
            versioning = select_versioning_payload(audit_entries)
        replay_sessions = list_replay_sessions(run_id)
        replay_details = []
        total_replay_steps = 0
        total_llm_traces = 0
        for session in replay_sessions:
            player = ReplayPlayer(session.id)
            steps = player.steps()
            llm_traces = [player.get_llm_trace(step.id).to_dict() for step in steps if player.get_llm_trace(step.id)]
            total_replay_steps += len(steps)
            total_llm_traces += len(llm_traces)
            replay_details.append({
                "session": session.to_dict(),
                "steps": [step.to_dict() for step in steps],
                "llm_traces": llm_traces,
                "audit_entries": player.audit_entries(self._audit, limit=500),
            })

        return {
            "run_id": run_id,
            "run_events": [e.to_dict() for e in run_events],
            "audit_entries": audit_entries,
            "lineage": lineage,
            "trace_events": trace_events,
            "trace_summary": trace_summary,
            "versioning": versioning,
            "replay_sessions": [item["session"] for item in replay_details],
            "replay_details": replay_details,
            "counts": {
                "run_events": len(run_events),
                "audit_entries": len(audit_entries),
                "lineage": len(lineage),
                "trace_events": len(trace_events),
                "replay_sessions": len(replay_details),
                "replay_steps": total_replay_steps,
                "llm_traces": total_llm_traces,
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
