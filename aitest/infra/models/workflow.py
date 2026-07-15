"""Workflow database models — SQLAlchemy ORM (P8-1).

Moved: 2026-07-14 from platform.workflow_models (Step 2.1 - eliminate infra → platform dependency)
"""

from sqlalchemy import Column, Text, DateTime
from sqlalchemy.sql import func
from aitest.infra.db import Base


class WorkflowModel(Base):
    """工作流定义表"""
    __tablename__ = "workflows"

    workflow_id = Column(Text, primary_key=True)
    name = Column(Text, nullable=False)
    description = Column(Text, default="")
    version = Column(Text, nullable=False)
    status = Column(Text, default="draft")  # "draft" | "published" | "archived"
    org_id = Column(Text, default="")
    created_by = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    graph_json = Column(Text, nullable=False)  # JSON schema
