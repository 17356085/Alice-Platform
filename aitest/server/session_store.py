# aitest/server/session_store.py — v3.1
# v3.1: Uses parameterized queries via aitest.infra.sql (no more f-string SQL).
import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from aitest.infra.sql import safe_exec, safe_query

def create_session(title: str = "") -> dict:
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    safe_exec(
        "INSERT INTO chat_sessions (id, title, messages, created_at, updated_at) VALUES (?, ?, '[]', ?, ?)",
        [session_id, title, now, now],
    )
    return {"id": session_id, "title": title, "messages": [], "created_at": now, "updated_at": now}

def get_session(session_id: str) -> Optional[dict]:
    rows = safe_query("SELECT * FROM chat_sessions WHERE id=?", [session_id])
    return rows[0] if rows else None

def list_sessions(limit: int = 50, offset: int = 0) -> list[dict]:
    return safe_query("SELECT * FROM chat_sessions ORDER BY updated_at DESC LIMIT ? OFFSET ?", [limit, offset])

def update_session_messages(session_id: str, messages: list) -> None:
    now = datetime.now(timezone.utc).isoformat()
    messages_json = json.dumps(messages, ensure_ascii=False)
    safe_exec("UPDATE chat_sessions SET messages=?, updated_at=? WHERE id=?", [messages_json, now, session_id])

def update_session_title(session_id: str, title: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    safe_exec("UPDATE chat_sessions SET title=?, updated_at=? WHERE id=?", [title, now, session_id])

def delete_session(session_id: str) -> None:
    safe_exec("DELETE FROM chat_sessions WHERE id=?", [session_id])
