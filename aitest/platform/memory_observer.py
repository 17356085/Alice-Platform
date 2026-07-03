"""Memory Observer — auto-detect dead-ends and create experience memories.

Task 3b (P0) — APERANT_MIGRATION_PLAN.md
Port of Aperant memory/observer/dead-end-detector.ts.

Subscribes to ObservationBus SKILL_FAILED events.  Tracks consecutive
failures per (module, skill_id) in a persistent JSON counter file.
When 3+ failures occur within 30 minutes, auto-creates a DEAD_END
memory in ChromaDB for future planner injection.

Design decisions:
  - Counters stored as JSON (not ChromaDB) — runtime state, not knowledge.
  - Atomic writes via tempfile + os.replace() for multi-process safety.
  - 30-minute window — old failures beyond window are cleaned automatically.

Usage:
    # Auto-registered via observation_bus.py on module import.
    # Manual usage:
    from aitest.platform.memory_observer import on_skill_failed
    on_skill_failed(event)
"""

import json
import os
import time
import shutil
import logging
import tempfile
from pathlib import Path
from typing import Optional

from aitest.platform.observation_bus import ObservationEvent

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

from aitest.platform.config_registry import cfg

# Thresholds (from config_registry, overridable via env vars)
DEAD_END_CONSECUTIVE_FAILURES = cfg.dead_end_consecutive_failures
FAILURE_WINDOW_MINUTES = cfg.dead_end_window_minutes
DEAD_END_MAX_AGE_MINUTES = cfg.dead_end_max_age_minutes


# ═══════════════════════════════════════════════════════════════════════════
#  Counter persistence (JSON + atomic write)
# ═══════════════════════════════════════════════════════════════════════════

def _load_counters() -> dict:
    """Load failure counters from JSON. Returns {} on missing/corrupt file."""
    counters_file = cfg.counters_path
    if not counters_file.exists():
        return {}
    try:
        return json.loads(counters_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        logger.warning("Failed to load counters.json: %s", e)
        return {}


def _save_counters(counters: dict) -> None:
    """Atomically write counters to JSON (tempfile + os.replace)."""
    counters_file = cfg.counters_path
    counters_dir = counters_file.parent
    counters_dir.mkdir(parents=True, exist_ok=True)
    try:
        fd, tmp_path = tempfile.mkstemp(
            suffix=".json", prefix="counters_", dir=str(counters_dir),
        )
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(counters, f, indent=2, ensure_ascii=False)
        os.replace(tmp_path, str(counters_file))
    except OSError as e:
        logger.warning("Failed to save counters.json: %s", e)


def _clean_expired_counters(
    counters: dict,
    window_minutes: int = DEAD_END_MAX_AGE_MINUTES,
) -> dict:
    """Remove counters where all timestamps are older than window_minutes."""
    now = time.time()
    cutoff = now - (window_minutes * 60)
    cleaned = {}
    for key, entry in counters.items():
        timestamps = entry.get("timestamps", [])
        # Parse ISO timestamps, keep only recent ones
        recent = []
        for ts in timestamps:
            try:
                t = _parse_iso(ts)
                if t >= cutoff:
                    recent.append(ts)
            except (ValueError, TypeError):
                continue
        if recent:
            entry["timestamps"] = recent
            entry["count"] = len(recent)
            cleaned[key] = entry
    return cleaned


def _parse_iso(ts: str) -> float:
    """Parse ISO 8601 timestamp to epoch seconds. Fallback to 0."""
    try:
        import datetime
        dt = datetime.datetime.fromisoformat(ts)
        return dt.timestamp()
    except (ValueError, TypeError):
        return 0.0


def _now_iso() -> str:
    """Current time as ISO 8601 string."""
    import datetime
    return datetime.datetime.now().isoformat(timespec="seconds")


# ═══════════════════════════════════════════════════════════════════════════
#  Dead-end detection
# ═══════════════════════════════════════════════════════════════════════════

def _counter_key(module: str, skill_id: str) -> str:
    """Build counter key: 'module:skill_id'."""
    mod = module or "unknown"
    sid = skill_id or "unknown"
    return f"{mod}:{sid}"


def _create_dead_end_memory(module: str, skill_id: str, last_error: str = "") -> None:
    """Create a DEAD_END memory in ChromaDB.

    Non-blocking — ChromaDB write failure is logged but does not raise.
    """
    try:
        from aitest.platform.testing_memory import (
            TestingMemory, MemoryType, Confidence,
        )
        from aitest.platform.testing_memory_store import TestingMemoryStore

        store = TestingMemoryStore()
        memory = TestingMemory(
            type=MemoryType.DEAD_END,
            content=(
                f"Skill '{skill_id}' in module '{module}' "
                f"failed {DEAD_END_CONSECUTIVE_FAILURES} consecutive times "
                f"within {FAILURE_WINDOW_MINUTES} minutes. "
                f"This strategy may be a dead end. "
                f"Last error: {last_error[:300]}"
            ),
            module=module,
            confidence=Confidence.INFERRED,
            source="memory_observer:dead_end_detector",
            tags=["dead_end", skill_id],
        )
        store.add(memory)
        logger.warning(
            "DEAD_END created: module=%s skill=%s error=%s",
            module, skill_id, last_error[:100],
        )
    except Exception as e:
        logger.warning("Failed to create DEAD_END memory: %s", e)


# ═══════════════════════════════════════════════════════════════════════════
#  ObservationBus subscribers
# ═══════════════════════════════════════════════════════════════════════════

def on_skill_failed(event: ObservationEvent) -> None:
    """Handle SKILL_FAILED event — track consecutive failures, detect dead-ends.

    Called automatically by ObservationBus when a skill fails.
    """
    data = event.data or {}
    module = str(data.get("module", "")) or "unknown"
    skill_id = str(data.get("skill_id", "")) or "unknown"
    error_msg = str(data.get("error", data.get("message", "")))[:500]

    key = _counter_key(module, skill_id)
    now_ts = _now_iso()

    # Load + clean
    counters = _load_counters()
    counters = _clean_expired_counters(counters)

    # Update counter
    entry = counters.get(key, {"timestamps": [], "last_error": "", "count": 0})
    entry.setdefault("timestamps", [])
    entry["timestamps"].append(now_ts)
    entry["last_error"] = error_msg
    entry["count"] = len(entry["timestamps"])
    counters[key] = entry

    _save_counters(counters)

    # Check threshold
    count = entry["count"]
    logger.debug(
        "Failure counter: %s = %d/%d", key, count, DEAD_END_CONSECUTIVE_FAILURES,
    )

    if count >= DEAD_END_CONSECUTIVE_FAILURES:
        _create_dead_end_memory(module, skill_id, error_msg)
        # Reset counter after creating dead-end to avoid duplicates
        if key in counters:
            del counters[key]
            _save_counters(counters)
        logger.info(
            "Dead-end detected for %s — memory created, counter reset", key,
        )


def on_skill_complete(event: ObservationEvent) -> None:
    """Handle SKILL_COMPLETE — reset failure counter for this skill.

    A successful execution means the strategy is not a dead end.
    """
    data = event.data or {}
    module = str(data.get("module", "")) or "unknown"
    skill_id = str(data.get("skill_id", "")) or "unknown"

    key = _counter_key(module, skill_id)
    counters = _load_counters()
    if key in counters:
        logger.debug("Resetting failure counter for successful skill: %s", key)
        del counters[key]
        _save_counters(counters)


def reset_failure_counter(module: str = "", skill_id: str = "") -> None:
    """Explicitly reset a failure counter. Called when strategy is changed."""
    if not module and not skill_id:
        # Full reset
        _save_counters({})
        logger.info("All failure counters reset")
        return

    key = _counter_key(module, skill_id)
    counters = _load_counters()
    if key in counters:
        del counters[key]
        _save_counters(counters)
        logger.info("Failure counter reset: %s", key)


def get_dead_ends(module: str) -> list[dict]:
    """Query DEAD_END memories for a module from ChromaDB."""
    try:
        from aitest.knowledge.rag_engine import search_context
        return search_context(
            query=f"{module} dead end",
            collection_name="project_context",
            module=module,
            n_results=5,
        )
    except Exception:
        return []


# ── Self-registration: subscribe to ObservationBus on import ─────
# Moved here from observation_bus.py to break circular dependency.
# Registration is idempotent — each handler deduplicates itself.
_registered_handlers = False


def _register_with_bus(bus=None) -> None:
    """Register MemoryObserver handlers with ObservationBus. Idempotent.

    Args:
        bus: ObservationBus instance. If None, uses get_bus() singleton.
    """
    global _registered_handlers
    if _registered_handlers:
        return
    _registered_handlers = True
    try:
        from aitest.platform.observation_bus import get_bus, EventType
        bus = bus or get_bus()
        bus.subscribe(EventType.SKILL_FAILED, on_skill_failed)
        bus.subscribe(EventType.SKILL_COMPLETE, on_skill_complete)
    except Exception:
        pass  # observation_bus is optional — memory_observer works without it


_register_with_bus()
