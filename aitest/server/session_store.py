# aitest/server/session_store.py — v3.0
# PostgreSQL persistence via docker exec psql.
import uuid
import json
from datetime import datetime, timezone
from typing import Optional
from aitest.infra.database import pg_exec, pg_query

def _escape(val):
    if val is None: return "NULL"
    return "'" + str(val).replace("'", "''") + "'"

def _escape_json(val):
    if val is None: return "'[]'"
    return "'" + json.dumps(val, ensure_ascii=False).replace("'", "''") + "'"

def create_session(title: str = "") -> dict:
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    pg_exec(f"INSERT INTO chat_sessions (id, title, messages, created_at, updated_at) VALUES ('{session_id}', {_escape(title)}, '[]', '{now}', '{now}')")
    return {"id": session_id, "title": title, "messages": [], "created_at": now, "updated_at": now}

def get_session(session_id: str) -> Optional[dict]:
    rows = pg_query(f"SELECT * FROM chat_sessions WHERE id='{session_id}'")
    return rows[0] if rows else None

def list_sessions(limit: int = 50, offset: int = 0) -> list[dict]:
    return pg_query(f"SELECT * FROM chat_sessions ORDER BY updated_at DESC LIMIT {limit} OFFSET {offset}")

def update_session_messages(session_id: str, messages: list) -> None:
    now = datetime.now(timezone.utc).isoformat()
    messages_json = json.dumps(messages, ensure_ascii=False).replace("'", "''")
    pg_exec(f"UPDATE chat_sessions SET messages='{messages_json}', updated_at='{now}' WHERE id='{session_id}'")

def update_session_title(session_id: str, title: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    pg_exec(f"UPDATE chat_sessions SET title={_escape(title)}, updated_at='{now}' WHERE id='{session_id}'")

def delete_session(session_id: str) -> None:
    pg_exec(f"DELETE FROM chat_sessions WHERE id='{session_id}'")
