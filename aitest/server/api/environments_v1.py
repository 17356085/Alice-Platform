"""Environment REST API — /api/v1/environments (P6-4)

端点:
- POST   /api/v1/environments              # 创建 Environment
- GET    /api/v1/environments              # 列出 Environments
- GET    /api/v1/environments/:id          # 获取 Environment
- PUT    /api/v1/environments/:id          # 更新 Environment
- DELETE /api/v1/environments/:id          # 删除 Environment
- POST   /api/v1/environments/:id/default  # 设置为默认
- GET    /api/v1/environments/:id/resolved # 获取解析后的变量
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from sqlalchemy.orm import Session

from aitest.infra.db import get_session
from aitest.platform.environment_store import EnvironmentStore

environments_router = APIRouter(prefix="/api/v1/environments", tags=["environments"])


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateEnvironmentRequest(BaseModel):
    """创建 Environment 请求"""
    environment_id: str = Field(..., description="Environment ID（唯一标识）")
    name: str = Field(..., description="显示名称")
    base_url: str = Field(..., description="测试环境 URL")
    description: str = Field(default="", description="描述信息")
    variables: Dict[str, str] = Field(default_factory=dict, description="环境变量（可包含 secret_ref）")
    tags: List[str] = Field(default_factory=list, description="标签列表")
    org_id: str = Field(default="default-org", description="组织 ID")
    created_by: str = Field(default="admin", description="创建者")
    is_default: bool = Field(default=False, description="是否设为默认环境")


class UpdateEnvironmentRequest(BaseModel):
    """更新 Environment 请求"""
    name: Optional[str] = Field(default=None, description="新名称")
    base_url: Optional[str] = Field(default=None, description="新 base_url")
    description: Optional[str] = Field(default=None, description="新描述")
    variables: Optional[Dict[str, str]] = Field(default=None, description="新变量")
    tags: Optional[List[str]] = Field(default=None, description="新标签列表")
    is_default: Optional[bool] = Field(default=None, description="是否设为默认")


class EnvironmentResponse(BaseModel):
    """Environment 响应"""
    environment_id: str
    name: str
    base_url: str
    description: str
    variables: Dict[str, str]
    tags: List[str]
    org_id: str
    created_by: str
    created_at: str
    updated_at: str
    is_default: bool


class ResolvedVariablesResponse(BaseModel):
    """解析后的变量响应"""
    environment_id: str
    variables: Dict[str, str]


# ============================================================================
# API Endpoints
# ============================================================================

@environments_router.post("", response_model=EnvironmentResponse)
async def create_environment(
    req: CreateEnvironmentRequest,
    session: Session = Depends(get_session)
):
    """创建 Environment

    variables 中可以使用 secret_ref（如 "secret:db-password"）。
    """
    try:
        store = EnvironmentStore(session)
        env = store.create_environment(
            environment_id=req.environment_id,
            name=req.name,
            base_url=req.base_url,
            description=req.description,
            variables=req.variables,
            tags=req.tags,
            org_id=req.org_id,
            created_by=req.created_by,
            is_default=req.is_default,
        )
        return EnvironmentResponse(**env.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create environment: {e}")


@environments_router.get("", response_model=List[EnvironmentResponse])
async def list_environments(
    org_id: Optional[str] = None,
    tags: Optional[str] = None,  # 逗号分隔的标签列表
    session: Session = Depends(get_session)
):
    """列出 Environments

    支持过滤:
    - org_id: 组织 ID
    - tags: 标签（逗号分隔，如 "staging,qa"）
    """
    try:
        store = EnvironmentStore(session)
        tag_list = tags.split(",") if tags else None
        environments = store.list_environments(
            org_id=org_id,
            tags=tag_list,
        )
        return [EnvironmentResponse(**env.to_dict()) for env in environments]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list environments: {e}")


@environments_router.get("/{environment_id}", response_model=EnvironmentResponse)
async def get_environment(
    environment_id: str,
    session: Session = Depends(get_session)
):
    """获取 Environment

    返回 Environment 配置（variables 不解密 secret_ref）。
    如果需要解密后的变量，请使用 GET /api/v1/environments/:id/resolved
    """
    try:
        store = EnvironmentStore(session)
        env = store.get_environment(environment_id)
        if not env:
            raise HTTPException(status_code=404, detail=f"Environment not found: {environment_id}")
        return EnvironmentResponse(**env.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get environment: {e}")


@environments_router.get("/{environment_id}/resolved", response_model=ResolvedVariablesResponse)
async def get_resolved_variables(
    environment_id: str,
    session: Session = Depends(get_session)
):
    """获取解析后的变量

    ⚠️ 安全警告: 此端点返回解密后的变量（包含 Secret 明文值）。
    建议配合权限控制使用。
    """
    try:
        store = EnvironmentStore(session)
        resolved = store.resolve_variables(environment_id)
        return ResolvedVariablesResponse(
            environment_id=environment_id,
            variables=resolved
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve variables: {e}")


@environments_router.put("/{environment_id}", response_model=EnvironmentResponse)
async def update_environment(
    environment_id: str,
    req: UpdateEnvironmentRequest,
    session: Session = Depends(get_session)
):
    """更新 Environment

    可以更新名称、base_url、描述、变量、标签、默认状态。
    """
    try:
        store = EnvironmentStore(session)
        env = store.update_environment(
            environment_id=environment_id,
            name=req.name,
            base_url=req.base_url,
            description=req.description,
            variables=req.variables,
            tags=req.tags,
            is_default=req.is_default,
        )
        return EnvironmentResponse(**env.to_dict())
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update environment: {e}")


@environments_router.delete("/{environment_id}")
async def delete_environment(
    environment_id: str,
    session: Session = Depends(get_session)
):
    """删除 Environment"""
    try:
        store = EnvironmentStore(session)
        success = store.delete_environment(environment_id)
        if not success:
            raise HTTPException(status_code=404, detail=f"Environment not found: {environment_id}")
        return {"success": True, "message": f"Environment deleted: {environment_id}"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete environment: {e}")


@environments_router.post("/{environment_id}/default")
async def set_default_environment(
    environment_id: str,
    org_id: str = "default-org",
    session: Session = Depends(get_session)
):
    """设置为默认 Environment

    将指定 Environment 设为默认，同时取消其他默认 Environment。
    """
    try:
        store = EnvironmentStore(session)
        store.set_default_environment(environment_id, org_id=org_id)
        return {"success": True, "message": f"Default environment set: {environment_id}"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to set default environment: {e}")
