"""
Webhook Server — 接收 CI 事件并自动触发 AI 测试工作流

端点:
  POST /webhook/jenkins     Jenkins 构建完成回调
  POST /webhook/github      GitHub PR/Commit (预留)
  GET  /health              健康检查

触发动作:
  - CI 失败 → 自动触发 Bug Analysis Agent + RAG 已知问题匹配
  - CI 成功 → 触发 Report Agent + Knowledge Agent 沉淀

启动:
  python -m aitest.infra.webhook_server --port=8099
"""
import os
import sys
import json
import time
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import uvicorn

WORKSTUDY = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSTUDY))

app = FastAPI(title="AI Test Platform Webhook", version="0.1.0")


@app.get("/health")
async def health():
    return {"status": "ok", "timestamp": time.time()}


@app.post("/webhook/jenkins")
async def jenkins_webhook(request: Request):
    """
    接收 Jenkins 构建通知。

    预期 payload:
    {
        "build_id": "123",
        "job_name": "ZJSN_Test",
        "status": "FAILURE" | "SUCCESS",
        "module": "equipment",
        "allure_dir": "/path/to/allure-results",
        "failed_count": 8,
        "total_count": 50,
        "build_url": "https://jenkins.../job/ZJSN_Test/123/"
    }
    """
    try:
        data = await request.json()
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("webhook_server", "parse_json", e)
        data = {}

    build_id = data.get("build_id", "unknown")
    job_name = data.get("job_name", "ZJSN_Test")
    status = data.get("status", "UNKNOWN")
    module = data.get("module", "")
    failed_count = data.get("failed_count", 0)
    total_count = data.get("total_count", 0)
    allure_dir = data.get("allure_dir", "")
    build_url = data.get("build_url", "")

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "build_id": build_id,
        "job_name": job_name,
        "status": status,
        "module": module,
        "failed_count": failed_count,
        "total_count": total_count,
    }

    # ── 路由到对应动作 ──
    actions = []

    if status in ("FAILURE", "UNSTABLE"):
        # CI 失败 → Bug Analysis Agent + RAG 匹配
        actions.append({
            "action": "trigger_bug_analysis",
            "agent": "bug-analysis-agent",
            "priority": "P0" if status == "FAILURE" else "P1",
            "rag_query": f"CI build {build_id} failed: {failed_count}/{total_count} failures in {module}",
        })

        # 如果有 Allure 结果，尝试自动分析
        if allure_dir:
            actions.append({
                "action": "analyze_allure",
                "tool": "allure-report-analyzer",
                "allure_dir": allure_dir,
            })

        # 发射 Event Bus 事件
        from aitest.governance.event_bus import emit
        emit("BugClosed", **{
            "bug_id": f"CI-{build_id}",
            "module": module,
            "root_cause": f"CI build {build_id} failed — {failed_count}/{total_count} failures",
            "known_issue_id": "TBD-RAG",
        })

    elif status == "SUCCESS":
        # CI 成功 → Report Agent + Knowledge Agent
        actions.append({
            "action": "trigger_report",
            "agent": "report-agent",
            "mode": "test-summary",
        })
        actions.append({
            "action": "trigger_knowledge",
            "agent": "knowledge-agent",
            "mode": "precipitate",
        })

        from aitest.governance.event_bus import emit
        emit("CycleEnd", **{
            "module": module,
            "stats": f"build #{build_id}: {total_count} tests passed"
        })

    # ── RAG 已知问题自动匹配 ──
    rag_matches = []
    if failed_count > 0:
        try:
            from aitest.knowledge.rag_engine import search_known_issues
            query = f"CI build failure {module} {failed_count} tests"
            rag_results = search_known_issues(query, n_results=3)
            rag_matches = [
                {"id": r["id"], "title": r["metadata"].get("title", ""), "distance": r.get("distance")}
                for r in rag_results
            ]
        except Exception as e:
            from aitest.infra.error_logger import log_error
            log_error("webhook_server.jenkins", "rag_enrich", e)

    response = {
        "received": True,
        "build_id": build_id,
        "status": status,
        "actions": actions,
        "rag_matches": rag_matches,
        "note": "Bug Analysis Agent will auto-trigger if failures detected",
    }

    # 写入 CI 日志
    log_dir = WORKSTUDY / "governance" / ".ci_logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"build-{build_id}-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_file, "w", encoding="utf-8") as f:
        json.dump({**log_entry, "actions": actions, "rag_matches": rag_matches}, f,
                  ensure_ascii=False, indent=2)

    return JSONResponse(response)


@app.post("/webhook/github")
async def github_webhook(request: Request):
    """GitHub Webhook — 代码推送时触发代码质量检查。"""
    try:
        data = await request.json()
    except Exception as e:
        from aitest.infra.error_logger import log_error
        log_error("webhook_server", "parse_json", e)
        data = {}

    # 检测是否测试代码变更
    head_commit = data.get("head_commit", {})
    modified = head_commit.get("modified", []) + data.get("commits", [{}])[0].get("modified", [])

    test_files = [f for f in modified if "page/" in f or "script/" in f or f.startswith("test_")]

    if test_files:
        return JSONResponse({
            "action": "trigger_code_check",
            "files": test_files,
            "suggestion": "Run aitest check --staged",
        })

    return JSONResponse({"action": "no_test_changes"})


@app.get("/webhook/status")
async def webhook_status():
    """查看 webhook 触发历史。"""
    log_dir = WORKSTUDY / "governance" / ".ci_logs"
    if not log_dir.exists():
        return {"logs": []}

    logs = []
    for f in sorted(log_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:20]:
        with open(f, "r") as fh:
            logs.append(json.load(fh))
    return {"logs": logs, "total": len(logs)}


# ── Entry ─────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8099)
    parser.add_argument("--host", default="0.0.0.0")
    args = parser.parse_args()

    print(f"AI Test Platform Webhook starting on {args.host}:{args.port}")
    print(f"Endpoints:")
    print(f"  POST /webhook/jenkins   — Jenkins CI callback")
    print(f"  POST /webhook/github    — GitHub push callback")
    print(f"  GET  /webhook/status    — Recent webhook history")
    print(f"  GET  /health            — Health check")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
