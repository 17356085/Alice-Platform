"""
Chat API — SSE 流式聊天端点。

端点:
  POST   /api/chat/sessions              创建会话
  POST   /api/chat/sessions/{id}/messages  发送消息
  GET    /api/chat/sessions/{id}/stream/{mid}  SSE 流
  POST   /api/chat/sessions/{id}/interact   交互响应
  GET    /api/chat/sessions/{id}/history    消息历史

架构:
  浏览器 ←SSE→ FastAPI ←asyncio.Queue← 后台线程(AgentLoop.run_interactive)
"""
import json
import os
import uuid
import time
import asyncio
import threading
from dataclasses import dataclass, field

from fastapi import APIRouter, Request, HTTPException
from sse_starlette.sse import EventSourceResponse

from aitest.agents.agent_runner import AgentLoop, AgentEvent, list_agents
from aitest.chat.intent_parser import parse_intent

chat_router = APIRouter(prefix="/api/chat", tags=["chat"])

# ── 默认 Provider 自动检测 ──────────────────────────────────────────────
# 优先级: 显式 AITEST_PROVIDER > 已配置 API Key 的 Provider > deepseek
_PROVIDER_DETECT_CHAIN = [
    ("deepseek", "DEEPSEEK_API_KEY"),
    ("claude",   "ANTHROPIC_API_KEY"),
    ("openai",   "OPENAI_API_KEY"),
    ("ollama",   "OLLAMA_BASE_URL"),
    # 后续新增平台只需加一行，如:
    # ("zhipu",   "ZHIPU_API_KEY"),
]


def _resolve_default_provider() -> str:
    """自动检测首个可用的 LLM Provider。"""
    explicit = os.environ.get("AITEST_PROVIDER", "")
    if explicit:
        return explicit
    for name, env_var in _PROVIDER_DETECT_CHAIN:
        if os.environ.get(env_var):
            return name
    return "deepseek"  # 最后的 fallback


_DEFAULT_PROVIDER = _resolve_default_provider()


# ── Session persistence (lazy init) ──────────────────────────────────────
_db_initialized = False

async def _ensure_db():
    global _db_initialized
    if not _db_initialized:
        from aitest.server.session_store import init_db
        await init_db()
        _db_initialized = True


async def _persist_session(session_id: str, messages: list, title: str = ""):
    """Persist chat session to SQLite (best-effort, non-blocking)."""
    try:
        await _ensure_db()
        from aitest.server.session_store import (
            async_session_factory, create_session, update_session_messages,
            update_session_title, get_session, ChatSessionRecord,
        )
        import uuid as _uuid
        try:
            sid = _uuid.UUID(session_id.replace("chat-", ""))
        except ValueError:
            sid = _uuid.uuid4()
        async with async_session_factory() as db:
            existing = await get_session(db, sid)
            if existing:
                await update_session_messages(db, sid, messages)
                if title:
                    await update_session_title(db, sid, title)
            else:
                s = await create_session(db, title=title or f"Chat {session_id[:12]}")
                await update_session_messages(db, s.id, messages)
    except Exception:
        pass  # Best-effort: don't break chat if DB fails


# ══════════════════════════════════════════════════════════════════════════
#  Session 管理
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ChatSession:
    session_id: str
    messages: list[dict] = field(default_factory=list)
    agent: AgentLoop | None = None
    agent_thread: threading.Thread | None = None
    agent_queue: asyncio.Queue | None = None  # AgentEvent → SSE 桥接
    created_at: float = 0.0
    last_active: float = 0.0

    def __post_init__(self):
        self.created_at = time.time()
        self.last_active = self.created_at


sessions: dict[str, ChatSession] = {}


def _cleanup_old_sessions(max_age_seconds: int = 1800) -> int:
    """清理超过 max_age_seconds 未活动的会话。返回清理数量。"""
    now = time.time()
    stale = [sid for sid, s in sessions.items() if now - s.last_active > max_age_seconds]
    for sid in stale:
        del sessions[sid]
    return len(stale)


# ══════════════════════════════════════════════════════════════════════════
#  端点
# ══════════════════════════════════════════════════════════════════════════

@chat_router.post("/sessions")
async def create_session():
    """创建新聊天会话。"""
    _cleanup_old_sessions()
    sid = f"chat-{uuid.uuid4().hex[:8]}"
    sessions[sid] = ChatSession(session_id=sid)
    return {"session_id": sid, "created_at": sessions[sid].created_at}


@chat_router.get("/sessions/{session_id}/history")
async def get_history(session_id: str):
    """获取会话消息历史。"""
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    s.last_active = time.time()
    return {"session_id": session_id, "messages": s.messages}


@chat_router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话。"""
    if session_id in sessions:
        del sessions[session_id]
        return {"status": "deleted", "session_id": session_id}
    raise HTTPException(status_code=404, detail="Session not found")


@chat_router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, body: dict):
    """
    发送消息，返回 stream_url。

    Body: {"content": "用户输入内容"}
    """
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    s.last_active = time.time()
    mid = f"msg-{uuid.uuid4().hex[:8]}"

    msg = {
        "message_id": mid,
        "role": "user",
        "content": content,
        "timestamp": time.time(),
    }
    s.messages.append(msg)

    return {
        "session_id": session_id,
        "message_id": mid,
        "stream_url": f"/api/chat/sessions/{session_id}/stream/{mid}",
    }


@chat_router.post("/sessions/{session_id}/interact")
async def interact(session_id: str, body: dict):
    """
    用户交互响应 — 向暂停中的 Agent 发送指令。

    Body: {"interaction_id": "int-xxx", "response": "retry"|"skip"|"abort"|"approve"}
    """
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    if not s.agent:
        raise HTTPException(status_code=400, detail="No active agent in this session")

    response = body.get("response", "").strip()
    if not response:
        raise HTTPException(status_code=400, detail="response is required")

    s.last_active = time.time()
    s.agent.send_interaction(response)

    return {"status": "accepted", "session_id": session_id}


@chat_router.get("/sessions/{session_id}/stream/{message_id}")
async def stream_response(session_id: str, message_id: str, request: Request):
    """
    SSE 流式端点。

    后台线程跑 AgentLoop.run_interactive()，
    通过 asyncio.Queue 桥接到 SSE EventSourceResponse。
    """
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    # 找到用户消息
    user_msg = None
    for m in s.messages:
        if m.get("message_id") == message_id:
            user_msg = m
            break
    if not user_msg:
        raise HTTPException(status_code=404, detail="Message not found")

    s.last_active = time.time()
    content = user_msg["content"]

    # 解析意图
    intent = parse_intent(content)

    # 如果是一般聊天，直接流式回复
    if intent["type"] == "chat":
        s.messages.append({
            "message_id": f"resp-{message_id}",
            "role": "assistant",
            "content": "",
            "timestamp": time.time(),
        })

        async def chat_event_generator():
            from aitest.llm.provider import get_provider
            try:
                llm = get_provider(_DEFAULT_PROVIDER)
                full_text = ""
                for se in llm.stream_complete(
                    "你是 AI 自动化测试助手。用中文简洁回答。",
                    content,
                    max_tokens=1000,
                ):
                    if se.type == "content_chunk":
                        full_text += se.content
                        yield {"event": "chunk", "data": json.dumps(
                            {"content": se.content}, ensure_ascii=False)}
                    elif se.type == "done":
                        yield {"event": "done", "data": json.dumps(
                            {"success": True, "token_usage": se.token_usage}, ensure_ascii=False)}
                    elif se.type == "error":
                        yield {"event": "error", "data": json.dumps(
                            {"message": se.error_message}, ensure_ascii=False)}
                for m in s.messages:
                    if m.get("message_id") == f"resp-{message_id}":
                        m["content"] = full_text
            except Exception as e:
                import traceback
                print(f"[Chat ERROR] {traceback.format_exc()}", flush=True)
                yield {"event": "error", "data": json.dumps(
                    {"message": f"聊天出错: {str(e)[:200]}"}, ensure_ascii=False)}

        return EventSourceResponse(chat_event_generator())

    # ── Agent 执行 ──
    s.messages.append({
        "message_id": f"resp-{message_id}",
        "role": "assistant",
        "content": "",
        "timestamp": time.time(),
    })

    if intent["type"] == "run_agent":
        agent_name = intent.get("agent", "test-design-agent")
        # 验证 agent 名称
        valid = [a for a in list_agents() if a.endswith("-agent")]
        if agent_name not in valid:
            agent_name = "test-design-agent"

        s.agent = AgentLoop(
            agent_name,
            provider=_DEFAULT_PROVIDER,
            module=intent.get("module", ""),
            page=intent.get("page", ""),
            verbose=False,
        )
    elif intent["type"] == "run_sop":
        # Phase 6: 真正的 SOP 图流式执行
        from aitest.graphs.sop_runner import SOPRunner
        s.agent = SOPRunner(
            module=intent.get("module", ""),
            pages=[intent.get("page", "")] if intent.get("page") else [],
            provider=_DEFAULT_PROVIDER,
        )
    elif intent["type"] == "status":
        s.agent = None
        # 直接返回状态信息
        async def status_generator():
            from aitest.agents.agent_scheduler import check_preconditions
            from aitest.chat.intent_parser import _get_known_modules
            mod = intent.get("module", "")
            if mod:
                result = check_preconditions(mod)
                status_text = json.dumps(result, ensure_ascii=False, indent=2)
            else:
                status_text = f"可用模块: {', '.join(_get_known_modules())}"
            yield {"event": "message", "data": json.dumps(
                {"role": "assistant", "type": "text", "content": f"## 状态\n\n```json\n{status_text}\n```"},
                ensure_ascii=False)}
            yield {"event": "done", "data": json.dumps({"success": True}, ensure_ascii=False)}
        return EventSourceResponse(status_generator())
    else:
        s.agent = None
        async def unknown_generator():
            yield {"event": "message", "data": json.dumps(
                {"role": "assistant", "type": "text", "content": "抱歉，我没有理解你的意图。试试：\n- 给 equipment/alarm-config 写自动化测试\n- 分析 tank/alarm-config 页面\n- 查看状态"},
                ensure_ascii=False)}
            yield {"event": "done", "data": json.dumps({"success": True}, ensure_ascii=False)}
        return EventSourceResponse(unknown_generator())

    # ── 桥接：后台线程 Agent → asyncio.Queue → SSE ──
    s.agent_queue = asyncio.Queue()
    # 捕获当前 event loop（Python 3.12+ 后台线程中 get_event_loop() 不可用）
    try:
        agent_loop_ref = asyncio.get_running_loop()
    except RuntimeError:
        agent_loop_ref = asyncio.get_event_loop()

    # 后台线程
    def _run_agent():
        nonlocal agent_loop_ref
        try:
            for event in s.agent.run_interactive():
                agent_loop_ref.call_soon_threadsafe(s.agent_queue.put_nowait, event)
        except Exception as e:
            agent_loop_ref.call_soon_threadsafe(
                s.agent_queue.put_nowait,
                AgentEvent(type="agent_end", status="fail", error=str(e)),
            )

    s.agent_thread = threading.Thread(target=_run_agent, daemon=True)
    active_interaction_id = None  # 当前待处理的交互 ID

    async def agent_event_generator():
        nonlocal active_interaction_id
        accumulated_text = ""

        # 启动 Agent 线程
        s.agent_thread.start()

        # 先发送一条欢迎消息
        yield {"event": "message", "data": json.dumps(
            {"role": "assistant", "type": "text", "content": "正在执行..."},
            ensure_ascii=False)}

        error_count = 0

        while True:
            try:
                # 等待 Agent 事件（30 秒超时防止永久挂起）
                event: AgentEvent = await asyncio.wait_for(s.agent_queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                yield {"event": "error", "data": json.dumps(
                    {"message": "执行超时，Agent 可能卡住了"}, ensure_ascii=False)}
                break

            if event.type in ("skill_start", "plan_result"):
                yield {"event": "skill_start", "data": json.dumps({
                    "skill_id": event.skill_id,
                    "label": event.content or event.skill_id,
                    "progress": event.progress,
                }, ensure_ascii=False)}

            elif event.type == "skill_chunk":
                accumulated_text += event.content
                yield {"event": "chunk", "data": json.dumps(
                    {"content": event.content}, ensure_ascii=False)}

            elif event.type == "skill_end":
                yield {"event": "skill_end", "data": json.dumps({
                    "skill_id": event.skill_id,
                    "status": "pass" if not event.error else "fail",
                    "summary": (event.content or "")[:200],
                    "token_usage": event.token_usage,
                }, ensure_ascii=False)}

            elif event.type == "observation":
                yield {"event": "skill_end", "data": json.dumps({
                    "skill_id": event.skill_id,
                    "status": event.status,
                    "summary": event.summary,
                }, ensure_ascii=False)}

            elif event.type == "interaction_required":
                active_interaction_id = event.interaction_id
                yield {"event": "interaction", "data": json.dumps({
                    "interaction_id": event.interaction_id,
                    "type": event.interaction_type,
                    "prompt": event.interaction_prompt,
                    "options": event.interaction_options,
                    "skill_id": event.skill_id,
                }, ensure_ascii=False)}
                # 等待用户响应（由 /interact 端点触发）
                # 用户响应后 Agent 线程继续，新事件推入队列
                # 我们继续循环等待下一个事件

            elif event.type == "agent_message":
                yield {"event": "message", "data": json.dumps(
                    {"role": "assistant", "type": "text", "content": event.content},
                    ensure_ascii=False)}

            elif event.type == "agent_end":
                yield {"event": "message", "data": json.dumps(
                    {"role": "assistant", "type": "text", "content": event.summary or event.content},
                    ensure_ascii=False)}
                yield {"event": "done", "data": json.dumps({
                    "success": event.status == "pass",
                    "summary": event.summary,
                    "error": event.error if event.error else "",
                }, ensure_ascii=False)}
                break

            # ── SOP 流水线事件 (Phase 6) ──
            elif event.type == "sop_start":
                accumulated_text += event.content + "\n"
                yield {"event": "message", "data": json.dumps(
                    {"role": "assistant", "type": "text", "content": event.content},
                    ensure_ascii=False)}

            elif event.type == "sop_phase":
                accumulated_text += event.content + "\n"
                yield {"event": "sop_phase", "data": json.dumps({
                    "content": event.content,
                    "progress": event.progress,
                    "status": event.status,
                    "phase_id": event.skill_id or "",
                }, ensure_ascii=False)}

            elif event.type == "sop_complete":
                accumulated_text += event.content + "\n"
                yield {"event": "message", "data": json.dumps(
                    {"role": "assistant", "type": "text", "content": event.content or event.summary},
                    ensure_ascii=False)}
                yield {"event": "done", "data": json.dumps({
                    "success": event.status not in ("failed", "completed_with_issues", "fail"),
                    "summary": event.summary or event.content,
                    "error": event.error if event.error else "",
                }, ensure_ascii=False)}
                break

            elif event.type == "error" or hasattr(event, 'error') and event.error:
                yield {"event": "error", "data": json.dumps(
                    {"message": getattr(event, 'error', 'Unknown error')}, ensure_ascii=False)}

        # 更新消息记录
        for m in s.messages:
            if m.get("message_id") == f"resp-{message_id}":
                m["content"] = accumulated_text or (event.summary if 'event' in dir() else "") or ""

        # 持久化会话到 SQLite（best-effort）
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_persist_session(session_id, s.messages))
        except RuntimeError:
            pass

    # 包装 generator，添加顶层异常捕获
    async def safe_agent_generator():
        try:
            async for event_data in agent_event_generator():
                yield event_data
        except Exception as e:
            import traceback
            tb = traceback.format_exc()
            print(f"[Chat SSE ERROR] {tb}", flush=True)
            yield {"event": "error", "data": json.dumps(
                {"message": f"内部错误: {str(e)[:200]}"}, ensure_ascii=False)}

    return EventSourceResponse(safe_agent_generator())
