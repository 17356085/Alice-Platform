"""Bug History REST API — Bug 历史库查询与管理。

端点:
  GET  /api/bugs/list       — 列出 Bug 记录（支持筛选）
  POST /api/bugs/add        — 新增 Bug 记录
  GET  /api/bugs/trends     — Bug 趋势统计
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

bugs_router = APIRouter(prefix="/api/v1/bugs", tags=["Bugs"])


class BugAddRequest(BaseModel):
    module: str
    page: str = ""
    error_type: str = ""
    root_cause: str = ""
    severity: str = "medium"       # high | medium | low
    status: str = "open"           # open | fixed | wont_fix
    matched_issue: str = ""        # 关联的 known-issue ID


class BugUpdateRequest(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    fix_description: Optional[str] = None
    fix_files: Optional[str] = None


@bugs_router.get("/list")
async def list_bugs(
    module: str = "",
    severity: str = "",
    status: str = "",
    limit: int = 20,
):
    """列出 Bug 记录（支持按模块/严重度/状态筛选）。"""
    try:
        from aitest.testing.bug_history import list_bugs as _list
        bugs = _list(
            module=module or None,
            severity=severity or None,
            status=status or None,
            limit=limit,
        )
        return {"bugs": bugs, "total": len(bugs), "filters": {
            "module": module, "severity": severity, "status": status
        }}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@bugs_router.post("/add")
async def add_bug(req: BugAddRequest):
    """新增一条 Bug 记录。"""
    try:
        from aitest.testing.bug_history import add_bug
        bug_id = add_bug(
            module=req.module,
            page=req.page,
            error_type=req.error_type,
            root_cause=req.root_cause,
            severity=req.severity,
            status=req.status,
            matched_issue=req.matched_issue,
        )
        return {"status": "added", "bug_id": bug_id}
    except Exception as e:
        return {"status": "error", "message": str(e)}


@bugs_router.patch("/{bug_id}")
async def update_bug_record(bug_id: str, req: BugUpdateRequest):
    """Update a bug lifecycle field for Gap Discovery actions."""
    try:
        from aitest.testing.bug_history import update_bug

        values = {key: value for key, value in req.model_dump().items() if value is not None}
        updated = update_bug(bug_id, **values)
        return {"status": "updated" if updated else "not_found", "bug_id": bug_id}
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


@bugs_router.get("/trends")
async def bug_trends(module: str = ""):
    """Bug 趋势统计。"""
    try:
        from aitest.testing.bug_history import get_trends
        trends = get_trends(module or None)
        return {"module": module or "all", "trends": trends}
    except Exception as e:
        return {"status": "error", "message": str(e)}
