"""Shared-database notification read state.

Notification content is derived from bugs and runs.  Only the user's read
markers are persisted here, in the same SQLAlchemy database used by the rest
of the platform.  A legacy JSON file is imported lazily once per scope so
existing local installations do not lose their read state during migration.
"""
from __future__ import annotations

import json
import logging
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select

from aitest.infra.db import get_db_session
from aitest.infra.models import NotificationReadModel
from aitest.platform.paths import get_workstudy


logger = logging.getLogger(__name__)
_LOCK = threading.Lock()


def _legacy_state_path() -> Path:
    configured = os.environ.get("AITEST_NOTIFICATION_STATE_FILE", "").strip()
    if configured:
        return Path(configured)
    return get_workstudy() / "governance" / ".data" / "notification-state.json"


def _legacy_ids(scope: str) -> set[str]:
    path = _legacy_state_path()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return set()
    scopes = value.get("scopes", {}) if isinstance(value, dict) else {}
    ids = scopes.get(scope, []) if isinstance(scopes, dict) else []
    return {str(item) for item in ids} if isinstance(ids, list) else set()


def _ensure_table(session) -> None:
    # SQLite creates this table through Base.metadata.create_all.  The
    # checkfirst path also makes an already-running PostgreSQL deployment
    # self-healing until its formal migration is applied.
    NotificationReadModel.__table__.create(bind=session.get_bind(), checkfirst=True)


def _read_ids_from_db(scope: str) -> set[str]:
    with get_db_session() as session:
        _ensure_table(session)
        rows = session.scalars(
            select(NotificationReadModel.notification_id).where(NotificationReadModel.scope == scope)
        ).all()
        ids = {str(item) for item in rows}

        # One-way compatibility import from the pre-database JSON store.
        missing = _legacy_ids(scope) - ids
        if missing:
            now = datetime.now(timezone.utc)
            for notification_id in missing:
                session.add(NotificationReadModel(scope=scope, notification_id=notification_id, read_at=now))
            session.commit()
            ids.update(missing)
        return ids


def _write_legacy_marker(notification_id: str, scope: str) -> None:
    """Best-effort fallback if the shared database is temporarily unavailable."""
    path = _legacy_state_path()
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            value = {}
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        value = {}
    scopes = value.setdefault("scopes", {})
    current = scopes.setdefault(scope, [])
    if notification_id not in current:
        current.append(notification_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_ids(scope: str = "default") -> set[str]:
    normalized_scope = scope.strip() or "default"
    with _LOCK:
        try:
            return _read_ids_from_db(normalized_scope)
        except Exception as exc:
            logger.warning("notification_read_state_db_unavailable", error=str(exc))
            return _legacy_ids(normalized_scope)


def mark_read(notification_id: str, scope: str = "default") -> None:
    normalized_scope = scope.strip() or "default"
    normalized_id = notification_id.strip()
    if not normalized_id:
        return
    with _LOCK:
        try:
            with get_db_session() as session:
                _ensure_table(session)
                existing = session.get(NotificationReadModel, (normalized_scope, normalized_id))
                if existing is None:
                    session.add(NotificationReadModel(
                        scope=normalized_scope,
                        notification_id=normalized_id,
                        read_at=datetime.now(timezone.utc),
                    ))
                    session.commit()
        except Exception as exc:
            logger.warning("notification_read_state_db_write_failed", error=str(exc))
            _write_legacy_marker(normalized_id, normalized_scope)
