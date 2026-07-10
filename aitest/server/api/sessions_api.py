# aitest/server/api/sessions_api.py
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..session_store import (
    list_sessions,
    get_session,
    delete_session,
    update_session_title,
)

router = APIRouter(prefix="/api/v1/sessions", tags=["sessions"])


# ── Pydantic Schemas ─────────────────────────────────────────────────────────

class SessionListItem(BaseModel):
    id: str
    title: str
    message_count: int
    created_at: str


class SessionDetail(BaseModel):
    id: str
    title: str
    messages: list
    created_at: str
    updated_at: str


class SessionTitleUpdate(BaseModel):
    title: str


# ── Endpoints ────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[SessionListItem])
async def list_all_sessions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    """List all chat sessions (ordered by updated_at desc)."""
    sessions = list_sessions(limit=limit, offset=offset)
    return [
        SessionListItem(
            id=s.get("id", ""),
            title=s.get("title", ""),
            message_count=len(s.get("messages", [])),
            created_at=s.get("created_at", ""),
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session_detail(
    session_id: str,
):
    """Get a single session with full messages."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionDetail(
        id=session.get("id", ""),
        title=session.get("title", ""),
        messages=session.get("messages", []),
        created_at=session.get("created_at", ""),
        updated_at=session.get("updated_at", ""),
    )


@router.delete("/{session_id}", status_code=204)
async def delete_session_endpoint(
    session_id: str,
):
    """Delete a session."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    delete_session(session_id)
    return None


@router.patch("/{session_id}/title", response_model=SessionDetail)
async def update_title(
    session_id: str,
    payload: SessionTitleUpdate,
):
    """Update session title."""
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    update_session_title(session_id, payload.title)
    updated = get_session(session_id)
    return SessionDetail(
        id=updated.get("id", ""),
        title=updated.get("title", ""),
        messages=updated.get("messages", []),
        created_at=updated.get("created_at", ""),
        updated_at=updated.get("updated_at", ""),
    )
