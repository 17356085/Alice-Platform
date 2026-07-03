# 模块解耦审计报告

> 审计日期: 2026-07-03 | 审计范围: aitest/ 全目录 + packages/alice-engine/ + aitest/web/src/
> 隐性耦合点: 142 个 (HIGH 52 / MEDIUM 62 / LOW 28) → 详见 [HIDDEN_COUPLING_POINTS.md](HIDDEN_COUPLING_POINTS.md)
> 目标: 回答一个问题——当前系统是否真的解耦？

---

## 1. 模块边界分析

### 核心模块清单

| 模块 | 职责 | 输入 | 输出 |
|------|------|------|------|
| **ExecutionService** | 编排层：API→Run 生命周期 | ExecutionContext, module, pages, agent, provider | ExecutionResult |
| **Run** | 不可变执行记录 | dataclass 字段 | to_dict() |
| **ExecutionRequest** | 用户意图实体，有生命周期 | dataclass 字段 | to_dict() |
| **RunEvent** | 不可变事件 | event_type, run_id, data(dict[str,Any]) | to_dict() |
| **EventBus** | 进程内 pub/sub | RunEvent.publish() / publish_async() | 同步/异步调用 handlers |
| **RunStore** | PostgreSQL 持久化 | Run, RunEvent, ExecutionRequest | SQL rows |
| **AuditLogger** | 审计日志，通配符订阅所有事件 | RunEvent (priority=0, "*") | PG audit_entries |
| **BillingHook** | 计费事件生成 | run.completed, cost.recorded | billing.jsonl |
| **MetricsConsumer** | 聚合统计 | run.completed/failed/cancelled | in-memory counters + metrics.jsonl |
| **QuotaUsage** | 配额追踪（仅统计） | run.completed, run.failed | in-memory counters |
| **WebhookDispatcher** | 外部 webhook 推送 | 所有 EventType | HTTP POST |
| **ReportConsumer** | AI 执行报告 | run.completed, run.failed | JSON report files |
| **Timeline** | 时间线视图 | RunStore 查询 | list[dict] |
| **ObservationBus** | Agent 观测事件总线 | ObservationEvent | 同步调用 handlers |
| **MemoryObserver** | 死胡同检测 | SKILL_FAILED on ObservationBus | ChromaDB DEAD_END memory |
| **MemoryConsumer** | 观测→Memory 桥接 | TEST_FAILED, TOOL_CALL_FAILED | TestingMemoryStore |
| **GovernanceBridge** | 治理事件→平台 EventBus 桥接 | governance event file bus | RunEvent on platform bus |
| **EngineEventBusAdapter** | 引擎事件→平台 EventBus 桥接 | engine emit() | RunEvent on platform bus |
| **PlatformBridge** | ObservationBus→平台 EventBus 桥接 | ObservationEvent | RunEvent on platform bus |
| **UIProjection** | AgentEvent→SSE 映射 | AgentEvent | SSE dict |
| **ExecutionEngine(Protocol)** | 执行引擎抽象 | engine_type, module, pages | run()/run_interactive()/cancel() |
| **API 层 (execution.py, chat.py)** | HTTP 端点 | HTTP requests | JSON / SSE |
| **Frontend (chat.ts)** | Zustand store + SSE 消费 | SSE events | React state |
| **QueryLayer** | 统一查询 API | fluent filter chain | list[dict] |
| **Replay** | 执行录制回放 | step input/output | PG execution_steps |
| **Preflight** | 执行前依赖检查 | agent, module, page | PASS/WARN/BLOCK |
| **ArtifactLineage** | 产物依赖追踪 | project, module, artifact | PG artifact_lineage |
| **WorkspaceManager** | 工作空间管理 | org_id, ws_id | Workspace JSON |
| **OrganizationManager** | 组织管理 | org_id | Organization JSON |
| **LifecycleRegistry** | 运行时 GC + 内存观测 | ObjectRef | dispose/snapshot/leak_report |
| **OwnedDict** | 生命周期追踪的 dict | key, value | auto-register/dispose |

### 跨模块直接访问内部状态

| 耦合点 | 证据 | 严重度 |
|--------|------|--------|
| ReportConsumer._build_report() 直接调用 get_run_store().load_run() | report_consumer.py:113-118 | 中 |
| QuotaUsage.get_usage() 直接调用 store.count_runs() | quota_usage.py:128-130 | 中 |
| ExecutionService.cancel() 调用 list_runs(limit=500) 然后 in-memory filter | execution_service.py:392-393 | 中 |
| event_query.py 同时依赖 RunStore + AuditLogger + ArtifactLineage | event_query.py:16-29 | 中 |
| Timeline 直接查询 RunStore | timeline.py:29-30 | 低 |
| execution.py 大部分端点直接调用 get_run_store() 绕过 ExecutionService | execution.py:88,127,151,256 | 中 |
| kanban.py 直接读写 SOP_STATUS JSON 文件 | kanban.py:85-98 | 高 |

---

## 2. 真实耦合分析

### A. 数据耦合（Data Coupling）

**event.data dict key 依赖 — 中等**

所有 Consumer 通过 `event.data.get("key", default)` 访问字段，TypedDict 仅用于静态检查，运行时零验证。

| 生产者 (make_event kwargs) | 消费者 (event.data.get) | 隐式 key |
|---|---|---|
| execution_service.py:206 `org_id=ctx.org_id` | billing_hook.py:87 `event.data.get("org_id")` | "org_id" |
| execution_service.py:209 `total_tokens=run.total_tokens` | metrics_consumer.py:117 `event.data.get("total_tokens")` | "total_tokens" |
| execution_service.py:210 `total_cost=run.total_cost` | billing_hook.py:113 `event.data.get("total_cost")` | "total_cost" |
| execution_service.py:207 `workspace_id=ctx.workspace_id` | quota_usage.py:84 `event.data.get("workspace_id")` | "workspace_id" |
| execution_service.py:208 `module=module` | metrics_consumer.py:119 `event.data.get("module")` | "module" |

**RunStore 行映射 — 中等**

`_row_to_run()` (run_store.py:38-50) 硬编码 PG 列名到 Run 字段的映射。列名变更会级联破坏。

**SOP_STATUS JSON 文件结构 — 高**

kanban.py 和前端 Kanban 组件隐式依赖 SOP_STATUS JSON 的 key（completed_phases, status, progress）。

### B. 控制耦合（Control Coupling）

**EventBus priority 常量控制 Consumer 执行顺序 — 低**

各 Consumer 的 start() 中硬编码 priority 数字。AuditLogger=0, BillingHook=10, QuotaUsage=15, MetricsConsumer=20, WebhookDispatcher=30。约束仅通过注释表达。

**engine_factory 硬编码 agent name 白名单 — 中**

engine_factory.py:68-69 硬编码 6 个 agent name。新增 agent 必须手动注册。

**kanban.py 硬编码 stage_map — 中**

kanban.py:108-110 硬编码 Kanban stage 到 SOP_STATUS status 的映射。

### C. 时间耦合（Temporal Coupling）

**ExecutionService 必须先 save_event 再 publish — 高**

execution_service.py:137-138, 168-169, 199-215。如果 publish 先于 save，Consumer 读 DB 会找不到事件。

**EventBus handlers 同步执行 — 高**

publish() 在调用线程内串行执行所有 handlers。WebhookDispatcher 的 HTTP POST (timeout=10s) 会阻塞 ExecutionService 的执行线程。（publish_async 已缓解但未完全消除）

**chat.py asyncio→threading→asyncio 桥接 — 中**

chat.py:466-472。AgentLoop 在子线程中执行，通过 asyncio.Queue 桥接到 SSE。边界极其脆弱。

### D. 隐式耦合

**两个 EventBus 系统并存 — 高**

ObservationBus（Agent 层）和 EventBus（Platform 层）是完全独立的系统。PlatformBridge 做单向桥接，但反向不通。

**Singleton 全局状态 — 高**

每个模块都有 `get_xxx()` 全局单例。模块间通过全局状态隐式耦合。测试隔离困难。

**RunStore 在多个模块中共享 — 中**

QuotaUsage, ReportConsumer, Timeline, event_query 都直接注入 RunStore。Consumer 之间通过共享 Store 产生隐式数据依赖。

**ExecutionService 直接访问 loop._abort — 高**

execution_service.py:185 访问 engine 的私有属性 `_abort`。ExecutionEngine Protocol 未定义此接口。

**memory_observer 模块导入时自注册 — 中**

memory_observer.py:282-284 在 import 时调用 `_register_with_bus()`，触发副作用。

---

## 3. Event System 评估

### RunEvent 是否是 stable contract？

**否。** 理由：

1. `RunEvent.data` 是 `dict[str, Any]` — TypedDict 仅用于 IDE 提示，运行时零验证
2. `make_event()` 接受 `**data` kwargs — 无 schema 校验
3. EventType 常量只是字符串，bus 不做注册/验证
4. 每个 Consumer 自行用 `event.data.get("key", default)` 访问字段 — key 拼写错误静默失败

### EventBus 评估

| 特性 | 状态 | 证据 |
|------|------|------|
| Ordering guarantee | ✅ 有，priority 排序 | event_bus.py:145 |
| Backpressure | ❌ 无 | publish() fire-and-forget |
| Retry semantics | ❌ 无 | handler 异常被 catch+log，不重试 |
| Persistence | ❌ 无 | 纯内存，进程重启丢失 |
| Dead letter queue | ❌ 无 | 失败直接丢弃 |
| Wildcard subscription | ✅ 有 | `"*"` 通配符 |
| Thread safety | ✅ 有 | threading.Lock |
| Async dispatch | ✅ 有 (v3.0) | publish_async() + ThreadPoolExecutor |

### Consumer 独立性评估

| Consumer | 可独立运行？ | 可替换？ | 可重放？ |
|----------|------------|---------|---------|
| AuditLogger | ✅ | ✅ set_audit_logger() | ❌ |
| BillingHook | ✅ | ✅ 注入 | ⚠️ JSONL 可重读 |
| MetricsConsumer | ✅ | ✅ 注入 | ❌ 内存态 |
| QuotaUsage | ⚠️ 依赖 RunStore | ✅ 注入 | ❌ 内存态 |
| WebhookDispatcher | ✅ | ✅ 注入 | ❌ 无重试 |
| ReportConsumer | ⚠️ 依赖 RunStore+Timeline | ✅ 注入 | ⚠️ 文件持久化 |

---

## 4. Execution Path Trace

```
Browser (chat.ts)
  │  POST /api/chat/sessions/{id}/messages  ──── HTTP ────
  ▼
FastAPI (chat.py:250)
  │  parse_intent() → "run_sop" | "run_agent"
  │  创建 ChatSession, get_engine()
  │  asyncio.Queue(maxsize=256)  ← backpressure
  ▼
asyncio.create_task(_run_agent_producer)  ──── async Task ────
  │  asyncio.to_thread(engine.run_interactive())  ← 跨线程
  ▼
engine.run_interactive()  ──── 子线程 ────
  │  yield AgentEvent(type="skill_start", ...)
  │  yield AgentEvent(type="skill_chunk", ...)
  │  yield AgentEvent(type="agent_end", ...)
  ▼
agent_event_generator()  ──── 回到 async ────
  │  map_agent_event(event) → SSE dict  ← UIProjection
  │  yield {"event": "ui.skill_started", "data": "{...}"}
  ▼
EventSourceResponse  ──── SSE ────→  Browser (chat.ts sseStart)
  │  es.addEventListener("ui.skill_started", ...)
  ▼
Zustand Store (chat.ts)  →  React UI 更新

═══════════════════════════════════════════════════════════════

Parallel path: Execution API (execution.py)
  │  POST /api/workspaces/{ws_id}/executions
  ▼
ExecutionService.execute()  ──── 同步，在 asyncio.to_thread 中 ────
  │  1. ctx.require("execute")
  │  2. ExecutionRequest(created)
  │  3. store.save_event(ev_requested) ──── PG write ────
  │  4. bus.publish_async(ev_requested) ──── 混合同步/异步 ────
  │     ├─ AuditLogger._on_event (priority=0, sync) → deque
  │     ├─ BillingHook (priority=10, sync) → skip (不是 completed)
  │     ├─ MetricsConsumer (priority=20, sync) → skip
  │     └─ WebhookDispatcher._on_event (priority=30, async) → HTTP POST
  │  5. Run(created)
  │  6. store.save_run(run)
  │  7. bus.publish_async(ev_started)
  │  8. engine.run() ← 执行
  │  9. run.complete()
  │  10. store.save_run(run)
  │  11. bus.publish_async(ev_completed)
  │     ├─ AuditLogger → deque → flush线程(2s) → PG
  │     ├─ BillingHook → billing.jsonl
  │     ├─ MetricsConsumer → 内存计数
  │     ├─ QuotaUsage → 内存计数 + RunStore交叉验证
  │     ├─ ReportConsumer → RunStore + Timeline → JSON file
  │     └─ WebhookDispatcher → HTTP POST (async)
  │  12. return ExecutionResult
  ▼
API 返回 JSON

═══════════════════════════════════════════════════════════════

ObservationBus path (独立总线)
  │  ObservationEvent(type=SKILL_FAILED, data={...})
  ▼
  ├─ PlatformBridge → RunEvent on platform EventBus
  ├─ MemoryObserver → counters.json → ChromaDB
  └─ MemoryConsumer → TestingMemoryStore
```

### 同步/异步边界

| 边界 | 类型 | 风险 |
|------|------|------|
| FastAPI → asyncio.to_thread(ExecutionService.execute) | async→sync | 正确 |
| FastAPI → asyncio.to_thread(engine.run_interactive) | async→sync | 正确 |
| Agent子线程 → asyncio.Queue.put_nowait() | sync→async | 脆弱 |
| EventBus.publish_async() → ThreadPoolExecutor | sync→async | 无 backpressure |
| AuditLogger → deque → flush线程 | 异步批量 | 正确 |
| terminal.py → call_soon_threadsafe → asyncio.Queue | sync→async | 队列满时丢数据 |

### Hidden Coupling

1. chat.py 直接构造 engine（通过 factory，但 factory 内部 import 具体类）
2. ExecutionService 访问 engine._abort（私有属性）
3. 两个 EventBus 系统之间通过 3 个 Bridge 单向连接
4. ObservationBus 和 EventBus 完全隔离

---

## 5. 解耦评分

| 维度 | 分数 | 理由 |
|------|------|------|
| **模块边界清晰度** | 7/10 | Run/RunEvent/ExecutionRequest 有清晰的 dataclass 边界。ExecutionService 是好的编排层。但 API 层直接 import 具体实现类，kanban.py 直接读写文件。 |
| **事件系统解耦程度** | 5/10 | EventBus 有 priority、weakref、thread-safety、async dispatch。但：两个 bus 系统并存，event data 无 schema 验证，无重试/重放/persistence。 |
| **Consumer 独立性** | 6/10 | 每个 Consumer 有 start/stop 生命周期、可注入 bus。但 QuotaUsage 和 ReportConsumer 直接依赖 RunStore，不是纯事件驱动。 |
| **状态集中程度** | 5/10 | RunStore(PG) 是好的集中存储。但 BillingHook 写 JSONL、MetricsConsumer 内存态、WebhookRegistry 写 JSON、kanban 写 SOP_STATUS 文件——状态分散在 6+ 个存储后端。 |
| **可替换性（pluggability）** | 6/10 | set_bus(), set_run_store(), set_audit_logger() 提供了注入点。RunEventConsumer Protocol 定义了接口。但 singleton 模式让替换只能在启动时发生。 |

### **总评分：5.8 / 10**

---

## 6. 最终判定

> **👉 "这个系统是否已经达到了 plugin-like architecture（插件化架构）？"**

## **NO**

**理由：**

1. **Event contract 是隐式的。** `RunEvent.data` 是 `dict[str, Any]`，Consumer 通过硬编码字符串 key 访问字段。没有运行时 schema 验证，没有 event registry，没有 versioning。

2. **同步 EventBus 是致命瓶颈。** `publish()` 在调用线程内同步执行所有 handlers。WebhookDispatcher 做 HTTP POST 会阻塞 ExecutionService。publish_async 已缓解但未完全消除。

3. **Consumer 不是真正的独立进程。** 它们共享同一个进程、同一个 EventBus singleton、同一个 RunStore singleton。一个 Consumer 的崩溃直接影响其他 Consumer。

4. **两个 EventBus 系统并存。** ObservationBus 和 EventBus 是完全独立的系统，通过 3 个 Bridge 做单向桥接。不是统一的事件基础设施。

5. **Singleton 全局状态取代了依赖注入。** 虽然每个模块都提供了 `set_xxx()` 注入点，但实际使用中全部通过 `get_xxx()` 全局获取。

6. **执行路径有硬依赖。** ExecutionService 通过 engine_factory 获取 engine，但直接访问 engine._abort 私有属性。ExecutionEngine Protocol 不完整。

**系统已经具备了插件化的骨架**（RunEventConsumer Protocol、EventBus priority、dependency injection points），但**骨架上长了肉**（同步执行、隐式 contract、singleton 全局状态、硬编码 import）。它是一个设计良好的**模块化单体**，不是插件化架构。
