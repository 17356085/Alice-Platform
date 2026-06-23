# AITest v1.0 Architecture Overview

> 参考源: Aperant v2.8.0-beta.6 (Agent 工程模式) + ChatGPT 领域分析
> 版本: v1.0-draft | 日期: 2026-06-23

## 1. 定位

AITest v1.0 不是 "Python 版 Aperant"。定位为：

> **测试自动化 Agent Native 平台** — 以 Browser/Page/SOP/Evidence/Knowledge 为第一公民，Agent 通过 Capability Router 自主调用测试能力。

与 Aperant 的本质差异：

| 维度 | Aperant | AITest v1.0 |
|------|---------|-------------|
| 核心流程 | NL Task → Plan → Code → Review → Fix → Git | Module → Strategy → Design → Page Analysis → Execute → Validate → Report → Knowledge |
| 第一公民 | Code, Diff, PR, Git | Browser, Page, SOP, Evidence, Knowledge |
| Agent 产出 | 代码文件 + Git commit | 测试脚本 + 执行报告 + Evidence |
| 工具系统 | Read/Write/Edit/Bash (文件操作) | Browser/RAG/PageAnalysis/Codegen/Execute/Report (测试能力) |
| 并行单元 | 子任务 (subtask) | 页面 (page) |
| 记忆类型 | 代码模式 + Gotcha + 决策 | UI Pattern + Locator History + Business Rule + Known Bug |

## 2. 目标架构

```
                            Task (SOPState)
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
              Complexity    Workflow      State
               Router       Engine        Manager
                    │      (LangGraph)       │
                    │            │           │
                    ▼            ▼           ▼
              ┌─────────┐  Capability   Checkpoint
              │ SIMPLE  │   Router       + Resume
              │ STANDARD│      │
              │ COMPLEX │      │
              └─────────┘      │
                    │           │
                    ▼           ▼
              ┌─────────────────────────────────────┐
              │        Capability Providers          │
              ├─────────┬─────────┬─────────────────┤
              │ Browser │  RAG    │  Codegen        │
              │ (BU/    │ (Chroma │ (Script/Fixture │
              │  PW/SE) │  DB)    │  Gen)           │
              ├─────────┼─────────┼─────────────────┤
              │ Execute │ Report  │  Validate       │
              │ (pytest │ (Excel/ │ (Assertion/     │
              │  /bash) │  JSON)  │  Evidence)      │
              └─────────┴─────────┴─────────────────┘
                                 │
                                 ▼
                        Observation Bus
                        (Event Stream)
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
                Testing       Audit         UI
                Memory        Log          (SSE)
```

## 3. 核心模块

### 3.1 Workflow Engine (演进，非重写)

当前 `sop_graph.py` (LangGraph StateGraph) 保持为编排核心。增强：
- **Complexity Routing** — 入口根据页面复杂度选不同流水线
- **Parallel Fan-out** — LangGraph `Send()` API 实现多页面并行
- **Context Window Continuation** — 长 SOP 自动摘要续跑

### 3.2 Capability Router (新增)

统一能力注册与路由层。Agent 通过 Capability 名称调用能力，不关心底层实现。

参考：Aperant `AGENT_CONFIGS` 声明式 Agent 配置 + AITest 现有 MCP `ToolDef` 注册表。

详见 [01-CAPABILITY_ROUTER.md](./01-CAPABILITY_ROUTER.md)

### 3.3 Provider Reliability Chain (增强)

当前 `provider.py` 的 `get_provider()` 只有一个 provider。增强为带 retry/fallback/cache 的可靠性链。

参考：Aperant `factory.ts` 的多 provider + OAuth 检测 + `continuation.ts` 的摘要 LLM 选择 + Anthropic Prompt Caching 文档。

详见 [02-PROVIDER_RELIABILITY.md](./02-PROVIDER_RELIABILITY.md)

### 3.4 Context Window Management (新增)

长 SOP 运行的上下文窗口监控与自动 continuation。

参考：Aperant `continuation.ts` (85%/90% 阈值 + Haiku 摘要 + 最多 5 次 continuation)。

详见 [03-CONTEXT_WINDOW.md](./03-CONTEXT_WINDOW.md)

### 3.5 Testing Memory (重构)

从 `AgentState.memory: dict` 升级为结构化的 Testing Memory 系统。

参考：Aperant `Memory.md` 的设计理念（类型化 Memory + 行为信号），但 Schema 完全重新设计为测试领域专用。

详见 [04-TESTING_MEMORY.md](./04-TESTING_MEMORY.md)

### 3.6 Complexity Routing (新增)

根据页面复杂度（字段数、组件类型、是否有工作流）自动选择不同 SOP 流水线。

参考：Aperant `spec-orchestrator.ts` 的快速路径启发式 + COMPLEXITY 三档路由。

详见 [05-COMPLEXITY_ROUTING.md](./05-COMPLEXITY_ROUTING.md)

### 3.7 Security Layer (新增)

命令执行三层安全模型：denylist → per-command validator → pre-exec hook。

参考：Aperant `security/` 目录 (bash-validator, command-parser, denylist, per-command validators)。

详见 [06-SECURITY_LAYER.md](./06-SECURITY_LAYER.md)

## 4. 关键设计原则

1. **Capability 抽象高于 Tool 实现** — Agent 调用 `browser.navigate()`，不关心底层是 BrowserUse 还是 Playwright
2. **声明式配置** — Agent 能力、Provider 链、Memory Schema 均为声明式注册，新增无需改业务逻辑
3. **渐进式迁移** — 每个模块独立可交付，不要求大爆炸重写
4. **参考但不照搬** — Aperant 的工程模式翻译为 Python/测试领域惯用写法
5. **LangGraph 为主线** — 编排层继续使用 LangGraph，不做无谓的技术栈切换

## 5. 与 Aperant 的参考映射

| AITest 模块 | 参考 Aperant 源 | 参考程度 |
|------------|----------------|---------|
| Provider Chain | `providers/factory.ts`, `session/runner.ts` (auth refresh) | 模式 + 部分代码翻译 |
| Context Window | `session/continuation.ts` | 几乎直接翻译 |
| Capability Router | `config/agent-configs.ts` (声明式配置) + `tools/registry.ts` | 模式借鉴 + 领域适配 |
| Security Layer | `security/bash-validator.ts`, `denylist.ts`, `validators/` | 模式几乎照搬 |
| Complexity Routing | `orchestration/spec-orchestrator.ts` (快速路径) | 模式借鉴 + 测试领域映射 |
| Testing Memory | `Memory.md` (设计理念), `memory/injection/`, `memory/retrieval/` | 理念借鉴 + Schema 重设计 |

## 6. 不参考的 Aperant 模块

| Aperant 模块 | 不参考理由 |
|-------------|-----------|
| planner/coder/qa_reviewer 流水线 | Coding 流程，非 Testing 流程 |
| PR Review engine (18 prompts) | AITest 无 PR Review 场景 |
| Code graph extraction (tree-sitter) | 对测试场景价值有限 |
| Electron 桌面壳 + 自动更新 | 后续考虑开发 |
| Worker thread 执行 | Python 用 asyncio 更自然 |
| Vercel AI SDK v6 全栈 | 技术栈不可迁移 |
| Graphiti MCP sidecar | Aperant 自身标记为可选 |
| 多账户自动切换 | 后续考虑开发                 |

## 7. 实施路径

详见 [07-MIGRATION_PLAN.md](./07-MIGRATION_PLAN.md)

```
Week 1: 可靠性基础 (Provider Chain + Prompt Cache + Context Window + Security)
Week 2: Agent 能力升级 (Capability Router + Tool Calling + Complexity Routing)
Week 3: 并行化 + 记忆 (Page Parallel + Testing Memory + Observation Bus)
Week 4: 前端补齐 (API Client + Router + ChatStore SSE + i18n)
```
