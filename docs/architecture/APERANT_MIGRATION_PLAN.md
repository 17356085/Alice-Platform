# Aperant → aitest 架构借鉴与迁移方案

> 分析日期: 2026-06-24 | Aperant 版本: HEAD | aitest 版本: v1.0
> 方法论: 逐模块对比，源码级映射，不独立分析 Aperant
> **v1.1**: 审阅增补 — 3 个遗漏模块 (MCP Client / Context Builder / 分层架构) + 2 个风险缓解方案

---

## 概要

Aperant (Auto Claude) — Electron 桌面应用，面向全栈应用开发的自主多 Agent 编码框架。TypeScript-first，Vercel AI SDK v6 驱动。
aitest — Python FastAPI + LangGraph 测试自动化平台，面向 Web 测试执行。

**核心差异**: Aperant 面向"代码生成"（create），aitest 面向"测试执行"（verify）。前者是创造型流水线，后者是验证型工作流。借鉴时需过滤掉代码生成生命周期，保留编排、记忆、审批三类机制。

---

# Step 1: Aperant 三大核心机制在 aitest 中的映射缺口

## 机制 1: 多角色规划-执行-合并流水线 (Multi-Role Pipeline)

### Aperant 实现全景

```
spec-orchestrator.ts          → 复杂度评估 → 分层路由 (SIMPLE/STANDARD/COMPLEX)
build-orchestrator.ts         → 阶段推进: planning → coding → qa_review → qa_fixing
subtask-iterator.ts           → 读 implementation_plan.json → 逐子任务迭代
parallel-executor.ts          → Promise.allSettled() 并发子任务执行
task-machine.ts (XState FSM)  → 显式状态转换: backlog/planning/plan_review/coding/qa_review/qa_fixing/human_review/done
```

**关键设计模式**:
- `COMPLEXITY_PHASES` 字典 — 按复杂度分层路由，不同 tier 走不同 phase 序列
- `PHASE_AGENT_MAP` — 每个 phase 绑定不同 agent type (spec_discovery → spec_writer → planner → coder → qa_reviewer → qa_fixer)
- `SubtaskIteratorConfig` — 带重试上限(3x)、stuck 检测、rate-limit 自动暂停、insight 提取
- XState `taskMachine` — 声明式状态转换 + guard 条件 (`requiresReview`, `noPlanYet`, `unexpectedExit`)
- `plan_review` 状态 — 计划完成后等待人工审批才进入 coding

### aitest 已有实现

| 文件 | 当前能力 | 对应 Aperant 模块 |
|------|---------|------------------|
| [aitest/agents/plan_engine.py](d:/Desktop/Alice/aitest/agents/plan_engine.py) | 规则+LLM 决策下一步 Skill | `subtask-iterator.ts` (弱化版) |
| [aitest/graphs/sop_graph.py](d:/Desktop/Alice/aitest/graphs/sop_graph.py) | LangGraph 定义的 SOP 执行图 | `build-orchestrator.ts` (单路径，无分层) |
| [aitest/graphs_dev/](d:/Desktop/Alice/aitest/graphs_dev/) | 9 Agent 10 Phase 开发 SOP | `spec-orchestrator.ts` + `build-orchestrator.ts` |
| [aitest/agents/scheduler.py](d:/Desktop/Alice/aitest/agents/scheduler.py) | Agent 调度 | 无直接对应 (Aperant 用 build-orchestrator 统一调度) |

### 差距

| 维度 | aitest 现状 | Aperant 做法 | 缺口等级 |
|------|------------|-------------|---------|
| 复杂度路由 | 无 — 所有模块走相同 SOP | `COMPLEXITY_PHASES` 三层路由 | **P0** |
| 多角色协作 | `plan_engine.py` 是单一决策函数 | 5 个独立 agent type 串行协作 | **P0** |
| 子任务跟踪 | 无 formal subtask tracking | `subtask-iterator.ts` 带 stuck/retry/recovery | **P0** |
| 并发执行 | [graphs/parallel_sop.py](d:/Desktop/Alice/aitest/graphs/parallel_sop.py) 有 LangGraph Send() 多页面 | `parallel-executor.ts` 有 rate-limit 感知并发 | P1 |
| 状态机 | 隐式状态 (Python if/else) | XState 声明式 FSM + guard + action | P1 |
| 人工审批关卡 | `plan_engine.py` 有 HITL `confirm_required` | `plan_review` + `human_review` 显式状态 | **P0** |

**核心定性差距**: aitest 是"单次执行"模型 — 启动 SOP → 顺序跑 Skill → 结束。Aperant 是"持续演进"模型 — 复杂度评估 → 分阶段 → 每个阶段有独立 agent → QA 验证 → 人工审批 → 合并。

### ⚠️ 语义映射: 代码生成 → 测试执行

Aperant 的 Phase-Agent 流水线面向**代码生成**（创建新代码），aitest 面向**测试执行**（验证现有系统）。移植前须完成语义重新定义:

| Aperant Phase | Aperant Agent | aitest Phase | aitest Agent | 职责重新定义 |
|--------------|---------------|-------------|-------------|------------|
| planning | planner | test_planning | test_planner | 制定测试策略，选择测试 Skill，非生成实现计划 |
| coding | coder | test_execution | test_executor | 执行测试 Skill/用例，非编写应用代码 |
| qa_review | qa_reviewer | result_validation | result_validator | 验证测试结果正确性，非代码审查 |
| qa_fixing | qa_fixer | issue_retry | issue_retry | 失败重试+策略调整，非修复被测代码 |
| human_review | N/A | test_approval | N/A | 审批测试报告/放行，非 PR 合并 |

**关键约束**:
- 在 `pipeline_router.py` 和 `task_state_machine.py` 中使用 aitest 重命名的 phase/agent，避免术语污染
- 在 `agent-definitions.yaml` 新条目中使用 `test_planner` / `test_executor` / `result_validator` / `issue_retry` 名称
- Aperant 的 `coder` agent prompt 模板**不可直接使用** — 须改写为测试执行语义

---

## 机制 2: 持久化跨会话项目记忆 (Persistent Cross-Session Memory)

### Aperant 实现全景

```
memory/memory-service.ts      → libSQL 存储 + FTS + 向量嵌入
memory/types.ts               → 15 种 MemoryType (decision/gotcha/pattern/dead_end/workflow_recipe...)
memory/injection/             → planner-memory-context.ts / step-injection-decider.ts
memory/observer/              → memory-observer.ts / dead-end-detector.ts / trust-gate.ts
context/builder.ts            → keyword 提取 → 文件搜索 → service 匹配 → pattern 发现 → memory hints
session/continuation.ts       → 90% 上下文窗口阈值 → 摘要压缩 → 新会话继续 (最多 5 次)
```

**关键设计模式**:
- `MemoryType` 包含 `decision`, `gotcha`, `dead_end`, `work_unit_outcome`, `workflow_recipe`, `task_calibration` — 不仅是知识检索，更是"经验积累"
- `MemoryRelation` — `required_with | conflicts_with | validates | supersedes | derived_from` — 知识图谱关系
- `buildPlannerMemoryContext()` — 启动前向 planner agent 注入 5 类记忆 (calibrations, deadEnds, causalDeps, outcomes, recipes)
- `step-injection-decider.ts` — 决定每个步骤注入哪些记忆
- `memory-observer.ts` — 自动观察 agent 行为，推断记忆（不依赖 agent 显式调用）
- `decayHalfLifeDays` — 记忆衰减半衰期
- `trustLevelScope` — 信任等级控制

### aitest 已有实现

| 文件 | 当前能力 | 对应 Aperant 模块 |
|------|---------|------------------|
| [aitest/knowledge/rag_engine.py](d:/Desktop/Alice/aitest/knowledge/rag_engine.py) | 知识抽取 + ChromaDB 检索 | `memory/memory-service.ts` (弱化版) |
| [aitest/platform/observation_bus.py](d:/Desktop/Alice/aitest/platform/observation_bus.py) | 事件总线 + Memory 自动同步 | `memory/observer/` (事件粒度粗) |
| [aitest/platform/testing_memory.py](d:/Desktop/Alice/aitest/platform/testing_memory.py) | 8 种 Memory 类型 | `memory/types.ts` (15 种，缺决策/死胡同/工作流配方) |
| [aitest/llm/context_window.py](d:/Desktop/Alice/aitest/llm/context_window.py) | 85%/90% 阈值 + DeepSeek 摘要 | `session/continuation.ts` (无自动继续循环) |

### 差距

| 维度 | aitest 现状 | Aperant 做法 | 缺口等级 |
|------|------------|-------------|---------|
| 决策记忆 | 无 — 每次执行重新推理 | `decision` + `work_unit_outcome` 类型，跨会话复用 | **P0** |
| 死胡同记录 | 无 | `dead_end` 类型 + 自动检测器 | **P0** |
| 工作流配方 | 无 | `workflow_recipe` 类型 — 记住哪个策略有效 | **P0** |
| 自动记忆注入 | 需 agent 显式调用 | `planner-memory-context.ts` 启动前自动注入 | P1 |
| 记忆衰减 | 无 | `decayHalfLifeDays` + `staleAt` | P2 |
| 信任门控 | 无 | `trust-gate.ts` — 低信任记忆需 review | P1 |
| 会话继续循环 | `context_window.py` 单次摘要 | `continuation.ts` 自动循环 + 最多 5 次 | P1 |

**核心定性差距**: aitest 有知识库但没有"经验记忆"。每次执行独立，不积累"上次哪种策略有效/哪种路径是死胡同"。

---

## 机制 3: 规格驱动的审批关卡 (Spec-Driven Approval Gates)

### Aperant 实现全景

```
spec/spec-validator.ts        → JSON schema 验证 + auto-fix (尾逗号/bracket修复/LLM修复)
state-machines/task-machine.ts → plan_review / human_review 显式状态
orchestration/pause-handler.ts → 文件系统 sentinel: RATE_LIMIT_PAUSE / AUTH_PAUSE / PAUSE / RESUME
renderer/stores/task-store.ts  → Zustand store 跟踪 reviewReason
renderer/stores/rate-limit-store.ts → 前端 rate-limit 倒计时 UI
```

**关键设计模式**:
- `task-machine.ts` 的 `plan_review` 状态 — `PLANNING_COMPLETE` 事件带 `requireReviewBeforeCoding: boolean` guard，决定是否需要人工审批
- `human_review` 状态 — 任务完成后进入此状态，等待用户 `MARK_DONE` 或 `CREATE_PR`
- `pause-handler.ts` — 用 **文件系统 sentinel 文件** 而非 WebSocket/数据库 做前后端通信:
  - 后端写 `PAUSE` → 前端检测 → UI 显示审批按钮
  - 前端写 `RESUME` → 后端轮询检测 → 继续执行
  - 简单、可靠、无需额外基础设施
- `spec-validator.ts` — 3 层修复: JSON 语法修复 → schema 字段补全 → LLM 修复重试

### aitest 已有实现

| 文件 | 当前能力 | 对应 Aperant 模块 |
|------|---------|------------------|
| [aitest/audit_engine/sop_auditor.py](d:/Desktop/Alice/aitest/audit_engine/sop_auditor.py) | SOP 治理审计 (被动，事后) | `spec-validator.ts` (被动 vs 主动门控) |
| [aitest/audit_engine/qa_loop.py](d:/Desktop/Alice/aitest/audit_engine/qa_loop.py) | QA 循环 (自动重试) | `build-orchestrator.ts` qa_review → qa_fixing 循环 |
| [aitest/agents/plan_engine.py:73-79](d:/Desktop/Alice/aitest/agents/plan_engine.py#L73-L79) | HITL `confirm_required` action | `task-machine.ts` plan_review 状态 |
| [aitest/server/api/chat.py](d:/Desktop/Alice/aitest/server/api/chat.py) | SSE 流式 chat | 无审批 sentinel 机制 |
| [aitest/web/src/stores/kanban.ts](d:/Desktop/Alice/aitest/web/src/stores/kanban.ts) | 看板状态 | `task-store.ts` (无 reviewReason 跟踪) |

### 差距

| 维度 | aitest 现状 | Aperant 做法 | 缺口等级 |
|------|------------|-------------|---------|
| 执行前审批 | `confirm_required` 仅标记，无 true gate | `plan_review` 状态 + guard 条件，真正阻塞 | **P0** |
| 执行后审批 | 无 | `human_review` 状态 — 完成后等待确认 | P1 |
| Pause/Resume 通信 | 无 | 文件 sentinel — 简单可靠 | **P0** |
| Schema 验证门控 | `sop_auditor.py` 事后审计 | `spec-validator.ts` 事前门控 + 自动修复 | P1 |
| 前端审批 UI | 无 | 看板 + reviewReason chip + 操作按钮 | P1 |
| Rate-limit 恢复 | 无前端联动 | `rate-limit-store.ts` 倒计时 UI + 自动切换账户 | P2 |

**核心定性差距**: aitest 有 HITL 的概念但无真正的"暂停-审批-恢复"机制。Aperant 用 sentinel 文件实现了一个极简但完整的审批闭环。

---

## 🆕 遗漏 1 (审阅增补): MCP 客户端双向通信层

> 原报告未分析 Aperant 的 `mcp/` 模块。aitest 只有 MCP Server 端，缺 Client 端能力。

### Aperant 实现全景

```
mcp/client.ts              → createMCPClient() + createMcpClientsForAgent()
mcp/registry.ts            → 6 个 MCP Server 定义 (context7/linear/memory/electron/puppeteer/auto-claude)
mcp/types.ts               → StdioTransportConfig | StreamableHttpTransportConfig
config/agent-configs.ts    → AGENT_CONFIGS: 每个 AgentType 绑定 mcpServers[] + autoClaudeTools[]
```

**关键设计模式**:
- **Per-Agent MCP Server 绑定** — `AGENT_CONFIGS[agentType].mcpServers` 声明每个 agent 需要哪些 MCP server
  ```typescript
  planner: {
    mcpServers: ['context7', 'auto-claude'],
    mcpServersOptional: ['memory', 'linear'],
    autoClaudeTools: [TOOL_UPDATE_SUBTASK_STATUS, TOOL_GET_BUILD_PROGRESS, ...],
  },
  qa_reviewer: {
    mcpServers: ['auto-claude', 'puppeteer'],  // QA 有浏览器自动化
    mcpServersOptional: ['electron'],
  }
  ```
- **双传输协议** — `stdio` (子进程) + `streamable-http` (远程 SSE)，`@ai-sdk/mcp` 统一抽象
- **优雅降级** — `Promise.allSettled()` 初始化，MCP server 连接失败不阻塞 agent 启动
- **工具合并** — `mergeMcpTools()` 将多个 MCP server 的工具合并为一个 tools object 传给 LLM
- **自定义 MCP Server** — `auto-claude` 是 Aperant 自建 MCP server，暴露 `update_subtask_status` / `record_gotcha` / `get_session_context` 等内部工具

### aitest 已有实现

| 文件 | 当前能力 | 对应 Aperant 模块 |
|------|---------|------------------|
| [aitest/mcp/__init__.py](d:/Desktop/Alice/aitest/mcp/__init__.py) | MCP Server 框架 | `auto-claude` MCP server (同向) |
| [aitest/mcp/browser_server.py](d:/Desktop/Alice/aitest/mcp/browser_server.py) | 浏览器控制 MCP Server | `puppeteer` + `electron` server |
| [aitest/mcp/tools/](d:/Desktop/Alice/aitest/mcp/tools/) | Tools 注册 | 仅本地注册，无远程调用 |
| 无 | MCP Client | `mcp/client.ts` — **完全缺失** |

### 差距

| 维度 | aitest 现状 | Aperant 做法 | 缺口等级 |
|------|------------|-------------|---------|
| MCP Client | 无 — 只能暴露 tool，不能调用外部 tool | `createMcpClientsForAgent()` per-agent 绑定 | **P1** |
| Per-Agent 工具绑定 | 所有 agent 共享同一 tool set | `AGENT_CONFIGS` 精确控制每个 agent 的工具 | P1 |
| 优雅降级 | 无 | `Promise.allSettled()` — MCP 连接失败不阻塞 | P1 |
| 内部 MCP 工具 | 无 | `auto-claude` server 暴露 session context/progress tracking | P1 |
| 双传输协议 | 仅 FastAPI HTTP | stdio + streamable-http 双模 | P2 |

**核心定性差距**: aitest 的 MCP 是"服务端思维" — 暴露 tool 给外部 AI。Aperant 的 MCP 是"客户端思维" — agent 调用外部 tool (文档查询、浏览器控制、项目管理)。aitest 的测试 agent 无法调用外部 MCP server (如 Playwright MCP、数据库 MCP)。

### 建议改造

**目标文件**: 新建 `aitest/mcp/mcp_client.py` + 修改 `aitest/agents/agent_config.py`

1. 移植 `client.ts` → `mcp_client.py` — 用 `mcp` Python SDK 实现 `create_mcp_client(server_config)` + `create_mcp_clients_for_agent(agent_type)`
2. 移植 `registry.ts` → `mcp/registry.py` — 定义 6 个 server config (保留 context7/browser/memory，新增 aitest 自建 server)
3. 移植 `agent-configs.ts` 的 `mcpServers` 字段 → `agents/agent_config.py` — 每个 agent type 声明所需 MCP servers
4. 在 `agent_runner.py` 启动时调用 `create_mcp_clients_for_agent()` 获取工具并注入 prompt

**改动规模**: 中（~200 行新建 + ~50 行修改）
**优先级**: P1（两周冲刺后追加 sprint）

---

## 🆕 遗漏 2 (审阅增补): Context Builder 作为独立"智能上下文组装器"

> 原报告将 `context/builder.ts` 列为 Memory 的附属组件，实际它是与 Memory 解耦的独立模块。

### Aperant 实现全景

```
context/builder.ts        → 6 步流水线: keyword提取→文件搜索→service匹配→分类→pattern发现→memory hints
context/keyword-extractor.ts → 从任务描述提取关键词
context/search.ts         → 基于关键词搜索项目文件
context/categorizer.ts    → 将匹配文件分为 modify/reference
context/service-matcher.ts → 匹配服务/模块
context/pattern-discovery.ts → 发现代码模式
context/graphiti-integration.ts → 最后才查 Memory (可选)
```

**关键设计模式**:
- **6 步流水线独立于 Memory** — 前 5 步仅依赖文件系统和项目索引（`project_index.json`），第 6 步才查询 Memory
- **`buildContext()` 返回 `SubtaskContext`** — 包含 `files[]`, `services[]`, `patterns[]`, `keywords[]`，直接注入 agent prompt
- **`buildTaskContext()` 返回 `TaskContext`** — 更细粒度，包含 `filesToModify[]`, `filesToReference[]`，供 planner/coder 使用
- **静态 fallback** — Memory 不可用时 (`isMemoryEnabled() === false`) 仍然返回完整的文件/服务/模式上下文，不依赖向量数据库

### aitest 已有实现

| 文件 | 当前能力 | 对应 Aperant 模块 |
|------|---------|------------------|
| [aitest/llm/context_injector.py](d:/Desktop/Alice/aitest/llm/context_injector.py) | 静态上下文注入 (~900 行) | `context/builder.ts` (弱化版 — 只做注入，不做发现) |
| [aitest/llm/skill_registry.py](d:/Desktop/Alice/aitest/llm/skill_registry.py) | Skill 注册和查找 | 无直接对应 |
| 无 | 动态文件发现 | `context/search.ts` + `context/categorizer.ts` |
| 无 | 代码模式发现 | `context/pattern-discovery.ts` |
| 无 | 项目索引 | `project_index.json` (Aperant 特有) |

### 差距

| 维度 | aitest 现状 | Aperant 做法 | 缺口等级 |
|------|------------|-------------|---------|
| 动态文件发现 | 无 — 依赖静态配置 | keyword 提取 → 文件搜索 → 相关文件列表 | P1 |
| 文件分类 | 无 | `categorizeMatches()` → modify vs reference | P1 |
| 模式发现 | 无 | `discoverPatterns()` 从参考文件中提取代码模式 | P1 |
| Memory 解耦 | context_injector 硬编码注入 | Memory 作为最后一步可选步骤 | P1 |
| 冷启动降级 | 无 | Memory 不可用时仍返回完整上下文 | **P0** (影响 Task 3) |

**核心定性差距**: aitest 的 `context_injector.py` 是"被动注入" — 把已有信息拼成 prompt。Aperant 的 `context/builder.ts` 是"主动发现" — 从任务描述出发，动态搜索相关文件、匹配服务、发现模式、查询记忆，每一步都可能发现新信息。

### 建议改造

**目标文件**: 新建 `aitest/llm/context_builder.py` + 修改 `aitest/llm/context_injector.py`

**改造方案**:
1. 新建 `context_builder.py` — 移植 6 步流水线 (适配 aitest 的测试项目结构替代 `project_index.json`)
2. 步骤 1-5 不依赖 Memory/向量数据库 — 纯文件系统操作
3. 步骤 6 可选查 Memory — 调用 `rag_engine.py` 的 `build_planner_memory_context()`
4. 修改 `context_injector.py` — 注入前先调用 `build_context()` 动态发现上下文

**改动规模**: 中（~200 行新建 + ~30 行修改）
**优先级**: P1（两周冲刺内作为 Task 3 的前置条件）

---

## 🆕 遗漏 3 (审阅增补): State-Machine / Orchestration / Communication 三层分离设计

> 原报告把 `task-machine.ts` 视为独立状态机，但未识别 Aperant 的三层分离架构模式。

### Aperant 三层分离

```
层 1: 状态定义层 (Pure Declarative)
  └── shared/state-machines/task-machine.ts     ← XState 声明，无副作用
  └── shared/state-machines/terminal-machine.ts
  └── shared/state-machines/pr-review-machine.ts

层 2: 执行引擎层 (Side-Effect Driven)
  └── ai/orchestration/build-orchestrator.ts     ← 读 FSM 状态，触发 runAgentSession()
  └── ai/orchestration/subtask-iterator.ts       ← 子任务迭代
  └── ai/orchestration/parallel-executor.ts      ← 并发执行

层 3: 通信层 (Transport Agnostic)
  └── ai/orchestration/pause-handler.ts          ← 文件 sentinel
  └── ai/session/stream-handler.ts              ← SSE/stdio 事件流
```

**关键设计模式**:
- **状态定义零依赖** — `task-machine.ts` 不引用任何 I/O、网络、文件系统 — 纯 XState 声明
- **执行引擎单向依赖状态层** — `build-orchestrator.ts` 根据 `taskMachine` 的当前状态决定下一步动作，但不修改状态定义
- **通信层独立于状态和执行** — `pause-handler.ts` 只做 sentinel 文件读写，不关心状态机内部
- **可测试性** — FSM 可独立单元测试，执行引擎可 mock FSM，通信层可 mock 文件系统

### aitest 现状

| 文件 | 当前混合情况 | 对应 Aperant 层 |
|------|-------------|----------------|
| [aitest/agents/plan_engine.py](d:/Desktop/Alice/aitest/agents/plan_engine.py) | 决策逻辑 + HITL + 状态判断混在一起 | 层 1+2 混合 |
| [aitest/agents/runner_state.py](d:/Desktop/Alice/aitest/agents/runner_state.py) | 隐式状态 (dict/Enum) | 层 1 (弱化) |
| [aitest/agent_runner.py](d:/Desktop/Alice/aitest/agent_runner.py) | AgentLoop 执行 | 层 2 |

**核心风险**: 如果按原报告 Task 4 的方案"把 task-machine.ts 直接翻译为 task_state_machine.py"，但不做三层分离，结果是又一个混合体。正确做法是:

```
新建 aitest/agents/task_state_machine.py   ← 层 1: 纯状态定义 (无副作用)
新建 aitest/agents/pipeline_router.py      ← 层 2: 读取 FSM 状态，驱动执行
新建 aitest/infra/pause_handler.py         ← 层 3: 文件 sentinel 通信
修改 aitest/agents/plan_engine.py          ← 改为查询 FSM 状态，不再内嵌决策
```

**改动规模**: 已在原 Task 4 中估算，但架构需调整为三层分离。
**优先级**: P1（在 Task 4 实现中体现）

---

## 🆕 风险缓解 (审阅增补)

### 风险 1: Sentinel 文件在多进程/分布式环境下的竞态条件

**场景**: Aperant 是单机 Electron 应用（单进程），sentinel 文件无竞态问题。aitest 是 FastAPI 多进程服务（uvicorn workers），可能同时运行多个测试任务。

| 场景 | 风险 |
|------|------|
| 两个任务并发写同一个 `governance/.data/task_id/pause.json` | 内容覆盖，任务 A 的暂停理由被任务 B 覆盖 |
| 轮询 RESUME 文件时无任务 ID 隔离 | 任务 A 写 RESUME，任务 B 误读导致提前恢复 |
| `wait_for_resume()` 轮询间隔过短 | 多任务并发时磁盘 I/O 放大 |

**缓解方案** (纳入 Task 2 验收标准):

```python
# 改为 task-specific sentinel 路径
# Before (Aperant 原版 — 单任务安全):
pause_file = ".tlo/PAUSE"

# After (aitest 适配 — 多任务安全，使用 governance/.data/ 而非 .tlo/):
pause_file = f"governance/.data/{task_id}/pause.json"   # ✅ 任务隔离，平台状态不跟随项目
resume_file = f"governance/.data/{task_id}/resume.json"

# pause_handler.py 增加 task_id 参数
def write_pause_file(project_dir: str, task_id: str, reason: str) -> None:
    task_dir = Path(project_dir) / "governance" / ".data" / task_id
    task_dir.mkdir(parents=True, exist_ok=True)
    (task_dir / "pause.json").write_text(json.dumps({
        "paused_at": datetime.now().isoformat(),
        "reason": reason,
        "task_id": task_id,  # ← 自包含，防止误读
    }))

def wait_for_resume(project_dir: str, task_id: str, timeout: int = 7200) -> bool:
    task_dir = Path(project_dir) / "governance" / ".data" / task_id
    resume_path = task_dir / "resume.json"
    # Poll with exponential backoff: 1s → 2s → 4s → ... → max 30s
    ...
```

**验收标准追加**:
- 并发运行 2 个任务，任务 A pause → 任务 B pause → 任务 A resume → 任务 A 恢复、任务 B 仍暂停
- `wait_for_resume()` 在 task_id 不匹配时不恢复
- 轮询间隔指数退避 (1s → 30s max)，减少磁盘 I/O

### 风险 2: Memory 检索的"冷启动"问题

**场景**: Aperant 的 `buildPlannerMemoryContext()` 查询 5 类记忆，当 `search()` 返回空时（新项目/无历史数据），依赖隐性策略:
1. `memory-service.ts` 返回空数组 `[]` 而非抛异常
2. `formatPlannerSections()` 对空 sections 返回空字符串 `""`
3. `buildContext()` 的步骤 1-5 (文件发现) 不依赖 Memory — Memory 只是步骤 6 的可选增强

**aitest 的风险**: `rag_engine.py` 目前无显式空结果降级逻辑。新项目冷启动时:
- `search()` 返回空 → 无任何上下文注入 → agent 从零开始推理
- 无"无记忆时用静态 fallback"机制

**缓解方案** (纳入 Task 3 实现):

```python
# rag_engine.py 增加优雅降级
def build_planner_memory_context(
    task_description: str,
    relevant_modules: list[str],
    project_id: str,
) -> str:
    try:
        calibrations = search_memories(types=['task_calibration'], ...)
        dead_ends = search_memories(types=['dead_end'], ...)
        causal_deps = search_memories(types=['causal_dependency'], ...)
        outcomes = search_memories(types=['work_unit_outcome'], ...)
        recipes = search_workflow_recipes(task_description, limit=2)
    except Exception:
        # DB not initialized / connection failed → silent fallback
        return ""

    # If all empty, return explicit hint rather than empty string
    all_empty = all(
        len(r) == 0 for r in [calibrations, dead_ends, causal_deps, outcomes, recipes]
    )
    if all_empty:
        return (
            "[Memory] No relevant project memory found. "
            "This appears to be a first-time execution for this module. "
            "Proceed with fresh reasoning — decisions will be recorded for future runs."
        )

    return format_planner_sections(calibrations, dead_ends, causal_deps, outcomes, recipes)
```

**验收标准追加**:
- 新建项目 (空 ChromaDB) 首次执行 → 返回提示文本而非空字符串
- Memory DB 不可用 (连接失败) → 返回空字符串，不抛异常阻塞执行
- 有部分记忆 (如只有 calibrations 无 dead_ends) → 只显示有数据的 section

---

# Step 2: 具体代码级别的借鉴点 (P0/P1/P2)

## 🆕 P1-新增: MCP Client 双向通信层移植

### 借鉴源

**Aperant 文件**: `mcp/client.ts` (行 74-128) — `createMcpClient()` + `createMcpClientsForAgent()`
```typescript
export async function createMcpClientsForAgent(
  agentType: AgentType,
  resolveOptions: McpServerResolveOptions = {},
  registryOptions: McpRegistryOptions = {},
): Promise<McpClientResult[]> {
  const serverIds = getRequiredMcpServers(agentType, resolveOptions);
  const serverConfigs = resolveMcpServers(serverIds, registryOptions);
  const results = await Promise.allSettled(
    serverConfigs.map((config) => createMcpClient(config)),
  );
  // Collect successful, skip failed — MCP failure is non-fatal
  ...
}
```

**Aperant 文件**: `config/agent-configs.ts` (行 177+) — Per-agent MCP server 声明
```typescript
export const AGENT_CONFIGS: Record<AgentType, AgentConfig> = {
  planner: {
    tools: [...ALL_BUILTIN_TOOLS],
    mcpServers: ['context7', 'auto-claude'],
    mcpServersOptional: ['memory', 'linear'],
    autoClaudeTools: [TOOL_UPDATE_SUBTASK_STATUS, TOOL_GET_BUILD_PROGRESS, ...],
  },
  qa_reviewer: {
    tools: [...ALL_BUILTIN_TOOLS],
    mcpServers: ['auto-claude', 'puppeteer'],  // QA gets browser automation
    mcpServersOptional: ['electron'],
  },
};
```

### 对应 aitest 改造

**目标文件**: 新建 `aitest/mcp/mcp_client.py` + 修改 `aitest/agents/agent_config.py`

**改造方案**:
1. 新建 `mcp_client.py` — 用 Python `mcp` SDK 实现 `create_mcp_clients_for_agent(agent_type) → list[McpClientResult]`
2. 移植 `registry.ts` → `mcp/registry.py` — 注册外部 MCP server (context7, browser, memory)
3. 在 `agent_config.py` 增加 `mcp_servers` 字段 — 声明每个 agent type 的 MCP server 绑定
4. 在 `agent_runner.py` 启动时调用 `create_mcp_clients_for_agent()` 获取外部 tools

**改动规模**: 中（~200 行新建 + ~50 行修改）
**优先级**: P1（两周冲刺后追加 Task 6）

---

## 🆕 P1-新增: Context Builder 独立模块 — 动态上下文发现

### 借鉴源

**Aperant 文件**: `context/builder.ts` (行 149-212) — 6 步流水线
```typescript
export async function buildContext(config: BuildContextConfig): Promise<SubtaskContext> {
  // Step 1: Determine which services to search
  const services = providedServices ?? suggestServices(taskDescription, projectIndex);
  // Step 2: Extract keywords
  const keywords = providedKeywords ?? extractKeywords(taskDescription);
  // Step 3: Search each service
  for (const serviceName of services) { ... }
  // Step 4: Categorize (modify vs reference)
  const { toModify, toReference } = categorizeMatches(allMatches, taskDescription);
  // Step 5: Discover patterns
  const rawPatterns = discoverPatterns(projectDir, toReference, keywords);
  // Step 6: Graph hints (optional, memory-dependent)
  const graphHints = includeGraphHints && isMemoryEnabled()
    ? await fetchGraphHints(taskDescription, projectDir) : [];
}
```

### 对应 aitest 改造

**目标文件**: 新建 `aitest/llm/context_builder.py` + 修改 `aitest/llm/context_injector.py`

**改造方案**:
1. 新建 `context_builder.py` — 移植 6 步流水线，前 5 步纯文件系统操作，不依赖 Memory/向量数据库
2. 步骤 6 可选调用 `rag_engine.build_planner_memory_context()`
3. 修改 `context_injector.py` — 注入前先调用 `build_context()` 动态发现

**改动规模**: 中（~200 行新建 + ~30 行修改）
**优先级**: P1（两周冲刺内作为 Task 3 前置 — Task 3a）

### 借鉴源

**Aperant 文件**: `spec-orchestrator.ts` (行 91-104)
```typescript
const COMPLEXITY_PHASES: Record<ComplexityTier, SpecPhase[]> = {
  simple:   ['quick_spec', 'validation'],
  standard: ['discovery', 'requirements', 'spec_writing', 'planning', 'validation'],
  complex:  ['discovery', 'requirements', 'research', 'context',
             'spec_writing', 'self_critique', 'planning', 'validation'],
};
```

**Aperant 文件**: `build-orchestrator.ts` (行 63-68)
```typescript
const PHASE_AGENT_MAP: Record<BuildPhase, AgentType> = {
  planning: 'planner',
  coding: 'coder',
  qa_review: 'qa_reviewer',
  qa_fixing: 'qa_fixer',
};
```

### 对应 aitest 改造

**目标文件**: `aitest/agents/plan_engine.py` + 新建 `aitest/agents/pipeline_router.py`

**改造方案**:
1. 在 `plan_engine.py` 增加 `assess_complexity()` 函数 — 复用 [aitest/platform/complexity/](d:/Desktop/Alice/aitest/platform/complexity/) 的 18 因子评分，映射为 SIMPLE/STANDARD/COMPLEX 三档
2. 新建 `pipeline_router.py` — 定义 `COMPLEXITY_PHASES` 字典，每档映射不同 Agent 序列
3. 修改 `plan_next_action()` — 不再硬编码 sequential advance，改为从 `PHASE_AGENT_MAP` 查询当前 phase 的 agent type

**改动规模**: 中（~150 行新增 + ~30 行修改）
**审批要求**: Light Review — `plan_engine.py` 在 Agent Runtime (STABLE) 层，可优化实现；`pipeline_router.py` 为新建文件
**Extension Point 评估**: Config 不可行 (需要运行时动态路由，YAML 静态配置不足); MCP 不可行 (路由是内部编排逻辑); Plugin 可行但过度设计 → 直接实现为 Agent Runtime 层模块
**涉及治理文件**: 需在 `governance/agents/agent-definitions.yaml` 新增 `test_planner` / `test_executor` / `result_validator` / `issue_retry` 条目

### 借鉴源

**Aperant 文件**: `task-machine.ts` (完整 187 行)
```typescript
plan_review: {
  on: {
    PLAN_APPROVED: { target: 'coding', actions: 'clearReviewReason' },
    USER_STOPPED: { target: 'backlog', actions: 'clearReviewReason' },
  }
},
human_review: {
  on: {
    CREATE_PR: 'creating_pr',
    MARK_DONE: 'done',
    USER_RESUMED: { target: 'coding', actions: 'clearReviewReason' },
  }
},
```

### 对应 aitest 改造

**目标文件**: `aitest/agents/runner_state.py` + 新建 `aitest/agents/task_state_machine.py`

**改造方案**:
1. 新建 `task_state_machine.py` — Python 版状态机 (用 `transitions` 库或手写)，移植 Aperant 的 9 个状态 + 30 个事件
2. 在 `runner_state.py` 增加 `task_state: TaskState` 字段
3. 修改 `plan_engine.py` — 在 `plan_review` 状态时返回 `confirm_required` 并真正阻塞执行

**改动规模**: 中（~200 行新建）
**审批要求**: Light Review — `task_state_machine.py` 新建在 Agent Runtime 层；不影响 FROZEN 接口
**Extension Point 评估**: Plugin 可行 (状态机作为 Plugin 加载) 但过度设计 → 直接实现；Config 不可行 (需要运行时事件驱动)
**涉及治理文件**: 需在 `governance/agents/agent-definitions.yaml` 新增状态定义引用

---

## P0-2: 持久化决策记忆 + 死胡同检测

### 借鉴源

**Aperant 文件**: `memory/types.ts` (行 11-30)
```typescript
export type MemoryType =
  | 'gotcha' | 'decision' | 'preference' | 'pattern'
  | 'error_pattern' | 'module_insight'
  | 'dead_end'          // ← aitest 缺失
  | 'work_unit_outcome' // ← aitest 缺失
  | 'workflow_recipe'   // ← aitest 缺失
  | 'task_calibration'; // ← aitest 缺失
```

**Aperant 文件**: `memory/injection/planner-memory-context.ts` (行 24-65)
```typescript
export async function buildPlannerMemoryContext(
  taskDescription: string,
  relevantModules: string[],
  memoryService: MemoryService,
  projectId: string,
): Promise<string> {
  const [calibrations, deadEnds, causalDeps, outcomes, recipes] =
    await Promise.all([
      memoryService.search({ types: ['task_calibration'], ... }),
      memoryService.search({ types: ['dead_end'], ... }),
      memoryService.search({ types: ['causal_dependency'], ... }),
      memoryService.search({ types: ['work_unit_outcome'], ... }),
      memoryService.searchWorkflowRecipe(taskDescription, { limit: 2 }),
    ]);
  return formatPlannerSections({...});
}
```

**Aperant 文件**: `memory/observer/dead-end-detector.ts` — 自动检测死胡同模式

### 对应 aitest 改造

**目标文件**: `aitest/platform/testing_memory.py` + `aitest/knowledge/rag_engine.py`

**改造方案**:
1. 扩展 `testing_memory.py` 的 MemoryType 枚举 — 已有 `WORKFLOW_RECIPE` (行 42)，新增 `DEAD_END`, `TASK_CALIBRATION`, `DECISION` 共 3 个类型
2. 在 `rag_engine.py` 增加 `build_planner_memory_context()` — 启动前查询 5 类记忆并格式化为 prompt 前缀
3. 新建 `aitest/platform/memory_observer.py` — 移植 Aperant 的 `dead-end-detector.ts` 逻辑: 连续 3 次同类型失败 → 自动记录 `DEAD_END` memory
4. 在 `observation_bus.py` 订阅 `SKILL_FAILED` 事件 → `memory_observer.on_skill_failed()`

**改动规模**: 大（~300 行新建 + ~50 行修改）
**审批要求**: Architecture Review Required — 涉及 `aitest/llm/rag_engine.py` (Platform Core, FROZEN) 和 `aitest/platform/testing_memory.py` (Platform Core, FROZEN)。§4.3 流程须在 PR 前完成
**Extension Point 评估**: Plugin 不可行 (memory observer 需深度集成 ObservationBus); Skill 不可行 (不是 prompt 模板); MCP 不可行 (内部状态观测) → Core 变更
**涉及治理文件**: `governance/context/shared-language.md` 需追加 `DEAD_END` / `TASK_CALIBRATION` / `DECISION` 术语；`governance/agents/agent-definitions.yaml` 无变更 (Memory Observer 是平台能力，非 Agent Skill)

---

## P0-3: Sentinel-File 审批关卡 (Pause/Resume)

### 借鉴源

**Aperant 文件**: `pause-handler.ts` (行 21-30, 113-136)
```typescript
export const RATE_LIMIT_PAUSE_FILE = 'RATE_LIMIT_PAUSE';
export const AUTH_FAILURE_PAUSE_FILE = 'AUTH_PAUSE';
export const RESUME_FILE = 'RESUME';
export const HUMAN_INTERVENTION_FILE = 'PAUSE';

export function writeRateLimitPauseFile(specDir, error, resetTimestamp): void {
  const data: RateLimitPauseData = {
    pausedAt: new Date().toISOString(),
    resetTimestamp,
    error,
  };
  writeFileSync(join(specDir, RATE_LIMIT_PAUSE_FILE), JSON.stringify(data, null, 2));
}

export async function waitForRateLimitResume(specDir, sourceSpecDir?, signal?): Promise<void> {
  // Poll every 30s for RESUME file; timeout after 2h
}
```

**Aperant 文件**: `task-machine.ts` — `plan_review` 和 `human_review` 状态

### 对应 aitest 改造

**目标文件**: `aitest/agents/plan_engine.py` + 新建 `aitest/infra/pause_handler.py` + `aitest/server/api/chat.py`

**改造方案**:
1. 新建 `aitest/infra/pause_handler.py` — 移植 sentinel 文件机制:
   - `write_pause_file(project_dir, task_id, reason)` → 写 `governance/.data/{task_id}/pause.json`
   - `wait_for_resume(project_dir, task_id, timeout)` → 轮询 `governance/.data/{task_id}/resume.json`
   - `check_pause_status(project_dir, task_id)` → 返回当前暂停状态
2. 修改 `plan_engine.py` — HITL `confirm_required` 时调用 `write_pause_file()` 真正暂停
3. 修改 `aitest/server/api/chat.py` — 增加 `POST /api/resume` 端点，写 `RESUME` 文件
4. 前端 [aitest/web/src/stores/kanban.ts](d:/Desktop/Alice/aitest/web/src/stores/kanban.ts) — 增加 `reviewReason` 字段 + 审批按钮

**改动规模**: 中（~120 行新建 pause_handler + ~50 行 API + ~60 行前端）
**审批要求**: Architecture Review Required — `aitest/server/api/chat.py` 新增端点 (FROZEN §1.2: 端点路径不可变，新增需审批); `aitest/infra/pause_handler.py` 新建 → Light Review
**Extension Point 评估**: MCP 不可行 (sentinel 是内部通信); Config 不可行 (需要运行时写文件); Plugin 过度设计 → 直接实现
**数据存储约束**: sentinel 文件写 `governance/.data/{task_id}/` 而非 `.tlo/` (ADR-001 + CONSTITUTION §3.1)

---

## P1-1: 自动会话继续循环

### 借鉴源

**Aperant 文件**: `session/continuation.ts` (行 95-120)
```typescript
export async function runContinuableSession(
  config: SessionConfig,
  options: RunnerOptions,
  continuationConfig: ContinuationConfig,
): Promise<ContinuationResult> {
  const maxContinuations = continuationConfig.maxContinuations ?? 5;
  // Loop: run session → if context_window → compact → re-run
}
```

### 对应 aitest 改造

**目标文件**: `aitest/llm/context_window.py`

**改造方案**: 将现有单次摘要逻辑包装为循环，增加 `max_continuations=5` 和 `ContinuationResult` 累积

**改动规模**: 小（~40 行修改）
**审批要求**: Architecture Review Required — `aitest/llm/context_window.py` 在 Platform Core (FROZEN)。修改为 wrapper 循环，不改变 `ContextWindowMonitor` 公开接口
**Extension Point 评估**: Config 可行但不足 (需运行时循环); Plugin 过度设计 → 直接修改 Core (轻量改动)

---

## P2-1: 前端 Rate-Limit 恢复 UI

### 借鉴源

**Aperant 文件**: `renderer/stores/rate-limit-store.ts` + `renderer/stores/auth-failure-store.ts`

### 对应 aitest 改造

**目标文件**: `aitest/web/src/stores/settings.ts` + `aitest/web/src/components/Toast.vue` (已删除，需重建)

**改动规模**: 小（~80 行）

---

# Step 3: Aperant 中"不应照搬"的部分 (避坑指南)

## 3.1 代码生成沙箱 → ❌ 不搬

**Aperant 模块**: `ai/worktree/`, `ai/merge/` (语义合并), `ai/tools/` (代码生成工具)

**原因**: aitest 是测试执行平台，不生成应用代码。worktree 隔离已由 `aitest/infra/worktree_manager.py` 覆盖测试项目隔离。语义合并 (`semantic-analyzer.ts`, `conflict-detector.ts`) 面向代码冲突解决，与测试平台无关。

**建议**: 保留现有 `worktree_manager.py`，不引入 code-gen 语义合并。

## 3.2 Electron IPC 层 → ❌ 不搬

**Aperant 模块**: `main/ipc-handlers/`, `preload/api/`

**原因**: aitest 是 Web 应用 (FastAPI + Vue)，不是 Electron 桌面应用。IPC 机制是 Electron 特有，aitest 用 HTTP/SSE/WS 已足够。

## 3.3 前端部署流水线 → ❌ 不搬

**Aperant 模块**: `.github/workflows/`, `apps/desktop/scripts/` (macOS 公证、auto-update)

**原因**: aitest 无桌面应用分发需求。CI 已有 GitHub Actions。

## 3.4 GitHub/GitLab Issue 集成 → ⚠️ 部分参考

**Aperant 模块**: `renderer/stores/github/`, `renderer/stores/gitlab/`, `ipc-handlers/github/`

**原因**: aitest 不需要 Issue 导入/PR 创建。但 `investigation-store.ts` 的 AI 调查模式可借鉴 — 类似 aitest 的缺陷分析流程。

**建议**: 参考 investigation 的 prompt 结构，但不搬整个集成层。

## 3.5 多账户轮换 → ❌ 不搬

**Aperant 模块**: `claude-profile/`, `ai/auth/codex-oauth.ts`

**原因**: aitest 已有 `aitest/llm/reliable_provider.py` 的 Retry+Fallback 机制 (claude→deepseek→openai)。多账户轮换是 Aperant 特有的 rate-limit 规避策略，aitest 的 provider fallback 已覆盖此需求。

## 3.6 复杂度评估 18 因子 → ⚠️ 已存在

**Aperant 模块**: `spec-orchestrator.ts` 的 `complexity_assessment` phase

**原因**: aitest 已有 `aitest/platform/complexity/` 18 因子评分。不需要移植 Aperant 的评估 prompt，直接复用现有评分映射为三档路由即可。

---

# Step 4: 两周冲刺计划 (Sprint Plan) — v1.1 修订

> 修订: Task 3 拆分为 3a+3b；Task 2/3 增加风险缓解验收标准；追加 Task 6 (MCP Client)。

## Week 1: 核心架构移植 (Task 1-2 + Task 3a)

### Task 1: 复杂度分层路由 (P0) — 2 天

| 项目 | 内容 |
|------|------|
| **目标** | 移植 Aperant 的 `COMPLEXITY_PHASES` 三档路由到 aitest |
| **涉及文件** | [aitest/agents/plan_engine.py](d:/Desktop/Alice/aitest/agents/plan_engine.py) (修改 ~30 行) |
| | **新建** [aitest/agents/pipeline_router.py](d:/Desktop/Alice/aitest/agents/pipeline_router.py) (~120 行) |
| | [aitest/agents/runner_state.py](d:/Desktop/Alice/aitest/agents/runner_state.py) (修改 ~20 行) |
| | [aitest/platform/complexity/](d:/Desktop/Alice/aitest/platform/complexity/) (引用现有 18 因子) |
| **改动规模** | 中 |
| **验收标准** | `aitest graph run --module=<m>` 对 simple/standard/complex 模块走不同 phase 序列 |
| | 复用现有 18 因子评分 → 映射 SIMPLE/STANDARD/COMPLEX，不引入新评估 prompt |

### Task 2: Sentinel-File Pause/Resume 机制 (P0) — 2 天

| 项目 | 内容 |
|------|------|
| **目标** | 移植 Aperant 的 `pause-handler.ts` sentinel 文件审批闭环，**增加多任务隔离** |
| **涉及文件** | **新建** [aitest/infra/pause_handler.py](d:/Desktop/Alice/aitest/infra/pause_handler.py) (~150 行，含 task_id 隔离) |
| | [aitest/agents/plan_engine.py](d:/Desktop/Alice/aitest/agents/plan_engine.py) (修改 ~40 行 — HITL 集成) |
| | [aitest/server/api/chat.py](d:/Desktop/Alice/aitest/server/api/chat.py) (新增 `POST /api/tasks/{id}/resume` ~30 行) |
| | [aitest/web/src/stores/kanban.ts](d:/Desktop/Alice/aitest/web/src/stores/kanban.ts) (修改 ~40 行 — reviewReason) |
| **改动规模** | 中 |
| **验收标准 (含风险缓解)** | |
| | ✅ 高风险 Skill 执行前写 `governance/.data/{task_id}/pause.json` → 前端显示审批按钮 |
| | ✅ 点击审批后写 `governance/.data/{task_id}/resume.json` → 后端继续执行 |
| | ✅ **多任务隔离**: 并发 2 任务，A pause → B pause → A resume → A 恢复、B 仍暂停 |
| | ✅ **轮询优化**: 指数退避 1s → 2s → 4s → ... → max 30s |

### Task 3a: Context Builder — 动态上下文发现 (P1, Task 3 前置) — 2 天

| 项目 | 内容 |
|------|------|
| **目标** | 移植 Aperant `context/builder.ts` 的 6 步流水线，作为独立"智能上下文组装器" |
| **涉及文件** | **新建** [aitest/llm/context_builder.py](d:/Desktop/Alice/aitest/llm/context_builder.py) (~200 行) |
| | [aitest/llm/context_injector.py](d:/Desktop/Alice/aitest/llm/context_injector.py) (修改 ~30 行 — 注入前调用 build_context) |
| **改动规模** | 中 |
| **验收标准** | |
| | ✅ 从任务描述提取关键词 → 搜索相关测试文件 → 分类 modify/reference |
| | ✅ 步骤 1-5 不依赖 Memory/向量数据库 (纯文件系统) |
| | ✅ Memory 不可用时返回完整上下文 (文件列表 + 服务匹配)，不阻塞 |
| | ✅ 步骤 6 可选调用 `rag_engine.build_planner_memory_context()` |

## Week 2: 记忆系统 + 状态机 + 继续循环 (Task 3b-5)

### Task 3b: Memory 类型扩展 + 死胡同检测 + 优雅降级 (P0) — 3 天

| 项目 | 内容 |
|------|------|
| **目标** | 增加 `DEAD_END`/`WORKFLOW_RECIPE`/`DECISION`/`TASK_CALIBRATION` 记忆类型 + 自动观测 + 冷启动降级 |
| **涉及文件** | [aitest/platform/testing_memory.py](d:/Desktop/Alice/aitest/platform/testing_memory.py) (修改 ~50 行 — 扩展 MemoryType 枚举) |
| | [aitest/knowledge/rag_engine.py](d:/Desktop/Alice/aitest/knowledge/rag_engine.py) (新增 `build_planner_memory_context()` ~80 行 + 降级逻辑) |
| | **新建** [aitest/platform/memory_observer.py](d:/Desktop/Alice/aitest/platform/memory_observer.py) (~150 行 — dead-end-detector 移植) |
| | [aitest/platform/observation_bus.py](d:/Desktop/Alice/aitest/platform/observation_bus.py) (新增订阅 ~30 行) |
| | [aitest/agents/plan_engine.py](d:/Desktop/Alice/aitest/agents/plan_engine.py) (启动时调用 context_builder + memory_context ~20 行) |
| **改动规模** | 大 |
| **验收标准 (含风险缓解)** | |
| | ✅ 连续 3 次同类型失败 → 自动写 DEAD_END → 下次 planner 收到警告 → 跳过该策略 |
| | ✅ **冷启动降级**: 新项目 (空 ChromaDB) 首次执行 → 返回 `[Memory] No relevant project memory found...` 提示文本 |
| | ✅ **DB 故障降级**: Memory DB 不可用 → 返回空字符串，不抛异常阻塞 |
| | ✅ 有部分记忆时 (如只有 calibrations) → 只显示有数据的 section |
| | ✅ `build_planner_memory_context()` 通过 `context_builder.py` 步骤 6 调用 |

### Task 4: Task 状态机 — 三层分离架构 (P1) — 2 天

| 项目 | 内容 |
|------|------|
| **目标** | 移植 Aperant `task-machine.ts` 的声明式状态机，**遵循三层分离设计** |
| **涉及文件** | **新建** [aitest/agents/task_state_machine.py](d:/Desktop/Alice/aitest/agents/task_state_machine.py) (~200 行 — **层 1**: 纯状态定义，无副作用) |
| | [aitest/agents/runner_state.py](d:/Desktop/Alice/aitest/agents/runner_state.py) (修改 ~30 行) |
| | [aitest/agents/pipeline_router.py](d:/Desktop/Alice/aitest/agents/pipeline_router.py) (修改 ~30 行 — **层 2**: 读 FSM 状态，驱动执行) |
| | [aitest/agents/plan_engine.py](d:/Desktop/Alice/aitest/agents/plan_engine.py) (修改 ~15 行 — 查询 FSM 状态，不再内嵌决策) |
| | [aitest/web/src/stores/kanban.ts](d:/Desktop/Alice/aitest/web/src/stores/kanban.ts) (状态显示 ~30 行) |
| **改动规模** | 中 |
| **验收标准** | |
| | ✅ 状态转换: `backlog → test_planning → plan_review → test_execution → result_validation → test_approval → done` |
| | ✅ **三层分离**: task_state_machine.py 零 I/O 依赖 → 可独立单元测试 |
| | ✅ pipeline_router.py 单向依赖状态机，不修改状态定义 |
| | ✅ pause_handler.py (层 3) 独立于状态机和执行引擎 |
| | ✅ **多任务隔离**: 每个 task_id 独立 FSM 实例，不共享状态 |

### Task 5: 上下文窗口自动继续循环 (P1) — 1 天

| 项目 | 内容 |
|------|------|
| **目标** | 移植 Aperant `continuation.ts` 的自动循环继续 |
| **涉及文件** | [aitest/llm/context_window.py](d:/Desktop/Alice/aitest/llm/context_window.py) (修改 ~50 行) |
| | [aitest/agent_runner.py](d:/Desktop/Alice/aitest/agent_runner.py) (包装调用 ~20 行) |
| **改动规模** | 小 |
| **验收标准** | 长 SOP 自动 compact → 继续执行，最多 5 次，超出返回 partial |

---

## 追加 Sprint (两周后): MCP Client

### Task 6: MCP Client 双向通信层 (P1) — 3 天

| 项目 | 内容 |
|------|------|
| **目标** | 移植 Aperant `mcp/client.ts` + `mcp/registry.ts`，让 aitest agent 能调用外部 MCP Server |
| **涉及文件** | **新建** [aitest/mcp/mcp_client.py](d:/Desktop/Alice/aitest/mcp/mcp_client.py) (~150 行) |
| | **新建** [aitest/mcp/registry.py](d:/Desktop/Alice/aitest/mcp/registry.py) (~80 行 — 6 个 server config) |
| | [aitest/agents/agent_config.py](d:/Desktop/Alice/aitest/agents/agent_config.py) (新增 `mcp_servers` 字段 ~50 行) |
| | [aitest/agent_runner.py](d:/Desktop/Alice/aitest/agent_runner.py) (启动时调用 `create_mcp_clients_for_agent()` ~20 行) |
| **改动规模** | 中 |
| **验收标准** | |
| | ✅ `create_mcp_clients_for_agent('qa_reviewer')` 返回 browser MCP tools |
| | ✅ MCP server 连接失败不阻塞 agent 启动 (优雅降级) |
| | ✅ stdio + streamable-http 双传输协议支持 |
| | ✅ `merge_mcp_tools()` 合并多 server tools 为一个 tool set |
| | ✅ **安全审计**: 外部 MCP 调用通过 `mcp/audit.py` 记录 (outbound rate limiting 纳入 `mcp/client_security.py`) |
| | ✅ **术语对齐**: shared-language.md 新增加 "MCP Server" / "MCP Client" 区分定义 |

---

## 总结: 移植优先级矩阵 (v1.1 修订)

```
        高影响 ───────────────────────────── 低影响
         │                                       │
   P0    │  Task 1 (路由)          Task 6 (MCP)  │
         │  Task 2 (审批+隔离)     P2            │
 高复杂度│  Task 3a (Context Builder) Rate-limit  │
         │  Task 3b (记忆+降级)    UI            │
         │                                       │
   ──────┼───────────────────────────────────────│
         │                                       │
   P1    │  Task 4 (状态机+分层)    不搬          │
         │  Task 5 (继续循环)       Code-gen     │
 低复杂度│                           IPC/Electron │
         │                           OAuth轮换    │
```

### 改动统计总览

| 指标 | 原计划 | v1.1 修订 |
|------|--------|----------|
| Task 数量 | 5 | 6 (Task 6 追加 sprint) |
| 新建文件 | 5 | 8 |
| 新增代码 | ~750 行 | ~1,100 行 |
| 修改代码 | ~300 行 | ~360 行 |
| Sprint 总天数 | 10 | 12 (Week 1: 6d, Week 2: 6d) |

**关键原则**:
1. **只搬"编排、记忆、审批、MCP"四类机制** — Aperant 的代码生成、桌面分发、GitHub 集成不搬
2. **Sentinel 文件 + task_id 隔离** — 多进程安全，文件系统操作无额外基础设施
3. **三层分离** — 状态定义/执行引擎/通信层解耦，可独立测试
4. **优雅降级优先** — Memory 冷启动、MCP 连接失败、DB 不可用均不阻塞执行
5. **Python 移植 TypeScript 不追求 1:1** — 保留设计模式，适配 Python 生态
6. **复用 aitest 已有资产** — complexity 18 因子、observation_bus、reliable_provider、ChromaDB
