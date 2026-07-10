"""Environment Resource — 环境资源数据模型 (P6-4)

Environment 是平台的环境配置资源，支持:
1. 多环境管理（dev/staging/prod）
2. 统一配置（base_url、变量）
3. Secret 引用（variables 中使用 secret_ref）
4. Run 关联（environment_id）
5. 默认环境设置

数据模型:
- Environment: 环境资源定义
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any


@dataclass
class Environment:
    """Environment 资源"""
    environment_id: str                     # 唯一标识（如 "staging", "production"）
    name: str                               # 显示名称
    base_url: str                           # 测试环境 URL
    description: str = ""                   # 描述信息
    variables: Dict[str, str] = field(default_factory=dict)  # 环境变量（可包含 secret_ref）
    tags: List[str] = field(default_factory=list)  # 标签（如 ["staging", "web"]）
    org_id: str = "default-org"             # 组织 ID
    created_by: str = "admin"               # 创建者
    created_at: str = ""                    # 创建时间
    updated_at: str = ""                    # 更新时间
    is_default: bool = False                # 是否默认环境

    def to_dict(self, include_resolved: bool = False) -> Dict[str, Any]:
        """转换为字典

        Args:
            include_resolved: 是否包含解析后的变量（默认不包含）
        """
        result = {
            "environment_id": self.environment_id,
            "name": self.name,
            "base_url": self.base_url,
            "description": self.description,
            "variables": self.variables,
            "tags": self.tags,
            "org_id": self.org_id,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "is_default": self.is_default,
        }
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Environment":
        """从字典创建"""
        return cls(
            environment_id=data["environment_id"],
            name=data["name"],
            base_url=data["base_url"],
            description=data.get("description", ""),
            variables=data.get("variables", {}),
            tags=data.get("tags", []),
            org_id=data.get("org_id", "default-org"),
            created_by=data.get("created_by", "admin"),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            is_default=data.get("is_default", False),
        )

    def has_secret_ref(self) -> bool:
        """判断是否包含 secret_ref"""
        for value in self.variables.values():
            if isinstance(value, str) and value.startswith("secret:"):
                return True
        return False

    def get_secret_refs(self) -> List[str]:
        """获取所有 secret_ref"""
        refs = []
        for value in self.variables.values():
            if isinstance(value, str) and value.startswith("secret:"):
                refs.append(value)
        return refs
