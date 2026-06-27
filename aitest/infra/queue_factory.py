"""Unified queue factory — auto-detect Redis/RQ, fallback to SQLite.

P4 (2026-06-25): single entry point for task queue. Code doesn't need to
know which backend is active.

Usage:
    from aitest.infra.queue_factory import get_queue

    queue = get_queue()              # auto-detect
    queue = get_queue(force="rq")    # force Redis
    queue.enqueue("automation-agent", module="equipment")

Config:
    REDIS_URL=redis://localhost:6379/0   → RQTaskQueue
    (unset)                                → SQLite TaskQueue
"""
from __future__ import annotations

import os
import logging
from typing import Literal

logger = logging.getLogger("queue_factory")

BackendType = Literal["auto", "rq", "sqlite"]
_queue = None
_backend: str = "unknown"


def get_queue(force: BackendType = "auto"):
    """Get the active task queue. Auto-detects Redis or uses SQLite.

    Args:
        force: "rq" for Redis/RQ, "sqlite" for SQLite, "auto" to detect.

    Returns:
        TaskQueue-compatible instance (SQLite TaskQueue or RQTaskQueue).

    Raises:
        RuntimeError: If force="rq" but Redis is not available.
    """
    global _queue, _backend

    if _queue is not None:
        return _queue

    redis_url = os.environ.get("REDIS_URL", "")

    if force == "sqlite":
        _queue, _backend = _create_sqlite()
    elif force == "rq":
        _queue, _backend = _create_rq(redis_url)
    else:  # auto
        if redis_url or _redis_reachable():
            try:
                _queue, _backend = _create_rq(redis_url)
            except Exception:
                logger.warning("redis_detected_but_unreachable_falling_back")
                _queue, _backend = _create_sqlite()
        else:
            _queue, _backend = _create_sqlite()

    logger.info("queue_factory_initialized", backend=_backend)
    return _queue


def get_backend() -> str:
    """Return active backend name: 'redis' or 'sqlite'."""
    if _queue is None:
        get_queue()
    return _backend


def _redis_reachable() -> bool:
    """Check if Redis is running on localhost."""
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, socket_connect_timeout=1)
        return r.ping()
    except Exception:
        return False


def _create_sqlite():
    from aitest.infra.task_queue import TaskQueue
    return TaskQueue(), "sqlite"


def _create_rq(redis_url: str = ""):
    from aitest.infra.rq_queue import RQTaskQueue, RQTaskQueueNotAvailable
    if redis_url:
        return RQTaskQueue(redis_url=redis_url), "redis"
    raise RQTaskQueueNotAvailable(
        "REDIS_URL not set and Redis not running on localhost. "
        "Install: pip install rq redis. Start: redis-server.")
