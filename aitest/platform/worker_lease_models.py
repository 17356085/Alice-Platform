"""WorkerLeaseModel — Worker 心跳表 ORM 模型 (P3-5)"""

from sqlalchemy import Column, String, Integer, DateTime, Text, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone

from aitest.infra.db import Base

JSON_PAYLOAD = JSON().with_variant(JSONB, "postgresql")


class WorkerLeaseModel(Base):
    """Worker 租约与心跳状态表"""
    __tablename__ = "workers"

    worker_id = Column(String(64), primary_key=True)
    hostname = Column(String(255), nullable=False)
    pid = Column(Integer, nullable=False)
    status = Column(String(32), nullable=False, default="running", index=True)  # running | draining | stopped | dead
    started_at = Column(DateTime(timezone=True), nullable=False)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=False, index=True)
    heartbeat_interval_seconds = Column(Integer, nullable=False, default=30)
    claimed_requests = Column(JSON_PAYLOAD, nullable=False, default=list)  # list[str]
    stats = Column(JSON_PAYLOAD, nullable=False, default=dict)  # {claimed: int, completed: int, ...}
    # ``metadata`` belongs to SQLAlchemy's Declarative API.  Keep the
    # persisted column name for the migration/API contract, but use a safe
    # Python attribute name on the model.
    metadata_json = Column("metadata", JSON_PAYLOAD, nullable=False, default=dict)  # {version: str, region: str, ...}
    org_id = Column(String(64), nullable=False, default="default-org", index=True)

    __table_args__ = (
        Index("idx_workers_status_heartbeat", "status", "last_heartbeat_at"),
        Index("idx_workers_org", "org_id", "status"),
    )
