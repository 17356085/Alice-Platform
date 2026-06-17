"""Webhook 端点 — Jenkins/GitLab CI 集成（异步任务队列版）。

端点:
  POST /api/webhook/jenkins  — Jenkins Pipeline 完成时自动入队对应 Agent
  GET  /api/webhook/health   — Webhook 健康检查
"""
from fastapi import APIRouter, Request

webhooks_router = APIRouter(prefix="/api/webhook", tags=["Webhooks"])


@webhooks_router.post("/jenkins")
async def jenkins_webhook(request: Request):
    """
    Jenkins CI 完成后回调。自动入队异步任务。

    预期 Payload:
      {
        "build_status": "SUCCESS" | "FAILURE" | "UNSTABLE",
        "module": "equipment",
        "build_url": "https://jenkins.company.com/job/ZJSN_Test/123/",
        "build_id": 123
      }

    行为:
      - FAILURE  → 自动入队 bug-analysis-agent 任务
      - SUCCESS  → 自动入队 report-agent 任务（生成测试总结）
      - UNSTABLE → 入队 bug-analysis-agent（存在不稳定用例）
    """
    from aitest.infra.task_queue import get_queue

    payload = await request.json()
    build_status = payload.get("build_status", "UNKNOWN")
    module = payload.get("module", "")
    build_id = payload.get("build_id", "N/A")

    queue = get_queue()

    if build_status == "FAILURE" or build_status == "UNSTABLE":
        task_id = queue.enqueue(
            agent="bug-analysis-agent",
            module=module,
            provider="claude",
        )
        return {
            "action": "trigger_bug_analysis",
            "module": module,
            "task_id": task_id,
            "poll_url": f"/api/agent/task/{task_id}",
            "build_id": build_id,
        }

    elif build_status == "SUCCESS":
        task_id = queue.enqueue(
            agent="report-agent",
            module=module,
            provider="claude",
        )
        return {
            "action": "trigger_report",
            "module": module,
            "task_id": task_id,
            "poll_url": f"/api/agent/task/{task_id}",
            "build_id": build_id,
        }

    else:
        return {
            "action": "no_action",
            "build_status": build_status,
            "build_id": build_id,
            "note": f"未知的构建状态 '{build_status}'。仅处理 SUCCESS / FAILURE / UNSTABLE。",
        }


@webhooks_router.get("/health")
async def webhook_health():
    """Webhook 端点健康检查。"""
    from aitest.infra.task_queue import get_queue
    queue = get_queue()
    counts = queue.count_by_status()
    return {
        "status": "ok",
        "queue_size": sum(counts.values()),
        "queue_stats": counts,
    }
