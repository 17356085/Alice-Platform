"""
Timeline — time-ordered view of RunEvents for a Run. v2.3

Pure consumer of RunEvent data. Queries RunStore, formats output.
No new abstractions. No modification to ExecutionService or Runtime.

Usage:
    from aitest.platform.timeline import build_timeline
    timeline = build_timeline("run-abc123")
    for entry in timeline:
        _log.info(f"{entry['ts']}  {entry['type']}  {entry['message']}")
"""

from .run_store import get_run_store
from .run_event import EventType, EventDataKey as K
from aitest.infra.logging import get_logger
_log = get_logger(__name__)


def build_timeline(run_id: str, store=None) -> list[dict]:
    """Build a time-ordered timeline for a Run from its events.

    Args:
        run_id: The run to build a timeline for.
        store: RunStore instance. If None, uses get_run_store() singleton.

    Returns list of {ts, type, message, detail} entries.
    """
    store = store or get_run_store()
    run = store.load_run(run_id)
    if run is None:
        return []

    events = store.list_events(run_id=run_id, limit=500)

    entries = []

    # Run created
    entries.append({
        "ts": run.created_at,
        "type": "run_created",
        "message": f"Run {run_id[:8]} started",
        "detail": {
            "agent": run.agent,
            "module": run.module,
            "capability": run.capability,
        },
    })

    # Phase-style grouping from events
    phase_entries = []
    for e in events:
        entry = _event_to_entry(e)
        if entry:
            phase_entries.append(entry)

    entries.extend(phase_entries)

    # Run terminal
    if run.is_frozen:
        emoji = "✓" if run.status == "completed" else "✗"
        entries.append({
            "ts": run.completed_at,
            "type": f"run_{run.status}",
            "message": f"{emoji} Run {run.status}",
            "detail": {
                "total_tokens": run.total_tokens,
                "total_cost": run.total_cost,
                "agent_runs": run.agent_runs,
                "error": run.error_message if run.status == "failed" else "",
            },
        })

    entries.sort(key=lambda e: e["ts"])
    return entries


def _event_to_entry(event) -> dict | None:
    """Convert a RunEvent to a timeline entry."""
    event_type = event.event_type
    data = event.data

    if event_type == EventType.EXECUTION_REQUESTED:
        return {
            "ts": event.timestamp,
            "type": "execution_requested",
            "message": f"Execution requested: {data.get(K.MODULE, '')}",
            "detail": data,
        }

    elif event_type == EventType.EXECUTION_QUEUED:
        return {
            "ts": event.timestamp,
            "type": "queued",
            "message": "Queued",
        }

    elif event_type == EventType.EXECUTION_STARTED:
        return {
            "ts": event.timestamp,
            "type": "execution_started",
            "message": f"Agent {data.get(K.AGENT, '')} started on {data.get(K.MODULE, '')}",
            "detail": data,
        }

    elif event_type == EventType.PHASE_STARTED:
        return {
            "ts": event.timestamp,
            "type": "phase_started",
            "message": f"Phase started: {data.get(K.PHASE, '')}",
            "detail": data,
        }

    elif event_type == EventType.PHASE_COMPLETED:
        return {
            "ts": event.timestamp,
            "type": "phase_completed",
            "message": f"Phase completed: {data.get(K.PHASE, '')}",
            "detail": data,
        }

    elif event_type == EventType.ARTIFACT_CREATED:
        return {
            "ts": event.timestamp,
            "type": "artifact_created",
            "message": f"Artifact: {data.get(K.ARTIFACT_PATH, '')}",
            "detail": data,
        }

    elif event_type == EventType.RUN_COMPLETED:
        return {
            "ts": event.timestamp,
            "type": "run_completed",
            "message": f"✓ Completed — {data.get(K.TOTAL_TOKENS, 0)} tokens, ${data.get(K.TOTAL_COST, 0):.4f}",
            "detail": data,
        }

    elif event_type == EventType.RUN_FAILED:
        return {
            "ts": event.timestamp,
            "type": "run_failed",
            "message": f"✗ Failed: {data.get(K.ERROR, '')[:120]}",
            "detail": data,
        }

    elif event_type == EventType.RUN_CANCELLED:
        return {
            "ts": event.timestamp,
            "type": "run_cancelled",
            "message": "Cancelled",
        }

    elif event_type == EventType.COST_RECORDED:
        return {
            "ts": event.timestamp,
            "type": "cost_recorded",
            "message": f"Cost: ${data.get(K.TOTAL_COST, 0):.4f} ({data.get(K.TOTAL_TOKENS, 0)} tokens)",
            "detail": data,
        }

    return None


def timeline_summary(run_id: str, store=None) -> dict:
    """Return a compact summary suitable for list views.

    Args:
        run_id: The run to summarize.
        store: RunStore instance. If None, uses get_run_store() singleton.
    """
    store = store or get_run_store()
    run = store.load_run(run_id)
    if run is None:
        return {}

    events = store.list_events(run_id=run_id, limit=500)
    phases = [e.data.get(K.PHASE, "") for e in events
              if e.event_type in (EventType.PHASE_STARTED, EventType.PHASE_COMPLETED)]

    return {
        "run_id": run_id,
        "status": run.status,
        "module": run.module,
        "agent": run.agent,
        "capability": run.capability,
        "created_at": run.created_at,
        "completed_at": run.completed_at,
        "total_tokens": run.total_tokens,
        "total_cost": run.total_cost,
        "phases": list(set(phases)),
        "event_count": len(events),
    }
