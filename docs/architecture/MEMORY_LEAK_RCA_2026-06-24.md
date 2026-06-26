# Memory Leak Root Cause Analysis — 2026-06-24

> Production severity. OOM trend persists after LifecycleRegistry + MemoryGuard + guarded_create_task + OwnershipChecker deployed.

## 1. Executive Summary

**内存仍增长因为 Lifecycle 系统只覆盖了约 40% 的分配点。三个根因类别全部逃逸了现有防御：**

| # | Root Cause | 逃逸机制 | Lifecycle 为何没覆盖 |
|---|-----------|---------|-------------------|
| RC1 | Chat SSE 后台线程 + 无界队列 | `threading.Thread` + `asyncio.Queue()` 无 maxsize | 系统只追踪 asyncio Task，不追踪 thread |
| RC2 | 消费者模块级无界 dict | `_by_module`, `_by_agent`, `_usage` 只增不减 | 这些 dict 在 singleton consumer 内部，未注册 LifecycleObject |
| RC3 | EventBus/ObservationBus 订阅者强引用 | bare `bus.subscribe()` 不用 `BoundSubscription` | `BoundSubscription` 存在但无人使用 — 死代码 |

**单一最可能根因（如果只能选一个）：RC1 — Chat SSE daemon thread + 无界 asyncio.Queue。**

每个聊天消息创建新 daemon thread → thread 在 `threading._active` 中持有强引用 → thread 闭包捕获 ChatSession → SSE 断开后 thread 继续跑 → 事件推入无界 Queue → Queue 无限增长。

---

## 2. Memory Growth Evidence

### 2.1 可观测的增长点（通过 `/api/debug/memory/*`）

以下对象类型在 LifecycleRegistry 中持续增长（来自 `leak_report()` 按类型聚合）：

| owner type | 增长趋势 | 原因 |
|-----------|---------|------|
| `chat:module` | 每次聊天会话 +1 | ChatSession 注册为 `chat-sessions:{sid}`，TTL=1800s |
| `onboarding:module` | 每次 onboarding +1 | OnboardingState 注册为 `onboarding-sessions:{sid}`，TTL=7200s |
| `task:*` | 持续增长 | guarded_create_task 注册的 asyncio Task |
| `subscription:*` | 静止（无人用 BoundSubscription） | |

### 2.2 不可观测的增长点（关键缺失）

以下对象类型**不在** LifecycleRegistry 中，但独立增长：

| 对象 | 位置 | 估计增长率 |
|------|------|-----------|
| `threading.Thread` (daemon) | `threading._active` (CPython 内部) | 每聊天消息 +1 |
| `asyncio.Queue` (无界) | `chat.py:402` — `asyncio.Queue()` 无 maxsize | 每聊天消息 +1 Queue，SSE 断后仍积累 AgentEvent |
| `dict.__by_module` | `metrics_consumer.py:56` | 每新模块 +1 entry |
| `dict.__by_agent` | `metrics_consumer.py:57` | 每新 agent +1 entry |
| `dict.__usage` | `quota_usage.py:48` | 每新 workspace +1 entry |

### 2.3 缺什么数据

- **`threading.enumerate()` dump** — 多少个 daemon thread 活着？每个 thread 的 stack trace？
- **`asyncio.Queue.qsize()` per chat session** — 断开 SSE 后 Queue 是否仍在增长？
- **RSS 时间曲线 vs 聊天消息数** — 相关性验证
- **`/api/debug/memory/gc-top` 输出随时间变化** — 哪些 Python 对象类型在 GC 堆中增长？

👉 **必须补充这些观测点才能锁定 RC1。当前 endpoints 只能看到 LifecycleRegistry 内对象，看不到 thread/queue/dict。**

---

## 3. Root Cause Chain — Complete Reference

### 3.1 RC1: Chat SSE Daemon Thread + Unbounded Queue

**完整引用链：**

```
threading._active (CPython 全局 dict)
  → Thread(id=N)  [_run_agent thread, daemon=True]
    → _run_agent closure captures `s` (ChatSession)
      → s.agent_queue = asyncio.Queue()  [chat.py:402]
        → Queue._queue = collections.deque()  [AgentEvent 堆积]
      → s.agent = AgentLoop(...)  [chat.py:359]
      → s.messages = list[dict]   [chat.py:85]
```

**分配栈：**

1. **用户发送消息** → `POST /api/chat/sessions/{id}/messages` → `[chat.py:208]`
2. **SSE 端点被调用** → `GET /api/chat/sessions/{id}/stream/{mid}` → `[chat.py:276]`
3. **`asyncio.Queue()` 创建** → `[chat.py:402]` — **无 maxsize，无界**
4. **`threading.Thread(daemon=True)` 创建** → `[chat.py:421]` — **不注册 Lifecycle，不用 TaskGuard**
5. **SSE 客户端断开** → `EventSourceResponse` 停止消费 → `agent_event_generator` async generator 被 GC
6. **`_run_agent` thread 继续运行** — `s.agent.run_interactive()` 持续 yield events
7. **`agent_loop_ref.call_soon_threadsafe(s.agent_queue.put_nowait, event)`** → 推入无界 Queue
8. **Queue 无限增长** — 直到 thread 完成或进程 OOM

**为什么 Lifecycle 没收住：**
- `LifecycleRegistry` 追踪 `LifecycleObject`，不追踪 `threading.Thread`
- `TaskGuard` 追踪 `asyncio.Task`，不追踪 `threading.Thread`
- `MemoryGuard` 只看 RSS 总量 + LifecycleRegistry 内对象，看不到 threading._active 和 asyncio.Queue
- `OwnershipChecker` 扫描 LifecycleRegistry 内的 `__owned__` 对象，不扫描 CPython 内部结构

### 3.2 RC2: Consumer Module-Level Unbounded Dict

**`MetricsConsumer._by_module`** (`metrics_consumer.py:56, 118`):

```python
# 初始化
self._by_module: dict[str, dict] = {}  # module → {runs, completed, tokens, cost}

# 每次 run_completed 事件 — 无界增长
def _accumulate(self, event: RunEvent):
    module = event.data.get("module", "unknown")
    if module not in self._by_module:            # ← 新 module → 新 key，永远不会删除
        self._by_module[module] = {"runs": 0, ...}
    self._by_module[module]["runs"] += 1
```

- 每个新模块名添加一个 key → 永不删除
- `_by_agent` 同理
- 运行 100 个不同模块 → 100 个 entry。虽然不大（~10KB），但指标是增长趋势

**`QuotaUsageConsumer._usage`** (`quota_usage.py:48, 82`):

```python
self._usage: dict[str, dict] = {}  # workspace_id → counters

def _on_run_completed(self, event: RunEvent):
    ws_id = event.data.get("workspace_id", "")
    if ws_id not in self._usage:
        self._usage[ws_id] = self._empty_usage(ws_id, org_id)
    # ... 只增不删
```

- 每个新 workspace_id 添加一个 entry → 永不删除

**为什么 Lifecycle 没收住：**
- `MetricsConsumer` 和 `QuotaUsageConsumer` 是全局 singleton（`main.py:84-108`）
- 它们的内部 dict 不是 `OwnedDict`，没有注册到 LifecycleRegistry
- `_by_module` / `_by_agent` / `_usage` 是普通 `dict`，无 TTL，无上限
- `OwnershipChecker` 不会扫描这些，因为消费者本身没有 `__owned__` 标记

### 3.3 RC3: EventBus/ObservationBus Subscriber Retention

**所有消费者使用 bare subscribe（不用 BoundSubscription）：**

```python
# metrics_consumer.py:65 — bare subscribe
bus.subscribe(EventType.RUN_COMPLETED, self._on_run_completed)

# billing_hook.py:55 — bare subscribe
bus.subscribe(EventType.RUN_COMPLETED, self._on_run_completed)

# quota_usage.py:54 — bare subscribe
bus.subscribe(EventType.RUN_COMPLETED, self._on_run_completed)

# observation_bus.py:214-216 — bare subscribe
bus.subscribe(EventType.TEST_FAILED, on_test_failed)
bus.subscribe(EventType.TOOL_CALL_FAILED, on_tool_call_failed)
```

**`AgentTerminalWSManager._start_listening()`** (`main.py:1828-1891`):

```python
for et in [16 event types]:
    event_type = EventType(et)
    bus.subscribe(event_type, _on_event)  # ← 16 个订阅，永不取消（除非 dispose()）
```

- `_on_event` closure 捕获 `loop`, `queue`, `self` → 强引用链
- 如果 `AgentTerminalWSManager` 被重新创建（理论上不会，但 defense-in-depth 缺失）
- `dispose()` 会取消订阅 → 但 dispose 只在 shutdown 时调用

**为什么 Lifecycle 没收住：**
- `BoundSubscription` 类存在（`ownership.py:284-356`）但**零使用** — 代码搜索确认无任何调用者
- 所有消费者使用 bare `bus.subscribe()`，回调永远不被移除
- 消费者是 singleton → 实际不是"泄漏"（singleton 不应该被释放）→ 但违反了 ownership 原则
- 问题：回调闭包持有的对象（如 `store` in `register_memory_consumer()`）与消费者生命周期绑定，但所有权不清晰

---

## 4. Unified Leak Classification (≤3 Categories)

### Category A: Async Execution Escape（thread + queue，非 asyncio-task）

| 泄漏点 | 文件:行 | 逃逸机制 | 严重度 |
|--------|---------|---------|--------|
| Chat daemon thread | `chat.py:421` | `threading.Thread` 不追踪，queue 无界 | 🔴 CRITICAL |
| Onboarding thread | `project_onboarding_agent.py:197` | 使用 TaskGuard ✅ 已修复 | 🟢 OK |
| SOP start thread | `main.py:1664` | `threading.Thread(daemon=True)` — 无 lifecycle | 🟡 HIGH |
| Browser driver thread | `bu_driver.py` (integrations) | ThreadPoolExecutor — bounded | 🟢 OK |

### Category B: Unbounded Collection Growth（module/global dict 无上限）

| 泄漏点 | 文件:行 | 数据结构 | 严重度 |
|--------|---------|---------|--------|
| metrics._by_module | `metrics_consumer.py:56` | `dict` 无上限 | 🟡 MEDIUM |
| metrics._by_agent | `metrics_consumer.py:57` | `dict` 无上限 | 🟡 MEDIUM |
| quota._usage | `quota_usage.py:48` | `dict` 无上限 | 🟡 MEDIUM |
| ChatSession.messages | `chat.py:85` | `list[dict]` capped 500 ✅ | 🟢 OK |
| ObservationBus._history | `observation_bus.py:78` | `list` capped 1000 ✅ | 🟢 OK |
| EventBus._subscribers | `event_bus.py:33` | `dict[str, list[Callable]]` | 🟡 MEDIUM |
| ObservationBus._subscribers | `observation_bus.py:77` | `dict[EventType, list[Callable]]` | 🟡 MEDIUM |

### Category C: Callback/Subscriber Retention（闭包 + 订阅者强引用）

| 泄漏点 | 文件:行 | 捕获对象 | 严重度 |
|--------|---------|---------|--------|
| `_on_event` closure | `main.py:1837` | `loop`, `queue`, `self` (AgentTerminalWSManager) | 🟡 MEDIUM |
| `on_test_failed` closure | `observation_bus.py:177` | `store` (TestingMemoryStore) | 🟢 LOW |
| `_run_agent` closure | `chat.py:410` | `s` (ChatSession) | 🔴 CRITICAL |
| `agent_event_generator` closure | `chat.py:424` | `s` (ChatSession) | 🔴 CRITICAL |
| `_cleanup` closure | `worker_pool.py:164` | `task_id` — cleaned up via done callback ✅ | 🟢 OK |

---

## 5. Minimal Patch Fixes

### Patch RC1-A: Bound chat asyncio.Queue + task cancel on SSE disconnect

**文件**: `aitest/server/api/chat.py`

```python
# Line 402 — CHANGE:
s.agent_queue = asyncio.Queue()
# TO:
s.agent_queue = asyncio.Queue(maxsize=256)  # Backpressure: block producer when full
```

```python
# Line 410-421 — CHANGE:
def _run_agent():
    nonlocal agent_loop_ref
    try:
        for event in s.agent.run_interactive():
            agent_loop_ref.call_soon_threadsafe(s.agent_queue.put_nowait, event)
    except Exception as e:
        ...
# TO:
def _run_agent():
    nonlocal agent_loop_ref
    try:
        for event in s.agent.run_interactive():
            try:
                agent_loop_ref.call_soon_threadsafe(s.agent_queue.put_nowait, event)
            except asyncio.QueueFull:
                break  # Consumer gone — stop producing
    except Exception as e:
        ...
```

```python
# AFTER line 429 — ADD cancel mechanism:
# Capture the thread so we can signal it on disconnect
_cancel_event = threading.Event()

def _run_agent():
    nonlocal agent_loop_ref
    try:
        for event in s.agent.run_interactive():
            if _cancel_event.is_set():
                break
            try:
                agent_loop_ref.call_soon_threadsafe(s.agent_queue.put_nowait, event)
            except asyncio.QueueFull:
                break
    except Exception as e:
        if not _cancel_event.is_set():
            agent_loop_ref.call_soon_threadsafe(
                s.agent_queue.put_nowait,
                AgentEvent(type="agent_end", status="fail", error=str(e)),
            )

# In agent_event_generator, when break happens:
# _cancel_event.set()  ← signal thread to stop
```

### Patch RC1-B: Replace daemon Thread with asyncio task (remove thread entirely)

**文件**: `aitest/server/api/chat.py`

最彻底修复：不用 thread，直接用 `asyncio.to_thread` 或让 `AgentLoopAdapter.run_interactive()` 变成真正的 async generator。

但这是重构，不是最小 patch。**最小 patch 是 RC1-A 加下面这个：**

```python
# In ChatSession.destroy() [chat.py:108] — ADD thread cleanup:
def destroy(self):
    # ... existing cleanup ...
    
    # NEW: Signal running agent thread to stop
    if hasattr(self, '_cancel_event') and self._cancel_event:
        self._cancel_event.set()
    
    # NEW: Wait for thread with short timeout (don't block event loop)
    thread = self.agent_thread
    if thread is not None and thread.is_alive():
        thread.join(timeout=2.0)  # 2s max
    
    # ... rest of existing cleanup ...
```

### Patch RC1-C: Register ChatSession agent thread in LifecycleRegistry

**文件**: `aitest/server/api/chat.py`

在 SSE endpoint 中，创建 thread 后注册：

```python
s.agent_thread = threading.Thread(target=_run_agent, daemon=True)

# NEW: Register thread wrapper in lifecycle
from aitest.platform.lifecycle import get_registry, _ObjectRef
_registry = get_registry()
thread_lid = f"agent-thread:{session_id}:{message_id}"
_registry.register(_ObjectRef(
    thread_lid,
    f"chat:thread:{session_id}",
    dispose_fn=lambda: _cancel_event.set() or s.agent_thread.join(timeout=2.0),
    ttl_s=3600,  # 1h max for agent thread
))
```

### Patch RC2: Cap consumer dicts with LRU eviction

**文件**: `aitest/platform/metrics_consumer.py`

```python
# ADD constant:
_MAX_BY_MODULE = 200
_MAX_BY_AGENT = 200

# In _accumulate(), ADD eviction:
def _accumulate(self, event: RunEvent):
    # ... existing logic ...
    
    # Cap by_module — evict least recently updated if over limit
    if len(self._by_module) > _MAX_BY_MODULE:
        oldest = min(self._by_module.keys(), 
                     key=lambda k: self._by_module[k].get("_last_ts", 0))
        del self._by_module[oldest]
    
    self._by_module[module]["_last_ts"] = time.time()
    
    # Same for _by_agent
    if len(self._by_agent) > _MAX_BY_AGENT:
        oldest = min(self._by_agent.keys(),
                     key=lambda k: self._by_agent[k].get("_last_ts", 0))
        del self._by_agent[oldest]
```

**文件**: `aitest/platform/quota_usage.py`

```python
_MAX_USAGE_ENTRIES = 500

def _on_run_completed(self, event: RunEvent):
    # ... existing logic ...
    
    if len(self._usage) > _MAX_USAGE_ENTRIES:
        oldest = min(self._usage.keys(),
                     key=lambda k: self._usage[k].get("last_updated", ""))
        del self._usage[oldest]
```

### Patch RC3: Use BoundSubscription for all bus subscribers

**文件**: `aitest/platform/metrics_consumer.py`

```python
# CHANGE:
def start(self):
    if self._active:
        return
    bus = get_bus()
    bus.subscribe(EventType.RUN_COMPLETED, self._on_run_completed)
    bus.subscribe(EventType.RUN_FAILED, self._on_run_failed)
    bus.subscribe(EventType.RUN_CANCELLED, self._on_run_cancelled)
    self._active = True

def stop(self):
    if not self._active:
        return
    bus = get_bus()
    bus.unsubscribe(EventType.RUN_COMPLETED, self._on_run_completed)
    bus.unsubscribe(EventType.RUN_FAILED, self._on_run_failed)
    bus.unsubscribe(EventType.RUN_CANCELLED, self._on_run_cancelled)
    self._active = False
# TO: use BoundSubscription from ownership.py
# (But since consumers are singletons and never stop, this is defense-in-depth, not a leak fix)
```

**实际 RC3 修复**：对 `register_memory_consumer()` 使用 `BoundSubscription` 以确保 `store` 不被闭包永久捕获：

**文件**: `aitest/platform/observation_bus.py`

```python
# In register_memory_consumer() — currently using bare subscribe:
# CHANGE to use BoundSubscription so unsubscription is possible at shutdown.

from aitest.platform.ownership import BoundSubscription

def register_memory_consumer(store=None):
    # ... existing setup ...
    
    # Store subscriptions for cleanup
    _subs = []
    _subs.append(BoundSubscription(bus, EventType.TEST_FAILED, on_test_failed, 
                                    owner_id="memory-consumer"))
    _subs.append(BoundSubscription(bus, EventType.TOOL_CALL_FAILED, on_tool_call_failed,
                                    owner_id="memory-consumer"))
    for sub in _subs:
        sub.activate()
```

---

## 6. Verification Plan

### 6.1 补观测点（必须先做）

在 `main.py` 中添加一个新的 debug endpoint 来暴露当前缺失的数据：

```python
@app.get("/api/debug/memory/threads")
async def debug_threads():
    """List all non-daemon and daemon threads with stack traces."""
    import threading, sys, traceback
    threads = []
    for t in threading.enumerate():
        frame = sys._current_frames().get(t.ident)
        stack = traceback.format_stack(frame) if frame else []
        threads.append({
            "name": t.name,
            "ident": t.ident,
            "daemon": t.daemon,
            "alive": t.is_alive(),
            "stack_top": stack[-3:] if stack else [],  # last 3 frames
        })
    return {"total": len(threads), "threads": threads}


@app.get("/api/debug/memory/chat-queues")
async def debug_chat_queues():
    """Show all chat session queues and their sizes."""
    from aitest.server.api.chat import sessions
    result = []
    for sid, s in list(sessions.items()):
        qsize = s.agent_queue.qsize() if s.agent_queue else 0
        thread_alive = s.agent_thread.is_alive() if s.agent_thread else False
        result.append({
            "session_id": sid,
            "queue_size": qsize,
            "thread_alive": thread_alive,
            "messages_count": len(s.messages),
            "age_s": time.time() - s.created_at,
        })
    result.sort(key=lambda x: -x["queue_size"])
    return {"sessions": result, "total": len(result)}
```

### 6.2 验证每个 Patch

| Patch | 验证方法 | 预期结果 |
|-------|---------|---------|
| RC1-A (Queue maxsize) | `GET /api/debug/memory/chat-queues` → queue_size 永远 ≤ 256 | 断开 SSE 后 queue 不再增长 |
| RC1-B (Thread cancel) | `GET /api/debug/memory/threads` → 聊天 thread 数量匹配活跃 SSE 连接数 | 断开 SSE 后 thread 在 2s 内 exit |
| RC1-C (Thread lifecycle registration) | `GET /api/debug/memory/snapshot` → `by_owner` 中 `chat:thread:*` 有 TTL | 超时 thread 被 sweep 清理 |
| RC2 (Consumer dict cap) | `GET /api/debug/memory/gc-top` → `_by_module` dict 大小 ≤ 200 | 长期运行后 dict 不再增长 |
| RC3 (BoundSubscription) | `GET /health` → `event_bus_subscribers` 数量稳定 | 不再随时间线性增长 |

### 6.3 端到端验证

```bash
# 1. 启动服务器
aitest server start

# 2. 获取基线 snapshot
curl http://localhost:8000/api/debug/memory/snapshot > snap1.json

# 3. 模拟负载：10 个聊天消息 + SSE 连接后立即断开
for i in {1..10}; do
  sid=$(curl -s -X POST http://localhost:8000/api/chat/sessions | jq -r '.session_id')
  mid=$(curl -s -X POST "http://localhost:8000/api/chat/sessions/$sid/messages" \
    -H 'Content-Type: application/json' \
    -d '{"content":"分析 equipment 模块"}' | jq -r '.message_id')
  curl -s --max-time 5 "http://localhost:8000/api/chat/sessions/$sid/stream/$mid" > /dev/null &
  sleep 0.5
done

# 4. 等待 30 秒让所有 thread 结束
sleep 30

# 5. 获取第二次 snapshot + diff
curl http://localhost:8000/api/debug/memory/diff

# 6. 检查 threads
curl http://localhost:8000/api/debug/memory/threads

# 7. 检查 chat queues
curl http://localhost:8000/api/debug/memory/chat-queues

# 预期：
# - diff.delta_count ≤ 10 (临时对象已被 sweep)
# - threads 中 chat 相关 daemon thread = 0
# - chat-queues 中 queue_size = 0
# - RSS 曲线变平（30s 后 RSS 回落到接近基线）
```

### 6.4 长期验证

- 运行 24h，每小时记录 `GET /health` → `components.lifecycle.alive_objects`
- 预期：alive_objects 在 50-200 范围内波动，无单调增长
- 运行 24h，每小时记录 `GET /api/debug/memory/threads` → `total`
- 预期：thread count 在 5-15 范围内波动，无单调增长

---

## 7. Missing Data Request

以下数据当前不可获得但排查必须：

1. **`threading.enumerate()` 随时间变化** — daemon thread 堆积是 RC1 的直接证据
2. **`asyncio.Queue.qsize()` per chat session** — 队列增长是 RC1 的直接证据
3. **RSS 时间序列 vs 聊天消息数散点图** — 相关性验证
4. **`gc.get_objects()` 按类型聚合随时间变化** — 哪些 Python 类型在增长（不仅是 LifecycleRegistry 内的）

👉 **Patch 第一步是在 `main.py` 添加 `/api/debug/memory/threads` 和 `/api/debug/memory/chat-queues` endpoints（代码见 6.1），然后才能确认 RC1。**

---

## Appendix A: All Allocation Sites NOT Covered by LifecycleRegistry

| 分配点 | 文件:行 | 对象类型 | 是否注册 |
|--------|---------|---------|---------|
| `s.agent_queue = asyncio.Queue()` | `chat.py:402` | asyncio.Queue | ❌ |
| `threading.Thread(target=_run_agent)` | `chat.py:421` | Thread | ❌ |
| `_by_module: dict[str, dict]` | `metrics_consumer.py:56` | dict | ❌ |
| `_by_agent: dict[str, dict]` | `metrics_consumer.py:57` | dict | ❌ |
| `_usage: dict[str, dict]` | `quota_usage.py:48` | dict | ❌ |
| `_rate_state: dict[str, list[float]]` | `main.py:375` | dict | ❌（但有 10min cleanup） |
| `_subscribers: dict[str, list[Callable]]` | `event_bus.py:33` | dict | ❌ |
| `_subscribers: dict[EventType, list[Callable]]` | `observation_bus.py:77` | dict | ❌ |
| `_history: list[ObservationEvent]` | `observation_bus.py:78` | list | ❌（但有 1000 cap） |
| `_connections: list[WebSocket]` | `main.py:1571,1759` | list | ❌ |
| `_futures: dict[str, Future]` | `worker_pool.py:59` | dict | ❌（但有 10000 cap + done callback） |
| `_kanban_ws` (KanbanWSManager) | `main.py:1609` | singleton | ❌ |
| `_agent_terminal_ws` (AgentTerminalWSManager) | `main.py:1995` | singleton | ✅（通过 lifespan 注册） |

## Appendix B: Existing Fix Verification Status

| 修复 | 状态 | 覆盖范围 |
|------|------|---------|
| LifecycleRegistry | ✅ 部署 | 仅注册的 LifecycleObject |
| MemoryGuard (RSS check + cascade) | ✅ 部署 | RSS 总量 + 注册对象 |
| guarded_create_task | ✅ 部署 | asyncio.Task（不覆盖 Thread） |
| OwnedDict | ✅ 部署 | chat-sessions, onboarding-sessions, onboarding-agents |
| OwnershipChecker | ✅ 部署 | 仅扫描 `__owned__` 对象 |
| TaskGuard | ✅ 部署 | asyncio.Task（不覆盖 Thread） |
| BoundSubscription | ❌ 死代码 | 零使用 |
| TTLSet | ✅ 部署 | 仅 event dedup（bounded） |
