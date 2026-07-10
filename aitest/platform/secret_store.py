"""SecretStore — Secret 资源 CRUD 操作 (P6-5)

职责:
1. Secret CRUD 操作（自动加密/解密）
2. 审计日志记录
3. 过期检查
4. secret_ref 解析
"""

import uuid
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from aitest.platform.secret import Secret, SecretAuditLog
from aitest.platform.secret_models import SecretModel, SecretAuditLogModel
from aitest.infra.encryption import EncryptionProvider, get_encryption_provider

logger = logging.getLogger(__name__)


class SecretStore:
    """Secret 资源存储"""

    def __init__(
        self,
        session: Session,
        encryption_provider: Optional[EncryptionProvider] = None
    ):
        """初始化 SecretStore

        Args:
            session: SQLAlchemy Session
            encryption_provider: 加密 Provider（默认使用全局单例）
        """
        self.session = session
        self.encryption = encryption_provider or get_encryption_provider()

    def create_secret(
        self,
        secret_id: str,
        name: str,
        type: str,
        value: str,  # 明文
        description: str = "",
        tags: List[str] = None,
        org_id: str = "default-org",
        created_by: str = "admin",
        expires_at: Optional[str] = None,
    ) -> Secret:
        """创建 Secret（自动加密）

        Args:
            secret_id: Secret ID
            name: 显示名称
            type: 类型（api_key/password/token/certificate）
            value: 明文值
            description: 描述
            tags: 标签列表
            org_id: 组织 ID
            created_by: 创建者
            expires_at: 过期时间（ISO 8601 格式）

        Returns:
            Secret 对象（不包含明文 value）

        Raises:
            ValueError: Secret 已存在
        """
        # 检查是否已存在
        existing = self.session.query(SecretModel).filter_by(secret_id=secret_id).first()
        if existing:
            raise ValueError(f"Secret already exists: {secret_id}")

        # 加密值
        encrypted_value = self.encryption.encrypt(value)

        # 创建时间
        now = datetime.now(timezone.utc).isoformat()

        # 创建 ORM 模型
        secret_model = SecretModel(
            secret_id=secret_id,
            name=name,
            type=type,
            encrypted_value=encrypted_value,
            description=description,
            tags="[]",
            org_id=org_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
        )

        # 设置标签
        if tags:
            secret_model.set_tags(tags)

        # 保存到数据库
        self.session.add(secret_model)
        self.session.commit()

        logger.info(f"Secret created: {secret_id} (type={type}, org_id={org_id})")

        # 记录审计日志
        self._log_action(secret_id, "create", created_by)

        # 返回 Secret（不包含明文）
        return Secret(
            secret_id=secret_id,
            name=name,
            type=type,
            value="",  # 不返回明文
            description=description,
            tags=tags or [],
            org_id=org_id,
            created_by=created_by,
            created_at=now,
            updated_at=now,
            expires_at=expires_at,
        )

    def get_secret(
        self,
        secret_id: str,
        decrypt: bool = True,
        check_expiry: bool = True,
    ) -> Optional[Secret]:
        """获取 Secret

        Args:
            secret_id: Secret ID
            decrypt: 是否解密（默认 True）
            check_expiry: 是否检查过期（默认 True）

        Returns:
            Secret 对象（decrypt=True 时包含明文 value）

        Raises:
            ValueError: Secret 过期
        """
        secret_model = self.session.query(SecretModel).filter_by(secret_id=secret_id).first()
        if not secret_model:
            return None

        # 解密值
        value = ""
        if decrypt:
            try:
                value = self.encryption.decrypt(secret_model.encrypted_value)
            except Exception as e:
                logger.error(f"Failed to decrypt secret {secret_id}: {e}")
                raise ValueError(f"Failed to decrypt secret: {e}")

        # 构建 Secret 对象
        secret = Secret(
            secret_id=secret_model.secret_id,
            name=secret_model.name,
            type=secret_model.type,
            value=value,
            description=secret_model.description,
            tags=secret_model.get_tags(),
            org_id=secret_model.org_id,
            created_by=secret_model.created_by,
            created_at=secret_model.created_at.isoformat() if secret_model.created_at else "",
            updated_at=secret_model.updated_at.isoformat() if secret_model.updated_at else "",
            last_accessed_at=secret_model.last_accessed_at.isoformat() if secret_model.last_accessed_at else None,
            expires_at=secret_model.expires_at.isoformat() if secret_model.expires_at else None,
        )

        # 检查过期
        if check_expiry and secret.is_expired():
            raise ValueError(f"Secret expired: {secret_id}")

        # 更新最后访问时间
        if decrypt:
            self._update_last_accessed(secret_id)
            self._log_action(secret_id, "read", "system")

        return secret

    def list_secrets(
        self,
        org_id: Optional[str] = None,
        type: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_expired: bool = False,
    ) -> List[Secret]:
        """列出 Secrets（不返回解密值）

        Args:
            org_id: 过滤组织 ID
            type: 过滤类型
            tags: 过滤标签（包含任意一个标签即可）
            include_expired: 是否包含过期的 Secret

        Returns:
            Secret 列表（不包含 value）
        """
        query = self.session.query(SecretModel)

        # 过滤条件
        if org_id:
            query = query.filter_by(org_id=org_id)
        if type:
            query = query.filter_by(type=type)

        results = query.all()

        # 转换为 Secret 对象
        secrets = []
        for secret_model in results:
            secret = Secret(
                secret_id=secret_model.secret_id,
                name=secret_model.name,
                type=secret_model.type,
                value="",  # 不返回明文
                description=secret_model.description,
                tags=secret_model.get_tags(),
                org_id=secret_model.org_id,
                created_by=secret_model.created_by,
                created_at=secret_model.created_at.isoformat() if secret_model.created_at else "",
                updated_at=secret_model.updated_at.isoformat() if secret_model.updated_at else "",
                last_accessed_at=secret_model.last_accessed_at.isoformat() if secret_model.last_accessed_at else None,
                expires_at=secret_model.expires_at.isoformat() if secret_model.expires_at else None,
            )

            # 过滤标签
            if tags:
                secret_tags = set(secret.tags)
                filter_tags = set(tags)
                if not secret_tags.intersection(filter_tags):
                    continue

            # 过滤过期
            if not include_expired and secret.is_expired():
                continue

            secrets.append(secret)

        return secrets

    def update_secret(
        self,
        secret_id: str,
        name: Optional[str] = None,
        value: Optional[str] = None,  # 明文，如果提供则重新加密
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        expires_at: Optional[str] = None,
        updated_by: str = "admin",
    ) -> Secret:
        """更新 Secret

        Args:
            secret_id: Secret ID
            name: 新名称
            value: 新值（明文，如果提供则重新加密）
            description: 新描述
            tags: 新标签列表
            expires_at: 新过期时间
            updated_by: 更新者

        Returns:
            更新后的 Secret（不包含明文 value）

        Raises:
            ValueError: Secret 不存在
        """
        secret_model = self.session.query(SecretModel).filter_by(secret_id=secret_id).first()
        if not secret_model:
            raise ValueError(f"Secret not found: {secret_id}")

        # 更新字段
        if name is not None:
            secret_model.name = name
        if value is not None:
            secret_model.encrypted_value = self.encryption.encrypt(value)
        if description is not None:
            secret_model.description = description
        if tags is not None:
            secret_model.set_tags(tags)
        if expires_at is not None:
            secret_model.expires_at = expires_at

        secret_model.updated_at = datetime.now(timezone.utc)

        self.session.commit()

        logger.info(f"Secret updated: {secret_id}")

        # 记录审计日志
        self._log_action(secret_id, "update", updated_by)

        # 返回更新后的 Secret（不解密）
        return self.get_secret(secret_id, decrypt=False)

    def delete_secret(self, secret_id: str, deleted_by: str = "admin") -> bool:
        """删除 Secret

        Args:
            secret_id: Secret ID
            deleted_by: 删除者

        Returns:
            是否成功删除
        """
        secret_model = self.session.query(SecretModel).filter_by(secret_id=secret_id).first()
        if not secret_model:
            return False

        # 记录审计日志（在删除前）
        self._log_action(secret_id, "delete", deleted_by)

        # 删除（级联删除审计日志）
        self.session.delete(secret_model)
        self.session.commit()

        logger.info(f"Secret deleted: {secret_id}")
        return True

    def get_audit_logs(
        self,
        secret_id: str,
        limit: int = 100,
    ) -> List[SecretAuditLog]:
        """获取 Secret 审计日志

        Args:
            secret_id: Secret ID
            limit: 返回数量限制

        Returns:
            审计日志列表（按时间倒序）
        """
        logs = (
            self.session.query(SecretAuditLogModel)
            .filter_by(secret_id=secret_id)
            .order_by(SecretAuditLogModel.timestamp.desc())
            .limit(limit)
            .all()
        )

        return [
            SecretAuditLog(
                log_id=log.log_id,
                secret_id=log.secret_id,
                action=log.action,
                actor=log.actor,
                timestamp=log.timestamp.isoformat() if log.timestamp else "",
                ip_address=log.ip_address,
                metadata=log.get_metadata(),
            )
            for log in logs
        ]

    def _update_last_accessed(self, secret_id: str):
        """更新最后访问时间"""
        secret_model = self.session.query(SecretModel).filter_by(secret_id=secret_id).first()
        if secret_model:
            secret_model.last_accessed_at = datetime.now(timezone.utc)
            self.session.commit()

    def _log_action(
        self,
        secret_id: str,
        action: str,
        actor: str,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """记录审计日志"""
        log_id = f"log_{uuid.uuid4().hex[:16]}"
        now = datetime.now(timezone.utc)

        log_model = SecretAuditLogModel(
            log_id=log_id,
            secret_id=secret_id,
            action=action,
            actor=actor,
            timestamp=now,
            ip_address=ip_address,
            metadata="{}",
        )

        if metadata:
            log_model.set_metadata(metadata)

        self.session.add(log_model)
        self.session.commit()


# 全局单例
_secret_store: Optional[SecretStore] = None


def get_secret_store(session: Session = None) -> SecretStore:
    """获取 SecretStore（单例模式）

    Args:
        session: SQLAlchemy Session（如果提供则使用，否则创建新的）

    Returns:
        SecretStore 实例
    """
    global _secret_store

    if session:
        return SecretStore(session)

    if _secret_store is None:
        from aitest.infra.db import get_session
        _secret_store = SecretStore(next(get_session()))

    return _secret_store


def reset_secret_store():
    """重置全局 Store（用于测试）"""
    global _secret_store
    _secret_store = None


def resolve_secret_ref(ref: str, session: Session = None) -> str:
    """解析 secret_ref，返回明文值

    Args:
        ref: secret_ref 或普通字符串
        session: SQLAlchemy Session

    Returns:
        明文值（如果是 secret_ref 则解析，否则原样返回）

    Raises:
        ValueError: Secret 不存在或已过期
    """
    if not ref or not isinstance(ref, str):
        return ref

    if not ref.startswith("secret:"):
        return ref  # 不是 secret_ref，直接返回

    secret_id = ref[7:]  # 去掉 "secret:" 前缀
    store = get_secret_store(session)
    secret = store.get_secret(secret_id, decrypt=True, check_expiry=True)

    if not secret:
        raise ValueError(f"Secret not found: {secret_id}")

    return secret.value
