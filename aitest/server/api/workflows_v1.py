"""Workflow REST API — 工作流资源管理 (P8-1)。

端点:
  POST   /api/v1/workflows              — 创建工作流
  GET    /api/v1/workflows/:id          — 获取工作流
  GET    /api/v1/workflows              — 列出工作流
  PUT    /api/v1/workflows/:id          — 更新工作流
  DELETE /api/v1/workflows/:id          — 删除工作流
  POST   /api/v1/workflows/:id/publish  — 发布工作流版本
  POST   /api/v1/workflows/:id/validate — 静态校验工作流
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uuid

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


class DebugWorkflowRequest(BaseModel):
    input: dict = {}
    org_id: str = "default-org"
    workspace_id: str = "debug-workspace"
    user_id: str = "debugger"
    max_steps: Optional[int] = None
    breakpoints: List[str] = []


@workflows_v1_router.post("")
async def create_workflow(req: CreateWorkflowRequest):
    """创建工作流"""
    try:
        # The web builder intentionally sends only the editable graph body.
        # Fill the domain-required identity fields at the API boundary so a
        # valid UI submission is not rejected with a KeyError.
        workflow_id = f"wf_{uuid.uuid4().hex[:16]}"
        graph_data = dict(req.graph)
        graph_data.setdefault("workflow_id", workflow_id)
        graph_data.setdefault("name", req.name)
        graph_data.setdefault("version", req.version)
        graph = WorkflowGraph.from_dict(graph_data)
        store = get_workflow_store()
        workflow = store.create_workflow(
            name=req.name,
            description=req.description,
            version=req.version,
            graph=graph,
            org_id=req.org_id,
            created_by=req.created_by,
            status=req.status,
            workflow_id=workflow_id,
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


@workflows_v1_router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str):
    """删除工作流定义。"""
    store = get_workflow_store()
    if not store.delete_workflow(workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"workflow_id": workflow_id, "status": "deleted"}


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

    if not workflow.graph or not getattr(workflow.graph, "nodes", None):
        return {
            "workflow_id": workflow_id,
            "valid": False,
            "errors": ["Workflow has no graph"],
            "warnings": [],
        }

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


@workflows_v1_router.post("/{workflow_id}/debug")
async def debug_workflow(workflow_id: str, req: DebugWorkflowRequest):
    """Execute an inspectable debug session with breakpoints/step limits."""
    workflow = get_workflow_store().get_workflow(workflow_id)
    if not workflow or not workflow.graph:
        raise HTTPException(status_code=404, detail="Workflow not found or has no graph")
    from aitest.platform.workflow_executor import WorkflowExecutor, WorkflowRuntime
    from aitest.platform.workspace import ExecutionContext
    ctx = ExecutionContext(workspace_id=req.workspace_id, org_id=req.org_id, user_id=req.user_id, scopes=["read", "execute"])
    runtime = WorkflowRuntime(
        run_id=f"debug_{workflow_id}", workflow_id=workflow_id, ctx=ctx,
        params=req.input, runtime_config={"debug": True},
    )
    result = WorkflowExecutor(workflow.graph, runtime).execute_debug(
        breakpoints=set(req.breakpoints), max_steps=req.max_steps,
    )
    return {"workflow_id": workflow_id, **result}
