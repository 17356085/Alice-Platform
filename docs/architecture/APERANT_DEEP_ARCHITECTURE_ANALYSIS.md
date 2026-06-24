# Aperant Deep Architecture Analysis

> 从源码层面对 Aperant 架构的完整剖析  
> 目标：提取可借鉴的设计，而非 Fork 实现  
> 日期：2026-06-23 | 基准：Aperant v2.8.0-beta.6

---

## 1. Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        APERANT ARCHITECTURE                             │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                    PRESENTATION (Electron Renderer)                │ │
│  │  React 19 + Zustand 5 + Tailwind 4 + Radix UI + xterm.js          │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │ │
│  │  │ Kanban   │ │ Terminal │ │ Insights │ │ Settings / Onboarding │  │ │
│  │  │ Board    │ │ (x12)    │ │ / Chat   │ │ / GitHub / Roadmap   │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘  │ │
│  └──────────────────────────┬────────────────────────────────────────┘ │
│                              │ IPC (contextBridge)                      │
│  ┌──────────────────────────┼────────────────────────────────────────┐ │
│  │                    MAIN PROCESS                                    │ │
│  │  ┌──────────────────────┼──────────────────────────────────────┐  │ │
│  │  │              AGENT LIFECYCLE LAYER                           │  │ │
│  │  │  AgentManager (facade) ─── EventEmitter                      │  │ │
│  │  │  ├─ AgentState      (running agents, queue status)           │  │ │
│  │  │  ├─ AgentQueue      (priority queue, rate-limit routing)     │  │ │
│  │  │  ├─ AgentProcess    (Worker Thread spawn/monitor/cleanup)    │  │ │
│  │  │  └─ AgentEvents     (lifecycle events → IPC → UI)            │  │ │
│  │  └──────────────────────┬──────────────────────────────────────┘  │ │
│  │                          │ postMessage()                            │ │
│  │  ┌──────────────────────┼──────────────────────────────────────┐  │ │
│  │  │              AI AGENT LAYER (Worker Thread)                  │  │ │
│  │  │                                                              │  │ │
│  │  │  ┌─────────────────────────────────────────────────────┐    │  │ │
│  │  │  │            ORCHESTRATION                             │    │  │ │
│  │  │  │  BuildOrchestrator    SpecOrchestrator               │    │  │ │
│  │  │  │  planning→coding→QA   complexity→spec→validate       │    │  │ │
│  │  │  │  SubtaskIterator      ParallelExecutor               │    │  │ │
│  │  │  │  RecoveryManager      QALoop                          │    │  │ │
│  │  │  └──────────────────────┬──────────────────────────────┘    │  │ │
│  │  │                          │                                    │  │ │
│  │  │  ┌──────────────────────┼──────────────────────────────┐    │  │ │
│  │  │  │            SESSION RUNNER                            │    │  │ │
│  │  │  │  runAgentSession() — streamText() loop               │    │  │ │
│  │  │  │  ├─ Provider (factory.ts → 9+ providers)             │    │  │ │
│  │  │  │  ├─ Tools (registry.ts → per-agent filtering)        │    │  │ │
│  │  │  │  ├─ Context Window Guard (85%/90% → continuation)    │    │  │ │
│  │  │  │  ├─ Error Classifier (401/429/timeout → retry)       │    │  │ │
│  │  │  │  ├─ Progress Tracker (step counting, convergence)    │    │  │ │
│  │  │  │  └─ Memory Injection (prepareStep callback)          │    │  │ │
│  │  │  └──────────────────────┬──────────────────────────────┘    │  │ │
│  │  │                          │                                    │  │ │
│  │  │  ┌──────────────────────┼──────────────────────────────┐    │  │ │
│  │  │  │            CAPABILITY LAYER                           │    │  │ │
│  │  │  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌──────────────┐  │    │  │ │
│  │  │  │  │ Tools  │ │Security│ │Context │ │   Prompt     │  │    │  │ │
│  │  │  │  │Read    │ │Denylist│ │Builder │ │  Loader (.md)│  │    │  │ │
│  │  │  │  │Write   │ │CmdParse│ │Pattern │ │  Subtask     │  │    │  │ │
│  │  │  │  │Edit    │ │PathCtn │ │Discov. │ │  Generator   │  │    │  │ │
│  │  │  │  │Bash    │ │SecScan │ │Search  │ │              │  │    │  │ │
│  │  │  │  │Glob    │ │ToolVal │ │        │ │              │  │    │  │ │
│  │  │  │  │Grep    │ └────────┘ └────────┘ └──────────────┘  │    │  │ │
│  │  │  │  │WebFetch│                                          │    │  │ │
│  │  │  │  └────────┘                                          │    │  │ │
│  │  │  └──────────────────────────────────────────────────────┘    │  │ │
│  │  │                                                              │  │ │
│  │  │  ┌──────────────────────────────────────────────────────┐    │  │ │
│  │  │  │            MEMORY SYSTEM (V5)                          │    │  │ │
│  │  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐    │    │  │ │
│  │  │  │  │ Observer │  │Scratchpad│  │  Knowledge Graph │    │    │  │ │
│  │  │  │  │ (17 sig) │→ │ → Trust  │→ │  Structural      │    │    │  │ │
│  │  │  │  │ passive  │  │   Gate   │  │  Semantic        │    │    │  │ │
│  │  │  │  │ <2ms     │  │ 2-cycle  │  │  Knowledge       │    │    │  │ │
│  │  │  │  └──────────┘  └──────────┘  └──────────────────┘    │    │  │ │
│  │  │  │  ┌──────────────────────────────────────────────┐    │    │  │ │
│  │  │  │  │         RETRIEVAL PIPELINE                    │    │    │  │ │
│  │  │  │  │  QueryClassifier → BM25 + Dense + Graph      │    │    │  │ │
│  │  │  │  │  → RRF Fusion → Graph Boost → Reranker       │    │    │  │ │
│  │  │  │  │  → Context Packer → Injection                │    │    │  │ │
│  │  │  │  └──────────────────────────────────────────────┘    │    │  │ │
│  │  │  └──────────────────────────────────────────────────────┘    │  │ │
│  │  └─────────────────────────────────────────────────────────────┘  │ │
│  │                                                                    │ │
│  │  ┌──────────────────────────────────────────────────────────────┐  │ │
│  │  │            INFRASTRUCTURE                                     │  │ │
│  │  │  Worktree Mgr  │  MCP Client   │  Merge Engine  │  Auth      │  │ │
│  │  │  (git worktree) │  (graceful)   │  (semantic)    │  (OAuth)   │  │ │
│  │  └──────────────────────────────────────────────────────────────┘  │ │
│  └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌────────────────────────────────────────────────────────────────────┐ │
│  │            DATA LAYER (file-based, no DB)                          │ │
│  │  .auto-claude/                                                     │ │
│  │  ├── specs/{id}/  spec.md, requirements.json, context.json,        │ │
│  │  │                implementation_plan.json, qa_report.md            │ │
│  │  ├── github/      PR reviews, triage state                         │ │
│  │  └── worktrees/   git worktree per task                            │ │
│  └────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 分层分析

### 2.1 实际分层 (非理想化)

Aperant 不是教科书式的分层架构。它是 Electron 应用特有的**进程边界分层**：

| 层 | 运行位置 | 职责 | 文件数 |
|---|---------|------|--------|
| **Presentation** | Renderer Process | React UI, Zustand stores, IPC 调用 | ~100 |
| **Agent Lifecycle** | Main Process | 队列、进程管理、状态、事件分发 | ~15 |
| **AI Agent** | Worker Thread | LLM 调用、编排、工具、Memory | ~200 |
| **Infrastructure** | Main/Worker | Worktree、MCP、Merge、Auth | ~20 |
| **Data** | Filesystem | `.auto-claude/` JSON/MD 文件 | — |

**关键洞察：** AITest 的 5 层冻结架构（Platform Core → Agent Runtime → Infrastructure → Domain → Experimental）比 Aperant 的进程边界分层更清晰。Aperant 的 Agent Lifecycle 和 AI Agent 层存在大量交叉依赖（通过 EventEmitter + IPC）。

### 2.2 Platform vs Domain 边界

```
┌──────────────────────────────────────────────────┐
│              PLATFORM (领域无关)                    │
│  providers/      → 多 LLM Provider 抽象            │
│  session/        → Agent 执行循环                  │
│  tools/          → 文件系统工具 (Read/Write/Bash)   │
│  security/       → 命令安全校验                    │
│  context/        → 项目结构分析                    │
│  mcp/            → MCP 协议客户端                  │
│  worktree/       → Git 工作区隔离                  │
│  memory/         → 通用记忆系统 (Observer+KG)       │
│  prompts/        → 提示词加载器                    │
├──────────────────────────────────────────────────┤
│              CODING DOMAIN (编码领域)               │
│  orchestration/  → BuildOrchestrator (plan→code→QA)│
│  spec/           → Spec Pipeline (需求→规格)        │
│  runners/        → Insights/Roadmap/PR/Changelog  │
│  merge/          → 语义合并                        │
│  schema/         → ImplementationPlan/QA/PR Schema │
│  project/        → 框架检测、项目索引               │
└──────────────────────────────────────────────────┘
```

**Platform 占比：~65%** | **Coding Domain 占比：~35%**

Aperant 的平台层已经非常接近一个**通用 AI Agent Framework**。如果把 Coding Domain 的 35% 替换为 Testing Domain，就能得到一个 AI Testing Platform。

---

## 3. 逐模块设计评价

### 3.1 BuildOrchestrator — ⭐⭐⭐ 可借鉴思想

```
planning → coding → qa_review → qa_fixing → complete
```

- **职责：** 驱动完整构建生命周期的阶段转换
- **实现：** EventEmitter + 文件状态机。每个 Phase 调用 `runAgentSession()`，产出写入 `.auto-claude/specs/{id}/`
- **优点：** 阶段转换清晰，每个 Phase 有明确的输入/输出 artifact
- **缺点：** EventEmitter 不是形式化状态机。阶段转换逻辑散布在回调中，难以验证正确性。混合了编排、验证、重试、文件 I/O
- **AITest 对比：** LangGraph StateGraph 更强。形式化状态 + 持久化 checkpoint + Send() 并行。不需要借鉴 EventEmitter 模式
- **借鉴：** Artifact-first pipeline 思想。每阶段产出明确文件，阶段间通过文件传递上下文

### 3.2 SpecOrchestrator — ⭐⭐⭐⭐ 值得借鉴

```
Complexity Assessment → SIMPLE/STANDARD/COMPLEX → phased spec creation
```

- **职责：** 复杂度评估 → 选择不同深度的 Spec Pipeline
- **实现：** 18 因子评分（代码量、文件数、依赖复杂度等）→ 三档路由
- **优点：** 复杂度自适应。简单任务不走重流程。这正是 AITest Complexity Router 的参考源
- **缺点：** 复杂度因子偏向代码项目（文件数、依赖图、AST 深度）。测试场景需要不同因子
- **AITest 对比：** 已有 `complexity/classifier.py`（18 因子 + 三档路由），但因子需要从代码项目适配到测试页面
- **借鉴：** 三档路由思想已采纳。需适配测试领域因子（页面字段数、组件类型、是否有工作流）

### 3.3 Memory System (V5) — ⭐⭐⭐⭐⭐ 最值得借鉴的单一模块

```
Observer (17 signals, <2ms) → Scratchpad → Trust Gate (2-cycle)
    → Promotion → Structured Memory (3-layer Knowledge Graph)
    → Retrieval Pipeline (BM25 + Dense + Graph → RRF → Rerank → Pack)
    → Injection (Passive/Reactive/Active three-tier)
```

- **职责：** 被动观察 Agent 行为，积累跨会话知识
- **实现：**
  - **Observer:** 主线程运行。监听每个 Worker Thread postMessage。17 种行为信号。硬约束：`observe()` <2ms，永不 await，永不访问 DB，永不抛异常
  - **Scratchpad:** 内存中临时存储候选记忆。同 session 内去重
  - **Trust Gate:** 两周期验证。Session 内出现 ≥2 次的行为才提升。外部工具调用需额外验证
  - **Knowledge Graph:** 三层闭包表（Structural / Semantic / Knowledge）。深度限制 5 防 O(n²)
  - **Retrieval:** 混合检索管道。QueryClassifier → BM25 + Dense + Graph → RRF Fusion → Graph Boost → Reranker → Context Packer
  - **Injection:** 三档注入（Passive 会话开始 / Reactive Agent 请求 / Active prepareStep 每步注入）
- **优点：** Observer-first 哲学正确。最有价值的记忆来自行为观察，非显式记录。Trust Gate 防止噪声。三档注入精准控制上下文
- **缺点：** libSQL/Turso 依赖。实现复杂度极高（~40 文件）。需要充分积累才能发挥价值（冷启动问题）
- **AITest 对比：** `testing_memory.py` 仅有 8 种类型 + ChromaDB CRUD。无 Observer，无 Scratchpad，无 Trust Gate，无 KG，无混合检索
- **借鉴：** **设计思想，非实现。** Observer-first + Trust Gate + 三档注入。不借鉴 libSQL/KG/tree-sitter（测试场景不需要）

### 3.4 Session Runner — ⭐⭐⭐ 可借鉴模式

```
runAgentSession() = streamText() loop + error classification + progress tracking + continuation
```

- **职责：** Agent 执行循环的运行时环境
- **实现：** Vercel AI SDK `streamText()`。`stopWhen: stepCountIs(N)`。`prepareStep` 回调注入 Memory。错误分类（401/429/400→不同策略）
- **优点：** 收敛推动（75% step 时提醒 Agent 产出结论）。上下文窗口守卫（85%/90% 阈值）。Stream inactivity 超时（60s 无数据则 abort）
- **缺点：** 与 Vercel AI SDK 强绑定。TypeScript-only
- **AITest 对比：** `AgentLoop.run()` + `ReliableProvider` 已实现类似功能。LangGraph 的 checkpoint 比 EventEmitter 更强
- **借鉴：** 收敛推动（convergence nudge）模式。Stream inactivity timeout 防卡死

### 3.5 Worktree + Merge — ⭐⭐ 不适合 Testing

- **职责：** Git worktree 隔离每个 Task。语义合并解决多 Task 并行冲突
- **实现：** 每个 Task 创建 `auto-claude/{specId}` 分支。`.auto-claude/worktrees/tasks/{specId}/` 工作区。Merge Engine 先用确定性规则，再用 AI resolver
- **优点：** 代码修改隔离完美。失败 Task 不影响主分支。可并行
- **缺点：** 强依赖 git。Testing 场景不需要
- **AITest 对比：** 已有 `worktree_manager.py`（Agent 级隔离）。测试场景不需要语义合并
- **借鉴：** 不借鉴。测试需要的是 Execution Workspace（临时目录运行测试，验证后合并到 script/），不是 Git Worktree

### 3.6 AgentManager + AgentProcess — ⭐⭐ 过度设计

- **职责：** Agent 进程的完整生命周期管理
- **实现：** `AgentManager` (facade) → `AgentProcess` (Worker Thread spawn/monitor) + `AgentQueue` (priority routing) + `AgentState` (status tracking)
- **优点：** 进程级隔离。Rate limit 自动切换账户。启动恢复
- **缺点：** 800+ 行 AgentManager。Worker Thread 在 Electron 中合理，在 Python 中不必要（asyncio 更自然）
- **AITest 对比：** `agent_runner.py` AgentLoop 作为 async function，轻量得多。Worker Pool (`worker_pool.py`) 提供并发
- **借鉴：** 启动恢复扫描（stuck SOP 自动发现 → reset）。Rate limit 自动切换

### 3.7 Prompt System — ⭐⭐⭐ 已有类似

- **职责：** 可编辑的 Agent 提示词管理
- **实现：** `.md` 文件存储。`SubtaskPromptGenerator` 按子任务类型动态组装片段（~100-150 行定制提示 vs 完整 900 行）
- **优点：** Token 节省 ~70%。非开发者可编辑
- **AITest 对比：** 已有 40+ Skill `.md` 文件 + `skill_loader.py`。但全量加载，不做动态组装
- **借鉴：** Subtask-focused → Phase-focused prompt assembly

---

## 4. SOLID 违规与耦合分析

### 4.1 单一职责违规

| 位置 | 问题 | 严重度 |
|------|------|--------|
| `AgentManager` | Facade 编排 5+ 子模块，同时处理 spec creation、task execution、roadmap、ideation | High |
| `BuildOrchestrator` | 混合阶段转换 + 验证 + 重试 + 文件 I/O + EventEmitter 事件 | High |
| `runner.ts` (`runAgentSession`) | 混合 streamText + error classification + progress + continuation + memory injection | Medium |

### 4.2 耦合问题

| 耦合 | 位置 | 影响 |
|------|------|------|
| **Vercel AI SDK lock-in** | 全局 | `streamText()`, `tool()`, `generateText()` 无法替换 |
| **Git dependency** | worktree, merge | 非 git 项目不可用 |
| **File-based state** | 全局 | JSON 文件无事务，并发写可能损坏 |
| **IPC coupling** | Agent ↔ UI | postMessage 接口非版本化 |
| **EventEmitter spaghetti** | orchestration/ | 事件监听器散布在多处，难以追踪流程 |

### 4.3 依赖倒置缺失

Aperant 没有正式的依赖注入。所有模块直接 import 具体实现：

```typescript
// runner.ts — 直接依赖具体实现
import { streamText } from 'ai';                    // SDK lock-in
import { createProvider } from '../providers/factory';  // 具体工厂
import { buildRegistry } from '../tools/build-registry'; // 具体注册
import { MemoryObserver } from '../memory/observer';    // 直接依赖
```

AITest 的 `CapabilityRouter` + `PluginManager` + `BrowserRuntime(driver_factory=...)` 在这方面做得更好。

---

## 5. Workspace / Task / Memory / Pipeline / Timeline 协同

### Aperant 的协同模型

```
Workspace (.auto-claude/)
  │
  ├── Task (spec/{id}/)
  │   ├── spec.md           ← SpecOrchestrator 产出
  │   ├── implementation_plan.json ← BuildOrchestrator.planning 产出
  │   ├── qa_report.md       ← BuildOrchestrator.qa_review 产出
  │   └── context.json       ← ContextBuilder 产出
  │
  ├── Memory (libSQL DB)
  │   ├── Observer → 行为信号收集
  │   ├── Knowledge Graph → 结构化知识
  │   └── Retrieval → 三档注入
  │
  ├── Pipeline
  │   ├── Spec Pipeline (complexity → spec → validate)
  │   └── Build Pipeline (plan → code → QA → fix)
  │
  └── Timeline
      ├── Agent Events (lifecycle events → IPC → UI)
      └── Task Logs (task-log-writer.ts → .auto-claude/logs/)
```

### 协同流程

```
1. User creates Task → SpecOrchestrator 评估复杂度 → 生成 spec.md
2. BuildOrchestrator 读取 spec.md → Planner 生成 implementation_plan.json
3. SubtaskIterator 按 plan 逐个执行 Subtask
4. 每个 Subtask → Coder Agent in Worker Thread → streamText() loop
5. MemoryObserver 监听 Worker Thread postMessage → 收集行为信号
6. Scratchpad 累积 → Trust Gate 验证 → Promotion → Knowledge Graph
7. QA Reviewer 验证 → qa_report.md
8. QA Fixer 修复 → 循环直到通过
9. Merge Engine 合并 worktree → Timeline 记录完成
10. Memory 注入下一 Task 的 Planner prompt
```

**AITest 的对应协同：**

```
1. Project (.tlo/) → Agent 读取 MODULE_CONTEXT.md
2. SOPGraph → Preflight 验证 → Complexity Router 选档
3. AgentLoop → Perceive→Plan→Act→Observe→Update
4. 每个 Skill 执行 → LLM 调用 → 产出 artifact
5. ObservationBus 发射事件 → 审计日志
6. TestingMemory 存储 → 下次检索
7. SOP Gate → 验证产出完整性
8. Report Agent → 生成报告
9. KPI Timeseries → 记录趋势
```

---

## 6. 改造成 AI Testing Platform — 替换映射

```
Aperant                          →  AITest Platform
──────────────────────────────────────────────────
Spec Pipeline (spec-orchestrator) → Complexity Router + SOP Preflight
Build Pipeline (build-orchestrator)→ SOPGraph (LangGraph StateGraph)
SubtaskIterator                   → AgentLoop.run() (Perceive→Plan→Act→Observe)
Spec artifacts (.md/.json)        → Test artifacts (PAGE_CONTEXT, TEST_CASES, ...)
Git Worktree                      → Execution Workspace (temp dir, not git)
Merge Engine                      → 不需要（测试不修改源码）
PR Review Engine                  → 不需要
Code tools (Read/Write/Edit/Bash) → Capability Providers (Browser/RAG/Execute/Report)
Coding Memory (AST/Gotcha/Pattern)→ Testing Memory (Locator/UI Pattern/Business Rule)
Coder Agent                       → Automation Agent
QA Reviewer/Fixer                 → Bug Analysis Agent
Planner                           → Test Design Agent
Insights                          → Test Gap Scanner
Roadmap                           → Test Roadmap (Phase planning)
Changelog                         → Test Report (Excel/JSON)
```

---

## 7. Architecture Diagram — AITest Platform 借鉴后

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     AITEST PLATFORM (理想目标架构)                        │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                   PROJECT WORKSPACE (.tlo/)                        │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │ │
│  │  │Requirements│ │ Strategy │ │ SOP Runs │ │ Reports / Artifacts │  │ │
│  │  │(.md)     │ │(.yaml)   │ │(.jsonl)  │ │(.xlsx/.html)         │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘  │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │ │
│  │  │ Knowledge │ │ Timeline │ │Regression│ │ Metrics              │  │ │
│  │  │(ChromaDB)│ │(.jsonl)  │ │(baseline)│ │(operational)         │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                   PIPELINE (LangGraph)                              │ │
│  │  Requirement → Analysis → Strategy → Design → Execute              │ │
│  │  → Failure Analysis → Report → Regression → Knowledge              │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                   PLATFORM CORE (FROZEN)                            │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │ │
│  │  │Capability│ │ Provider │ │ Security │ │ Plugin Manager       │  │ │
│  │  │ Router   │ │ Chain    │ │ Layer    │ │                      │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘  │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────────┐  │ │
│  │  │ Agent    │ │ Context  │ │Testing   │ │ Observation Bus      │  │ │
│  │  │ Runtime  │ │ Window   │ │ Memory   │ │                      │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────────────────┘  │ │
│  └───────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐ │
│  │                   EXTENSION POINTS                                  │ │
│  │  Plugin (YAML) │ Skill (.md) │ MCP Server │ Agent (YAML) │ Config │ │
│  └───────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 8. 总结：借鉴清单

| 借鉴程度 | 内容 | 理由 |
|----------|------|------|
| ⭐⭐⭐⭐⭐ | Memory Observer 设计思想 | 被动观察 + Trust Gate + 三档注入。测试领域最需要的差异化能力 |
| ⭐⭐⭐⭐⭐ | Artifact-first Pipeline | 每阶段产出明确文件，Pipeline 即文档 |
| ⭐⭐⭐⭐⭐ | Workspace 组织方式 | Project 为第一公民，非 Chat |
| ⭐⭐⭐⭐ | Complexity-adaptive routing | 三档路由已有，需适配测试因子 |
| ⭐⭐⭐⭐ | Timeline + 运行指标 | 测试过程的时间线比聊天记录有价值 |
| ⭐⭐⭐ | 收敛推动 | 75% step 预算时提醒 Agent |
| ⭐⭐⭐ | Subtask-focused prompt assembly | → Phase-focused prompt assembly |
| ⭐⭐ | Worker Thread 隔离 | Python asyncio 更自然，不需要 |
| ⭐⭐ | Git Worktree | Testing 不需要代码隔离 |
| ⭐ | Agent Hierarchy | 已有 SOP + Capability Router，不需要多层 Agent |
| ☆ | PR Review / Merge / Changelog | Coding 领域专属，完全不适用 |

### 一句话总结

**Aperant 的产品架构（Workspace + Pipeline + Artifact + Timeline + Memory）值得借鉴。Aperant 的 Agent 实现（EventEmitter + Worker Thread + AI SDK lock-in）不需要模仿。AITest 的 LangGraph + CapabilityRouter + Plugin 在架构层面已经更优。**
