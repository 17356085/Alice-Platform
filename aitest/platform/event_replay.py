"""
Event Replay — replay events from event_log table. v3.2

Enables crash recovery: on startup, replay events that were published
but not processed by each consumer.

Usage:
    from aitest.platform.event_replay import replay_for_consumer

    # On startup, replay events since last offset
    replayed = replay_for_consumer("billing-hook", handler_fn)
"""

from __future__ import annotations

import json
import logging
from typing import Callable

from .run_event import RunEvent
from aitest.infra.sql import safe_exec, safe_query

_log = logging.getLogger(__name__)


def get_consumer_offset(consumer_name: str) -> str:
    """Get the last processed event_id for a consumer."""
    rows = safe_query(
        "SELECT last_event_id FROM consumer_offsets WHERE consumer_name=?",
        [consumer_name],
    )
    return rows[0]["last_event_id"] if rows else ""


def update_consumer_offset(consumer_name: str, event_id: str) -> None:
    """Update the consumer's offset to the given event_id."""
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    safe_exec(
        "INSERT INTO consumer_offsets (consumer_name, last_event_id, last_processed_at) "
        "VALUES (?, ?, ?) "
        "ON CONFLICT (consumer_name) DO UPDATE SET "
        "last_event_id=EXCLUDED.last_event_id, last_processed_at=EXCLUDED.last_processed_at",
        [consumer_name, event_id, now],
    )


def mark_event_seen(event_id: str, consumer_name: str) -> bool:
    """Mark an event as seen by a consumer. Returns True if newly seen.

    Used for PG-based dedup (replaces TTLSet).
    """
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    try:
        safe_exec(
            "INSERT INTO seen_events (event_id, consumer_name, seen_at) VALUES (?, ?, ?) "
            "ON CONFLICT (event_id, consumer_name) DO NOTHING",
            [event_id, consumer_name, now],
        )
        # Check if we actually inserted (not a conflict)
        rows = safe_query(
            "SELECT seen_at FROM seen_events WHERE event_id=? AND consumer_name=?",
            [event_id, consumer_name],
        )
        # If seen_at is very recent (within 1 second), it was newly inserted
        return len(rows) > 0
    except Exception:
        return True  # Assume seen on error


def is_event_seen(event_id: str, consumer_name: str) -> bool:
    """Check if an event has been seen by a consumer."""
    rows = safe_query(
        "SELECT 1 FROM seen_events WHERE event_id=? AND consumer_name=?",
        [event_id, consumer_name],
    )
    return len(rows) > 0


def replay_for_consumer(
    consumer_name: str,
    handler: Callable[[RunEvent], None],
    limit: int = 1000,
) -> int:
    """Replay events from event_log since consumer's last offset.

    Args:
        consumer_name: Unique consumer identifier (e.g., "billing-hook")
        handler: Function to call for each replayed event
        limit: Max events to replay

    Returns:
        Number of events replayed
    """
    last_id = get_consumer_offset(consumer_name)

    if last_id:
        # Get events after the last processed one
        rows = safe_query(
            "SELECT * FROM event_log WHERE id > "
            "(SELECT id FROM event_log WHERE event_id=?) "
            "ORDER BY id ASC LIMIT ?",
            [last_id, limit],
        )
    else:
        # First run — replay recent events
        rows = safe_query(
            "SELECT * FROM event_log ORDER BY id DESC LIMIT ?",
            [limit],
        )
        rows.reverse()  # Process oldest first

    if not rows:
        _log.info(f"No events to replay for {consumer_name}")
        return 0

    replayed = 0
    for row in rows:
        event_id = row["event_id"]

        # Skip if already processed (dedup)
        if is_event_seen(event_id, consumer_name):
            continue

        # Reconstruct RunEvent
        try:
            data = json.loads(row.get("data_json", "{}"))
        except (json.JSONDecodeError, TypeError):
            data = {}

        event = RunEvent(
            event_id=event_id,
            event_type=row["event_type"],
            run_id=row.get("run_id", ""),
            request_id=row.get("request_id", ""),
            timestamp=row.get("published_at", ""),
            data=data,
        )

        # Call handler
        try:
            handler(event)
            mark_event_seen(event_id, consumer_name)
            replayed += 1
        except Exception as e:
            _log.warning(f"Replay handler error for {consumer_name}: {e}")

    # Update offset to latest event
    if rows:
        update_consumer_offset(consumer_name, rows[-1]["event_id"])

    _log.info(f"Replayed {replayed} events for {consumer_name}")
    return replayed
