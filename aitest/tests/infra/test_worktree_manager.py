"""Tests for infra/worktree_manager.py — Git worktree isolation.

Tests: WorktreeContext (write/read/exists), WorktreeManager._make_name,
list_worktrees parsing, cleanup_stale, isolate() context manager.
Git operations mocked — no real worktree created in unit tests.
"""
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from aitest.infra.worktree_manager import (
    WorktreeManager, WorktreeContext, _WorktreeSession,
)


# ══════════════════════════════════════════════════════════════════════════
#  WorktreeContext — pure data class, no git needed
# ══════════════════════════════════════════════════════════════════════════


class TestWorktreeContext:
    def test_write_creates_file(self, temp_dir):
        ctx = WorktreeContext(
            name="test-wt", path=temp_dir,
            base_branch="main", branch="tlo/test-wt",
        )
        ctx.write("subdir/test.py", "print('hello')")
        assert ctx.exists("subdir/test.py")
        assert (temp_dir / "subdir" / "test.py").read_text() == "print('hello')"

    def test_write_tracks_changed_files(self, temp_dir):
        ctx = WorktreeContext(name="wt", path=temp_dir, base_branch="main", branch="tlo/wt")
        ctx.write("a.py", "a")
        ctx.write("b.py", "b")
        assert ctx.changed_files == ["a.py", "b.py"]
        assert ctx.is_dirty is True

    def test_read_existing_file(self, temp_dir):
        ctx = WorktreeContext(name="wt", path=temp_dir, base_branch="main", branch="tlo/wt")
        (temp_dir / "existing.txt").write_text("content here")
        assert ctx.read("existing.txt") == "content here"

    def test_read_nonexistent_raises(self, temp_dir):
        ctx = WorktreeContext(name="wt", path=temp_dir, base_branch="main", branch="tlo/wt")
        with pytest.raises(FileNotFoundError):
            ctx.read("nope.txt")

    def test_exists_false_for_missing(self, temp_dir):
        ctx = WorktreeContext(name="wt", path=temp_dir, base_branch="main", branch="tlo/wt")
        assert ctx.exists("nothing.here") is False

    def test_not_dirty_initially(self, temp_dir):
        ctx = WorktreeContext(name="wt", path=temp_dir, base_branch="main", branch="tlo/wt")
        assert ctx.is_dirty is False
        assert ctx.changed_files == []

    def test_mark_success(self, temp_dir):
        ctx = WorktreeContext(name="wt", path=temp_dir, base_branch="main", branch="tlo/wt")
        assert ctx.success is False
        ctx.mark_success()
        assert ctx.success is True

    def test_default_created_at_is_isoformat(self, temp_dir):
        ctx = WorktreeContext(name="wt", path=temp_dir, base_branch="main", branch="tlo/wt")
        assert "T" in ctx.created_at  # ISO format
        assert ctx.merged is False


# ══════════════════════════════════════════════════════════════════════════
#  WorktreeManager — constructor + _make_name
# ══════════════════════════════════════════════════════════════════════════


class TestWorktreeManagerInit:
    def test_default_base_ref(self):
        mgr = WorktreeManager()
        assert mgr.base_ref == "HEAD"

    def test_custom_base_ref(self):
        mgr = WorktreeManager(base_ref="origin/main")
        assert mgr.base_ref == "origin/main"

    def test_make_name_includes_agent(self, temp_dir, monkeypatch):
        monkeypatch.setattr(
            "aitest.infra.worktree_manager._WORKTREE_ROOT",
            temp_dir / ".claude" / "worktrees",
        )
        mgr = WorktreeManager()
        name = mgr._make_name("automation-agent")
        assert "tlo-automation-agent-" in name
        # Format: tlo-{agent}-{YYMMDD-HHMMSS}-{6 hex}
        parts = name.split("-")
        assert parts[0] == "tlo"
        assert len(parts[-1]) == 6  # 6 hex chars

    def test_make_name_truncates_long_agent(self, temp_dir, monkeypatch):
        monkeypatch.setattr(
            "aitest.infra.worktree_manager._WORKTREE_ROOT",
            temp_dir / ".claude" / "worktrees",
        )
        mgr = WorktreeManager()
        long_name = "very-long-agent-name-that-exceeds-twenty-chars"
        name = mgr._make_name(long_name)
        agent_part = name.split("-")[1]
        assert len(agent_part) <= 20

    def test_make_name_unique(self, temp_dir, monkeypatch):
        monkeypatch.setattr(
            "aitest.infra.worktree_manager._WORKTREE_ROOT",
            temp_dir / ".claude" / "worktrees",
        )
        mgr = WorktreeManager()
        names = {mgr._make_name("test-agent") for _ in range(20)}
        assert len(names) == 20  # All unique


# ══════════════════════════════════════════════════════════════════════════
#  WorktreeManager — list_worktrees (mocked subprocess)
# ══════════════════════════════════════════════════════════════════════════


class TestListWorktrees:
    def test_parses_porcelain_output(self, temp_dir, monkeypatch):
        wt_root = temp_dir / ".claude" / "worktrees"
        monkeypatch.setattr("aitest.infra.worktree_manager._WORKTREE_ROOT", wt_root)

        porcelain = (
            f"worktree {wt_root / 'tlo-agent-001'}\n"
            "HEAD abc123def\n"
            "branch refs/heads/tlo/tlo-agent-001\n"
            f"worktree {wt_root / 'tlo-agent-002'}\n"
            "HEAD 456789abc\n"
            "branch refs/heads/tlo/tlo-agent-002\n"
        )
        mock_run = MagicMock()
        mock_run.return_value.stdout = porcelain
        mock_run.return_value.returncode = 0

        with patch("subprocess.run", mock_run):
            mgr = WorktreeManager()
            worktrees = mgr.list_worktrees()

        assert len(worktrees) == 2
        assert worktrees[0]["branch"] == "tlo/tlo-agent-001"
        assert worktrees[1]["branch"] == "tlo/tlo-agent-002"

    def test_empty_output_returns_empty_list(self, temp_dir, monkeypatch):
        monkeypatch.setattr(
            "aitest.infra.worktree_manager._WORKTREE_ROOT",
            temp_dir / ".claude" / "worktrees",
        )
        mock_run = MagicMock()
        mock_run.return_value.stdout = ""
        mock_run.return_value.returncode = 0

        with patch("subprocess.run", mock_run):
            mgr = WorktreeManager()
            assert mgr.list_worktrees() == []

    def test_filters_non_tlo_worktrees(self, temp_dir, monkeypatch):
        """Only worktrees under _WORKTREE_ROOT are returned."""
        wt_root = temp_dir / ".claude" / "worktrees"
        monkeypatch.setattr("aitest.infra.worktree_manager._WORKTREE_ROOT", wt_root)

        porcelain = (
            f"worktree {wt_root / 'tlo-keep-me'}\n"
            "HEAD abc\n"
            "branch refs/heads/tlo/tlo-keep-me\n"
            "worktree /tmp/other-worktree\n"
            "HEAD def\n"
            "branch refs/heads/other\n"
        )
        mock_run = MagicMock()
        mock_run.return_value.stdout = porcelain
        mock_run.return_value.returncode = 0

        with patch("subprocess.run", mock_run):
            mgr = WorktreeManager()
            worktrees = mgr.list_worktrees()

        assert len(worktrees) == 1
        assert worktrees[0]["branch"] == "tlo/tlo-keep-me"


# ══════════════════════════════════════════════════════════════════════════
#  WorktreeManager — cleanup_stale
# ══════════════════════════════════════════════════════════════════════════


class TestCleanupStale:
    def test_removes_old_directories(self, temp_dir, monkeypatch):
        import os
        wt_root = temp_dir / ".claude" / "worktrees"
        wt_root.mkdir(parents=True)
        monkeypatch.setattr("aitest.infra.worktree_manager._WORKTREE_ROOT", wt_root)

        # Create a stale directory (old mtime)
        stale_dir = wt_root / "tlo-stale-001"
        stale_dir.mkdir()
        stale_file = stale_dir / "file.txt"
        stale_file.write_text("stale")
        # Set mtime to 48 hours ago using os.utime
        old_time = time.time() - (48 * 3600)
        os.utime(str(stale_dir), (old_time, old_time))
        os.utime(str(stale_file), (old_time, old_time))

        mgr = WorktreeManager()
        count = mgr.cleanup_stale(max_age_hours=24)

        assert count == 1
        assert not stale_dir.exists()

    def test_keeps_recent_directories(self, temp_dir, monkeypatch):
        wt_root = temp_dir / ".claude" / "worktrees"
        wt_root.mkdir(parents=True)
        monkeypatch.setattr("aitest.infra.worktree_manager._WORKTREE_ROOT", wt_root)

        recent = wt_root / "tlo-recent-001"
        recent.mkdir()
        (recent / "file.txt").write_text("recent")

        mgr = WorktreeManager()
        count = mgr.cleanup_stale(max_age_hours=24)

        assert count == 0  # Recently created, not cleaned
        assert recent.exists()

    def test_empty_worktree_dir(self, temp_dir, monkeypatch):
        wt_root = temp_dir / ".claude" / "worktrees"
        wt_root.mkdir(parents=True)
        monkeypatch.setattr("aitest.infra.worktree_manager._WORKTREE_ROOT", wt_root)

        mgr = WorktreeManager()
        assert mgr.cleanup_stale() == 0


# ══════════════════════════════════════════════════════════════════════════
#  _WorktreeSession — context manager behavior
# ══════════════════════════════════════════════════════════════════════════


class TestWorktreeSession:
    def test_exc_marks_failure(self, temp_dir, monkeypatch):
        """Exception during session → success=False, force-removed."""
        monkeypatch.setattr(
            "aitest.infra.worktree_manager._WORKTREE_ROOT",
            temp_dir / ".claude" / "worktrees",
        )

        mgr = WorktreeManager()
        # Mock create + merge_and_cleanup
        mgr.create = MagicMock()
        mgr.merge_and_cleanup = MagicMock()

        fake_ctx = WorktreeContext(
            name="test-wt", path=temp_dir,
            base_branch="main", branch="tlo/test-wt",
            success=True,
        )
        mgr.create.return_value = fake_ctx

        with pytest.raises(ValueError):
            with _WorktreeSession(mgr, "test-wt") as wt:
                raise ValueError("something broke")

        assert fake_ctx.success is False
        mgr.merge_and_cleanup.assert_called_once_with(fake_ctx)

    def test_normal_exit_calls_merge_and_cleanup(self, temp_dir, monkeypatch):
        """Normal exit → merge_and_cleanup called."""
        monkeypatch.setattr(
            "aitest.infra.worktree_manager._WORKTREE_ROOT",
            temp_dir / ".claude" / "worktrees",
        )

        mgr = WorktreeManager()
        mgr.create = MagicMock()
        mgr.merge_and_cleanup = MagicMock()

        fake_ctx = WorktreeContext(
            name="ok-wt", path=temp_dir,
            base_branch="main", branch="tlo/ok-wt",
        )
        mgr.create.return_value = fake_ctx

        with _WorktreeSession(mgr, "ok-wt") as wt:
            wt.mark_success()

        assert fake_ctx.success is True
        mgr.merge_and_cleanup.assert_called_once_with(fake_ctx)

    def test_does_not_suppress_exception(self, temp_dir, monkeypatch):
        """Context manager re-raises exceptions (does not swallow)."""
        monkeypatch.setattr(
            "aitest.infra.worktree_manager._WORKTREE_ROOT",
            temp_dir / ".claude" / "worktrees",
        )

        mgr = WorktreeManager()
        mgr.create = MagicMock()
        mgr.merge_and_cleanup = MagicMock()
        mgr.create.return_value = WorktreeContext(
            name="err-wt", path=temp_dir,
            base_branch="main", branch="tlo/err-wt",
        )

        with pytest.raises(RuntimeError, match="test error"):
            with _WorktreeSession(mgr, "err-wt"):
                raise RuntimeError("test error")

    def test_returns_false_does_not_suppress(self, temp_dir, monkeypatch):
        """__exit__ returns False — does not suppress exceptions."""
        monkeypatch.setattr(
            "aitest.infra.worktree_manager._WORKTREE_ROOT",
            temp_dir / ".claude" / "worktrees",
        )
        session = _WorktreeSession(WorktreeManager(), "return-val-test")
        # Without __enter__, ctx is None → should return False
        result = session.__exit__(None, None, None)
        assert result is False
