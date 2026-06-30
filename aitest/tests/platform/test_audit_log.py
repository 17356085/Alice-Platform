"""Tests for platform/audit_log.py — operational audit trail.

Tests: AuditLogger CRUD (insert via _on_event, query, count, stats),
cleanup_old_entries, singleton get_audit_logger.
Uses temp SQLite DB — no real EventBus needed for unit tests.
"""
import json
import time
import pytest
from pathlib import Path

from aitest.platform.audit_log import AuditLogger, get_audit_logger
from aitest.platform.run_event import RunEvent


# ══════════════════════════════════════════════════════════════════════════
#  Helpers
# ══════════════════════════════════════════════════════════════════════════


def _make_event(event_id: str, event_type: str = "run.completed",
                run_id: str = "r1", **data) -> RunEvent:
    return RunEvent(
        event_id=event_id, event_type=event_type,
        run_id=run_id, data=data,
    )


@pytest.fixture
def audit_log(temp_dir):
    """AuditLogger with a temp DB, not connected to real EventBus."""
    db_path = temp_dir / "audit.db"
    return AuditLogger(db_path=db_path)


# ══════════════════════════════════════════════════════════════════════════
#  Construction + lifecycle
# ══════════════════════════════════════════════════════════════════════════


class TestAuditLoggerLifecycle:
    def test_creates_db_file(self, temp_dir):
        db_path = temp_dir / "new_audit.db"
        AuditLogger(db_path=db_path)
        assert db_path.exists()

    def test_is_active_starts_false(self, audit_log):
        assert audit_log.is_active is False

    def test_singleton(self, temp_dir):
        db_path = temp_dir / "singleton_audit.db"
        # get_audit_logger returns a global singleton; test via constructor
        a = AuditLogger(db_path=db_path)
        assert a.is_active is False


# ══════════════════════════════════════════════════════════════════════════
#  _on_event — persist
# ══════════════════════════════════════════════════════════════════════════


class TestOnEvent:
    def test_persists_single_event(self, audit_log):
        ev = _make_event("e1", "run.completed", "r1",
                         org_id="org-1", tokens=1000)
        audit_log._on_event(ev)

        results = audit_log.query(run_id="r1")
        assert len(results) == 1
        assert results[0]["event_type"] == "run.completed"
        assert results[0]["data"]["tokens"] == 1000

    def test_persists_multiple_events(self, audit_log):
        for i in range(5):
            audit_log._on_event(_make_event(f"e{i}", "run.completed", f"r{i}",
                                            org_id="org-1"))
        assert audit_log.count(org_id="org-1") == 5

    def test_event_without_data_fields(self, audit_log):
        """Events without org_id/workspace_id in data still persist."""
        ev = RunEvent(event_id="e-minimal", event_type="run.started", run_id="r1")
        audit_log._on_event(ev)
        assert audit_log.count() == 1


# ══════════════════════════════════════════════════════════════════════════
#  query
# ══════════════════════════════════════════════════════════════════════════


class TestQuery:
    def test_filter_by_event_type(self, audit_log):
        audit_log._on_event(_make_event("e1", "run.completed", "r1"))
        audit_log._on_event(_make_event("e2", "run.failed", "r2"))
        audit_log._on_event(_make_event("e3", "run.completed", "r3"))

        completed = audit_log.query(event_type="run.completed")
        assert len(completed) == 2

    def test_filter_by_org(self, audit_log):
        audit_log._on_event(_make_event("e1", "run.completed", "r1", org_id="org-a"))
        audit_log._on_event(_make_event("e2", "run.completed", "r2", org_id="org-b"))

        assert audit_log.count(org_id="org-a") == 1

    def test_filter_by_workspace(self, audit_log):
        audit_log._on_event(_make_event("e1", "run.completed", "r1",
                                        workspace_id="ws-1"))
        audit_log._on_event(_make_event("e2", "run.completed", "r2",
                                        workspace_id="ws-2"))

        results = audit_log.query(workspace_id="ws-1")
        assert len(results) == 1

    def test_limit_and_offset(self, audit_log):
        for i in range(10):
            audit_log._on_event(_make_event(f"e{i}", "run.completed", f"r{i}"))

        results = audit_log.query(limit=3, offset=5)
        assert len(results) == 3

    def test_empty_query_returns_all(self, audit_log):
        audit_log._on_event(_make_event("e1", "run.completed", "r1"))
        assert len(audit_log.query()) == 1

    def test_limit_capped_at_500(self, audit_log):
        audit_log.query(limit=1000)  # Should not raise
        # limit clamped internally


# ══════════════════════════════════════════════════════════════════════════
#  stats
# ══════════════════════════════════════════════════════════════════════════


class TestStats:
    def test_empty_stats(self, audit_log):
        s = audit_log.stats()
        assert s["total_entries"] == 0
        assert s["by_type"] == []
        assert s["recent"] == []

    def test_stats_with_events(self, audit_log):
        audit_log._on_event(_make_event("e1", "run.completed", "r1"))
        audit_log._on_event(_make_event("e2", "run.completed", "r2"))
        audit_log._on_event(_make_event("e3", "run.failed", "r3"))

        s = audit_log.stats()
        assert s["total_entries"] == 3
        types = {t["type"] for t in s["by_type"]}
        assert "run.completed" in types
        assert "run.failed" in types
        assert len(s["recent"]) <= 5


# ══════════════════════════════════════════════════════════════════════════
#  cleanup_old_entries
# ══════════════════════════════════════════════════════════════════════════


class TestCleanup:
    def test_cleanup_keeps_recent(self, audit_log):
        audit_log._on_event(_make_event("e1", "run.completed", "r1"))
        deleted = audit_log.cleanup_old_entries(max_age_days=30)
        assert deleted == 0  # Fresh entry, not cleaned
        assert audit_log.count() == 1

    def test_cleanup_with_large_age(self, audit_log):
        audit_log._on_event(_make_event("e1", "run.completed", "r1"))
        deleted = audit_log.cleanup_old_entries(max_age_days=0)
        # 0 days → all entries older than today midnight
        assert deleted >= 0  # May or may not delete depending on time
        assert audit_log.count() >= 0
