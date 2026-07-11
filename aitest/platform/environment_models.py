"""Environment ORM Models — Environment 数据库模型 (P6-4)

数据库表:
1. environments: Environment 资源存储
"""

from sqlalchemy import Column, String, DateTime, Text, Boolean, Index
from aitest.infra.db import Base
import json


class EnvironmentModel(Base):
    """Environment 资源 ORM 模型"""
    __tablename__ = "environments"

    environment_id = Column(String(64), primary_key=True)
    name = Column(String(256), nullable=False)
    base_url = Column(String(512), nullable=False)
    description = Column(Text, default="")
    variables = Column(Text, default="{}")  # JSON 对象（SQLite 用 Text，PostgreSQL 用 JSONB）
    tags = Column(Text, default="[]")  # JSON 数组
    org_id = Column(String(64), nullable=False, default="default-org", index=True)
    created_by = Column(String(128), nullable=False, default="admin")
    created_at = Column(DateTime(timezone=True), nullable=False)
    updated_at = Column(DateTime(timezone=True), nullable=False)
    is_default = Column(Boolean, default=False, index=True)

    # 复合索引
    __table_args__ = (
        Index('idx_environments_org_default', 'org_id', 'is_default'),
    )

    def get_variables(self) -> dict:
        """获取变量字典（解析 JSON）"""
        if not self.variables:
            return {}
        try:
            return json.loads(self.variables)
        except Exception:
            return {}

    def set_variables(self, variables: dict):
        """设置变量字典（序列化为 JSON）"""
        self.variables = json.dumps(variables)

    def get_tags(self) -> list:
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
