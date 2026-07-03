# AITest Platform 架构总览

> 版本: v3.2 | 日期: 2026-07-03
> 前置: Architecture Cleanup Sprint 完成

---

## 1. 系统定位

AITest Platform 是一个 **AI 测试自动化 Agent Native 平台**。

核心能力：
- 8 个测试 Agent 的 SOP 编排
- 9 个开发 Agent 的 Dev SOP
- 实时 SSE 聊天工作台
- 事件驱动的审计、计费、指标、Webhook

---

## 2. 分层架构

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React 18)                   │
│              aitest/web/src/ (Zustand + SSE)             │
└──────────────────────────┬──────────────────────────────┘
                           │ HTTP / SSE / WebSocket
┌──────────────────────────▼──────────────────────────────┐
│                    Server API Layer                       │
│         aitest/server/api/ (FastAPI endpoints)            │
│  execution.py | chat.py | kanban.py | terminal.py | ...  │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                   Platform Layer                         │
│              aitest/platform/ (核心业务)                  │
│                                                          │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │ ExecutionSvc │  │  EventBus    │  │  RunStore      │ │
│  │  (编排层)    │  │  (事件总线)  │  │  (持久化)      │ │
│  └──────┬──────┘  └──────┬───────┘  └────────────────┘ │
│         │                │                               │
│  ┌──────▼──────┐  ┌──────▼───────┐  ┌────────────────┐ │
│  │ EngineFactory│  │  Consumers   │  │  ConfigRegistry│ │
│  │  (引擎工厂) │  │  (事件消费)  │  │  (配置中心)    │ │
│  └─────────────┘  └──────────────┘  └────────────────┘ │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                    Infra Layer                           │
│              aitest/infra/ (基础设施)                     │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ database  │  │   sql    │  │  paths   │  │ config │ │
│  │ (PG/SQLite)│  │ (参数化) │  │ (路径)   │  │ (注册) │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  cache   │  │  metrics │  │ security │  │ logging│ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└──────────────────────────┬──────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────┐
│                  alice-engine (SDK)                       │
│          packages/alice-engine/alice_engine/              │
│                                                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ executor │  │ planner  │  │ task     │  │ skill  │ │
│  │ (AgentLoop)│  │ (规划器) │  │ (数据结构)│  │ (加载) │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ workflow │  │ provider │  │ security │             │
│  │ (SOP图)  │  │ (LLM)    │  │ (安全)   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Import 方向规则

```
server/api  →  platform  →  infra  →  runtime
                ↓
            alice-engine
```

| 方向 | 状态 |
|------|------|
| `server` → `platform` | ✅ 允许 |
| `platform` → `infra` | ✅ 允许 |
| `infra` → `runtime` | ✅ 允许 |
| `infra` → `platform` | ❌ 禁止 (已修复，15→0) |
| `platform` → `server` | ❌ 禁止 |
| `alice-engine` → `aitest` | ❌ 禁止 |

---

## 4. 核心执行链路

### 4.1 Execution API

```
POST /api/workspaces/{ws_id}/executions
  │
  ▼
ExecutionService.execute(ctx, module, pages, agent)
  │
  ├─ 1. ctx.require("execute")           — 权限检查
  ├─ 2. ExecutionRequest(created)         — 创建请求
  ├─ 3. store.save_event(ev_requested)    — 持久化事件到 PG
  ├─ 4. bus.publish_async(ev_requested)   — 异步派发
  │     ├─ AuditLogger (priority=0, sync) → PG audit_entries
  │     ├─ BillingHook (priority=10, sync) → billing.jsonl
  │     ├─ MetricsConsumer (priority=20, sync) → memory + PG metrics_daily
  │     └─ WebhookDispatcher (priority=30, async) → HTTP POST
  │
  ├─ 5. Run(created)                      — 创建执行记录
  ├─ 6. store.save_run(run)               — 持久化
  ├─ 7. bus.publish_async(ev_started)     — 通知开始
  │
  ├─ 8. engine = get_engine(agent)        — 工厂获取引擎
  ├─ 9. engine.run()                      — 执行
  │     └─ AgentLoop: Perceive → Plan → Act → Observe → Update
  │
  ├─ 10. run.complete(tokens, cost)       — 标记完成
  ├─ 11. store.save_run(run)              — 持久化
  ├─ 12. bus.publish_async(ev_completed)  — 通知完成
  │
  └─ return ExecutionResult
```

### 4.2 Chat SSE

```
POST /api/chat/sessions/{id}/messages
  │
  ▼
GET /api/chat/sessions/{id}/stream/{mid}  (SSE)
  │
  ▼
parse_intent(content) → "run_agent" | "run_sop" | "chat"
  │
  ├─ "run_agent": get_engine(agent_name)
  ├─ "run_sop": get_engine("sop")
  └─ "chat": LLM stream_complete
  │
  ▼
engine.run_interactive() → yield AgentEvent
  │
  ▼
map_agent_event(event) → SSE dict
  │
  ▼
EventSourceResponse → Browser
  │
  ▼
chat.ts: es.addEventListener("ui.xxx", handler) → Zustand store → React UI
```

---

## 5. 事件系统

### 5.1 两个 EventBus

| 系统 | 用途 | 事件类型 | 文件 |
|------|------|---------|------|
| **Platform EventBus** | Run 生命周期 | RunEvent (10 types) | `platform/event_bus.py` |
| **ObservationBus** | Agent 内部观测 | ObservationEvent (20 types) | `platform/observation_bus.py` |

桥接：
- `PlatformBridge`: ObservationBus → Platform EventBus
- `GovernanceBridge`: Governance events → Platform EventBus
- `EngineEventBusAdapter`: Engine events → Platform EventBus

### 5.2 RunEvent 类型

```python
class EventType:
    EXECUTION_REQUESTED = "execution.requested"
    EXECUTION_QUEUED    = "execution.queued"
    EXECUTION_STARTED   = "execution.started"
    PHASE_STARTED       = "phase.started"
    PHASE_COMPLETED     = "phase.completed"
    ARTIFACT_CREATED    = "artifact.created"
    RUN_COMPLETED       = "run.completed"
    RUN_FAILED          = "run.failed"
    RUN_CANCELLED       = "run.cancelled"
    COST_RECORDED       = "cost.recorded"
```

### 5.3 Event Data Key 常量

```python
class EventDataKey:
    MODULE = "module"
    AGENT = "agent"
    WORKSPACE_ID = "workspace_id"
    ORG_ID = "org_id"
    TOTAL_TOKENS = "total_tokens"
    TOTAL_COST = "total_cost"
    ERROR = "error"
    PHASE = "phase"
    # ... 共 16 个
```

### 5.4 Consumer 优先级

```
priority=0   AuditLogger      (sync, 通配符 "*")
priority=10  BillingHook      (sync)
priority=15  QuotaUsage       (sync)
priority=20  MetricsConsumer  (sync)
priority=20  ReportConsumer   (sync)
priority=30  WebhookDispatcher (async via ThreadPoolExecutor)
```

### 5.5 EventBus 持久化 + 去重

```
EventBus.publish_async()
  ├─ _log_event() → PG event_log 表 (append-only)
  ├─ sync handlers (priority < 30)
  └─ async handlers (priority >= 30) → ThreadPoolExecutor

Consumer 去重:
  PG seen_events 表 (event_id, consumer_name) → 跨重启持久化

崩溃恢复:
  event_replay.replay_for_consumer(consumer_name, handler)
  → 从 event_log 重放未处理事件
  → consumer_offsets 表追踪每个 consumer 的进度
```

---

## 6. 数据存储

| 数据 | 存储 | 文件 |
|------|------|------|
| Run / RunEvent / ExecutionRequest | PG (runs, run_events, execution_requests) | `platform/run_store.py` |
| Audit entries | PG (audit_entries) | `platform/audit_log.py` |
| Event log | PG (event_log) | `platform/event_bus.py` |
| Consumer offsets | PG (consumer_offsets) | `platform/event_replay.py` |
| Seen events (dedup) | PG (seen_events) | `platform/event_replay.py` |
| Metrics daily | PG (metrics_daily) | `platform/hooks/metrics_consumer.py` |
| Webhook registrations | PG (webhook_registrations) | `platform/hooks/webhook.py` |
| Tasks | PG (tasks) | `infra/task_queue.py` |
| Bugs | PG (bugs) | `testing/bug_history.py` |
| Billing records | JSONL (billing.jsonl) | `platform/hooks/billing_hook.py` |
| Chat sessions | PG (chat_sessions) + localStorage (cache) | `server/session_store.py` |
| Workspace | JSON files | `platform/workspace.py` |
| Organization | JSON files | `platform/organization.py` |

---

## 7. DI 模式

```python
# main.py lifespan — 创建共享实例
app.state.execution_service = ExecutionService()
app.state.run_store = get_run_store()
app.state.event_bus = get_bus()
app.state.audit_logger = get_audit_logger(bus=bus)
# ... 所有 consumer

# API 端点 — DI 优先
def _get_from_state(request, attr, factory):
    obj = getattr(request.app.state, attr, None)
    return obj if obj else factory()

# 模块内部 — fallback
self._store = store or get_run_store()
```

---

## 8. 公共 API (已冻结)

| 模块 | `__all__` 导出 |
|------|---------------|
| `execution_service.py` | ExecutionService, ExecutionResult |
| `event_bus.py` | EventBus, get_bus, set_bus, reset_bus, priority 常量 |
| `run_event.py` | RunEvent, EventType, EventDataKey, make_event, EVENT_SCHEMAS |
| `run_store.py` | RunStore, get_run_store, set_run_store, reset_run_store |
| `audit_log.py` | AuditLogger, get_audit_logger, set_audit_logger, reset_audit_logger |
| `consumer.py` | RunEventConsumer |
| `engine_factory.py` | ExecutionEngine, get_engine, register_engine |

---

## 9. 目录结构

```
aitest/
├── infra/                    # 基础设施层 (无 platform 依赖)
│   ├── sql.py                # 统一参数化查询
│   ├── config_registry.py    # 集中配置中心
│   ├── paths.py              # 路径解析
│   ├── database.py           # PG/SQLite 自动检测
│   ├── database_pg.py        # PostgreSQL 后端
│   ├── database_sqlite.py    # SQLite 后端
│   ├── task_queue.py         # 任务队列
│   ├── cache_layer.py        # 缓存层
│   ├── metrics.py            # Prometheus 指标
│   ├── security.py           # 安全模块
│   └── logging.py            # 结构化日志
│
├── platform/                 # 平台层 (核心业务)
│   ├── run.py                # Run 数据结构
│   ├── run_event.py          # RunEvent + EventType + EventDataKey
│   ├── execution_request.py  # ExecutionRequest 数据结构
│   ├── execution_service.py  # 编排层 (API→Run)
│   ├── event_bus.py          # EventBus (持久化 + async)
│   ├── event_replay.py       # 事件重放 + PG 去重
│   ├── run_store.py          # Run/Event PG 持久化
│   ├── audit_log.py          # 审计日志 (同步写 PG)
│   ├── consumer.py           # RunEventConsumer Protocol
│   ├── engine_factory.py     # 执行引擎工厂
│   ├── config_registry.py    # 配置中心 (re-export from infra)
│   ├── hooks/                # 事件消费者
│   │   ├── billing_hook.py   # 计费 (billing.jsonl)
│   │   ├── metrics_consumer.py # 指标 (PG metrics_daily)
│   │   ├── quota_usage.py    # 配额 (内存 + PG)
│   │   ├── webhook.py        # Webhook (HTTP POST)
│   │   └── report_consumer.py # AI 报告 (JSON files)
│   ├── observation_bus.py    # Agent 观测事件总线
│   ├── workspace.py          # 工作空间管理
│   ├── organization.py       # 组织管理
│   ├── tenant.py             # 租户管理
│   └── ownership.py          # 生命周期所有权
│
├── server/                   # 服务层
│   ├── main.py               # FastAPI 入口 + lifespan
│   ├── auth.py               # 认证中间件
│   ├── session_store.py      # 会话持久化
│   ├── api/                  # API 端点
│   │   ├── execution.py      # 执行 API
│   │   ├── chat.py           # 聊天 SSE
│   │   ├── kanban.py         # Kanban WebSocket
│   │   ├── terminal.py       # Agent Terminal WS
│   │   └── ...
│   └── core/                 # 核心服务
│       ├── subscribers.py    # Consumer 激活
│       ├── health.py         # 健康检查
│       ├── sweep.py          # 生命周期清扫
│       └── audit_scheduler.py # 定时审计
│
├── agents/                   # Agent 定义
├── graphs/                   # SOP 图
├── knowledge/                # 知识库
├── chat/                     # 聊天意图解析
└── web/                      # React 前端
    └── src/
        ├── api/
        │   ├── sse-events.ts   # SSE 事件常量
        │   └── ws-events.ts    # WS 事件定义
        └── stores/
            └── chat.ts         # 聊天状态管理

packages/
└── alice-engine/             # SDK 包
    └── alice_engine/
        ├── core/
        │   ├── executor.py     # AgentLoop
        │   ├── task.py         # AgentState, AgentEvent, AgentEventProtocol
        │   ├── planner.py      # 规划器
        │   ├── skill_loader.py # Skill 加载
        │   └── skill_registry.py # Skill 注册
        ├── workflow/
        │   ├── sop_runner.py   # SOP 执行器
        │   └── state.py        # SOP 状态
        └── providers/          # LLM Provider

docs/
├── architecture/
│   ├── 00-ARCHITECTURE_OVERVIEW.md  # 本文档
│   └── Architecture_Freeze_v1.1.md  # 冻结定义
└── audit/
    ├── MODULE_DECOUPLING_AUDIT.md   # 解耦审计报告
    └── HIDDEN_COUPLING_POINTS.md    # 隐性耦合清单
```

---

## 10. 测试

```bash
pytest tests/ -v  # 87 tests
```

| 测试文件 | 覆盖 | tests |
|---------|------|-------|
| `test_sql_parameterization.py` | SQL 注入防护 | 29 |
| `test_event_schema.py` | EventDataKey 验证 | 16 |
| `test_event_bus_improvements.py` | EventBus 改进 | 8 |
| `test_di_injection.py` | DI 注入验证 | 22 |
| `test_config_registry.py` | 配置中心验证 | 12 |
