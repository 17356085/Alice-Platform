"""
Structured Logging — unified log output replacing scattered print().

Design:
  - JSONL file (structured, queryable) + console (human-readable)
  - Level-based: DEBUG < INFO < WARNING < ERROR
  - Context binding: attach module/agent/run_id to all subsequent logs
  - Thread-safe, zero external deps beyond stdlib

Usage:
    from aitest.infra.logging import get_logger

    log = get_logger("sop_graph")
    log.info("preflight_start", module="equipment", pages=4)
    log.warning("gate_blocked", module="tank", missing=["MODULE_CONTEXT.md"])
    log.error("agent_crash", agent="automation-agent", error=str(e))

    # Context binding for repeated calls:
    ctx = log.bind(module="equipment", run_id="abc123")
    ctx.info("phase_start", phase=0)
    ctx.info("phase_end", phase=0, duration_ms=4200)
"""

import json
import logging as _stdlib_logging
import sys
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# ── Paths ──────────────────────────────────────────────────────────────
_WORKSTUDY = Path(__file__).resolve().parent.parent.parent
_LOG_DIR = _WORKSTUDY / "governance" / ".traces"
_LOG_FILE = _LOG_DIR / "app_log.jsonl"

_write_lock = threading.Lock()

# ── Stdlib logger fallback ─────────────────────────────────────────────
_stdlib = _stdlib_logging.getLogger("aitest")
_stdlib.setLevel(_stdlib_logging.DEBUG)
if not _stdlib.handlers:
    _h = _stdlib_logging.StreamHandler(sys.stderr)
    _h.setFormatter(_stdlib_logging.Formatter(
        "[%(levelname).1s %(asctime)s %(name)s] %(message)s",
        datefmt="%H:%M:%S",
    ))
    _stdlib.addHandler(_h)


def _ensure_dir():
    _LOG_DIR.mkdir(parents=True, exist_ok=True)


# ── Core: write one structured entry ──────────────────────────────────

def _write_entry(
    level: str,
    component: str,
    event: str,
    message: str = "",
    **context,
):
    """Thread-safe write of one JSONL log entry."""
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "level": level,
        "component": component,
        "event": event,
        "msg": message,
        **context,
    }

    # Console (human-readable)
    ctx_str = " ".join(f"{k}={v}" for k, v in context.items() if k not in ("error", "traceback"))
    line = f"[{level[0]} {component}] {event}"
    if message:
        line += f" — {message}"
    if ctx_str:
        line += f"  [{ctx_str}]"
    if level == "ERROR":
        _stdlib.error(line)
    elif level == "WARNING":
        _stdlib.warning(line)
    else:
        _stdlib.info(line)

    # JSONL file (structured, queryable)
    try:
        _ensure_dir()
        with _write_lock:
            with open(_LOG_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False, default=str) + "\n")
    except Exception:
        pass  # never let logging crash the app


# ── Logger class ───────────────────────────────────────────────────────

class Logger:
    """Structured logger for one component."""

    def __init__(self, component: str, bindings: dict = None):
        self._component = component
        self._bindings = bindings or {}

    def bind(self, **kwargs) -> "Logger":
        """Return a new Logger with additional fixed context."""
        merged = {**self._bindings, **kwargs}
        return Logger(self._component, merged)

    def debug(self, event: str, message: str = "", **ctx):
        _write_entry("DEBUG", self._component, event, message, **self._bindings, **ctx)

    def info(self, event: str, message: str = "", **ctx):
        _write_entry("INFO", self._component, event, message, **self._bindings, **ctx)

    def warning(self, event: str, message: str = "", **ctx):
        _write_entry("WARNING", self._component, event, message, **self._bindings, **ctx)

    def error(self, event: str, message: str = "", **ctx):
        _write_entry("ERROR", self._component, event, message, **self._bindings, **ctx)


# ── Global registry (singletons per component) ─────────────────────────

_loggers: dict[str, Logger] = {}
_loggers_lock = threading.Lock()


def get_logger(component: str) -> Logger:
    """Get or create a Logger for the given component."""
    with _loggers_lock:
        if component not in _loggers:
            _loggers[component] = Logger(component)
        return _loggers[component]
