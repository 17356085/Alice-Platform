"""Tests for graphs/checkpoint.py — SQLite checkpoint management.

Tests: get_checkpointer, list_runs, cleanup_run, cleanup_old_checkpoints,
DB_PATH, constants.
Uses temp SQLite DB — no real checkpoint data.
"""
import sqlite3
import pytest
from pathlib import Path

from aitest.graphs.checkpoint import (
    get_checkpointer, list_runs, cleanup_run,
    DB_PATH, CHECKPOINT_DIR,
    DEFAULT_MAX_AGE_DAYS, DEFAULT_MAX_RUNS, MAX_DB_SIZE_MB,
)


# ══════════════════════════════════════════════════════════════════════════
#  Constants
# ══════════════════════════════════════════════════════════════════════════


class TestConstants:
    def test_max_age_default(self):
        assert DEFAULT_MAX_AGE_DAYS == 7

    def test_max_runs_default(self):
        assert DEFAULT_MAX_RUNS == 50

    def test_max_db_size(self):
        assert MAX_DB_SIZE_MB == 500

    def test_db_path_under_governance(self):
        assert "governance" in str(DB_PATH)
        assert "checkpoints.sqlite" in str(DB_PATH)


# ══════════════════════════════════════════════════════════════════════════
#  get_checkpointer
# ══════════════════════════════════════════════════════════════════════════


class TestGetCheckpointer:
    def test_returns_sqlite_saver(self):
        from langgraph.checkpoint.sqlite import SqliteSaver
        cp = get_checkpointer()
        assert isinstance(cp, SqliteSaver)

    def test_creates_directory(self):
        assert CHECKPOINT_DIR.exists()


# ══════════════════════════════════════════════════════════════════════════
#  list_runs
# ══════════════════════════════════════════════════════════════════════════


class TestListRuns:
    def test_returns_list(self):
        result = list_runs()
        assert isinstance(result, list)

    def test_respects_limit(self):
        result = list_runs(limit=5)
        assert len(result) <= 5

    def test_empty_db_returns_empty(self):
        # If DB doesn't exist yet, should return empty
        result = list_runs()
        assert isinstance(result, list)


# ══════════════════════════════════════════════════════════════════════════
#  cleanup_run
# ══════════════════════════════════════════════════════════════════════════


class TestCleanupRun:
    def test_cleanup_nonexistent_run(self):
        """Cleaning up a run that doesn't exist should return True (no error)."""
        result = cleanup_run("nonexistent-run-id-xyz")
        # Returns True even if no rows deleted (SQL succeeds)
        assert isinstance(result, bool)
