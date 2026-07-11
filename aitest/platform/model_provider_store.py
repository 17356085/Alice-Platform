"""ModelProvider Store — CRUD 操作 (P6-1)"""

import logging
from typing import Optional, List
from datetime import datetime, timezone

from aitest.infra.db import get_db_session
from aitest.platform.model_provider import ModelProvider, ProviderConfig
from aitest.platform.model_provider_models import ModelProviderModel

logger = logging.getLogger(__name__)


class ModelProviderStore:
    """ModelProvider 存储层"""

    def __init__(self, db_session=None):
        self.session = db_session or get_db_session()

    def create_provider(
        self,
        provider_id: str,
        name: str,
        type: str,
        config: ProviderConfig,
        org_id: str = "",
        created_by: str = "",
        status: str = "active",
    ) -> ModelProvider:
        """创建 ModelProvider"""
        now = datetime.now(timezone.utc).isoformat()

        model = ModelProviderModel(
            provider_id=provider_id,
            name=name,
            type=type,
            config=config.to_dict(),
            status=status,
            org_id=org_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

        self.session.add(model)
        self.session.commit()

        logger.info(f"[ModelProviderStore] Created provider: {provider_id} (type={type})")

        return ModelProvider(
            provider_id=provider_id,
            name=name,
            type=type,
            config=config,
            status=status,
            org_id=org_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
        )

    def get_provider(self, provider_id: str) -> Optional[ModelProvider]:
        """获取 ModelProvider"""
        model = self.session.query(ModelProviderModel).filter_by(provider_id=provider_id).first()

        if not model:
            return None

        return ModelProvider(
            provider_id=model.provider_id,
            name=model.name,
            type=model.type,
            config=ProviderConfig.from_dict(model.config),
            status=model.status,
            org_id=model.org_id,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def list_providers(
        self,
        org_id: Optional[str] = None,
        status: Optional[str] = None,
        type: Optional[str] = None,
    ) -> List[ModelProvider]:
        """列出 ModelProviders"""
        query = self.session.query(ModelProviderModel)

        if org_id:
            query = query.filter_by(org_id=org_id)
        if status:
            query = query.filter_by(status=status)
        if type:
            query = query.filter_by(type=type)

        models = query.all()

        return [
            ModelProvider(
                provider_id=m.provider_id,
                name=m.name,
                type=m.type,
                config=ProviderConfig.from_dict(m.config),
                status=m.status,
                org_id=m.org_id,
                created_by=m.created_by,
                created_at=m.created_at,
                updated_at=m.updated_at,
            )
            for m in models
        ]

    def update_provider(
        self,
        provider_id: str,
        name: Optional[str] = None,
        config: Optional[ProviderConfig] = None,
        status: Optional[str] = None,
    ) -> Optional[ModelProvider]:
        """更新 ModelProvider"""
        model = self.session.query(ModelProviderModel).filter_by(provider_id=provider_id).first()

        if not model:
            logger.warning(f"[ModelProviderStore] Provider not found: {provider_id}")
            return None

        if name:
            model.name = name
        if config:
            model.config = config.to_dict()
        if status:
            model.status = status

        model.updated_at = datetime.now(timezone.utc).isoformat()

        self.session.commit()

        logger.info(f"[ModelProviderStore] Updated provider: {provider_id}")

        return self.get_provider(provider_id)

    def delete_provider(self, provider_id: str) -> bool:
        """删除 ModelProvider"""
        model = self.session.query(ModelProviderModel).filter_by(provider_id=provider_id).first()

        if not model:
            logger.warning(f"[ModelProviderStore] Provider not found: {provider_id}")
            return False

        self.session.delete(model)
        self.session.commit()

        logger.info(f"[ModelProviderStore] Deleted provider: {provider_id}")
        return True

    def get_default_provider(self, org_id: str = "", type: str = "anthropic") -> Optional[ModelProvider]:
        """获取默认 Provider（第一个 active 的指定类型）"""
        query = self.session.query(ModelProviderModel).filter_by(status="active", type=type)

        if org_id:
            query = query.filter_by(org_id=org_id)

        model = query.first()

        if not model:
            return None

        return ModelProvider(
            provider_id=model.provider_id,
            name=model.name,
            type=model.type,
            config=ProviderConfig.from_dict(model.config),
            status=model.status,
            org_id=model.org_id,
            created_by=model.created_by,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )


# 全局单例
_store = None


def get_model_provider_store() -> ModelProviderStore:
    """获取全局 ModelProviderStore 实例"""
    global _store
    if _store is None:
        _store = ModelProviderStore()
    return _store
