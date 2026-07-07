# aitest/server/session_store.py — v3.2
# v3.2: 独立 SQLite 数据库，不依赖 PostgreSQL
import uuid
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

# Chat sessions 使用独立的 SQLite 数据库
_DB_PATH = Path(__file__).parent.parent.parent / "governance" / ".data" / "chat_sessions.db"


def _get_conn() -> sqlite3.Connection:
    """获取 SQLite 连接。"""
    _DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


async def init_db():
    """初始化数据库表。"""
    with _get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL DEFAULT '',
                messages TEXT NOT NULL DEFAULT '[]',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        conn.commit()


def create_session(title: str = "") -> dict:
    """创建新会话。"""
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            "INSERT INTO chat_sessions (id, title, messages, created_at, updated_at) VALUES (?, ?, '[]', ?, ?)",
            [session_id, title, now, now],
        )
        conn.commit()
    return {"id": session_id, "title": title, "messages": [], "created_at": now, "updated_at": now}


def get_session(session_id: str) -> Optional[dict]:
    """获取单个会话。"""
    with _get_conn() as conn:
        row = conn.execute("SELECT * FROM chat_sessions WHERE id=?", [session_id]).fetchone()
        if row:
            return {
                "id": row["id"],
                "title": row["title"],
                "messages": json.loads(row["messages"]) if row["messages"] else [],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
    return None


def list_sessions(limit: int = 50, offset: int = 0) -> list[dict]:
    """列出会话。"""
    with _get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM chat_sessions ORDER BY updated_at DESC LIMIT ? OFFSET ?",
            [limit, offset],
        ).fetchall()
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "messages": json.loads(row["messages"]) if row["messages"] else [],
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
            for row in rows
        ]


def update_session_messages(session_id: str, messages: list) -> None:
    """更新会话消息。"""
    now = datetime.now(timezone.utc).isoformat()
    messages_json = json.dumps(messages, ensure_ascii=False)
    with _get_conn() as conn:
        conn.execute(
            "UPDATE chat_sessions SET messages=?, updated_at=? WHERE id=?",
            [messages_json, now, session_id],
        )
        conn.commit()


def update_session_title(session_id: str, title: str) -> None:
    """更新会话标题。"""
    now = datetime.now(timezone.utc).isoformat()
    with _get_conn() as conn:
        conn.execute(
            "UPDATE chat_sessions SET title=?, updated_at=? WHERE id=?",
            [title, now, session_id],
        )
        conn.commit()


def delete_session(session_id: str) -> None:
    """删除会话。"""
    with _get_conn() as conn:
        conn.execute("DELETE FROM chat_sessions WHERE id=?", [session_id])
        conn.commit()
