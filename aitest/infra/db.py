"""SQLAlchemy compatibility facade for resource stores.

The platform's operational database helpers live in :mod:`aitest.infra.database`.
Resource stores (workflows, quality, secrets, environments) use SQLAlchemy ORM,
so they share this small, lazily-initialised SQLite facade in local mode.
"""

from __future__ import annotations

import os
from pathlib import Path
from collections.abc import Generator
from threading import Lock

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


class Base(DeclarativeBase):
    """Declarative base used by resource ORM models."""


_lock = Lock()
_engine = None
_session_factory: sessionmaker[Session] | None = None


def _database_url() -> str:
    configured = os.environ.get("AITEST_SQLALCHEMY_URL")
    if configured:
        return configured
    root = Path(__file__).resolve().parents[2]
    db_path = root / "governance" / ".data" / "aitest.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


def _get_session_factory() -> sessionmaker[Session]:
    global _engine, _session_factory
    if _session_factory is None:
        with _lock:
            if _session_factory is None:
                url = _database_url()
                connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
                _engine = create_engine(url, future=True, connect_args=connect_args)
                _session_factory = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)
    return _session_factory


def get_db_session() -> Session:
    """Return an ORM session for resource-store operations."""
    return _get_session_factory()()


def get_session() -> Generator[Session, None, None]:
    """FastAPI dependency yielding an ORM session and closing it afterwards."""
    session = get_db_session()
    try:
        yield session
    finally:
        session.close()
