# aitest/server/api/sessions_api.py
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from ..session_store import (
    get_db,
    list_sessions,
    get_session,
    delete_session,
    update_session_title,
)

router = APIRouter(prefix="/api/sessions", tags=["sessions"])


# ── Pydantic Schemas ─────────────────────────────────────────────────────────
class SessionListItem(BaseModel):
    id: uuid.UUID
    title: str
    message_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionDetail(BaseModel):
    id: uuid.UUID
    title: str
    messages: list
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionTitleUpdate(BaseModel):
    title: str


# ── Endpoints ────────────────────────────────────────────────────────────────
@router.get("/", response_model=list[SessionListItem])
async def list_all_sessions(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    """List all chat sessions (ordered by updated_at desc)."""
    sessions = await list_sessions(db, limit=limit, offset=offset)
    return [
        SessionListItem(
            id=s.id,
            title=s.title,
            message_count=len(s.messages),
            created_at=s.created_at,
        )
        for s in sessions
    ]


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session_detail(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get a single session with full messages."""
    session = await get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.delete("/{session_id}", status_code=204)
async def delete_session_endpoint(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Delete a session."""
    try:
        await delete_session(db, session_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return None


@router.patch("/{session_id}/title", response_model=SessionDetail)
async def update_title(
    session_id: uuid.UUID,
    payload: SessionTitleUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update session title."""
    try:
        await update_session_title(db, session_id, payload.title)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    session = await get_session(db, session_id)
    return session