"""Worker Lease REST API — /api/v1/workers (P3-5)

端点:
- GET  /api/v1/workers         # 列出所有 Worker（可按状态过滤）
- GET  /api/v1/workers/:id     # 获取单个 Worker 详情
- POST /api/v1/workers/:id/drain  # 优雅停止（draining）
- POST /api/v1/workers/cleanup    # 清理僵尸 Worker（标记为 dead）
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Header
from pydantic import BaseModel, Field
from typing import Optional, List
from sqlalchemy.orm import Session

from aitest.infra import db
from aitest.platform.worker_lease_store import WorkerLeaseStore
from aitest.platform.worker_auth import WorkerAuthError, validate_request_token
from aitest.platform.worker_scheduler import WorkerScheduler

workers_router = APIRouter(prefix="/api/v1/workers", tags=["workers"])


# ============================================================================
# Response Models
# ============================================================================

class WorkerResponse(BaseModel):
    """Worker 响应"""
    worker_id: str
    hostname: str
    pid: int
    status: str  # running | draining | stopped | dead
    started_at: str
    last_heartbeat_at: str
    heartbeat_interval_seconds: int
    claimed_requests: List[str]
    stats: dict
    metadata: dict
    org_id: str


class WorkerListResponse(BaseModel):
    """Worker 列表响应"""
    workers: List[WorkerResponse]
    total: int


class DrainResponse(BaseModel):
    """Drain 操作响应"""
    success: bool
    message: str


class CleanupResponse(BaseModel):
    """Cleanup 操作响应"""
    dead_workers: List[str]
    total: int


class RegisterWorkerRequest(BaseModel):
    worker_id: str = Field(..., min_length=1)
    hostname: str = ""
    pid: int = 0
    heartbeat_interval_seconds: int = Field(default=30, ge=1, le=3600)
    metadata: dict = Field(default_factory=dict)
    org_id: str = "default-org"


class HeartbeatRequest(BaseModel):
    stats: dict = Field(default_factory=dict)
    claimed_requests: List[str] = Field(default_factory=list)
    org_id: str = "default-org"


class WorkerTaskResponse(BaseModel):
    task: Optional[dict] = None


class DispatchResponse(BaseModel):
    worker_id: Optional[str] = None
    org_id: str
    task: Optional[dict] = None


class TaskCompleteRequest(BaseModel):
    org_id: str = "default-org"
    result: dict = Field(default_factory=dict)


class TaskFailureRequest(BaseModel):
    org_id: str = "default-org"
    error: str = Field(..., min_length=1, max_length=4000)


def _authorize(worker_id: str, org_id: str, authorization: Optional[str]) -> None:
    token = authorization.split(" ", 1)[1] if authorization and authorization.lower().startswith("bearer ") else None
    try:
        validate_request_token(token, worker_id, org_id)
    except WorkerAuthError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc


# ============================================================================
# API Endpoints
# ============================================================================

@workers_router.post("/register", response_model=WorkerResponse)
async def register_worker(
    req: RegisterWorkerRequest,
    authorization: Optional[str] = Header(None),
    session: Session = Depends(db.get_session),
):
    """Register a local or remote worker and return its lease."""
    try:
        _authorize(req.worker_id, req.org_id, authorization)
        lease = WorkerLeaseStore(session).register(
            req.worker_id,
            hostname=req.hostname,
            pid=req.pid,
            heartbeat_interval_seconds=req.heartbeat_interval_seconds,
            metadata=req.metadata,
            org_id=req.org_id,
        )
        return WorkerResponse(**lease.to_dict())
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@workers_router.post("/{worker_id}/heartbeat")
async def heartbeat_worker(
    worker_id: str,
    req: HeartbeatRequest,
    authorization: Optional[str] = Header(None),
    session: Session = Depends(db.get_session),
):
    """Accept a remote worker heartbeat scoped to its organization."""
    _authorize(worker_id, req.org_id, authorization)
    ok = WorkerLeaseStore(session).heartbeat(
        worker_id,
        stats=req.stats,
        claimed_requests=req.claimed_requests,
        org_id=req.org_id,
    )
    if not ok:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")
    return {"success": True, "worker_id": worker_id}

@workers_router.get("", response_model=WorkerListResponse)
async def list_workers(
    status: Optional[str] = Query(None, description="按状态过滤（running/draining/stopped/dead/alive）"),
    org_id: Optional[str] = Query(None, description="按组织过滤"),
    session: Session = Depends(db.get_session)
):
    """列出所有 Worker

    参数:
        status: 过滤条件
            - running: 仅运行中的 Worker
            - draining: 仅正在排空的 Worker
            - stopped: 仅已停止的 Worker
            - dead: 仅僵尸 Worker
            - alive: 仅存活的 Worker（心跳正常）
            - None: 所有 Worker
        org_id: 组织 ID 过滤（None = 所有）
    """
    store = WorkerLeaseStore(session)

    if status == "alive":
        workers = store.list_alive()
    else:
        workers = store.list_all(org_id=org_id)
        if status:
            workers = [w for w in workers if w.status == status]

    return WorkerListResponse(
        workers=[WorkerResponse(**w.to_dict()) for w in workers],
        total=len(workers)
    )


@workers_router.get("/{worker_id}", response_model=WorkerResponse)
async def get_worker(
    worker_id: str,
    org_id: str = Query("default-org", description="组织 ID"),
    authorization: Optional[str] = Header(None),
    session: Session = Depends(db.get_session)
):
    """获取单个 Worker 详情

    参数:
        worker_id: Worker ID
    """
    _authorize(worker_id, org_id, authorization)
    store = WorkerLeaseStore(session)
    worker = store.get(worker_id, org_id=org_id)

    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")

    return WorkerResponse(**worker.to_dict())


@workers_router.post("/{worker_id}/drain", response_model=DrainResponse)
async def drain_worker(
    worker_id: str,
    org_id: str = Query("default-org", description="组织 ID"),
    authorization: Optional[str] = Header(None),
    session: Session = Depends(db.get_session)
):
    """将 Worker 设置为 draining 状态（优雅停止）

    Worker 设置为 draining 后：
    - 不再 claim 新任务
    - 完成当前任务后自动停止
    - 运维人员可用于滚动更新、维护等场景

    参数:
        worker_id: Worker ID
    """
    _authorize(worker_id, org_id, authorization)
    store = WorkerLeaseStore(session)

    # 先检查 Worker 是否存在
    worker = store.get(worker_id, org_id=org_id)
    if not worker:
        raise HTTPException(status_code=404, detail=f"Worker not found: {worker_id}")

    # 执行 drain
    success = store.drain(worker_id, org_id=org_id)

    if not success:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot drain worker in status: {worker.status}"
        )

    return DrainResponse(
        success=True,
        message=f"Worker {worker_id} set to draining"
    )


@workers_router.post("/{worker_id}/claim", response_model=WorkerTaskResponse)
async def claim_worker_task(
    worker_id: str,
    org_id: str = Query("default-org", description="组织 ID"),
    authorization: Optional[str] = Header(None),
):
    """Atomically claim one queued task for an authenticated Worker."""
    _authorize(worker_id, org_id, authorization)
    from aitest.infra.task_queue import get_queue
    return WorkerTaskResponse(task=get_queue().claim_for_worker(worker_id, org_id=org_id))


@workers_router.post("/dispatch", response_model=DispatchResponse)
async def dispatch_worker_task(
    org_id: str = Query("default-org", description="组织 ID"),
    capability: Optional[str] = Query(None, description="Worker capability"),
    session: Session = Depends(db.get_session),
):
    """Central scheduler dispatch: select a healthy Worker and atomically claim."""
    from aitest.infra.task_queue import get_queue
    result = WorkerScheduler(WorkerLeaseStore(session), get_queue()).dispatch_once(org_id, capability)
    if result is None:
        return DispatchResponse(org_id=org_id)
    return DispatchResponse(**result)


@workers_router.post("/{worker_id}/tasks/{task_id}/complete")
async def complete_worker_task(
    worker_id: str,
    task_id: str,
    req: TaskCompleteRequest,
    authorization: Optional[str] = Header(None),
):
    _authorize(worker_id, req.org_id, authorization)
    from aitest.infra.task_queue import get_queue
    if not get_queue().complete_for_worker(task_id, worker_id, req.result):
        raise HTTPException(status_code=409, detail="Task is not owned by this Worker")
    return {"success": True, "task_id": task_id, "status": "completed"}


@workers_router.post("/{worker_id}/tasks/{task_id}/fail")
async def fail_worker_task(
    worker_id: str,
    task_id: str,
    req: TaskFailureRequest,
    authorization: Optional[str] = Header(None),
):
    _authorize(worker_id, req.org_id, authorization)
    from aitest.infra.task_queue import get_queue
    if not get_queue().fail_for_worker(task_id, worker_id, req.error):
        raise HTTPException(status_code=409, detail="Task is not owned by this Worker")
    return {"success": True, "task_id": task_id, "status": "failed_or_requeued"}


@workers_router.post("/cleanup", response_model=CleanupResponse)
async def cleanup_dead_workers(
    timeout_seconds: int = Query(90, description="心跳超时阈值（秒）"),
    session: Session = Depends(db.get_session)
):
    """清理僵尸 Worker（标记为 dead）

    扫描所有 running/draining Worker，将心跳超时的 Worker 标记为 dead。
    通常由定时任务调用（如每分钟一次）。

    参数:
        timeout_seconds: 心跳超时阈值（默认 90 秒 = 3 倍默认心跳间隔）
    """
    store = WorkerLeaseStore(session)
    # Task queue recovery is optional; WorkerScheduler handles an unavailable
    # queue while still marking leases dead.
    dead_ids = WorkerScheduler(store).recover_dead_workers(timeout_seconds=timeout_seconds)

    return CleanupResponse(
        dead_workers=dead_ids,
        total=len(dead_ids)
    )
