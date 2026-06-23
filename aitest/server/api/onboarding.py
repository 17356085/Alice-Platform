"""
Onboarding API endpoints — REST + WebSocket for project onboarding wizard.

Endpoints:
  POST   /api/onboarding/start          Start onboarding
  GET    /api/onboarding/{id}/status    Poll progress
  GET    /api/onboarding/{id}/menu      Preview discovered menu tree
  POST   /api/onboarding/{id}/confirm   Confirm/edit menu → continue
  POST   /api/onboarding/{id}/cancel    Cancel onboarding
  WS     /ws/onboarding/{id}            Real-time progress stream
"""
import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional

logger = logging.getLogger(__name__)

onboarding_router = APIRouter(prefix="/api/onboarding", tags=["onboarding"])

# ── In-memory agent store (shared with project_onboarding_agent) ─────────
# Import after router definition to avoid circular imports
_active_agents: dict[str, "ProjectOnboardingAgent"] = {}
_active_tasks: dict[str, asyncio.Task] = {}


def _get_agent():
    """Lazy import to avoid circular dependency at module load time."""
    from aitest.onboarding.project_onboarding_agent import (
        ProjectOnboardingAgent,
        _sessions,
        get_session,
        OnboardingStep,
    )
    return ProjectOnboardingAgent, _sessions, get_session, OnboardingStep


# ── Request/Response Models ──────────────────────────────────────────────

class OnboardingStartRequest(BaseModel):
    url: str = Field(default="", description="Application base URL (for source_type=url)")
    project_id: str = Field(..., description="Unique project identifier")
    name: str = Field(default="", description="Human-readable project name")
    username: str = Field(default="admin")
    password: str = Field(default="")
    app_type: str = Field(default="vue-hash-router", description="vue-hash-router | standard-url | react-spa")
    source_type: str = Field(default="url", description="url | local | openapi")
    project_path: str = Field(default="", description="Local project path (for source_type=local)")
    observe_pages: bool = Field(default=True)
    generate_page_objects: bool = Field(default=False)


class OnboardingConfirmRequest(BaseModel):
    menu_tree: Optional[list[dict]] = Field(default=None, description="Edited menu tree (null = accept as-is)")
    module_names: Optional[dict[str, str]] = Field(default=None, description="Override module slugs {label: slug}")


# ── REST Endpoints ───────────────────────────────────────────────────────

@onboarding_router.post("/start")
async def start_onboarding(req: OnboardingStartRequest):
    """Start project onboarding. Returns session_id for polling."""
    ProjectOnboardingAgent, _sessions, _, _ = _get_agent()

    agent = ProjectOnboardingAgent(headless=True)
    state = await agent.start(
        project_id=req.project_id,
        base_url=req.url,
        credentials={"username": req.username, "password": req.password} if req.password else None,
        app_type=req.app_type,
        source_type=req.source_type,
        project_path=req.project_path,
        observe_pages=req.observe_pages,
        generate_page_objects=req.generate_page_objects,
    )

    _active_agents[state.session_id] = agent

    return {
        "session_id": state.session_id,
        "project_id": state.project_id,
        "step": state.step.value,
        "started_at": state.started_at,
    }


# ── Path Validation (before parameterized routes to avoid match conflicts) ──

class PathValidateRequest(BaseModel):
    project_path: str = Field(..., description="Local project directory path")


@onboarding_router.post("/validate-path")
async def validate_project_path(req: PathValidateRequest):
    """Validate a local project path BEFORE starting onboarding.

    Checks: path exists → has package.json → framework detection.
    Returns structured validation result with suggestions.
    """
    from pathlib import Path
    import json as _json

    path = Path(req.project_path)

    # 1. Path existence
    if not path.exists():
        return {
            "valid": False, "exists": False, "has_package_json": False,
            "framework": "", "framework_version": "", "ui_library": "", "typescript": False,
            "error": f"路径不存在: {path}",
            "suggestions": [
                "请确认路径拼写正确",
                "Windows 路径格式: D:\\Projects\\my-app",
                "可以从文件管理器复制路径后粘贴",
            ],
        }

    # 2. Tech stack detection (frontend + backend)
    from aitest.discovery.source.framework_detector import TechStackDetector
    detector = TechStackDetector()
    stack = detector.detect(str(path))

    # Determine if we found anything useful
    has_frontend = stack.has_frontend
    has_backend = stack.has_backend

    if not has_frontend and not has_backend:
        return {
            "valid": False, "exists": True, "has_package_json": False,
            "framework": "", "framework_version": "", "ui_library": "", "typescript": False,
            "resolved_path": "",
            "backend": {},
            "error": "未找到可识别的项目文件 (package.json / pom.xml / build.gradle)",
            "suggestions": [
                "所选目录不是前端或后端项目（缺少 package.json / pom.xml）",
                "请选择包含 package.json 或 pom.xml 的项目根目录",
                "对于多模块项目，确保子目录包含构建文件",
            ],
        }

    # Build frontend response
    fe = stack.frontend
    fe_valid = has_frontend and fe and fe.framework.value != "unknown"
    fe_result = {
        "framework": fe.framework.value if fe else "",
        "framework_version": fe.version if fe else "",
        "ui_library": fe.ui_library if fe else "",
        "typescript": fe.typescript if fe else False,
        "project_root": fe.project_root if fe else "",
    } if fe else {}

    resolved_path = fe.project_root if fe and fe.project_root else str(path)

    # Build backend summary
    backend_result = stack.backend_summary

    # Overall validity: at least one of frontend/backend detected
    valid = has_frontend or has_backend

    return {
        "valid": valid, "exists": True,
        "has_package_json": has_frontend,
        "framework": fe_result.get("framework", ""),
        "framework_version": fe_result.get("framework_version", ""),
        "ui_library": fe_result.get("ui_library", ""),
        "typescript": fe_result.get("typescript", False),
        "resolved_path": resolved_path,
        "backend": backend_result,
        "suggestions": [],
        "error": "",
    }


@onboarding_router.get("/{session_id}/status")
async def get_onboarding_status(session_id: str):
    """Poll onboarding progress."""
    _, _sessions, get_session, _ = _get_agent()
    state = get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return state.to_dict()


@onboarding_router.get("/{session_id}/menu")
async def get_menu_preview(session_id: str):
    """Get discovered menu tree for review."""
    _, _sessions, get_session, _ = _get_agent()
    state = get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    return {
        "session_id": session_id,
        "menu_tree": state.menu_tree,
        "step": state.step.value,
    }


@onboarding_router.post("/{session_id}/confirm")
async def confirm_menu(session_id: str, req: OnboardingConfirmRequest):
    """Confirm or edit the discovered menu tree. Onboarding continues after this."""
    ProjectOnboardingAgent, _sessions, get_session, _ = _get_agent()

    state = get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = _active_agents.get(session_id)
    if not agent:
        raise HTTPException(status_code=400, detail="Agent not found for session")

    menu = req.menu_tree or state.menu_tree
    await agent.confirm_menu(session_id, menu)

    return {"status": "confirmed", "session_id": session_id}


@onboarding_router.post("/{session_id}/cancel")
async def cancel_onboarding(session_id: str):
    """Cancel an ongoing onboarding session."""
    ProjectOnboardingAgent, _sessions, get_session, _ = _get_agent()

    state = get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")

    agent = _active_agents.get(session_id)
    if agent:
        await agent.cancel(session_id)

    return {"status": "cancelled", "session_id": session_id}


@onboarding_router.get("/sessions")
async def list_sessions():
    """List all active onboarding sessions."""
    _, _sessions, _, OnboardingStep = _get_agent()
    result = []
    for sid, state in _sessions.items():
        result.append({
            "session_id": sid,
            "project_id": state.project_id,
            "step": state.step.value,
            "progress": state.progress,
        })
    return {"sessions": result, "total": len(result)}


# ── WebSocket ────────────────────────────────────────────────────────────

@onboarding_router.websocket("/ws/{session_id}")
async def onboarding_websocket(ws: WebSocket, session_id: str):
    """
    WebSocket for real-time onboarding progress.

    Events sent:
      {type: "step", step: "scanning_menu", progress: 0.10}
      {type: "menu", menu_tree: [...]}
      {type: "page_progress", current: "...", completed: 3, total: 12}
      {type: "error", message: "..."}
      {type: "completed", result: {...}}
    """
    await ws.accept()
    _, _sessions, get_session, _ = _get_agent()

    state = get_session(session_id)
    if not state:
        await ws.send_json({"type": "error", "message": "Session not found"})
        await ws.close()
        return

    last_step = None
    last_progress = -1

    try:
        while True:
            # Refresh state
            state = get_session(session_id)
            if not state:
                break

            # Send step change
            if state.step.value != last_step:
                await ws.send_json({
                    "type": "step",
                    "step": state.step.value,
                    "progress": state.progress,
                })
                last_step = state.step.value

            # Send menu when available
            if state.menu_tree and last_step == "scanning_menu":
                await ws.send_json({
                    "type": "menu",
                    "menu_tree": state.menu_tree,
                })

            # Send page progress
            if state.total_pages > 0:
                if state.completed_pages != last_progress:
                    await ws.send_json({
                        "type": "page_progress",
                        "current": state.current_page,
                        "completed": state.completed_pages,
                        "total": state.total_pages,
                        "progress": state.progress,
                    })
                    last_progress = state.completed_pages

            # Send errors
            if state.errors:
                for err in state.errors:
                    await ws.send_json({"type": "error", "message": err})
                state.errors.clear()

            # Terminal states
            if state.step.value in ("completed", "failed", "cancelled"):
                await ws.send_json({
                    "type": state.step.value,
                    "result": state.result,
                    "errors": state.errors,
                })
                break

            await asyncio.sleep(1.0)

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for {session_id}")
    except Exception as e:
        logger.error(f"WebSocket error for {session_id}: {e}")
        await ws.send_json({"type": "error", "message": str(e)})
    finally:
        await ws.close()

