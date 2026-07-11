"""EnvironmentStore — Environment 资源 CRUD 操作 (P6-4)

职责:
1. Environment CRUD 操作
2. 默认 Environment 管理
3. 变量解析（自动解析 secret_ref）
"""

import logging
from typing import Optional, List, Dict
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from aitest.platform.environment import Environment
from aitest.platform.environment_models import EnvironmentModel
from aitest.platform.secret_store import resolve_secret_ref

logger = logging.getLogger(__name__)


class EnvironmentStore:
    """Environment 资源存储"""

    def __init__(self, session: Session):
        """初始化 EnvironmentStore

        Args:
            session: SQLAlchemy Session
        """
        self.session = session

    def create_environment(
        self,
        environment_id: str,
        name: str,
        base_url: str,
        description: str = "",
        variables: Dict[str, str] = None,
        tags: List[str] = None,
        org_id: str = "default-org",
        created_by: str = "admin",
        is_default: bool = False,
    ) -> Environment:
        """创建 Environment

        Args:
            environment_id: Environment ID
            name: 显示名称
            base_url: 测试环境 URL
            description: 描述
            variables: 环境变量（可包含 secret_ref）
            tags: 标签列表
            org_id: 组织 ID
            created_by: 创建者
            is_default: 是否设为默认环境

        Returns:
            Environment 对象

        Raises:
            ValueError: Environment 已存在
        """
        # 检查是否已存在
        existing = self.session.query(EnvironmentModel).filter_by(environment_id=environment_id).first()
        if existing:
            raise ValueError(f"Environment already exists: {environment_id}")

        # 如果设为默认，取消其他默认环境
        if is_default:
            self._clear_default(org_id)

        # 创建时间
        now = datetime.now(timezone.utc)

        # 创建 ORM 模型
        env_model = EnvironmentModel(
            environment_id=environment_id,
            name=name,
            base_url=base_url,
            description=description,
            variables="{}",
            tags="[]",
            org_id=org_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            is_default=is_default,
        )

        # 设置变量和标签
        if variables:
            env_model.set_variables(variables)
        if tags:
            env_model.set_tags(tags)

        # 保存到数据库
        self.session.add(env_model)
        self.session.commit()

        logger.info(f"Environment created: {environment_id} (org_id={org_id}, is_default={is_default})")

        # 返回 Environment
        return Environment(
            environment_id=environment_id,
            name=name,
            base_url=base_url,
            description=description,
            variables=variables or {},
            tags=tags or [],
            org_id=org_id,
            created_by=created_by,
            created_at=now.isoformat(),
            updated_at=now.isoformat(),
            is_default=is_default,
        )

    def get_environment(self, environment_id: str) -> Optional[Environment]:
        """获取 Environment

        Args:
            environment_id: Environment ID

        Returns:
            Environment 对象
        """
        env_model = self.session.query(EnvironmentModel).filter_by(environment_id=environment_id).first()
        if not env_model:
            return None

        return Environment(
            environment_id=env_model.environment_id,
            name=env_model.name,
            base_url=env_model.base_url,
            description=env_model.description,
            variables=env_model.get_variables(),
            tags=env_model.get_tags(),
            org_id=env_model.org_id,
            created_by=env_model.created_by,
            created_at=env_model.created_at.isoformat() if env_model.created_at else "",
            updated_at=env_model.updated_at.isoformat() if env_model.updated_at else "",
            is_default=env_model.is_default,
        )

    def list_environments(
        self,
        org_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> List[Environment]:
        """列出 Environments

        Args:
            org_id: 过滤组织 ID
            tags: 过滤标签（包含任意一个标签即可）

        Returns:
            Environment 列表
        """
        query = self.session.query(EnvironmentModel)

        # 过滤条件
        if org_id:
            query = query.filter_by(org_id=org_id)

        results = query.all()

        # 转换为 Environment 对象
        environments = []
        for env_model in results:
            env = Environment(
                environment_id=env_model.environment_id,
                name=env_model.name,
                base_url=env_model.base_url,
                description=env_model.description,
                variables=env_model.get_variables(),
                tags=env_model.get_tags(),
                org_id=env_model.org_id,
                created_by=env_model.created_by,
                created_at=env_model.created_at.isoformat() if env_model.created_at else "",
                updated_at=env_model.updated_at.isoformat() if env_model.updated_at else "",
                is_default=env_model.is_default,
            )

            # 过滤标签
            if tags:
                env_tags = set(env.tags)
                filter_tags = set(tags)
                if not env_tags.intersection(filter_tags):
                    continue

            environments.append(env)

        return environments

    def update_environment(
        self,
        environment_id: str,
        name: Optional[str] = None,
        base_url: Optional[str] = None,
        description: Optional[str] = None,
        variables: Optional[Dict[str, str]] = None,
        tags: Optional[List[str]] = None,
        is_default: Optional[bool] = None,
    ) -> Environment:
        """更新 Environment

        Args:
            environment_id: Environment ID
            name: 新名称
            base_url: 新 base_url
            description: 新描述
            variables: 新变量
            tags: 新标签列表
            is_default: 是否设为默认

        Returns:
            更新后的 Environment

        Raises:
            ValueError: Environment 不存在
        """
        env_model = self.session.query(EnvironmentModel).filter_by(environment_id=environment_id).first()
        if not env_model:
            raise ValueError(f"Environment not found: {environment_id}")

        # 更新字段
        if name is not None:
            env_model.name = name
        if base_url is not None:
            env_model.base_url = base_url
        if description is not None:
            env_model.description = description
        if variables is not None:
            env_model.set_variables(variables)
        if tags is not None:
            env_model.set_tags(tags)
        if is_default is not None:
            if is_default:
                self._clear_default(env_model.org_id)
            env_model.is_default = is_default

        env_model.updated_at = datetime.now(timezone.utc)

        self.session.commit()

        logger.info(f"Environment updated: {environment_id}")

        # 返回更新后的 Environment
        return self.get_environment(environment_id)

    def delete_environment(self, environment_id: str) -> bool:
        """删除 Environment

        Args:
            environment_id: Environment ID

        Returns:
            是否成功删除
        """
        env_model = self.session.query(EnvironmentModel).filter_by(environment_id=environment_id).first()
        if not env_model:
            return False

        # 删除
        self.session.delete(env_model)
        self.session.commit()

        logger.info(f"Environment deleted: {environment_id}")
        return True

    def get_default_environment(self, org_id: str = "default-org") -> Optional[Environment]:
        """获取默认 Environment

        Args:
            org_id: 组织 ID

        Returns:
            默认 Environment（如果存在）
        """
        env_model = (
            self.session.query(EnvironmentModel)
            .filter_by(org_id=org_id, is_default=True)
            .first()
        )
        if not env_model:
            return None

        return self.get_environment(env_model.environment_id)

    def set_default_environment(self, environment_id: str, org_id: str = "default-org"):
        """设置默认 Environment

        Args:
            environment_id: Environment ID
            org_id: 组织 ID

        Raises:
            ValueError: Environment 不存在
        """
        env_model = self.session.query(EnvironmentModel).filter_by(
            environment_id=environment_id,
            org_id=org_id,
        ).first()
        if not env_model:
            raise ValueError(f"Environment not found in organization: {environment_id}")

        # 取消其他默认环境
        self._clear_default(org_id)

        # 设置为默认
        env_model.is_default = True
        env_model.updated_at = datetime.now(timezone.utc)
        self.session.commit()

        logger.info(f"Default environment set: {environment_id} (org_id={org_id})")

    def resolve_variables(self, environment_id: str) -> Dict[str, str]:
        """解析 Environment 变量（自动解析 secret_ref）

        Args:
            environment_id: Environment ID

        Returns:
            解析后的变量字典（secret_ref 已解密）

        Raises:
            ValueError: Environment 不存在
        """
        env = self.get_environment(environment_id)
        if not env:
            raise ValueError(f"Environment not found: {environment_id}")

        resolved = {}
        for key, value in env.variables.items():
            # 自动解析 secret_ref
            resolved[key] = resolve_secret_ref(value, self.session)

        return resolved

    def _clear_default(self, org_id: str):
        """取消指定组织的默认 Environment"""
        self.session.query(EnvironmentModel).filter_by(
            org_id=org_id,
            is_default=True
        ).update({"is_default": False})
        self.session.commit()


# 全局单例
_environment_store: Optional[EnvironmentStore] = None


def get_environment_store(session: Session = None) -> EnvironmentStore:
    """获取 EnvironmentStore（单例模式）

    Args:
        session: SQLAlchemy Session（如果提供则使用，否则创建新的）

    Returns:
        EnvironmentStore 实例
    """
    global _environment_store

    if session:
        return EnvironmentStore(session)

    if _environment_store is None:
        from aitest.infra.db import get_session
        _environment_store = EnvironmentStore(next(get_session()))

    return _environment_store


def reset_environment_store():
    """重置全局 Store（用于测试）"""
    global _environment_store
    _environment_store = None
