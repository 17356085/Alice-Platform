"""Notification read-marker ORM model."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, String

from aitest.infra.db import Base


class NotificationReadModel(Base):
    """Persisted read markers for the derived notification feed."""

    __tablename__ = "notification_read_state"

    scope = Column(String(200), primary_key=True)
    notification_id = Column(String(256), primary_key=True)
    read_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


__all__ = ["NotificationReadModel"]
