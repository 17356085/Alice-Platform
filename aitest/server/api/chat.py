"""
Chat API — SSE 流式聊天端点。

端点:
  POST   /api/chat/sessions              创建会话
  POST   /api/chat/sessions/{id}/messages  发送消息
  GET    /api/chat/sessions/{id}/stream/{mid}  SSE 流
  POST   /api/chat/sessions/{id}/interact   交互响应
  GET    /api/chat/sessions/{id}/history    消息历史

架构:
  浏览器 ←SSE→ FastAPI ←asyncio.Queue← asyncio.Task(AgentLoop via to_thread) [P0-3]
"""
import json
import uuid
import time
import asyncio
import threading
import sys
import traceback as _traceback
from dataclasses import dataclass, field

from fastapi import APIRouter, Request, HTTPException
from sse_starlette.sse import EventSourceResponse

from alice_engine.core.executor import list_agents
from alice_engine.core.task import AgentEvent
from aitest.chat.intent_parser import parse_intent
from aitest.platform.ui_projection import map_agent_event, UIEventType
from aitest.server.core.dependencies import get_execution_service

chat_router = APIRouter(prefix="/api/chat", tags=["chat"])

# ── 默认 Provider 自动检测 (delegates to aitest.config) ────────────────
from aitest.config import config


def _resolve_default_provider() -> str:
    """自动检测首个可用的 LLM Provider。"""
    return config.resolve_llm_provider()


_DEFAULT_PROVIDER = _resolve_default_provider()


# ── Session persistence (lazy init) ──────────────────────────────────────
_db_initialized = False
_db_lock = asyncio.Lock()

async def _ensure_db():
    global _db_initialized
    if _db_initialized:
        return
    async with _db_lock:
        if _db_initialized:
            return
        from aitest.server.session_store import init_db
        await init_db()
        _db_initialized = True


async def _persist_session(session_id: str, messages: list, title: str = ""):
    """Persist chat session to SQLite (best-effort, non-blocking)."""
    try:
        await _ensure_db()
        from aitest.server.session_store import (
            create_session, update_session_messages,
            update_session_title, get_session,
        )
        existing = get_session(session_id)
        if existing:
            update_session_messages(session_id, messages)
            if title:
                update_session_title(session_id, title)
        else:
            create_session(title=title or f"Chat {session_id[:12]}")
            update_session_messages(session_id, messages)
    except Exception:
        pass  # Best-effort: don't break chat if DB fails


# ══════════════════════════════════════════════════════════════════════════
#  Session 管理
# ══════════════════════════════════════════════════════════════════════════

@dataclass
class ChatSession:
    session_id: str
    messages: list[dict] = field(default_factory=list)
    agent: object | None = None  # AgentLoop or SOPRunner (resolved via engine_factory)
    agent_thread: threading.Thread | None = None
    agent_queue: asyncio.Queue | None = None  # AgentEvent → SSE 桥接
    agent_task: asyncio.Task | None = None  # P0-3: tracked asyncio Task (replaces raw Thread)
    created_at: float = 0.0
    last_active: float = 0.0
    # ★ RCA RC1: Thread cancel signal — set when SSE client disconnects
    _cancel_event: threading.Event = field(default_factory=threading.Event)
    # MEM-AUDIT: track persist tasks so they can be cancelled on destroy
    _persist_tasks: set = field(default_factory=set)

    _MAX_MESSAGES = 500  # Truncate to prevent unbounded growth
    _QUEUE_MAXSIZE = 256  # Backpressure — block producer when consumer gone

    def __post_init__(self):
        self.created_at = time.time()
        self.last_active = self.created_at
        # ★ v2.9: Lifecycle registration handled by OwnedDict (ownership.py).
        # No self-registration — single owner principle. OwnedDict owns the
        # lifecycle entry under "chat-sessions:{session_id}".

    def append_message(self, msg: dict):
        """Append message with size cap — oldest evicted if over limit."""
        self.messages.append(msg)
        if len(self.messages) > self._MAX_MESSAGES:
            # Keep last _MAX_MESSAGES entries
            self.messages = self.messages[-self._MAX_MESSAGES:]

    def destroy(self):
        """Release all resources held by this session.

        Stops agent thread, clears queue, nulls heavy references.
        OwnedDict handles lifecycle unregistration — this method only
        clears internal resources. Idempotent.
        """
        # 0. Signal cancel — stop producer thread BEFORE draining queue
        self._cancel_event.set()

        # 1. Clear agent reference (may hold large state)
        agent = self.agent
        self.agent = None
        if agent is not None and hasattr(agent, 'cancel'):
            try:
                agent.cancel()
            except Exception:
                pass

        # 2. Drain and close agent queue
        queue = self.agent_queue
        self.agent_queue = None
        if queue is not None:
            while not queue.empty():
                try:
                    queue.get_nowait()
                except Exception:
                    break

        # 3. Cancel asyncio Task (P0-3: replaces raw Thread join)
        task = self.agent_task
        self.agent_task = None
        if task is not None and not task.done():
            task.cancel()

        # 3b. Thread compat: cancel leftover raw Thread (legacy sessions)
        thread = self.agent_thread
        self.agent_thread = None
        if thread is not None and thread.is_alive():
            thread.join(timeout=2.0)

        # 3c. Cancel pending persist tasks (MEM-AUDIT fix)
        for t in list(self._persist_tasks):
            if not t.done():
                t.cancel()
        self._persist_tasks.clear()

        # 4. Truncate messages to free memory
        self.messages.clear()

        # ★ v2.9: Lifecycle unregistration handled by OwnedDict.
        # No manual unregister — single owner principle.


# ★ v2.9: OwnedDict replaces bare dict — values auto-registered in LifecycleRegistry,
# auto-disposed on pop/delete, OwnershipChecker-verifiable. No external strong refs leak.
from aitest.platform.ownership import OwnedDict

import logging

logger = logging.getLogger(__name__)

sessions: OwnedDict[str, ChatSession] = OwnedDict(
    "chat-sessions", owner="chat:module", ttl_s=1800, max_size=500,
)


def _cleanup_old_sessions(max_age_seconds: int = 1800) -> int:
    """清理超过 max_age_seconds 未活动的会话。返回清理数量。

    OwnedDict.__delitem__ triggers destroy() via lifecycle.dispose().
    Single owner — OwnedDict handles both cleanup and lifecycle unregistration.
    """
    now = time.time()
    stale = [sid for sid, s in list(sessions.items()) if now - s.last_active > max_age_seconds]
    for sid in stale:
        try:
            del sessions[sid]  # OwnedDict triggers destroy → lifecycle.dispose → unregister
        except Exception:
            pass
    return len(stale)


def _touch_session(session_id: str) -> None:
    """Refresh last_touched in LifecycleRegistry to prevent premature TTL sweep.
    OwnedDict uses lifecycle ID: chat-sessions:{session_id}"""
    try:
        from aitest.platform.lifecycle import get_registry
        get_registry().touch(f"chat-sessions:{session_id}")
    except Exception:
        pass


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


@chat_router.get("/sessions")
async def list_sessions_endpoint(limit: int = 20):
    """列出聊天会话（用于前端同步）。v3.1: 支持前端缓存层同步。"""
    from aitest.server.session_store import list_sessions as _list_sessions
    try:
        result = _list_sessions(limit=min(limit, 50))
        return {"sessions": result}
    except Exception:
        # Fallback: 返回内存中的 sessions
        items = []
        for sid, s in list(sessions.items())[:limit]:
            title = "Chat"
            if s.messages:
                first_content = s.messages[0].get("content", "")
                title = first_content[:40] if first_content else "Chat"
            items.append({"id": sid, "title": title, "messages": s.messages, "created_at": s.created_at})
        return {"sessions": items}


@chat_router.get("/sessions/{session_id}/history")
async def get_history(session_id: str):
    """获取会话消息历史。"""
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    s.last_active = time.time()
    _touch_session(session_id)
    return {"session_id": session_id, "messages": s.messages}


@chat_router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """删除会话 — 释放所有关联资源（Agent、线程、队列）。
    OwnedDict.pop() triggers lifecycle.dispose() → destroy() automatically."""
    s = sessions.pop(session_id, None)
    if s is None:
        raise HTTPException(status_code=404, detail="Session not found")
    # destroy() already called by OwnedDict via lifecycle.dispose()
    return {"status": "deleted", "session_id": session_id}


@chat_router.post("/sessions/{session_id}/messages")
async def send_message(session_id: str, request: Request):
    """
    发送消息，返回 stream_url。

    Body: {"content": "用户输入内容"}
    """
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    content = body.get("content", "").strip()
    if not content:
        raise HTTPException(status_code=400, detail="content is required")

    s.last_active = time.time()
    _touch_session(session_id)
    mid = f"msg-{uuid.uuid4().hex[:8]}"

    msg = {
        "message_id": mid,
        "role": "user",
        "content": content,
        "timestamp": time.time(),
    }
    s.append_message(msg)

    return {
        "session_id": session_id,
        "message_id": mid,
        "stream_url": f"/api/chat/sessions/{session_id}/stream/{mid}",
    }


@chat_router.post("/sessions/{session_id}/interact")
async def interact(session_id: str, request: Request):
    """
    用户交互响应 — 向暂停中的 Agent 发送指令。

    Body: {"interaction_id": "int-xxx", "response": "retry"|"skip"|"abort"|"approve"}
    """
    s = sessions.get(session_id)
    if not s:
        raise HTTPException(status_code=404, detail="Session not found")
    if not s.agent:
        raise HTTPException(status_code=400, detail="No active agent in this session")

    try:
        body = await request.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {str(e)}")

    response = body.get("response", "").strip()
    if not response:
        raise HTTPException(status_code=400, detail="response is required")

    s.last_active = time.time()
    _touch_session(session_id)
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
    _touch_session(session_id)
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
                        yield {"event": UIEventType.THINKING_CHUNK, "data": json.dumps(
                            {"content": se.content}, ensure_ascii=False)}
                    elif se.type == "done":
                        yield {"event": UIEventType.DONE, "data": json.dumps(
                            {"success": True, "token_usage": se.token_usage}, ensure_ascii=False)}
                    elif se.type == "error":
                        yield {"event": UIEventType.ERROR, "data": json.dumps(
                            {"message": se.error_message}, ensure_ascii=False)}
                for m in s.messages:
                    if m.get("message_id") == f"resp-{message_id}":
                        m["content"] = full_text
            except Exception as e:
                import traceback
                logger.error(f"[Chat ERROR] {traceback.format_exc()}", flush=True)
                yield {"event": UIEventType.ERROR, "data": json.dumps(
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

        from aitest.platform.workspace import ExecutionContext
        svc = get_execution_service(request)
        ctx = ExecutionContext(
            workspace_id="chat",
            user_id=getattr(request.state, "user_id", "anonymous"),
            scopes=getattr(request.state, "scopes", ["read", "execute"]),
            org_id=getattr(request.state, "org_id", ""),
            entrypoint="server.chat",
        )
        s.agent = svc.create_engine(
            ctx,
            module=intent.get("module", ""),
            pages=[intent.get("page", "")] if intent.get("page") else [],
            agent=agent_name,
            provider=_DEFAULT_PROVIDER,
            verbose=False,
        )
    elif intent["type"] == "run_sop":
        # Phase 6: 真正的 SOP 图流式执行
        from aitest.platform.workspace import ExecutionContext
        svc = get_execution_service(request)
        ctx = ExecutionContext(
            workspace_id="chat",
            user_id=getattr(request.state, "user_id", "anonymous"),
            scopes=getattr(request.state, "scopes", ["read", "execute"]),
            org_id=getattr(request.state, "org_id", ""),
            entrypoint="server.chat",
        )
        s.agent = svc.create_engine(
            ctx,
            module=intent.get("module", ""),
            pages=[intent.get("page", "")] if intent.get("page") else [],
            agent="sop",
            provider=_DEFAULT_PROVIDER,
            mode="from-requirement",
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
            yield {"event": UIEventType.MESSAGE, "data": json.dumps(
                {"role": "assistant", "type": "text", "content": f"## 状态\n\n```json\n{status_text}\n```"},
                ensure_ascii=False)}
            yield {"event": UIEventType.DONE, "data": json.dumps({"success": True}, ensure_ascii=False)}
        return EventSourceResponse(status_generator())
    else:
        s.agent = None
        async def unknown_generator():
            yield {"event": UIEventType.MESSAGE, "data": json.dumps(
                {"role": "assistant", "type": "text", "content": "抱歉，我没有理解你的意图。试试：\n- 给 equipment/alarm-config 写自动化测试\n- 分析 tank/alarm-config 页面\n- 查看状态"},
                ensure_ascii=False)}
            yield {"event": UIEventType.DONE, "data": json.dumps({"success": True}, ensure_ascii=False)}
        return EventSourceResponse(unknown_generator())

    # ── 桥接：后台线程 Agent → asyncio.Queue → SSE ──
    # ★ RCA RC1: Bounded queue — backpressure when consumer gone (maxsize=256)
    s.agent_queue = asyncio.Queue(maxsize=s._QUEUE_MAXSIZE)
    # P0-3: agent_loop_ref removed — asyncio.to_thread() manages thread lifecycle,
    # no cross-thread call_soon_threadsafe needed.

    # ★ RCA RC1: Cancel event — signals producer thread to stop on disconnect
    cancel_evt = s._cancel_event
    cancel_evt.clear()  # Reset for this SSE session

    # P0-3: _run_agent removed — raw daemon Thread replaced by asyncio Task below.
    # call_soon_threadsafe + agent_loop_ref no longer needed — producer runs
    # via asyncio.to_thread() which is managed, cancellable, no threading._active leak.
    s.agent_thread = None  # No longer raw Thread
    active_interaction_id = None  # 当前待处理的交互 ID

    async def agent_event_generator():
        nonlocal active_interaction_id
        accumulated_text = ""

        # P0-3: to_thread binds run_interactive() to managed executor pool.
        # Task cancel on SSE disconnect → executor thread freed.
        async def _run_agent_producer():
            try:
                events = await asyncio.to_thread(list, s.agent.run_interactive())
                for event in events:
                    if cancel_evt.is_set():
                        break
                    try:
                        s.agent_queue.put_nowait(event)
                    except asyncio.QueueFull:
                        break
            except Exception as e:
                if not cancel_evt.is_set():
                    try:
                        s.agent_queue.put_nowait(
                            AgentEvent(type="agent_end", status="fail", error=str(e)))
                    except asyncio.QueueFull:
                        pass

        s.agent_task = asyncio.create_task(
            _run_agent_producer(), name=f"chat-{session_id[:20]}")

        # 先发送一条欢迎消息
        yield {"event": UIEventType.MESSAGE, "data": json.dumps(
            {"role": "assistant", "type": "text", "content": "正在执行..."},
            ensure_ascii=False)}

        error_count = 0

        while True:
            try:
                # 等待 Agent 事件（30 秒超时防止永久挂起）
                event: AgentEvent = await asyncio.wait_for(s.agent_queue.get(), timeout=30.0)
            except asyncio.TimeoutError:
                yield {"event": UIEventType.ERROR, "data": json.dumps(
                    {"message": "执行超时，Agent 可能卡住了"}, ensure_ascii=False)}
                break

            # Track text for final message persistence
            if event.type in ("skill_chunk", "sop_start", "sop_phase", "sop_complete"):
                accumulated_text += (event.content or "") + "\n"
            if event.type == "interaction_required":
                active_interaction_id = event.interaction_id

            # Map AgentEvent → UI SSE event via projection layer
            sse_event = map_agent_event(event)
            if sse_event:
                yield sse_event
                # Terminal events: end the stream
                if sse_event["event"] == UIEventType.DONE:
                    break

            # Handle error events not caught by map_agent_event
            elif event.type == "error" or (hasattr(event, 'error') and event.error):
                yield {"event": UIEventType.ERROR, "data": json.dumps(
                    {"message": getattr(event, 'error', 'Unknown error')}, ensure_ascii=False)}

        # 更新消息记录
        for m in s.messages:
            if m.get("message_id") == f"resp-{message_id}":
                m["content"] = accumulated_text or getattr(event, 'summary', '') or ""

        # 持久化会话到 SQLite（best-effort, tracked for cleanup）
        try:
            loop = asyncio.get_running_loop()
            task = loop.create_task(_persist_session(session_id, s.messages))
            s._persist_tasks.add(task)
            task.add_done_callback(lambda t: s._persist_tasks.discard(t))
        except RuntimeError:
            pass

    # 包装 generator，添加顶层异常捕获
    async def safe_agent_generator():
        try:
            async for event_data in agent_event_generator():
                yield event_data
        except Exception as e:
            tb = _traceback.format_exc()
            logger.error(f"[Chat SSE ERROR] {tb}", flush=True)
            yield {"event": UIEventType.ERROR, "data": json.dumps(
                {"message": f"内部错误: {str(e)[:200]}"}, ensure_ascii=False)}
        finally:
            # ★ RCA RC1: Signal thread to stop when SSE stream ends
            # (client disconnect, error, or natural completion)
            cancel_evt.set()

    return EventSourceResponse(safe_agent_generator())


# ═══════════════════════════════════════════════════════════════════════════
#  Task 2 (P0): Sentinel-file Pause/Resume endpoints
#  Storage: governance/.data/{task_id}/  (CONSTITUTION §3.1)
# ═══════════════════════════════════════════════════════════════════════════

@chat_router.get("/tasks/{task_id}/pause-status")
async def get_task_pause_status(task_id: str):
    """Query whether a task is currently paused awaiting user approval.

    Called by frontend polling (every ~3s) to detect paused tasks.
    Returns 200 with pause data, or 404 if task is not paused.
    """
    from aitest.infra.pause_handler import check_pause_status

    status = check_pause_status(task_id)
    if status is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{task_id}' is not paused or does not exist",
        )
    return {"task_id": task_id, "paused": True, **status}


@chat_router.post("/tasks/{task_id}/resume")
async def resume_task(task_id: str):
    """User approves a paused task — write resume.json to trigger continuation.

    Called by frontend when user clicks the approval button.
    The backend agent_runner's wait_for_resume() detects this file
    and continues execution.
    """
    from aitest.infra.pause_handler import write_resume_file, check_pause_status

    # Verify task is actually paused (prevent orphaned resume files)
    if check_pause_status(task_id) is None:
        raise HTTPException(
            status_code=404,
            detail=f"Task '{task_id}' is not currently paused",
        )

    write_resume_file(task_id)
    return {
        "status": "resumed",
        "task_id": task_id,
        "message": f"Task '{task_id}' resumed — agent will continue execution",
    }
