"""Secret Resource — 密钥资源数据模型 (P6-5)

Secret 是平台的敏感信息统一管理资源，支持:
1. API Key 加密存储
2. secret_ref 引用机制
3. 审计日志
4. 过期检查
5. 标签分类

数据模型:
- Secret: 密钥资源定义
- SecretAuditLog: 审计日志
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone


@dataclass
class Secret:
    """Secret 资源"""
    secret_id: str                      # 唯一标识（如 "anthropic-api-key"）
    name: str                           # 显示名称
    type: str                           # "api_key" | "password" | "token" | "certificate"
    value: str                          # 明文值（仅在 decrypt=True 时填充）
    description: str = ""               # 描述信息
    tags: List[str] = field(default_factory=list)  # 标签（如 ["production", "anthropic"]）
    org_id: str = "default-org"         # 组织 ID
    created_by: str = "admin"           # 创建者
    created_at: str = ""                # 创建时间
    updated_at: str = ""                # 更新时间
    last_accessed_at: Optional[str] = None  # 最后访问时间
    expires_at: Optional[str] = None    # 过期时间

    def to_dict(self, include_value: bool = False) -> Dict[str, Any]:
        """转换为字典

        Args:
            include_value: 是否包含解密值（默认不包含，安全考虑）
        """
        result = {
            "secret_id": self.secret_id,
            "name": self.name,
            "type": self.type,
            "description": self.description,
            "tags": self.tags,
            "org_id": self.org_id,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.last_accessed_at:
            result["last_accessed_at"] = self.last_accessed_at
        if self.expires_at:
            result["expires_at"] = self.expires_at
        if include_value:
            result["value"] = self.value
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Secret":
        """从字典创建"""
        return cls(
            secret_id=data["secret_id"],
            name=data["name"],
            type=data["type"],
            value=data.get("value", ""),  # 可能不包含 value
            description=data.get("description", ""),
            tags=data.get("tags", []),
            org_id=data.get("org_id", "default-org"),
            created_by=data.get("created_by", "admin"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            last_accessed_at=data.get("last_accessed_at"),
            expires_at=data.get("expires_at"),
        )

    def is_expired(self) -> bool:
        """判断 Secret 是否过期"""
        if not self.expires_at:
            return False
        try:
            expires = datetime.fromisoformat(self.expires_at.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            return now > expires
        except Exception:
            return False

    def to_secret_ref(self) -> str:
        """生成 secret_ref 引用"""
        return f"secret:{self.secret_id}"


@dataclass
class SecretAuditLog:
    """Secret 审计日志"""
    log_id: str                         # 日志 ID
    secret_id: str                      # 关联的 Secret ID
    action: str                         # "create" | "read" | "update" | "delete" | "rotate"
    actor: str                          # 执行者
    timestamp: str                      # 时间戳
    ip_address: Optional[str] = None    # IP 地址
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外元数据

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "log_id": self.log_id,
            "secret_id": self.secret_id,
            "action": self.action,
            "actor": self.actor,
            "timestamp": self.timestamp,
        }
        if self.ip_address:
            result["ip_address"] = self.ip_address
        if self.metadata:
            result["metadata"] = self.metadata
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SecretAuditLog":
        """从字典创建"""
        return cls(
            log_id=data["log_id"],
            secret_id=data["secret_id"],
            action=data["action"],
            actor=data["actor"],
            timestamp=data["timestamp"],
            ip_address=data.get("ip_address"),
            metadata=data.get("metadata", {}),
        )
