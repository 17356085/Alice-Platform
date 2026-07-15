"""ModelProvider ORM Model — 数据库表定义 (P6-1)

Moved: 2026-07-14 from platform.model_provider_models (Step 2.1 - eliminate infra → platform dependency)
"""

from sqlalchemy import Column, String, Text, DateTime, Index, JSON
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime, timezone

from aitest.infra.db import Base

JSON_PAYLOAD = JSON().with_variant(JSONB, "postgresql")


class ModelProviderModel(Base):
    """ModelProvider 表 — 外部 LLM Provider 配置"""
    __tablename__ = "model_providers"

    provider_id = Column(String(64), primary_key=True)
    name = Column(String(128), nullable=False)
    type = Column(String(32), nullable=False, index=True)  # anthropic | openai | deepseek | ollama | mimo
    config = Column(JSON_PAYLOAD, nullable=False, default=dict)   # ProviderConfig JSON
    status = Column(String(32), nullable=False, default="active", index=True)
    org_id = Column(String(64), nullable=False, default="", index=True)
    created_by = Column(String(128), nullable=False, default="")
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # 索引：org_id + status 查询
    __table_args__ = (
        Index("idx_model_providers_org_status", "org_id", "status"),
    )
