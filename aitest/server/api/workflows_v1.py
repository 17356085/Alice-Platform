"""Workflow REST API — 工作流资源管理 (P8-1)。

端点:
  POST   /api/v1/workflows              — 创建工作流
  GET    /api/v1/workflows/:id          — 获取工作流
  GET    /api/v1/workflows              — 列出工作流
  PUT    /api/v1/workflows/:id          — 更新工作流
  POST   /api/v1/workflows/:id/publish  — 发布工作流版本
  POST   /api/v1/workflows/:id/validate — 静态校验工作流
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from aitest.platform.workflow_store import get_workflow_store
from aitest.platform.workflow import WorkflowGraph, WorkflowNode, WorkflowEdge, ParallelPolicy, RetryPolicy

workflows_v1_router = APIRouter(prefix="/api/v1/workflows", tags=["Workflows V1"])


class CreateWorkflowRequest(BaseModel):
    name: str
    description: str = ""
    version: str = "1.0.0"
    graph: dict  # WorkflowGraph JSON
    org_id: str = ""
    created_by: str = ""
    status: str = "draft"


class UpdateWorkflowRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    graph: Optional[dict] = None


class PublishWorkflowRequest(BaseModel):
    version: str


@workflows_v1_router.post("")
async def create_workflow(req: CreateWorkflowRequest):
    """创建工作流"""
    try:
        graph = WorkflowGraph.from_dict(req.graph)
        store = get_workflow_store()
        workflow = store.create_workflow(
            name=req.name,
            description=req.description,
            version=req.version,
            graph=graph,
            org_id=req.org_id,
            created_by=req.created_by,
            status=req.status,
        )
        return workflow.to_dict()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@workflows_v1_router.get("/{workflow_id}")
async def get_workflow(workflow_id: str):
    """获取工作流"""
    store = get_workflow_store()
    workflow = store.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.to_dict()


@workflows_v1_router.get("")
async def list_workflows(
    org_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    """列出工作流"""
    store = get_workflow_store()
    workflows = store.list_workflows(org_id=org_id, status=status, limit=limit)
    return {
        "workflows": [w.to_dict() for w in workflows],
        "total": len(workflows),
    }


@workflows_v1_router.put("/{workflow_id}")
async def update_workflow(workflow_id: str, req: UpdateWorkflowRequest):
    """更新工作流"""
    store = get_workflow_store()

    graph = None
    if req.graph:
        try:
            graph = WorkflowGraph.from_dict(req.graph)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid graph: {e}")

    success = store.update_workflow(
        workflow_id=workflow_id,
        name=req.name,
        description=req.description,
        status=req.status,
        graph=graph,
    )

    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {"workflow_id": workflow_id, "status": "updated"}


@workflows_v1_router.post("/{workflow_id}/publish")
async def publish_workflow(workflow_id: str, req: PublishWorkflowRequest):
    """发布工作流新版本"""
    store = get_workflow_store()
    success = store.publish_workflow(workflow_id, req.version)

    if not success:
        raise HTTPException(status_code=404, detail="Workflow not found")

    return {"workflow_id": workflow_id, "version": req.version, "status": "published"}


@workflows_v1_router.post("/{workflow_id}/validate")
async def validate_workflow(workflow_id: str):
    """静态校验工作流（P8-3）"""
    store = get_workflow_store()
    workflow = store.get_workflow(workflow_id)

    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")

    if not workflow.graph:
        raise HTTPException(status_code=400, detail="Workflow has no graph")

    # 调用校验逻辑
    from aitest.server.api.workflows_v1_validate import validate_workflow_graph
    node_ids = [n.node_id for n in workflow.graph.nodes]
    errors, warnings = validate_workflow_graph(workflow.graph, node_ids)

    is_valid = len(errors) == 0

    return {
        "workflow_id": workflow_id,
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
    }
