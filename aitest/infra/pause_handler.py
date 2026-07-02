"""Sentinel-File Pause/Resume Handler.

Task 2 (P0) — APERANT_MIGRATION_PLAN.md
Port of Aperant's `pause-handler.ts` sentinel file mechanism,
adapted for aitest multi-process safety.

Storage: governance/.data/{task_id}/  (CONSTITUTION §3.1)
NOT .tlo/ — platform execution state ≠ project knowledge (ADR-001).

Usage:
    from aitest.infra.pause_handler import write_pause_file, wait_for_resume

    # Agent side — pause execution
    write_pause_file(task_id="equipment-alarm-config",
                     reason="High-risk skill requires approval",
                     skill_id="execution/data-sanitization",
                     risk_level="high")

    # Agent side — block until user approves
    resumed = wait_for_resume(task_id="equipment-alarm-config", timeout=7200)
    if resumed:
        logger.info("User approved, continuing...")

    # API side — user approves
    from aitest.infra.pause_handler import write_resume_file
    write_resume_file(task_id="equipment-alarm-config")

    # API side — check status
    from aitest.infra.pause_handler import check_pause_status
    status = check_pause_status(task_id="equipment-alarm-config")
"""

import json
import time
import threading
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

DEFAULT_BASE_DIR = Path("governance") / ".data"

# Exponential backoff intervals (seconds)
_BACKOFF_SEQUENCE = (1, 2, 4, 8, 15, 30)
_BACKOFF_MAX = 30

# How often to check the abort signal during sleep
_ABORT_CHECK_INTERVAL = 0.5


# ── Sentinel file I/O ─────────────────────────────────────────────────────

def _task_dir(task_id: str, base_dir: Path = DEFAULT_BASE_DIR) -> Path:
    """Resolve task-specific directory under governance/.data/."""
    return base_dir / task_id


def write_pause_file(
    task_id: str,
    reason: str,
    skill_id: str = "",
    risk_level: str = "high",
    base_dir: str | Path = DEFAULT_BASE_DIR,
) -> Path:
    """Write pause.json sentinel, blocking execution until user resumes.

    Args:
        task_id: Unique task identifier (e.g. "equipment-alarm-config").
                 Each task_id gets its own subdirectory — multi-task safe.
        reason: Human-readable reason for the pause (shown in UI).
        skill_id: The skill that triggered the HITL pause.
        risk_level: Risk level that caused the confirmation requirement.
        base_dir: Root directory for execution state (default: governance/.data).

    Returns:
        Path to the created pause.json file.
    """
    base = Path(base_dir)
    task_dir = _task_dir(task_id, base)
    task_dir.mkdir(parents=True, exist_ok=True)

    data = {
        "paused_at": _now_iso(),
        "reason": reason,
        "skill_id": skill_id,
        "risk_level": risk_level,
        "task_id": task_id,  # self-contained, prevents cross-task misreads
    }
    pause_path = task_dir / "pause.json"
    pause_path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                          encoding="utf-8")
    logger.info("Pause file written: %s (reason=%s)", pause_path, reason)
    return pause_path


def write_resume_file(
    task_id: str,
    base_dir: str | Path = DEFAULT_BASE_DIR,
) -> Path:
    """Write resume.json sentinel — called by API when user approves.

    Deletes any existing pause.json first (atomic handoff).
    """
    base = Path(base_dir)
    task_dir = _task_dir(task_id, base)
    task_dir.mkdir(parents=True, exist_ok=True)

    # Clear stale pause file (if still present)
    pause_path = task_dir / "pause.json"
    if pause_path.exists():
        pause_path.unlink()

    data = {
        "resumed_at": _now_iso(),
        "task_id": task_id,
    }
    resume_path = task_dir / "resume.json"
    resume_path.write_text(json.dumps(data, indent=2, ensure_ascii=False),
                           encoding="utf-8")
    logger.info("Resume file written: %s", resume_path)
    return resume_path


def check_pause_status(
    task_id: str,
    base_dir: str | Path = DEFAULT_BASE_DIR,
) -> Optional[dict]:
    """Query current pause state — called by API for frontend polling.

    Returns:
        dict with pause data if task is paused, None if not paused or task
        directory doesn't exist.
    """
    base = Path(base_dir)
    pause_path = _task_dir(task_id, base) / "pause.json"
    if not pause_path.exists():
        return None

    try:
        return json.loads(pause_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


# ── Blocking wait ─────────────────────────────────────────────────────────

def wait_for_resume(
    task_id: str,
    timeout: int = 7200,
    base_dir: str | Path = DEFAULT_BASE_DIR,
    abort_signal: Optional[threading.Event] = None,
) -> bool:
    """Block until resume.json appears, with exponential backoff polling.

    Polls resume.json at intervals: 1s → 2s → 4s → 8s → 15s → 30s (repeat).
    On detection, cleans up both pause.json and resume.json.

    Args:
        task_id: Task identifier matching the one used in write_pause_file().
        timeout: Maximum seconds to wait (default 2 hours).
        base_dir: Root directory for execution state.
        abort_signal: Optional Event; set to abort waiting early.

    Returns:
        True if resumed by user, False if timeout or aborted.
    """
    base = Path(base_dir)
    task_dir = _task_dir(task_id, base)
    resume_path = task_dir / "resume.json"
    pause_path = task_dir / "pause.json"

    start = time.monotonic()
    backoff_index = 0

    logger.info("Waiting for resume on task=%s (timeout=%ds)", task_id, timeout)

    while True:
        elapsed = time.monotonic() - start

        # Check timeout
        if elapsed >= timeout:
            logger.warning("Resume timeout for task=%s after %ds", task_id, timeout)
            _cleanup_sentinels(pause_path, resume_path)
            return False

        # Check abort signal
        if abort_signal and abort_signal.is_set():
            logger.info("Resume aborted for task=%s", task_id)
            _cleanup_sentinels(pause_path, resume_path)
            return False

        # Check for resume file
        if resume_path.exists():
            logger.info("Resume detected for task=%s after %.1fs", task_id, elapsed)
            _cleanup_sentinels(pause_path, resume_path)
            return True

        # Sleep with backoff, checking abort signal periodically
        delay = min(_BACKOFF_SEQUENCE[backoff_index], _BACKOFF_MAX)
        if backoff_index < len(_BACKOFF_SEQUENCE) - 1:
            backoff_index += 1

        # Interruptible sleep — check abort every _ABORT_CHECK_INTERVAL
        sleep_start = time.monotonic()
        while time.monotonic() - sleep_start < delay:
            if abort_signal and abort_signal.is_set():
                logger.info("Resume aborted during sleep for task=%s", task_id)
                _cleanup_sentinels(pause_path, resume_path)
                return False
            remaining = delay - (time.monotonic() - sleep_start)
            time.sleep(min(_ABORT_CHECK_INTERVAL, max(0, remaining)))


def _cleanup_sentinels(pause_path: Path, resume_path: Path) -> None:
    """Remove sentinel files after resume/timeout/abort."""
    for p in (pause_path, resume_path):
        try:
            if p.exists():
                p.unlink()
        except OSError:
            pass


def cleanup_task_dir(
    task_id: str,
    base_dir: str | Path = DEFAULT_BASE_DIR,
) -> None:
    """Remove entire task directory after completion (best-effort)."""
    task_dir = _task_dir(task_id, Path(base_dir))
    try:
        if task_dir.exists():
            import shutil
            shutil.rmtree(task_dir, ignore_errors=True)
            logger.debug("Cleaned up task dir: %s", task_dir)
    except Exception:
        pass


# ── Helpers ────────────────────────────────────────────────────────────────

def _now_iso() -> str:
    """ISO 8601 timestamp without microseconds."""
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime())
