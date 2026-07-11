"""Unified ORM models — all tables in one place.

Based on aitest.infra.database.Base. Alembic manages schema via these models.

Tables (8):
  runs, run_events, execution_requests  — from RunStore (runs.db)
  tasks                                  — from TaskQueue (tasks.db)
  audit_entries                          — from AuditLogger (audit.db)
  bugs                                   — from BugHistory (bugs.db)
  artifact_lineage                       — NEW (was in-memory dict)
  chat_sessions                          — from SessionStore (SQLAlchemy)
"""

from sqlalchemy import Column, String, Integer, Float, Text, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone
import uuid

from .db import Base

# Import all models to ensure they're registered with SQLAlchemy
from aitest.platform.workflow_models import WorkflowModel  # noqa: F401
from aitest.platform.model_provider_models import ModelProviderModel  # noqa: F401
from aitest.platform.secret_models import SecretModel, SecretAuditLogModel  # noqa: F401
from aitest.platform.environment_models import EnvironmentModel  # noqa: F401


# ── Platform: Run + Events + Requests ─────────────────────────────────


class RunModel(Base):
    __tablename__ = "runs"

    run_id = Column(String(64), primary_key=True)
    request_id = Column(String(64), nullable=False, index=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    org_id = Column(String(64), nullable=False, default="", index=True)
    triggered_by = Column(String(128), nullable=False, default="")
    capability = Column(String(32), nullable=False, default="browser")
    agent = Column(String(64), nullable=False, default="")
    module = Column(String(64), nullable=False, default="", index=True)
    pages = Column(JSONB, nullable=False, default=list)
    mode = Column(String(32), nullable=False, default="full")
    status = Column(String(32), nullable=False, default="running", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_tokens = Column(Integer, nullable=False, default=0)
    total_cost = Column(Float, nullable=False, default=0.0)
    agent_runs = Column(Integer, nullable=False, default=0)
    artifacts = Column(JSONB, nullable=False, default=list)
    error_message = Column(Text, nullable=False, default="")

    # P6-1: ModelProvider 关联（可选，向后兼容）
    provider_id = Column(String(64), nullable=True, default=None)


class RunEventModel(Base):
    __tablename__ = "run_events"

    event_id = Column(String(64), primary_key=True)
    event_type = Column(String(64), nullable=False, index=True)
    run_id = Column(String(64), nullable=False, index=True)
    request_id = Column(String(64), nullable=False, default="")
    timestamp = Column(DateTime(timezone=True), nullable=False)
    data = Column(JSONB, nullable=False, default=dict)
    # Phase 2: correlate events across EventBus / ObservationBus / Adapter Events
    correlation_id = Column(String(64), nullable=True, index=True)


class ExecutionRequestModel(Base):
    __tablename__ = "execution_requests"

    request_id = Column(String(64), primary_key=True)
    workspace_id = Column(String(64), nullable=False, index=True)
    org_id = Column(String(64), nullable=False, default="", index=True)
    triggered_by = Column(String(128), nullable=False, default="")
    trigger_type = Column(String(32), nullable=False, default="manual")
    agent = Column(String(64), nullable=False, default="")
    idempotency_key = Column(String(128), nullable=False, default="", index=True)
    module = Column(String(64), nullable=False, default="")
    pages = Column(JSONB, nullable=False, default=list)
    mode = Column(String(32), nullable=False, default="full")
    provider = Column(String(32), nullable=False, default="claude")
    priority = Column(Integer, nullable=False, default=0)
    status = Column(String(32), nullable=False, default="created", index=True)
    run_ids = Column(JSONB, nullable=False, default=list)
    created_at = Column(DateTime(timezone=True), nullable=False)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=0)


# ── Task Queue ────────────────────────────────────────────────────────


class TaskModel(Base):
    __tablename__ = "tasks"

    id = Column(String(64), primary_key=True)
    agent = Column(String(64), nullable=False)
    module = Column(String(64), nullable=False)
    page = Column(String(128), nullable=False, default="")
    provider = Column(String(32), nullable=False, default="claude")
    status = Column(String(32), nullable=False, default="queued", index=True)
    result_json = Column(Text, nullable=False, default="")
    error_msg = Column(Text, nullable=False, default="")
    retry_count = Column(Integer, nullable=False, default=0)
    max_retries = Column(Integer, nullable=False, default=3)
    retry_at = Column(Float, nullable=False, default=0.0)
    created_at = Column(Float, nullable=True)
    started_at = Column(Float, nullable=True)
    completed_at = Column(Float, nullable=True)


# ── Audit Log ─────────────────────────────────────────────────────────


class AuditEntryModel(Base):
    __tablename__ = "audit_entries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String(64), nullable=False)
    event_type = Column(String(64), nullable=False, index=True)
    run_id = Column(String(64), nullable=False, default="", index=True)
    request_id = Column(String(64), nullable=False, default="")
    org_id = Column(String(64), nullable=False, default="", index=True)
    workspace_id = Column(String(64), nullable=False, default="", index=True)
    user_id = Column(String(64), nullable=False, default="")
    timestamp = Column(DateTime(timezone=True), nullable=False)
    data_json = Column(JSONB, nullable=False, default=dict)


# ── Bug History ───────────────────────────────────────────────────────


class BugModel(Base):
    __tablename__ = "bugs"

    id = Column(String(64), primary_key=True)
    date = Column(String(16), nullable=False, index=True)
    module = Column(String(64), nullable=False, index=True)
    page = Column(String(128), nullable=False, default="")
    test_name = Column(String(256), nullable=False, default="")
    error_type = Column(String(64), nullable=False, default="")
    error_message = Column(Text, nullable=False, default="")
    root_cause = Column(Text, nullable=False, default="")
    severity = Column(String(16), nullable=False, default="medium", index=True)
    status = Column(String(16), nullable=False, default="open", index=True)
    matched_issue = Column(String(128), nullable=False, default="")
    fix_description = Column(Text, nullable=False, default="")
    fix_files = Column(Text, nullable=False, default="")
    regression_risk = Column(String(16), nullable=False, default="low")
    tags = Column(Text, nullable=False, default="")
    created_at = Column(Float, nullable=False)
    updated_at = Column(Float, nullable=False)


# ── Artifact Lineage (NEW — was in-memory dict) ──────────────────────


class ArtifactLineageModel(Base):
    __tablename__ = "artifact_lineage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project = Column(String(64), nullable=False)
    module = Column(String(64), nullable=False)
    page = Column(String(128), nullable=False, default="")
    artifact_name = Column(String(256), nullable=False)
    generated_by = Column(String(64), nullable=False)
    depends_on = Column(JSONB, nullable=False, default=list)
    version = Column(String(16), nullable=False, default="1")
    run_id = Column(String(64), nullable=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        Index("idx_lineage_project", "project", "module", "page"),
    )


# ── Chat Sessions (from SessionStore) ────────────────────────────────


class ChatSessionModel(Base):
    __tablename__ = "chat_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, default="")
    messages = Column(JSONB, nullable=False, default=list)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


# ── Quality Loop: Dataset/Evaluation/Experiment (P5-1) ────────────────

from aitest.platform.quality_models import DatasetModel, EvaluationModel, ExperimentModel

# ── Workflow: Graph Model (P8-1) ───────────────────────────────────────

from aitest.platform.workflow_models import WorkflowModel

__all__ = [
    "Base",
    "RunModel",
    "RunEventModel",
    "ExecutionRequestModel",
    "TaskModel",
    "AuditEntryModel",
    "BugModel",
    "ArtifactLineageModel",
    "ChatSessionModel",
    "DatasetModel",
    "EvaluationModel",
    "ExperimentModel",
    "WorkflowModel",
]
