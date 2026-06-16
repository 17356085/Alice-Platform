"""Workflow REST API — 工作流触发与状态查询。

端点:
  POST /api/workflow/run              — 触发工作流执行
  GET  /api/workflow/status/{run_id}  — 查询工作流进度
  GET  /api/workflow/list             — 列出可用工作流定义
  GET  /api/workflow/runs             — 列出最近的运行记录
"""
import json
import time
from pathlib import Path
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

workflows_router = APIRouter(prefix="/api/workflow", tags=["Workflows"])

WORKSTUDY = Path(__file__).resolve().parent.parent.parent.parent
WORKFLOW_DIR = WORKSTUDY / "governance" / "workflows"


class WorkflowRunRequest(BaseModel):
    workflow_id: str            # module-onboarding | automation-implementation | ...
    module: str                 # 模块名
    params: dict = {}           # 额外参数（如 pages, mode, provider）
    engine: str = "langgraph"   # langgraph (新) | legacy (旧 workflow_engine)


@workflows_router.post("/run")
async def trigger_workflow(req: WorkflowRunRequest):
    """触发工作流执行。支持 engine=langgraph（新）或 engine=legacy（旧）。"""
    module = req.module
    mode = req.params.get("mode", "full")
    pages_str = req.params.get("pages", "")
    pages = [p.strip() for p in pages_str.split(",") if p.strip()] if pages_str else []
    provider = req.params.get("provider", "claude")

    if req.engine == "langgraph":
        # ── LangGraph 引擎 ──
        try:
            from aitest.graphs.state import create_initial_state
            from aitest.graphs.checkpoint import get_checkpointer
            from aitest.graphs.sop_graph import build_sop_graph

            initial_state = create_initial_state(
                module=module, pages=pages, mode=mode, provider=provider
            )
            checkpointer = get_checkpointer()
            graph = build_sop_graph()
            compiled = graph.compile(checkpointer=checkpointer)
            thread = {"configurable": {"thread_id": initial_state["run_id"]}}

            events = []
            from langgraph.types import Command

            state_stream = initial_state
            for event in compiled.stream(state_stream, thread, stream_mode="updates"):
                if "__interrupt__" in event:
                    state_stream = Command(resume="approve")
                    continue
                for node_name, update in event.items():
                    if isinstance(update, dict):
                        events.append({
                            "node": node_name,
                            "phase": update.get("current_phase", ""),
                            "completed": update.get("completed_phases", []),
                        })

            final = compiled.get_state(thread)
            return {
                "status": final.values.get("status", "completed") if final and final.values else "completed",
                "run_id": initial_state["run_id"],
                "engine": "langgraph",
                "module": module,
                "mode": mode,
                "events_count": len(events),
                "completed_phases": final.values.get("completed_phases", []) if final and final.values else [],
                "poll_url": f"/api/workflow/graph-status/{initial_state['run_id']}",
            }
        except Exception as e:
            import traceback
            return {"status": "error", "engine": "langgraph", "message": str(e),
                    "traceback": traceback.format_exc()[-500:]}
    else:
        # ── 旧版 workflow_engine ──
        wf_path = WORKFLOW_DIR / f"{req.workflow_id}.yaml"
        if not wf_path.exists():
            available = [p.stem for p in sorted(WORKFLOW_DIR.glob("*.yaml"))]
            return {
                "status": "error",
                "message": f"Workflow not found: {req.workflow_id}",
                "available": available,
            }

    try:
        from aitest.workflow_engine import WorkflowDef, WorkflowRunner

        wf = WorkflowDef.from_yaml(wf_path)
        params = {"module": req.module, **req.params}
        runner = WorkflowRunner(wf, params)
        state = runner.start()

        # 收集步骤信息
        steps = []
        for step in wf.steps:
            steps.append({
                "id": step.id,
                "name": step.name,
                "agent": step.agent,
                "skill": step.skill,
                "phase": step.phase,
                "depends_on": step.depends_on,
                "auto_trigger": step.auto_trigger,
            })

        return {
            "status": "started",
            "run_id": state.run_id,
            "workflow": req.workflow_id,
            "module": req.module,
            "total_steps": len(steps),
            "steps": steps,
            "poll_url": f"/api/workflow/status/{state.run_id}",
        }

    except Exception as e:
        return {
            "status": "error",
            "workflow": req.workflow_id,
            "message": str(e),
        }


@workflows_router.get("/status/{run_id}")
async def workflow_status(run_id: str):
    """查询工作流运行进度。"""
    from aitest.workflow_engine import WorkflowRunner, RUNS_DIR

    state_path = RUNS_DIR / f"{run_id}.json"
    if not state_path.exists():
        return {"status": "not_found", "run_id": run_id, "message": "运行记录不存在"}

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            state = json.load(f)
    except Exception as e:
        return {"status": "error", "run_id": run_id, "message": str(e)}

    steps = state.get("steps", {})
    completed = sum(1 for s in steps.values() if s.get("status") == "completed")
    failed = sum(1 for s in steps.values() if s.get("status") == "failed")
    total = len(steps)

    return {
        "run_id": run_id,
        "workflow": state.get("workflow_id", ""),
        "status": state.get("status", "unknown"),
        "progress": f"{completed}/{total}",
        "completed": completed,
        "failed": failed,
        "total": total,
        "steps": {
            step_id: {
                "name": info.get("name", ""),
                "status": info.get("status", "pending"),
                "started_at": info.get("started_at"),
                "completed_at": info.get("completed_at"),
                "error": info.get("error", ""),
            }
            for step_id, info in steps.items()
        },
    }


@workflows_router.get("/list")
async def list_workflows():
    """列出所有可用工作流定义。"""
    workflows = []
    for wf_path in sorted(WORKFLOW_DIR.glob("*.yaml")):
        try:
            import yaml
            with open(wf_path, "r", encoding="utf-8") as f:
                wf_data = yaml.safe_load(f)
            workflows.append({
                "id": wf_data.get("id", wf_path.stem),
                "name": wf_data.get("name", wf_path.stem),
                "description": wf_data.get("description", ""),
                "steps": len(wf_data.get("steps", [])),
            })
        except Exception as e:
            from aitest.error_logger import log_error
            log_error("workflows_api.list", "parse_yaml", e, {"file": str(wf_path)})
            workflows.append({
                "id": wf_path.stem,
                "name": wf_path.stem,
                "description": "(无法解析)",
                "steps": 0,
            })

    return {"workflows": workflows, "total": len(workflows)}


@workflows_router.get("/runs")
async def list_runs(limit: int = 20):
    """列出最近的运行记录（含 LangGraph + 旧版 workflow）。"""
    from aitest.workflow_engine import RUNS_DIR

    runs = []

    # LangGraph runs
    try:
        from aitest.graphs.checkpoint import list_runs as list_graph_runs
        graph_runs = list_graph_runs(limit=limit)
        for r in graph_runs:
            runs.append({
                "run_id": r["run_id"],
                "engine": "langgraph",
                "status": "checkpointed",
                "updated_at": r.get("updated_at", ""),
            })
    except Exception as e:
        from aitest.error_logger import log_error
        log_error("workflows_api.status", "list_runs", e)

    # 旧版 workflow runs
    if RUNS_DIR.exists():
        for run_path in sorted(RUNS_DIR.glob("*.json"),
                               key=lambda p: p.stat().st_mtime, reverse=True)[:limit]:
            try:
                with open(run_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                steps = state.get("steps", {})
                completed = sum(1 for s in steps.values() if s.get("status") == "completed")
                runs.append({
                    "run_id": run_path.stem,
                    "engine": "legacy",
                    "workflow": state.get("workflow_id", ""),
                    "status": state.get("status", "unknown"),
                    "progress": f"{completed}/{len(steps)}",
                    "updated_at": run_path.stat().st_mtime,
                })
            except Exception as e:
                from aitest.error_logger import log_error
                log_error("workflows_api.status", "parse_run", e, {"run": str(run_path)})

    return {"runs": runs[:limit], "total": len(runs)}


@workflows_router.get("/graph-status/{run_id}")
async def graph_status(run_id: str):
    """查询 LangGraph 运行状态（从 SqliteSaver）。"""
    try:
        from aitest.graphs.checkpoint import get_latest_state
        state = get_latest_state(run_id)
        if not state:
            return {"status": "not_found", "run_id": run_id, "message": "Graph run not found"}
        return {
            "run_id": run_id,
            "engine": "langgraph",
            "status": state.get("status", "?"),
            "module": state.get("module", "?"),
            "mode": state.get("mode", "?"),
            "completed_phases": state.get("completed_phases", []),
            "failed_phases": state.get("failed_phases", []),
            "current_phase": state.get("current_phase", "?"),
            "pages": state.get("pages", []),
        }
    except Exception as e:
        return {"status": "error", "run_id": run_id, "message": str(e)}
