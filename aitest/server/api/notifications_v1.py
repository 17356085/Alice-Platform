"""Read-only notification resource for the Studio header.

Notifications are derived from durable platform records that already exist:
open bugs and failed runs. This keeps the header useful in local/SQLite mode
without introducing a second event store just for UI chrome.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Query


notifications_router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


def _notification(*, notification_id: str, kind: str, severity: str,
                  title: str, message: str, created_at: str = "",
                  resource: dict | None = None) -> dict:
    return {
        "id": notification_id,
        "kind": kind,
        "severity": severity,
        "title": title,
        "message": message,
        "created_at": created_at or datetime.now(timezone.utc).isoformat(),
        "read": False,
        "resource": resource or {},
    }


@notifications_router.get("")
async def list_notifications(
    limit: int = Query(20, ge=1, le=100),
    unread_only: bool = False,
    scope: str = Query("default", min_length=1, max_length=200),
):
    """Return actionable notifications derived from current platform state."""
    limit_value = limit if isinstance(limit, int) else 20
    scope_value = scope if isinstance(scope, str) else "default"
    from aitest.platform.notification_state import read_ids

    read_markers = read_ids(scope_value)
    items: list[dict] = []

    try:
        from aitest.testing.bug_history import list_bugs

        for bug in list_bugs(status="open", limit=limit_value):
            bug_id = str(bug.get("id", ""))
            severity = str(bug.get("severity", "medium"))
            module = str(bug.get("module", "unknown"))
            items.append(_notification(
                notification_id=f"bug:{bug_id}",
                kind="bug",
                severity=severity,
                title=f"Open defect in {module}",
                message=str(bug.get("error_message") or bug.get("error_type") or "Open defect requires review"),
                created_at=str(bug.get("updated_at") or bug.get("created_at") or bug.get("date") or ""),
                resource={"type": "bug", "id": bug_id, "module": module},
            ))
    except Exception:
        # A missing optional bug table must not break the header.
        pass

    try:
        from aitest.platform.run_store import get_run_store

        for run in get_run_store().list_runs(limit=limit_value):
            status = str(run.status or "").lower()
            if status not in {"failed", "error", "timed_out"}:
                continue
            items.append(_notification(
                notification_id=f"run:{run.run_id}",
                kind="run",
                severity="high",
                title="Run failed",
                message=run.error_message or f"Run {run.run_id} finished with status {run.status}",
                created_at=str(run.completed_at or run.created_at or ""),
                resource={"type": "run", "id": run.run_id, "module": run.module},
            ))
    except Exception:
        pass

    items.sort(key=lambda item: item.get("created_at", ""), reverse=True)
    for item in items:
        item["read"] = item["id"] in read_markers
    if unread_only:
        items = [item for item in items if not item["read"]]
    return {
        "notifications": items[:limit_value],
        "total": len(items),
        "unread": sum(1 for item in items if not item["read"]),
    }


@notifications_router.patch("/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    scope: str = Query("default", min_length=1, max_length=200),
):
    if not notification_id.strip():
        raise HTTPException(status_code=422, detail="Notification id is required")
    from aitest.platform.notification_state import mark_read

    mark_read(notification_id, scope)
    return {"status": "read", "id": notification_id, "scope": scope}
