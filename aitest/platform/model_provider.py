"""ModelProvider Resource — 外部 LLM Provider 资源化 (P6-1)

设计目标:
1. 将硬编码的环境变量（ANTHROPIC_API_KEY）抽象为可管理的 ModelProvider 资源
2. 支持多个 Provider 实例（prod/dev/test 环境）
3. 支持动态切换 Provider（无需重启服务）
4. 为 Secret Manager 预留接口（api_key_ref）

架构:
- ModelProvider: 资源定义（id/name/type/config/status）
- ModelProviderModel: ORM 模型
- ModelProviderStore: CRUD 操作
- REST API: /api/v1/providers

数据模型:
{
  "provider_id": "anthropic-prod",
  "name": "Anthropic Production",
  "type": "anthropic",  // anthropic | openai | deepseek | ollama | mimo
  "config": {
    "api_key": "sk-ant-...",       // 明文（临时），未来改为 api_key_ref
    "base_url": null,               // 可选：自定义 base_url
    "default_model": "claude-3-5-sonnet-20241022",
    "max_tokens": 4096,
    "timeout_seconds": 60
  },
  "status": "active",  // active | inactive
  "org_id": "default-org",
  "created_by": "admin",
  "created_at": "2026-07-10T10:00:00Z",
  "updated_at": "2026-07-10T10:00:00Z"
}

向后兼容:
- get_provider() 优先从 ModelProviderStore 加载，失败时 fallback 到环境变量
- 现有代码无需修改，透明升级

集成点:
1. aitest.adapters.llm.interface.get_provider() — 注入 ModelProvider config
2. aitest.platform.run_store.RunModel — 新增 provider_id 字段（可选）
3. aitest.server.api.runs.py — 支持 runtime.provider_id 参数
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from datetime import datetime, timezone


@dataclass
class ProviderConfig:
    """Provider 配置"""
    api_key: Optional[str] = None          # 明文 API Key（临时，未来改为 secret_ref）
    api_key_ref: Optional[str] = None      # Secret Manager 引用（未来）
    base_url: Optional[str] = None         # 自定义 base_url
    default_model: Optional[str] = None    # 默认模型
    max_tokens: int = 4096                 # 最大 token 数
    timeout_seconds: int = 60              # 超时时间

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        result = {
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout_seconds,
        }
        if self.api_key:
            result["api_key"] = self.api_key
        if self.api_key_ref:
            result["api_key_ref"] = self.api_key_ref
        if self.base_url:
            result["base_url"] = self.base_url
        if self.default_model:
            result["default_model"] = self.default_model
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        """从字典创建"""
        return cls(
            api_key=data.get("api_key"),
            api_key_ref=data.get("api_key_ref"),
            base_url=data.get("base_url"),
            default_model=data.get("default_model"),
            max_tokens=data.get("max_tokens", 4096),
            timeout_seconds=data.get("timeout_seconds", 60),
        )


@dataclass
class ModelProvider:
    """ModelProvider 资源"""
    provider_id: str
    name: str
    type: str  # "anthropic" | "openai" | "deepseek" | "ollama" | "mimo"
    config: ProviderConfig
    status: str = "active"  # "active" | "inactive"
    org_id: str = ""
    created_by: str = ""
    created_at: str = ""
    updated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "provider_id": self.provider_id,
            "name": self.name,
            "type": self.type,
            "config": self.config.to_dict(),
            "status": self.status,
            "org_id": self.org_id,
            "created_by": self.created_by,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ModelProvider":
        """从字典创建"""
        return cls(
            provider_id=data["provider_id"],
            name=data["name"],
            type=data["type"],
            config=ProviderConfig.from_dict(data.get("config", {})),
            status=data.get("status", "active"),
            org_id=data.get("org_id", ""),
            created_by=data.get("created_by", ""),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
        )

    def is_active(self) -> bool:
        """判断 Provider 是否激活"""
        return self.status == "active"

    def get_api_key(self) -> Optional[str]:
        """获取 API Key（支持 Secret Manager）

        优先级:
        1. api_key_ref（Secret Manager）
        2. api_key（明文，向后兼容）
        """
        # 优先级 1: api_key_ref（Secret Manager）
        if self.config.api_key_ref:
            try:
                from aitest.platform.secret_store import resolve_secret_ref
                return resolve_secret_ref(self.config.api_key_ref)
            except Exception as e:
                # 记录错误但不中断（可能是 Secret 不存在或已过期）
                import logging
                logging.error(f"Failed to resolve api_key_ref: {e}")
                # Fall through 到 api_key

        # 优先级 2: 明文 api_key（向后兼容）
        if self.config.api_key:
            return self.config.api_key

        return None

    def to_provider_kwargs(self) -> Dict[str, Any]:
        """转换为 get_provider() 的 kwargs"""
        kwargs = {}

        # API Key
        api_key = self.get_api_key()
        if api_key:
            kwargs["api_key"] = api_key

        # Base URL
        if self.config.base_url:
            kwargs["base_url"] = self.config.base_url

        # Model
        if self.config.default_model:
            kwargs["model"] = self.config.default_model

        return kwargs
