"""Agent 触发 API（异步任务队列版）。

端点:
  POST /api/agent/run              — 入队 Agent 任务，立即返回 task_id
  GET  /api/agent/task/{task_id}   — 查询任务状态和结果
  GET  /api/agent/queue            — 任务队列统计
  GET  /api/agent/status/{module}  — 查询模块 SOP 进度
  GET  /api/agent/list             — 列出所有可用 Agent
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

agents_router = APIRouter(prefix="/api/agent", tags=["Agents"])


class AgentRunRequest(BaseModel):
    agent: str                     # test-design-agent | automation-agent | bug-analysis-agent | report-agent
    module: str                    # 模块名
    page: Optional[str] = None     # 页面名（页面级 Agent 必填）
    provider: str = "claude"       # claude | openai | ollama
    mode: str = "full"             # full | resume | status


@agents_router.post("/run")
async def trigger_agent_async(req: AgentRunRequest):
    """触发 Agent 执行（异步）。任务入队后立即返回 task_id，后台消费线程执行。"""
    from aitest.task_queue import get_queue

    queue = get_queue()
    task_id = queue.enqueue(
        agent=req.agent,
        module=req.module,
        page=req.page or "",
        provider=req.provider,
    )

    return {
        "status": "queued",
        "task_id": task_id,
        "agent": req.agent,
        "module": req.module,
        "page": req.page or "N/A",
        "provider": req.provider,
        "poll_url": f"/api/agent/task/{task_id}",
    }


@agents_router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """查询异步任务的状态和结果。

    返回状态:
      - queued: 等待执行
      - running: 正在执行
      - completed: 执行完成，result 中包含产出
      - failed: 执行失败，error_msg 中包含错误信息
    """
    from aitest.task_queue import get_queue

    queue = get_queue()
    task = queue.get(task_id)

    if not task:
        return {"status": "not_found", "task_id": task_id, "message": "任务不存在或已过期"}

    response = {
        "task_id": task["id"],
        "status": task["status"],
        "agent": task["agent"],
        "module": task["module"],
        "page": task["page"],
        "provider": task["provider"],
        "created_at": task["created_at"],
    }

    if task["status"] == "completed":
        response["result"] = task.get("result", {})
        response["completed_at"] = task["completed_at"]
    elif task["status"] == "failed":
        response["error"] = task["error_msg"]
        response["completed_at"] = task["completed_at"]
    elif task["status"] == "running":
        response["started_at"] = task["started_at"]

    return response


@agents_router.get("/queue")
async def get_queue_stats():
    """查询任务队列统计信息。"""
    from aitest.task_queue import get_queue

    queue = get_queue()
    counts = queue.count_by_status()

    recent = queue.list_tasks(limit=10)

    return {
        "stats": counts,
        "recent_tasks": [
            {
                "task_id": t["id"],
                "agent": t["agent"],
                "module": t["module"],
                "status": t["status"],
                "created_at": t["created_at"],
            }
            for t in recent
        ],
    }


@agents_router.get("/status/{module}")
async def module_sop_status(module: str):
    """查询模块 SOP 进度（调用 agent_scheduler）。"""
    try:
        from aitest.agent_scheduler import check_preconditions
        return check_preconditions(module)
    except Exception as e:
        return {"status": "error", "module": module, "message": str(e)}


@agents_router.get("/status/all")
async def all_modules_status():
    """返回所有已知模块及其页面列表（供侧边栏树使用）。"""
    from pathlib import Path

    governance = Path(__file__).resolve().parent.parent.parent.parent / "governance"
    modules_dir = governance / "context" / "projects" / "web-automation" / "modules"

    result = {}
    if modules_dir.exists():
        for mod_dir in sorted(modules_dir.iterdir()):
            if mod_dir.is_dir() and not mod_dir.name.startswith("."):
                pages = []
                pages_dir = mod_dir / "pages"
                if pages_dir.exists():
                    pages = sorted([
                        d.name for d in pages_dir.iterdir()
                        if d.is_dir() and not d.name.startswith(".")
                    ])
                result[mod_dir.name] = pages

    if not result:
        # Fallback: hardcoded known modules
        result = {
            "equipment": ["alarm-config", "unit-management"],
            "tank": ["alarm-config", "monitor"],
            "production": ["workflow"],
        }

    return {"modules": result}


@agents_router.get("/list")
async def list_available_agents():
    """列出所有可用 Agent 及其 Skill 绑定。"""
    from aitest.agent_runner import AGENT_SKILL_MAP
    return {
        "agents": {
            agent: skills
            for agent, skills in AGENT_SKILL_MAP.items()
            if agent.endswith("-agent") and not agent.startswith(("project", "requirement"))
        }
    }
