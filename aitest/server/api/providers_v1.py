"""ModelProvider REST API — /api/v1/providers (P6-1)"""

import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from aitest.platform.model_provider import ModelProvider, ProviderConfig
from aitest.platform.model_provider_store import get_model_provider_store

logger = logging.getLogger(__name__)

providers_router = APIRouter(prefix="/api/v1/providers", tags=["providers"])


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Request/Response Models
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class ProviderConfigRequest(BaseModel):
    """Provider 配置请求"""
    api_key: Optional[str] = None
    api_key_ref: Optional[str] = None
    base_url: Optional[str] = None
    default_model: Optional[str] = None
    max_tokens: int = 4096
    timeout_seconds: int = 60


class CreateProviderRequest(BaseModel):
    """创建 Provider 请求"""
    provider_id: str
    name: str
    type: str  # anthropic | openai | deepseek | ollama | mimo
    config: ProviderConfigRequest
    org_id: str = "default-org"
    created_by: str = "admin"


class UpdateProviderRequest(BaseModel):
    """更新 Provider 请求"""
    name: Optional[str] = None
    config: Optional[ProviderConfigRequest] = None
    status: Optional[str] = None


class TestConnectionRequest(BaseModel):
    """测试连接请求"""
    type: str
    config: ProviderConfigRequest


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# API Endpoints
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


@providers_router.post("")
async def create_provider(req: CreateProviderRequest) -> Dict[str, Any]:
    """创建 ModelProvider"""
    store = get_model_provider_store()

    # 检查是否已存在
    existing = store.get_provider(req.provider_id)
    if existing:
        raise HTTPException(status_code=400, detail=f"Provider already exists: {req.provider_id}")

    # 创建 ProviderConfig
    config = ProviderConfig(
        api_key=req.config.api_key,
        api_key_ref=req.config.api_key_ref,
        base_url=req.config.base_url,
        default_model=req.config.default_model,
        max_tokens=req.config.max_tokens,
        timeout_seconds=req.config.timeout_seconds,
    )

    # 创建 Provider
    provider = store.create_provider(
        provider_id=req.provider_id,
        name=req.name,
        type=req.type,
        config=config,
        org_id=req.org_id,
        created_by=req.created_by,
    )

    return {
        "success": True,
        "provider": provider.to_dict(),
    }


@providers_router.get("/{provider_id}")
async def get_provider(provider_id: str) -> Dict[str, Any]:
    """获取 ModelProvider"""
    store = get_model_provider_store()
    provider = store.get_provider(provider_id)

    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider not found: {provider_id}")

    return {
        "success": True,
        "provider": provider.to_dict(),
    }


@providers_router.get("")
async def list_providers(
    org_id: Optional[str] = None,
    status: Optional[str] = None,
    type: Optional[str] = None,
) -> Dict[str, Any]:
    """列出 ModelProviders"""
    store = get_model_provider_store()
    providers = store.list_providers(org_id=org_id, status=status, type=type)

    return {
        "success": True,
        "providers": [p.to_dict() for p in providers],
        "total": len(providers),
    }


@providers_router.put("/{provider_id}")
async def update_provider(provider_id: str, req: UpdateProviderRequest) -> Dict[str, Any]:
    """更新 ModelProvider"""
    store = get_model_provider_store()

    # 转换 config
    config = None
    if req.config:
        config = ProviderConfig(
            api_key=req.config.api_key,
            api_key_ref=req.config.api_key_ref,
            base_url=req.config.base_url,
            default_model=req.config.default_model,
            max_tokens=req.config.max_tokens,
            timeout_seconds=req.config.timeout_seconds,
        )

    # 更新
    provider = store.update_provider(
        provider_id=provider_id,
        name=req.name,
        config=config,
        status=req.status,
    )

    if not provider:
        raise HTTPException(status_code=404, detail=f"Provider not found: {provider_id}")

    return {
        "success": True,
        "provider": provider.to_dict(),
    }


@providers_router.delete("/{provider_id}")
async def delete_provider(provider_id: str) -> Dict[str, Any]:
    """删除 ModelProvider"""
    store = get_model_provider_store()
    success = store.delete_provider(provider_id)

    if not success:
        raise HTTPException(status_code=404, detail=f"Provider not found: {provider_id}")

    return {
        "success": True,
        "message": f"Provider deleted: {provider_id}",
    }


@providers_router.post("/test")
async def test_connection(req: TestConnectionRequest) -> Dict[str, Any]:
    """测试 Provider 连接"""
    from aitest.adapters.llm.interface import get_provider

    try:
        # 构建 kwargs
        kwargs = {}
        if req.config.api_key:
            kwargs["api_key"] = req.config.api_key
        if req.config.base_url:
            kwargs["base_url"] = req.config.base_url
        if req.config.default_model:
            kwargs["model"] = req.config.default_model

        # 创建 Provider 实例
        provider = get_provider(req.type, **kwargs)

        # 测试简单调用
        response = provider.complete(
            system="You are a helpful assistant.",
            prompt="Reply with 'OK' if you can read this.",
            max_tokens=10,
        )

        return {
            "success": True,
            "message": "Connection successful",
            "test_response": response.text[:100],  # 截断输出
        }

    except Exception as e:
        logger.error(f"[ProvidersAPI] Test connection failed: {e}")
        return {
            "success": False,
            "error": str(e),
        }
