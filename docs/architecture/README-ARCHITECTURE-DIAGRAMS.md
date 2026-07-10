# AITest Platform 架构图文档

> 版本: v1.0 | 日期: 2026-07-09
> 格式: draw.io (可使用 draw.io、diagrams.net 或 VS Code draw.io 插件打开)

---

## 📋 架构图概览

本项目包含 **5 张核心架构图**，全面覆盖 AITest Platform 的各个层面：

| 序号 | 架构图 | 文件名 | 说明 |
|------|--------|--------|------|
| 1 | **整体架构** | `AITest-Architecture-Overall.drawio` | 项目分层架构，从前端到基础设施的完整视图 |
| 2 | **SDK 包架构** | `AITest-Architecture-SDK.drawio` | 三个 SDK 包的内部结构和依赖关系 |
| 3 | **平台层架构** | `AITest-Architecture-Platform.drawio` | aitest/platform/ 的详细模块组织 |
| 4 | **事件驱动架构** | `AITest-Architecture-Events.drawio` | 事件系统、总线、消费者和持久化机制 |
| 5 | **执行链路** | `AITest-Architecture-Execution-Flow.drawio` | 核心执行流程和 AgentLoop 工作流 |
| 6 | **LLM Provider** | `AITest-Architecture-LLM-Provider.drawio` | LLM 集成层、Provider 体系和上下文管理 |

---

## 🏗️ 1. 整体架构 (Overall Architecture)

**文件**: `AITest-Architecture-Overall.drawio`

**内容**:
- **Frontend Layer**: React 18 + Zustand + SSE 实时通信
- **Server API Layer**: FastAPI + 认证中间件 + 会话管理
- **Platform Layer**: 核心业务逻辑，包括执行编排、事件系统、智能路由
- **Infra Layer**: 基础设施层，数据库、缓存、安全、监控
- **SDK Layer**: 三个 SDK 包 (alice-engine, alice-governance, alice-discovery)
- **External Systems**: LLM Providers, ChromaDB, PostgreSQL, LangGraph, Selenium

**关键依赖方向**:
```
server → platform → infra → SDK (单向依赖)
```

---

## 📦 2. SDK 包架构 (SDK Architecture)

**文件**: `AITest-Architecture-SDK.drawio`

**内容**:

### alice-engine (运行时引擎 SDK)
- **core/**: AgentLoop, AgentState, AgentEvent, Planner, SkillLoader
- **workflow/**: SOPRunner, SOP 状态机
- **providers/**: LLMProvider, ReliableProvider
- **其他**: adapters, audit, runtime, extensions

### alice-governance (治理 SDK)
- **agents/**: 8 个测试 Agent + 9 个开发 Agent 定义
- **skills/**: 24 个测试 Skill + 32 个开发 Skill 提示
- **context/ & knowledge/**: 共享语言、业务术语、知识库
- **validators/**: 验证器
- **sop_dev/**: 开发 SOP

### alice-discovery (发现 SDK)
- **schema/**: 数据结构定义、来源追踪
- **source/**: 源码分析、文件索引、框架检测、后端检测
- **extractors/**: Vue 组件、Vue 路由、API 提取器

**依赖关系**:
```
alice-engine → alice-governance (单向依赖)
```

---

## 🎯 3. 平台层架构 (Platform Architecture)

**文件**: `AITest-Architecture-Platform.drawio`

**内容**:

### 执行核心 (Execution Core)
- `execution_service.py`: ExecutionService, 编排层核心
- `execution_request.py`: 执行请求数据结构
- `run.py`: Run 执行记录
- `run_store.py`: PG 持久化 (11 张表)
- `engine_factory.py`: 引擎工厂
- `execution_worker.py`: 异步执行工作器

### 事件系统 (Event System)
- `event_bus.py`: EventBus, 持久化 + 去重
- `run_event.py`: RunEvent + EventType (10 types) + EventDataKey (16 keys)
- `event_replay.py`: 事件重放、崩溃恢复
- `observation_bus.py`: ObservationBus, Agent 内部观测 (20 types)
- `consumer.py`: RunEventConsumer Protocol

### 智能路由 (Intelligence)
- `capability_router/`: CapabilityRouter, 8 Capabilities × 8 Agents
- `complexity/`: 18 因子评分, 3 档 SOP 路由 (SIMPLE/STANDARD/COMPLEX)
- `testing_memory.py`: TestingMemory, 8 种 Memory 类型
- `testing_memory_store.py`: 类型化 ChromaDB CRUD
- `memory_observer.py`: MemoryObserver, Signal 观测

### 事件消费者 (Event Consumers / Hooks)
- `audit_log.py`: AuditLogger (priority=0, sync, 通配符 *)
- `hooks/billing_hook.py`: BillingHook (priority=10, sync)
- `hooks/metrics_consumer.py`: MetricsConsumer (priority=20, sync)
- `hooks/quota_usage.py`: QuotaUsage (priority=15, sync)
- `hooks/report_consumer.py`: ReportConsumer (priority=20, sync)
- `hooks/webhook.py`: WebhookDispatcher (priority=30, async)

### 治理桥接 (Governance Bridge)
- `governance_bridge.py`: GovernanceBridge
- PlatformBridge: ObservationBus → Platform EventBus
- EngineEventBusAdapter: Engine events → Platform EventBus
- `plugin.py`: PluginManager

### 生命周期 & 运维 (Lifecycle)
- `ownership.py`: 所有权管理
- `workspace.py`: 工作空间管理
- `organization.py`: 组织管理
- `tenant.py`: 租户管理
- `scheduler.py`: 定时任务
- `versioning.py`: 版本管理

**统计**: 50+ Python 文件 | 11 张 PG 表 | 10 种 RunEvent | 20 种 ObservationEvent | 6 个 Event Consumer | 2 个 EventBus | 3 个 Bridge

---

## 🔄 4. 事件驱动架构 (Event-Driven Architecture)

**文件**: `AITest-Architecture-Events.drawio`

**内容**:

### 事件源 (Event Sources)
- Execution API
- Chat API
- AgentLoop
- SOP Runner
- Memory System

### 事件总线 (Event Buses)
- **EventBus (Platform)**: RunEvent (10 types), PG 持久化 + 去重, priority 排序
- **ObservationBus**: ObservationEvent (20 types), Agent 内部信号

### 桥接器 (Bridges)
- GovernanceBridge: 治理事件桥接
- PlatformBridge: 观测 → 平台桥接
- EngineEventBusAdapter: 引擎事件适配
- Event Replay: 崩溃恢复 + 重放

### 事件消费者 (Event Consumers)
- **AuditLogger**: priority=0 (sync), 通配符 *, → PG audit_entries
- **BillingHook**: priority=10 (sync), → billing.jsonl
- **QuotaUsage**: priority=15 (sync), 内存 + PG
- **MetricsConsumer**: priority=20 (sync), → PG metrics_daily
- **ReportConsumer**: priority=20 (sync), → JSON files
- **WebhookDispatcher**: priority=30 (async), ThreadPoolExecutor, → HTTP POST

### 持久化存储 (Storage)
- **PostgreSQL**: runs, run_events, execution_requests, event_log, seen_events, consumer_offsets, audit_entries, metrics_daily, webhook_registrations, tasks, bugs, chat_sessions
- **JSONL**: billing.jsonl
- **JSON**: workspace.json, organization.json, AI Reports

### 事件类型 (Event Types)
- **RunEvent (10 types)**: EXECUTION_REQUESTED, EXECUTION_QUEUED, EXECUTION_STARTED, PHASE_STARTED, PHASE_COMPLETED, ARTIFACT_CREATED, RUN_COMPLETED, RUN_FAILED, RUN_CANCELLED, COST_RECORDED
- **ObservationEvent (20 types)**: STEP_STARTED, STEP_COMPLETED, STEP_FAILED, TOOL_INVOKED, TOOL_RESULT, LLM_REQUEST, LLM_RESPONSE, MEMORY_STORED, MEMORY_RETRIEVED, CONTEXT_INJECTED, ARTIFACT_GENERATED, DECISION_MADE, ERROR_OCCURRED...

**核心特性**: PG 持久化 | 事件去重 (seen_events) | 崩溃恢复 (replay) | Priority 排序 | Sync/Async 分离 | Bridge 桥接

---

## ⚡ 5. 执行链路 (Execution Flow)

**文件**: `AITest-Architecture-Execution-Flow.drawio`

**内容**:

### 执行 API 链路 (Execution API Flow)
```
POST /api/executions
  → 权限检查 ctx.require("execute")
  → 创建 ExecutionRequest
  → 持久化 store.save_event() + 异步派发 bus.publish_async()
  → Event Consumers (AuditLogger, BillingHook, MetricsConsumer, WebhookDispatcher)
  → 创建 Run, 持久化 store.save_run()
  → 获取引擎 get_engine(agent)
  → 执行 engine.run() (AgentLoop)
  → 标记完成 run.complete()
  → 返回 ExecutionResult
```

### AgentLoop 执行流程 (packages/alice-engine)
```
Perceive (感知) → Plan (规划) → Act (执行) → Observe (观测) → Update (更新)
       ↑                                                          |
       └──────────────────── Loop ←────────────────────────────────┘
```

**关键类**: AgentLoop (executor.py) | AgentState (task.py) | AgentEvent
**工作流**: SOP Runner (workflow/) | LangGraph 编排
**工具**: Native Tool Calling | Skill Loader | Capability Router
**LLM**: Provider | ReliableProvider (Retry 3x + Fallback)

### Chat SSE 链路 (Chat SSE Flow)
```
POST /api/chat/sessions/{id}/messages (创建消息)
  → GET /api/chat/sessions/{id}/stream/{mid} (SSE 连接)
  → parse_intent() 意图解析 (run_agent / run_sop / chat)
  → engine.run_interactive() yield AgentEvent
  → map_agent_event() → SSE dict
  → EventSourceResponse → Browser
  → chat.ts addEventListener() → Zustand store → React UI
```

### 关键技术栈
FastAPI (Server) | SSE (实时流) | WebSocket (双向) | LangGraph (工作流) | AgentLoop (执行引擎) | LLM Providers (Claude/DeepSeek/OpenAI/Gemini) | PostgreSQL (持久化) | ChromaDB (向量存储) | Zustand (状态管理) | React 18 (前端)

---

## 🤖 6. LLM Provider 架构 (LLM Provider Architecture)

**文件**: `AITest-Architecture-LLM-Provider.drawio`

**内容**:

### LLM Provider 层 (aitest/llm/ + packages/alice-engine/providers/)
- **LLMProvider**: 抽象接口, stream_complete(), complete()
- **ReliableProvider**: Retry (3x) + Fallback Chain, 错误恢复
- **具体 Providers**:
  - ClaudeProvider: Anthropic API, claude-sonnet-5, 主力模型
  - DeepSeekProvider: DeepSeek API, DeepSeek-V2, 成本优化
  - OpenAIProvider: OpenAI API, GPT-4o, 通用能力
  - GeminiProvider: Google API, Gemini Pro, 多模态
  - MiMoProvider: Browser-Use, 小米 MiMo, Web 自动化
- **provider_base.py**: Provider 基类, 共享逻辑
- **context_injector.py**: 上下文注入, Prompt 增强

### Context Window Manager (上下文窗口管理)
- **context_window.py**: ContextWindowManager, 85%/90% 阈值, 窗口监控
- **TokenCounter**: Token 计数, 精确计算
- **DeepSeekSummarizer**: 上下文摘要, DeepSeek 专用
- **ContextTruncator**: 上下文截断, 智能裁剪
- **ContinuationHandler**: 续写处理, 长文本分段
- **MemoryInjection**: Memory 注入, 上下文增强

**阈值策略**: 85% → DeepSeek 摘要 | 90% → 强制截断 | Memory 自动注入 | 长文本续写 | 成本优化

### Provider 特性 (Provider Features)

#### Retry 策略 (重试策略)
- 最大重试: 3 次
- 指数退避: 1s → 2s → 4s
- 可配置超时
- 错误分类: 可重试/不可重试

#### Fallback 策略 (降级策略)
- Fallback Chain: Claude → DeepSeek → OpenAI
- 自动切换
- 健康检查
- 成本优先/性能优先

#### Streaming (流式处理)
- SSE 流式响应
- 实时 Token 输出
- 中断支持
- 进度回调

#### 成本优化 (Cost Optimization)
- 成本优先路由
- Token 限制
- 缓存复用
- cost_advisor.py

### 环境配置 (.env)
```
ANTHROPIC_API_KEY | GOOGLE_API_KEY | MIMO_API_KEY | DEEPSEEK_API_KEY | OPENAI_API_KEY
BU_LLM_PROVIDER=mimo (默认, Browser-Use)
LLM_PROVIDER=claude (默认, Agent)
```

**关键类**: LLMProvider | ReliableProvider | ContextWindowManager | TokenCounter | DeepSeekSummarizer | CostAdvisor

---

## 🎨 颜色说明

| 颜色 | 含义 |
|------|------|
| 🔵 蓝色 (#dae8fc) | 接口/抽象层/前端层 |
| 🟣 紫色 (#e1d5e7) | 核心组件/执行层 |
| 🟢 绿色 (#d5e8d4) | 服务层/平台层 |
| 🔴 红色 (#f8cecc) | 基础设施/监控层 |
| 🟠 橙色 (#ffe6cc) | SDK 层/工具层 |
| 🟡 黄色 (#fff2cc) | 具体实现/功能模块 |
| ⚪ 灰色 (#f5f5f5) | 辅助模块/其他 |

---

## 📖 如何使用

### 在 draw.io 中打开
1. 访问 [draw.io](https://app.diagrams.net/)
2. 选择 "Open Existing Diagram"
3. 选择对应的 `.drawio` 文件

### 在 VS Code 中打开
1. 安装 "Draw.io Integration" 插件
2. 直接双击 `.drawio` 文件即可编辑

### 在 JetBrains IDE 中打开
1. 安装 "PlantUML Integration" 或使用内置的 draw.io 支持
2. 右键选择 "Open with draw.io"

---

## 🔗 相关文档

- `docs/architecture/00-ARCHITECTURE_OVERVIEW.md`: 架构总览文档
- `docs/architecture/Architecture_Freeze_v1.1.md`: 架构冻结定义
- `CLAUDE.md`: 项目上下文和启动指南

---

## 📝 更新日志

### v1.0 (2026-07-09)
- ✅ 创建整体架构图
- ✅ 创建 SDK 包架构图
- ✅ 创建平台层架构图
- ✅ 创建事件驱动架构图
- ✅ 创建执行链路图
- ✅ 创建 LLM Provider 架构图
- ✅ 创建架构图文档 README

---

## 🤝 贡献指南

如需更新架构图：
1. 在 draw.io 中打开对应的 `.drawio` 文件
2. 进行修改
3. 更新本 README 文档
4. 提交变更

---

**维护者**: AITest Platform Team
**最后更新**: 2026-07-09
