"""Secret Manager REST API — /api/v1/secrets (P6-5)

端点:
- POST   /api/v1/secrets              # 创建 Secret
- GET    /api/v1/secrets              # 列出 Secrets（不返回解密值）
- GET    /api/v1/secrets/:id          # 获取 Secret（不返回解密值）
- GET    /api/v1/secrets/:id/value    # 获取 Secret 解密值
- PUT    /api/v1/secrets/:id          # 更新 Secret
- DELETE /api/v1/secrets/:id          # 删除 Secret
- GET    /api/v1/secrets/:id/audit    # 获取审计日志
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session

from aitest.infra.db import get_session
from aitest.platform.secret_store import SecretStore

secrets_router = APIRouter(prefix="/api/v1/secrets", tags=["secrets"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateSecretRequest(BaseModel):
    """创建 Secret 请求"""
    secret_id: str = Field(..., description="Secret ID（唯一标识）")
    name: str = Field(..., description="显示名称")
    type: str = Field(..., description="类型（api_key/password/token/certificate）")
    value: str = Field(..., description="明文值（服务端自动加密）")
    description: str = Field(default="", description="描述信息")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    org_id: str = Field(default="default-org", description="组织 ID")
    created_by: str = Field(default="admin", description="创建者")
    expires_at: Optional[str] = Field(default=None, description="过期时间（ISO 8601 格式）")


class UpdateSecretRequest(BaseModel):
    """更新 Secret 请求"""
    name: Optional[str] = Field(default=None, description="新名称")
    value: Optional[str] = Field(default=None, description="新值（明文，服务端自动加密）")
    description: Optional[str] = Field(default=None, description="新描述")
    tags: Optional[List[str]] = Field(default=None, description="新标签列表")
    expires_at: Optional[str] = Field(default=None, description="新过期时间")
    updated_by: str = Field(default="admin", description="更新者")


class SecretResponse(BaseModel):
    """Secret 响应（不包含解密值）"""
    secret_id: str
    name: str
    type: str
    description: str
    tags: List[str]
    org_id: str
    created_by: str
    created_at: str
    updated_at: str
    last_accessed_at: Optional[str]
    expires_at: Optional[str]


class SecretValueResponse(BaseModel):
    """Secret 解密值响应"""
    secret_id: str
    value: str


class AuditLogResponse(BaseModel):
    """审计日志响应"""
    log_id: str
    secret_id: str
    action: str
    actor: str
    timestamp: str
    ip_address: Optional[str]
    metadata: dict


# ============================================================================
# API Endpoints
# ============================================================================

@secrets_router.post("", response_model=SecretResponse)
async def create_secret(
    req: CreateSecretRequest,
    session: Session = Depends(get_session)
):
    """创建 Secret

    请求体中的 value 字段为明文，服务端自动加密存储。
    响应中不返回解密值。
    """
    try:
        store = SecretStore(session)
        secret = store.create_secret(
            secret_id=req.secret_id,
            name=req.name,
            type=req.type,
            value=req.value,
            description=req.description,
            tags=req.tags,
            org_id=req.org_id,
            created_by=req.created_by,
            expires_at=req.expires_at,
        )
        return SecretResponse(**secret.to_dict(include_value=False))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create secret: {e}")


@secrets_router.get("", response_model=List[SecretResponse])
async def list_secrets(
    org_id: Optional[str] = None,
    type: Optional[str] = None,
    tags: Optional[str] = None,  # 逗号分隔的标签列表
    include_expired: bool = False,
    session: Session = Depends(get_session)
):
    """列出 Secrets（不返回解密值）

    支持过滤:
    - org_id: 组织 ID
    - type: Secret 类型
    - tags: 标签（逗号分隔，如 "production,anthropic"）
    - include_expired: 是否包含过期的 Secret
    """
    try:
        store = SecretStore(session)
        tag_list = tags.split(",") if tags else None
        secrets = store.list_secrets(
            org_id=org_id,
            type=type,
            tags=tag_list,
            include_expired=include_expired,
        )
        return [SecretResponse(**s.to_dict(include_value=False)) for s in secrets]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list secrets: {e}")


@secrets_router.get("/{secret_id}", response_model=SecretResponse)
async def get_secret(
    secret_id: str,
    session: Session = Depends(get_session)
):
    """获取 Secret（不返回解密值）

    如果需要解密值，请使用 GET /api/v1/secrets/:id/value
    """
    try:
        store = SecretStore(session)
        secret = store.get_secret(secret_id, decrypt=False, check_expiry=False)
        if not secret:
            raise HTTPException(status_code=404, detail=f"Secret not found: {secret_id}")
        return SecretResponse(**secret.to_dict(include_value=False))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get secret: {e}")


@secrets_router.get("/{secret_id}/value", response_model=SecretValueResponse)
async def get_secret_value(
    secret_id: str,
    session: Session = Depends(get_session)
):
    """获取 Secret 解密值

    ⚠️ 安全警告: 此端点返回明文值，应配合权限控制使用。
    建议仅允许 secret:read_value 权限的用户访问。
    """
    try:
        store = SecretStore(session)
        secret = store.get_secret(secret_id, decrypt=True, check_expiry=True)
        if not secret:
            raise HTTPException(status_code=404, detail=f"Secret not found: {secret_id}")
        return SecretValueResponse(secret_id=secret_id, value=secret.value)
    except ValueError as e:
        # 过期或解密失败
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get secret value: {e}")


@secrets_router.put("/{secret_id}", response_model=SecretResponse)
async def update_secret(
    secret_id: str,
    req: UpdateSecretRequest,
    session: Session = Depends(get_session)
):
    """更新 Secret

    可以更新名称、描述、标签、过期时间。
    如果提供 value 字段，则重新加密存储。
    """
    try:
        store = SecretStore(session)
        secret = store.update_secret(
            secret_id=secret_id,
            name=req.name,
            value=req.value,
            description=req.description,
            tags=req.tags,
            expires_at=req.expires_at,
            updated_by=req.updated_by,
        )
        return SecretResponse(**secret.to_dict(include_value=False))
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update secret: {e}")


@secrets_router.delete("/{secret_id}")
async def delete_secret(
    secret_id: str,
    deleted_by: str = "admin",
    session: Session = Depends(get_session)
):
    """删除 Secret

    级联删除审计日志。
    """
    try:
        store = SecretStore(session)
        success = store.delete_secret(secret_id, deleted_by=deleted_by)
        if not success:
            raise HTTPException(status_code=404, detail=f"Secret not found: {secret_id}")
        return {"success": True, "message": f"Secret deleted: {secret_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete secret: {e}")


@secrets_router.get("/{secret_id}/audit", response_model=List[AuditLogResponse])
async def get_secret_audit_logs(
    secret_id: str,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """获取 Secret 审计日志

    返回按时间倒序排列的审计日志（最多 limit 条）。
    """
    try:
        store = SecretStore(session)
        logs = store.get_audit_logs(secret_id, limit=limit)
        return [AuditLogResponse(**log.to_dict()) for log in logs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get audit logs: {e}")
