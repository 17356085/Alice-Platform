"""
/api/v1/runs — 统一执行入口 (P7-2)

替代旧的 POST /api/workspaces/:ws_id/executions，支持：
- target.type/id/version 资源版本化
- environment_id 多环境
- 向后兼容旧参数（module/pages/agent）

Phase 1: 支持 target.type="agent" + 旧参数映射
Phase 2+: 支持 workflow/skill/evaluation 类型
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, Literal, Any
import asyncio

runs_router = APIRouter(prefix="/api/v1", tags=["runs"])


# ── Request Schema ──────────────────────────────────────────────────────

class RunTarget(BaseModel):
    """执行目标（Agent/Workflow/Skill/Evaluation）"""
    type: Literal["agent", "workflow", "skill", "evaluation"] = "agent"
    id: str = Field(..., description="agent_id / workflow_id / skill_id / evaluation_id")
    version: str = Field("latest", description="版本号或 'latest'")


class RunParams(BaseModel):
    """执行参数（类型依赖）"""
    # type="agent" 时（向后兼容）
    module: Optional[str] = None
    pages: Optional[list[str]] = None

    # type="workflow" 时
    input: Optional[dict[str, Any]] = None

    # type="skill" 时
    prompt: Optional[str] = None
    context: Optional[dict[str, Any]] = None

    # type="evaluation" 时
    dataset_id: Optional[str] = None
    eval_config: Optional[dict[str, Any]] = None


class RunRuntime(BaseModel):
    """运行时配置"""
    provider: Optional[str] = "claude"
    model: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    environment_id: Optional[str] = None


class RunExecution(BaseModel):
    """执行策略"""
    mode: Optional[str] = "full"
    priority: int = Field(5, ge=0, le=10)
    timeout_seconds: Optional[int] = None
    max_retries: int = 3
    async_mode: bool = Field(False, alias="async")


class RunMetadata(BaseModel):
    """元数据"""
    triggered_by: Optional[str] = "manual"
    tags: Optional[list[str]] = None
    idempotency_key: Optional[str] = None
    parent_run_id: Optional[str] = None


class CreateRunRequest(BaseModel):
    """POST /api/v1/runs 请求体"""
    target: RunTarget
    params: Optional[RunParams] = None
    runtime: Optional[RunRuntime] = None
    execution: Optional[RunExecution] = None
    metadata: Optional[RunMetadata] = None


# ── Response Schema ─────────────────────────────────────────────────────

class RunArtifact(BaseModel):
    type: str
    path: str
    url: Optional[str] = None


class RunMetrics(BaseModel):
    duration_ms: int
    tokens_used: int
    cost_usd: float


class RunError(BaseModel):
    type: str
    message: str
    details: Optional[dict[str, Any]] = None


class RunResult(BaseModel):
    status: Literal["success", "error"]
    artifacts: Optional[list[RunArtifact]] = None
    metrics: Optional[RunMetrics] = None
    error: Optional[RunError] = None


class CreateRunResponse(BaseModel):
    run_id: str
    status: Literal["pending", "running", "completed", "failed", "cancelled"]
    created_at: str
    target: RunTarget
    result: Optional[RunResult] = None


# ── Endpoints ───────────────────────────────────────────────────────────

@runs_router.post("/runs", response_model=CreateRunResponse)
async def create_run(req: CreateRunRequest, request: Request):
    """
    统一执行入口 — 创建新 Run。

    支持类型:
    - agent: 执行单个 Agent（需要 params.module/pages）
    - workflow: 执行 Workflow（需要 params.input）
    - skill: 执行单个 Skill（需要 params.prompt）
    - evaluation: 执行 Evaluation（需要 params.dataset_id）

    Phase 4: 支持所有类型（workflow/skill/evaluation 为占位实现）
    """
    # 解析 workspace_id（从 header 或默认值）
    workspace_id = request.headers.get("X-Workspace-Id", "default")
    user_id = getattr(request.state, "user_id", None) or request.headers.get("X-User-Id", "anonymous")
    org_id = getattr(request.state, "org_id", None) or request.headers.get("X-Org-Id", "")

    # 准备参数
    params = req.params or RunParams()
    runtime = req.runtime or RunRuntime()
    execution = req.execution or RunExecution()
    metadata = req.metadata or RunMetadata()

    # 构造 ExecutionContext
    from aitest.platform.workspace import ExecutionContext

    ctx = ExecutionContext(
        workspace_id=workspace_id,
        user_id=user_id,
        scopes=getattr(request.state, "scopes", ["read", "execute"]),
        org_id=org_id,
        entrypoint="api.v1.runs",
        metadata={
            "target_type": req.target.type,
            "target_id": req.target.id,
            "target_version": req.target.version,
            "environment_id": runtime.environment_id or "",
            "idempotency_key": metadata.idempotency_key or "",
            "parent_run_id": metadata.parent_run_id or "",
            "tags": metadata.tags or [],
        },
    )

    try:
        # Phase 4: 根据 target.type 分发执行
        from aitest.server.api.run_executor import RunExecutor
        import asyncio

        params_dict = params.dict() if params else {}
        runtime_dict = runtime.dict() if runtime else {}
        execution_dict = execution.dict() if execution else {}

        if req.target.type == "agent":
            result = await asyncio.to_thread(
                RunExecutor.execute_agent,
                ctx, req.target.id, req.target.version,
                params_dict, runtime_dict, execution_dict
            )
        elif req.target.type == "workflow":
            result = await RunExecutor.execute_workflow(
                ctx, req.target.id, req.target.version,
                params_dict, runtime_dict, execution_dict
            )
        elif req.target.type == "skill":
            result = await RunExecutor.execute_skill(
                ctx, req.target.id, req.target.version,
                params_dict, runtime_dict, execution_dict
            )
        elif req.target.type == "evaluation":
            result = await RunExecutor.execute_evaluation(
                ctx, req.target.id, req.target.version,
                params_dict, runtime_dict, execution_dict
            )
        else:
            raise HTTPException(400, f"Unknown target.type: {req.target.type}")

        # 转换为新格式响应
        from datetime import datetime, timezone

        return CreateRunResponse(
            run_id=result["run_id"],
            status=result["status"],
            created_at=datetime.now(timezone.utc).isoformat(),
            target=req.target,
            result=RunResult(
                status="success" if result["status"] == "completed" else "error",
                artifacts=[],
                metrics=RunMetrics(
                    duration_ms=result["metrics"]["duration_ms"],
                    tokens_used=result["metrics"]["tokens_used"],
                    cost_usd=result["metrics"]["cost_usd"],
                ),
                error=RunError(
                    type="execution_error",
                    message=result.get("error_message", ""),
                ) if result.get("error_message") else None,
            ) if not execution.async_mode else None,
        )

    except PermissionError as e:
        raise HTTPException(403, str(e))
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, str(e))

@runs_router.get("/runs/{run_id}")
async def get_run(run_id: str, request: Request):
    """查询 Run 状态（Phase 1: 委托给旧的 execution API）"""
    from aitest.platform.run_store import get_run_store

    store = get_run_store()
    run = store.get_run(run_id)

    if not run:
        raise HTTPException(404, f"Run {run_id} not found")

    # TODO: 返回新格式（当前返回旧格式）
    return run.to_dict()


# ── GET /api/v1/artifacts/:artifact_id/download ────────────────────────

@runs_router.get("/artifacts/{artifact_id}/download")
async def download_artifact(artifact_id: str):
    """下载 Artifact 文件（P3-3）
    
    artifact_id 格式: "project_id:module:page:filename"
    示例: "web-automation:user_manage:user_list:test_user_list.py"
    """
    from fastapi.responses import FileResponse
    from aitest.platform.artifacts import ArtifactStore
    
    try:
        # 解析 artifact_id
        parts = artifact_id.split(':', 3)
        if len(parts) != 4:
            raise HTTPException(
                400, 
                f"Invalid artifact_id format. Expected 'project:module:page:filename', got '{artifact_id}'"
            )
        
        project_id, module, page, filename = parts
        
        # 获取文件路径
        store = ArtifactStore(project_id)
        file_path = store.path(module, page, filename)
        
        if not file_path.exists():
            raise HTTPException(404, f"Artifact not found: {artifact_id}")
        
        # 返回文件
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/octet-stream"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, f"Failed to download artifact: {str(e)}")


# ── GET /api/v1/runs/compare ───────────────────────────────────────────

@runs_router.get("/runs/compare")
async def compare_runs(run_ids: str, request: Request):
    """对比多个 Runs（P3-2）
    
    参数:
        run_ids: 逗号分隔的 run_id 列表，例如 "run1,run2,run3"
    
    返回:
        runs: Run 详情列表
        comparison: 对比结果（tokens/cost/duration/status）
    """
    from aitest.platform.run_store import get_run_store
    
    if not run_ids:
        raise HTTPException(400, "run_ids parameter is required")
    
    ids = [rid.strip() for rid in run_ids.split(',') if rid.strip()]
    
    if len(ids) < 2:
        raise HTTPException(400, "At least 2 run_ids are required for comparison")
    
    if len(ids) > 10:
        raise HTTPException(400, "Maximum 10 runs can be compared at once")
    
    store = get_run_store()
    runs = []
    
    for run_id in ids:
        run = store.get_run(run_id)
        if run:
            runs.append(run.to_dict())
        else:
            runs.append({"run_id": run_id, "error": "not_found"})
    
    # 计算对比指标
    valid_runs = [r for r in runs if "error" not in r]
    
    comparison = {
        "total_runs": len(ids),
        "found_runs": len(valid_runs),
        "missing_runs": len(ids) - len(valid_runs),
    }
    
    if valid_runs:
        # Token 对比
        tokens = [r.get("total_tokens", 0) for r in valid_runs]
        comparison["tokens"] = {
            "values": tokens,
            "min": min(tokens) if tokens else 0,
            "max": max(tokens) if tokens else 0,
            "avg": sum(tokens) / len(tokens) if tokens else 0,
            "total": sum(tokens),
        }
        
        # Cost 对比
        costs = [r.get("total_cost", 0.0) for r in valid_runs]
        comparison["cost_usd"] = {
            "values": costs,
            "min": min(costs) if costs else 0.0,
            "max": max(costs) if costs else 0.0,
            "avg": sum(costs) / len(costs) if costs else 0.0,
            "total": sum(costs),
        }
        
        # Status 统计
        statuses = [r.get("status", "unknown") for r in valid_runs]
        status_counts = {}
        for s in statuses:
            status_counts[s] = status_counts.get(s, 0) + 1
        comparison["status_distribution"] = status_counts
        
        # Duration 对比（如果有 completed_at 和 created_at）
        durations = []
        for r in valid_runs:
            created = r.get("created_at")
            completed = r.get("completed_at")
            if created and completed:
                try:
                    from datetime import datetime
                    c = datetime.fromisoformat(created.replace('Z', '+00:00'))
                    f = datetime.fromisoformat(completed.replace('Z', '+00:00'))
                    duration_s = (f - c).total_seconds()
                    durations.append(duration_s)
                except Exception:
                    pass
        
        if durations:
            comparison["duration_seconds"] = {
                "values": durations,
                "min": min(durations),
                "max": max(durations),
                "avg": sum(durations) / len(durations),
            }
    
    return {
        "runs": runs,
        "comparison": comparison,
    }
