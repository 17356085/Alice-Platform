"""Redis-backed session store — persistent, shared across workers.

P2 (2026-06-25): Drop-in replacement for SQLAlchemy session_store.
Same CRUD interface. Auto-TTL 7 days. No async required (Redis is fast).

Storage:
  tlo:session:{id}  → Hash  {title, messages_json, created_at, updated_at}
  tlo:sessions      → ZSet  {session_id: updated_at_ts}  (sorted by recency)
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger("redis_session")

_REDIS_AVAILABLE = False
try:
    import redis as _redis
    _REDIS_AVAILABLE = True
except ImportError:
    pass


SESSION_TTL = 86400 * 7  # 7 days
SESSION_PREFIX = "tlo:session"
SESSION_INDEX = "tlo:sessions"


@dataclass
class SessionRecord:
    """Mirrors ChatSessionRecord for API compatibility."""
    id: uuid.UUID
    title: str = ""
    messages: list = field(default_factory=list)
    created_at: float = 0.0
    updated_at: float = 0.0


class RedisSessionStore:
    """Redis-backed chat session CRUD."""

    def __init__(self):
        self._redis: Optional[_redis.Redis] = None
        self._available = False
        if _REDIS_AVAILABLE:
            try:
                self._redis = _redis.Redis(host="localhost", port=6379,
                                           socket_connect_timeout=1)
                self._redis.ping()
                self._available = True
                logger.info("redis_session_connected")
            except Exception:
                pass

    @property
    def is_available(self) -> bool:
        return self._available

    def _key(self, session_id: uuid.UUID) -> str:
        return f"{SESSION_PREFIX}:{session_id.hex}"

    def _record_from_hash(self, data: dict, sid: uuid.UUID) -> SessionRecord:
        return SessionRecord(
            id=sid,
            title=data.get(b"title", b"").decode() if isinstance(data.get(b"title"), bytes) else data.get("title", ""),
            messages=json.loads(data.get(b"messages", data.get(b"messages_json", "[]"))) if isinstance(data.get(b"messages", data.get(b"messages_json", b"[]")), bytes) else data.get("messages", []),
            created_at=float(data.get(b"created_at", data.get(b"created_at", b"0")).decode() if isinstance(data.get(b"created_at", data.get(b"created_at", b"0")), bytes) else data.get("created_at", 0)),
            updated_at=float(data.get(b"updated_at", data.get(b"updated_at", b"0")).decode() if isinstance(data.get(b"updated_at", data.get(b"updated_at", b"0")), bytes) else data.get("updated_at", 0)),
        )

    # ── CRUD ──────────────────────────────────────────────────────────

    def create_session(self, title: str = "") -> SessionRecord:
        if not self._available:
            raise RuntimeError("Redis not available")
        sid = uuid.uuid4()
        now = time.time()
        data = {
            "title": title,
            "messages": json.dumps([]),
            "created_at": now,
            "updated_at": now,
        }
        key = self._key(sid)
        self._redis.hset(key, mapping=data)
        self._redis.expire(key, SESSION_TTL)
        self._redis.zadd(SESSION_INDEX, {sid.hex: now})
        return SessionRecord(id=sid, title=title, messages=[],
                             created_at=now, updated_at=now)

    def get_session(self, session_id: uuid.UUID) -> Optional[SessionRecord]:
        if not self._available:
            return None
        key = self._key(session_id)
        data = self._redis.hgetall(key)
        if not data:
            return None
        return self._record_from_hash(data, session_id)

    def list_sessions(self, limit: int = 50, offset: int = 0) -> list[SessionRecord]:
        if not self._available:
            return []
        ids_bytes = self._redis.zrevrange(SESSION_INDEX, offset, offset + limit - 1)
        sessions = []
        for sid_bytes in ids_bytes:
            sid_str = sid_bytes.decode() if isinstance(sid_bytes, bytes) else sid_bytes
            try:
                sid = uuid.UUID(sid_str)
                rec = self.get_session(sid)
                if rec:
                    sessions.append(rec)
            except ValueError:
                pass
        return sessions

    def update_session_messages(self, session_id: uuid.UUID, messages: list):
        if not self._available:
            raise ValueError(f"Session {session_id} not found")
        now = time.time()
        key = self._key(session_id)
        self._redis.hset(key, mapping={
            "messages": json.dumps(messages, ensure_ascii=False),
            "updated_at": now,
        })
        self._redis.zadd(SESSION_INDEX, {session_id.hex: now})

    def update_session_title(self, session_id: uuid.UUID, title: str):
        if not self._available:
            raise ValueError(f"Session {session_id} not found")
        now = time.time()
        key = self._key(session_id)
        self._redis.hset(key, mapping={
            "title": title,
            "updated_at": now,
        })
        self._redis.zadd(SESSION_INDEX, {session_id.hex: now})

    def delete_session(self, session_id: uuid.UUID):
        if not self._available:
            raise ValueError(f"Session {session_id} not found")
        self._redis.delete(self._key(session_id))
        self._redis.zrem(SESSION_INDEX, session_id.hex)

    def count(self) -> int:
        if not self._available:
            return 0
        return self._redis.zcard(SESSION_INDEX)

    def stats(self) -> dict:
        if not self._available:
            return {"backend": "redis", "status": "disconnected"}
        return {
            "backend": "redis",
            "total_sessions": self._redis.zcard(SESSION_INDEX),
            "prefix": SESSION_PREFIX,
            "ttl_days": 7,
        }


# Singleton
redis_session_store = RedisSessionStore()
