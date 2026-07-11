"""Billing REST API — /api/v1/billing (P3-6)

端点:
- GET /api/v1/billing/usage/:workspace_id  # 某 workspace 的用量统计
- GET /api/v1/billing/usage                # 所有 workspace 的用量（管理视图）
- GET /api/v1/billing/events               # Billing events 查询（可过滤 org/run）

设计说明:
- 不做余额、扣费、发票。只是"读出"已有数据。
- usage 数据来自 QuotaUsageConsumer（事件驱动，in-memory + JSONL 持久化）
- events 数据来自 BillingHookConsumer（billing.jsonl）
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from aitest.platform.hooks.billing_hook import get_billing_hook
from aitest.platform.hooks.quota_usage import get_quota_usage

billing_router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


# ============================================================================
# Response Models
# ============================================================================

class WorkspaceUsageResponse(BaseModel):
    """单个 workspace 的用量统计"""
    workspace_id: str
    org_id: str
    run_count: int
    token_usage: int
    cost_total: float
    storage_bytes: int
    last_updated: str  # ISO 时间戳，空字符串表示从未有过用量


class UsageListResponse(BaseModel):
    """所有 workspace 的用量列表（管理视图）"""
    workspaces: List[WorkspaceUsageResponse]
    total: int


class BillingEventResponse(BaseModel):
    """单个 billing event"""
    version: int
    event: str            # billing.usage_recorded | billing.cost_recorded
    run_id: str
    request_id: str
    org_id: str
    workspace_id: str
    timestamp: str
    # usage_recorded 特有
    usage: Optional[dict] = None
    # cost_recorded 特有
    cost: Optional[dict] = None


class BillingEventsResponse(BaseModel):
    """Billing events 查询结果"""
    events: List[BillingEventResponse]
    total: int


# ============================================================================
# API Endpoints
# ============================================================================

@billing_router.get("/usage/{workspace_id}", response_model=WorkspaceUsageResponse)
async def get_workspace_usage(workspace_id: str):
    """获取某 workspace 的用量统计

    数据来自 QuotaUsageConsumer（事件驱动，实时反映已完成的 Run）。

    注意：系统重启后内存数据会清空，持久化依赖 billing.jsonl 重放（未来扩展）。

    参数:
        workspace_id: Workspace ID
    """
    quota = get_quota_usage()
    usage = quota.get_usage(workspace_id)

    return WorkspaceUsageResponse(
        workspace_id=usage.get("workspace_id", workspace_id),
        org_id=usage.get("org_id", ""),
        run_count=usage.get("run_count", 0),
        token_usage=usage.get("token_usage", 0),
        cost_total=usage.get("cost_total", 0.0),
        storage_bytes=usage.get("storage_bytes", 0),
        last_updated=usage.get("last_updated", ""),
    )


@billing_router.get("/usage", response_model=UsageListResponse)
async def list_all_usage(
    org_id: Optional[str] = Query(None, description="按组织过滤（None = 全部）"),
    min_run_count: int = Query(0, description="最少 run_count 过滤（默认 0 = 不过滤）"),
):
    """列出所有 workspace 的用量统计（管理视图）

    参数:
        org_id: 组织 ID 过滤
        min_run_count: 最少 run 数量过滤（用于排除空 workspace）
    """
    quota = get_quota_usage()
    all_usage = quota.list_all()

    # 过滤
    if org_id:
        all_usage = [u for u in all_usage if u.get("org_id") == org_id]
    if min_run_count > 0:
        all_usage = [u for u in all_usage if u.get("run_count", 0) >= min_run_count]

    return UsageListResponse(
        workspaces=[
            WorkspaceUsageResponse(
                workspace_id=u.get("workspace_id", ""),
                org_id=u.get("org_id", ""),
                run_count=u.get("run_count", 0),
                token_usage=u.get("token_usage", 0),
                cost_total=u.get("cost_total", 0.0),
                storage_bytes=u.get("storage_bytes", 0),
                last_updated=u.get("last_updated", ""),
            )
            for u in all_usage
        ],
        total=len(all_usage),
    )


@billing_router.get("/events", response_model=BillingEventsResponse)
async def list_billing_events(
    org_id: Optional[str] = Query(None, description="按组织 ID 过滤"),
    workspace_id: Optional[str] = Query(None, description="按 workspace ID 过滤"),
    run_id: Optional[str] = Query(None, description="按 run ID 过滤"),
    event_type: Optional[str] = Query(
        None,
        description="按事件类型过滤（billing.usage_recorded | billing.cost_recorded）",
    ),
    limit: int = Query(50, ge=1, le=500, description="返回条数（最多 500）"),
):
    """查询 Billing Events

    数据来自 billing.jsonl（BillingHookConsumer 写入的持久化日志）。

    每次 Run 完成会写入一条 billing.usage_recorded；
    每次记录 cost 会写入一条 billing.cost_recorded。

    参数:
        org_id: 组织 ID 过滤
        workspace_id: Workspace 过滤
        run_id: Run ID 过滤（查询特定 Run 的账单事件）
        event_type: 事件类型过滤
        limit: 最多返回条数
    """
    hook = get_billing_hook()

    # billing_hook.query() 只支持 org_id 过滤，其他过滤在 Python 层处理
    events = hook.query(org_id=org_id or "", limit=limit * 10)  # 多取一些以备后续过滤

    # 二次过滤
    if workspace_id:
        events = [e for e in events if e.get("workspace_id") == workspace_id]
    if run_id:
        events = [e for e in events if e.get("run_id") == run_id]
    if event_type:
        events = [e for e in events if e.get("event") == event_type]

    # 限制条数
    events = events[:limit]

    return BillingEventsResponse(
        events=[
            BillingEventResponse(
                version=e.get("version", 1),
                event=e.get("event", ""),
                run_id=e.get("run_id", ""),
                request_id=e.get("request_id", ""),
                org_id=e.get("org_id", ""),
                workspace_id=e.get("workspace_id", ""),
                timestamp=e.get("timestamp", ""),
                usage=e.get("usage"),
                cost=e.get("cost"),
            )
            for e in events
        ],
        total=len(events),
    )
