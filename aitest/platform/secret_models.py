"""Secret ORM Models — Secret 数据库模型 (P6-5)

数据库表:
1. secrets: Secret 资源存储（加密值）
2. secret_audit_logs: 审计日志
"""

from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from aitest.infra.models import Base
import json


class SecretModel(Base):
    """Secret 资源 ORM 模型"""
    __tablename__ = "secrets"

    secret_id = Column(String(128), primary_key=True)
    name = Column(String(256), nullable=False)
    type = Column(String(32), nullable=False, index=True)  # "api_key" | "password" | "token" | "certificate"
    encrypted_value = Column(Text, nullable=False)  # 加密后的值
    description = Column(Text, default="")
    tags = Column(Text, default="[]")  # JSON 数组（SQLite 用 Text，PostgreSQL 用 JSONB）
    org_id = Column(String(64), nullable=False, default="default-org", index=True)
    created_by = Column(String(128), nullable=False, default="admin")
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)

    # 复合索引
    __table_args__ = (
        Index('idx_secrets_org_type', 'org_id', 'type'),
    )

    def get_tags(self):
        """获取标签列表（解析 JSON）"""
        if not self.tags:
            return []
        try:
            return json.loads(self.tags)
        except Exception:
            return []

    def set_tags(self, tags: list):
        """设置标签列表（序列化为 JSON）"""
        self.tags = json.dumps(tags)


class SecretAuditLogModel(Base):
    """Secret 审计日志 ORM 模型"""
    __tablename__ = "secret_audit_logs"

    log_id = Column(String(128), primary_key=True)
    secret_id = Column(String(128), ForeignKey('secrets.secret_id', ondelete='CASCADE'), nullable=False, index=True)
    action = Column(String(32), nullable=False)  # "create" | "read" | "update" | "delete" | "rotate"
    actor = Column(String(128), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    ip_address = Column(String(64), nullable=True)
    metadata = Column(Text, default="{}")  # JSON 对象

    def get_metadata(self):
        """获取元数据（解析 JSON）"""
        if not self.metadata:
            return {}
        try:
            return json.loads(self.metadata)
        except Exception:
            return {}

    def set_metadata(self, metadata: dict):
        """设置元数据（序列化为 JSON）"""
        self.metadata = json.dumps(metadata)
