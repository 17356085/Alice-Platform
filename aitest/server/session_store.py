# aitest/server/session_store.py
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import JSON, String, func, select, delete
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from aitest.config import config

DATABASE_URL = config.database_url

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


# ── Model ────────────────────────────────────────────────────────────────────
class ChatSessionRecord(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True, default=uuid.uuid4
    )
    title: Mapped[str] = mapped_column(String(255), default="")
    messages: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    def __repr__(self) -> str:
        return f"<ChatSessionRecord(id={self.id}, title='{self.title}')>"


# ── Database Initialization ──────────────────────────────────────────────────
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


# ── Dependency ───────────────────────────────────────────────────────────────
async def get_db():
    """FastAPI dependency: yields an async SQLAlchemy session."""
    async with async_session_factory() as session:
        yield session


# ── CRUD ─────────────────────────────────────────────────────────────────────
async def create_session(db: AsyncSession, title: str = "") -> ChatSessionRecord:
    session = ChatSessionRecord(title=title, messages=[])
    db.add(session)
    await db.flush()
    return session


async def get_session(
    db: AsyncSession, session_id: uuid.UUID
) -> Optional[ChatSessionRecord]:
    result = await db.execute(select(ChatSessionRecord).where(ChatSessionRecord.id == session_id))
    return result.scalar_one_or_none()


async def list_sessions(
    db: AsyncSession,
    limit: int = 50,
    offset: int = 0,
) -> list[ChatSessionRecord]:
    stmt = (
        select(ChatSessionRecord)
        .order_by(ChatSessionRecord.updated_at.desc())
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_session_messages(
    db: AsyncSession, session_id: uuid.UUID, messages: list
) -> None:
    session = await get_session(db, session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    session.messages = messages
    session.updated_at = datetime.utcnow()
    await db.flush()


async def update_session_title(
    db: AsyncSession, session_id: uuid.UUID, title: str
) -> None:
    session = await get_session(db, session_id)
    if not session:
        raise ValueError(f"Session {session_id} not found")
    session.title = title
    session.updated_at = datetime.utcnow()
    await db.flush()


async def delete_session(db: AsyncSession, session_id: uuid.UUID) -> None:
    stmt = delete(ChatSessionRecord).where(ChatSessionRecord.id == session_id)
    result = await db.execute(stmt)
    if result.rowcount == 0:
        raise ValueError(f"Session {session_id} not found")
    await db.flush()