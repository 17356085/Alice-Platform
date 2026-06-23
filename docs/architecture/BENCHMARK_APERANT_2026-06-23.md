# Architecture Benchmark — AITest Platform vs Aperant

> **类型:** 架构能力对标  
> **日期:** 2026-06-23  
> **基准:** AITest Platform v0.3-architecture-complete  
> **参考:** Aperant v2.8.0-beta.6 (实地考察源码)  
> **目的:** 识别可借鉴设计思想，非模仿实现  

---

## 1. Capability Mapping

按**职责**而非命名对标。状态定义：
- **Equivalent**: 功能对等
- **Partial**: 部分覆盖
- **Missing**: 缺失
- **Intentional Difference**: 有意差异，非缺陷

| 能力域 | Aperant | AITest | 状态 | 说明 |
|--------|---------|--------|------|------|
| **Agent 定义** | `AGENT_CONFIGS` (TS对象, 25+ Agent) | `governance/agents/*.yaml` (YAML, 20 Agent) | Equivalent | 均为声明式注册，YAML 更易于非开发者编辑 |
| **Agent 执行** | `runAgentSession()` (streamText loop) | `AgentLoop.run()` (Perceive→Plan→Act→Observe) | Equivalent | 均为 Agent 循环，AITest 多一层显式 Observe 阶段 |
| **LLM Provider** | `createProviderRegistry()` (9+ Provider) | `ReliableProvider` (3 Provider + Retry+Fallback) | Partial | AITest Provider 数量少但够用；Aperant 多账户轮换不适用（企业用 API Key） |
| **工具系统** | `Tool.define()` (Zod Schema, Agent-type-aware) | `CapabilityRouter` + `ToolDef` (MCP 注册) | Partial | AITest Capability 抽象更高级，但缺 Agent-type 级工具过滤 |
| **编排器** | `BuildOrchestrator` (EventEmitter, planner→coder→QA) | `SOPGraph` (LangGraph StateGraph, 8 Phase) | Equivalent | LangGraph 更强（形式化状态图+持久化），EventEmitter 更简单 |
| **上下文窗口** | `continuation.ts` (85%/90% 阈值, Haiku 摘要) | `context_window.py` (85%/90% 阈值, 摘要+continuation) | Equivalent | 功能对等，参考同一设计 |
| **安全检查** | `bash-validator.ts` + `denylist.ts` + `path-containment.ts` | `security.py` (Denylist+Validator+Pre-exec Hook) | Equivalent | 三层模型对等 |
| **Memory 系统** | Memory V5 (Observer+Scratchpad+Knowledge Graph, libSQL) | `testing_memory.py` (8类型 ChromaDB) | **Partial** | 关键差距。Aperant 的 Observer 模式 + 三档注入 + 知识图谱远超前 |
| **Context 构建** | `buildContext()` (文件分类+模式检测) | `context_injector.py` (项目上下文+Skill 注入) | Equivalent | 领域不同：代码上下文 vs 测试上下文 |
| **Prompt 管理** | `.md` 文件 + Subtask-focused 动态生成 | `.md` 文件 (Skill) + 完整加载 | Partial | AITest 是 file-based 但不做动态组装 |
| **MCP 集成** | `createMCPClient()` (Graceful degradation) | `mcp/protocol.py` (已有，无优雅降级) | Partial | 缺少连接失败非致命处理 |
| **Worktree 隔离** | git worktree per Task | `worktree_manager.py` (Agent 级) | Equivalent | 功能对等 |
| **前端** | React 19 + Zustand + Electron | Vue 3 + Pinia + Electron | Equivalent | 技术栈不同，能力对等 |
| **Kanban** | Kanban Board (Task 管理) | `KanbanView.vue` (SOP 管理) | Equivalent | 领域不同：Task vs SOP Phase |
| **并行执行** | `Promise.allSettled()` (子任务级) | `parallel_sop.py` (LangGraph Send, 页面级) | Equivalent | 并行策略不同，能力对等 |
| **Agent 生命周期** | `agent-process.ts` (Worker Thread) | `agent_runner.py` (async function) | Intentional Difference | Python asyncio 天然适合 IO 密集，不需进程隔离 |
| **CLI** | 无独立 CLI (Electron 内置) | `aitest` CLI (23 命令) | **AITest 更强** | 独立 CLI 工具包 |
| **API 服务** | 无 (本地 Electron) | FastAPI REST + SSE + WS | **AITest 更强** | 可独立部署为服务 |
| **多项目** | 单项目 (Workspace) | 多项目 + .tlo/ + project.yaml | **AITest 更强** | 企业多项目隔离 |
| **治理/审计** | 无 | SOP Gate + Validator + KPI + Audit Log | **AITest 更强** | 企业合规必需 |
| **多租户** | 无 | `tenant.py` (per-project limits) | **AITest 更强** | 平台级资源治理 |
| **Plugin 系统** | 无 (MCP 扩展) | `plugin.py` (YAML manifest + 动态加载) | **AITest 更强** | Capability Provider 可插拔 |
| **E2E 测试** | Playwright (Electron MCP) | Playwright (smoke.spec.ts, 19 tests) | Equivalent | 均用 Playwright |
| **观测性** | Sentry | OTel + Prometheus + Trace + Health | **AITest 更强** | 企业级可观测性栈 |
| **Rate Limiting** | Profile-based 切换 | MCP + REST 双层级 | Equivalent | 策略不同 |
| **Circuit Breaker** | 无 | `circuit_breaker.py` | **AITest 更强** | LLM 调用熔断 |
| **API 认证** | OAuth (Claude 订阅) | Bearer Token (API Key) | Equivalent | 场景不同 |
| **模型分层** | phase-config.ts (per-phase model tier) | 统一模型 (config.resolve_llm_provider) | **Missing** | Aperant 不同 Phase 用不同模型 |
| **收敛推动** | convergence nudge (75% step 时提醒) | 无 | **Missing** | 长任务防卡死 |
| **恢复扫描** | 启动扫描 stuck task | 部分 (LangGraph checkpoint 天然支持) | Partial | 缺少自动发现 stuck SOP |
| **Prompt 动态组装** | Subtask-focused 片段拼接 | 完整 Skill 加载 | **Missing** | Token 可省 ~70% |
| **Memory Observer** | 17 行为信号被动收集 | 无 (手动 record) | **Missing** | Aperant 核心技术护城河 |

---

## 2. Responsibility Comparison

### 2.1 Agent 执行层

| | Aperant | AITest |
|---|---|---|
| **职责** | `streamText()` 循环，工具调用，错误分类，收敛推动 | Perceive→Plan→Act→Observe→Update 显式循环 |
| **是否解决同一问题** | 是 — Agent 自主执行多步任务 | 是 — Agent 自主执行测试 SOP |
| **差异是否故意** | — | 是。测试场景需要显式 Observe（验证产出质量） |
| **差异是否有益** | — | 是。测试 SOP 的产出验证比代码生成更关键 |

### 2.2 编排层

| | Aperant | AITest |
|---|---|---|
| **职责** | `BuildOrchestrator` — planner→coder→QA 单线性管道 | `SOPGraph` — 8 Agent StateGraph，HITL 断点，checkpoint 续跑 |
| **是否解决同一问题** | 是 — 多阶段任务编排 | 是 — 多阶段测试编排 |
| **差异是否故意** | — | 是。LangGraph 提供形式化状态转换，优于 EventEmitter |
| **差异是否有益** | — | 是。测试 SOP 需要不可跳 Phase + 门禁检查 |

### 2.3 Memory 系统

| | Aperant | AITest |
|---|---|---|
| **职责** | Observer(17信号)→Scratchpad→Trust Gate→结构化Memory→三档注入 | 8 种 Memory 类型 → ChromaDB CRUD |
| **是否解决同一问题** | 是 — 跨会话知识积累 | 部分 — 知识存储但不做行为观察 |
| **差异是否故意** | — | 否。Observer 模式是 Aperant 的护城河，AITest 缺失 |
| **差异是否有益** | — | 否。测试场景同样需要观察 Agent 行为（定位器失败模式、断言模式等） |

### 2.4 工具/能力系统

| | Aperant | AITest |
|---|---|---|
| **职责** | `Tool.define()` + Agent-type-aware 过滤 + 路径 containment | `CapabilityRouter` — Agent→Capability 映射 + 原生 tool calling |
| **是否解决同一问题** | 是 — Agent 能力门控 | 是 — Agent 能力路由 |
| **差异是否故意** | — | 是。Capability 抽象高于 Tool：Agent 调 `browser.navigate()` 而非 `tool('browse')` |
| **差异是否有益** | — | 是。Capability 更贴近测试领域语义 |

### 2.5 Provider 系统

| | Aperant | AITest |
|---|---|---|
| **职责** | `createProviderRegistry()` (9+ Provider) + 多账户轮换 + OAuth | `ReliableProvider` (3 Provider) + Retry(3x) + Fallback |
| **是否解决同一问题** | 是 — LLM 调用可靠性 | 是 — LLM 调用可靠性 |
| **差异是否故意** | — | 是。企业用 API Key，不需 OAuth/多账户轮换 |
| **差异是否有益** | — | 是。AITest 的 Fallback 链 + Circuit Breaker 在企业场景更合适 |

### 2.6 Prompt 系统

| | Aperant | AITest |
|---|---|---|
| **职责** | File-based `.md` + Subtask-focused 动态生成 (~100行定制提示) | File-based `.md` (Skill) + 完整加载 (~500行) |
| **是否解决同一问题** | 是 — 可编辑、可版本控制的 Prompt | 是 — 可编辑、可版本控制的 Prompt |
| **差异是否故意** | — | 否。动态组装未实现，当前全量加载浪费 token |
| **差异是否有益** | — | 否。Token 成本可优化 |

---

## 3. Gap Analysis

### G1: Memory Observer — 行为信号被动收集

| 维度 | 内容 |
|------|------|
| **描述** | Aperant 通过 17 种行为信号（文件读取模式、编辑后立即撤销、重试同一错误等）被动收集 Memory。AITest 的 Memory 依赖手动记录 |
| **Aperant 为何有** | 核心技术护城河：最有价值的记忆来自观察，非显式记录 |
| **是否解决真实问题** | 是。定位器失败、Element Plus 已知坑位、页面加载异常——这些通过观察 Agent 行为可自动积累 |
| **对 AITest 是否有用** | 高。测试场景信号更清晰：定位器重试→failure pattern，断言失败→business rule change |
| **实现复杂度** | 高。需 Observer 线程/回调 + Scratchpad + Trust Gate + Promotion Pipeline |
| **架构影响** | 中。新增 `testing_memory/observer.py`，不改变现有接口 |
| **优先级** | **P1** — Aperant 最值得借鉴的单一设计 |

### G2: Phase-Aware Model Tier Selection

| 维度 | 内容 |
|------|------|
| **描述** | Aperant 不同 Phase 使用不同模型：analysis→Opus, implementation→Sonnet, validation→Haiku。AITest 所有 Phase 用同一模型 |
| **Aperant 为何有** | 成本优化 + 延迟优化。简单 Phase 不需要强模型 |
| **是否解决真实问题** | 是。Page Analysis 需强推理，Execute 只需执行，Report 只需结构化 |
| **对 AITest 是否有用** | 高。SOP 8 Phase 复杂度差异大 |
| **实现复杂度** | 低。在 `agent-definitions.yaml` 增加 `model_tier` 字段，ReliableProvider 按 tier 选模型 |
| **架构影响** | 低。纯配置增强 |
| **优先级** | **P0** — 立即采用，性价比极高 |

### G3: Prompt 动态组装

| 维度 | 内容 |
|------|------|
| **描述** | Aperant 根据子任务类型动态选择 Prompt 片段，生成 ~100-150 行定制提示。AITest 完整加载 Skill .md (~500行) |
| **Aperant 为何有** | Token 节省 ~70%，Agent 只看相关信息 |
| **是否解决真实问题** | 是。AITest SOP 每个 Phase 加载完整 Skill 列表，大量内容不相关 |
| **对 AITest 是否有用** | 中。Skill 文件可拆为"核心规则"+"上下文相关"两部分 |
| **实现复杂度** | 中。需 Skill 片段化 + 按 Phase/Complexity 组装逻辑 |
| **架构影响** | 低。Skill 文件重构，不影响接口 |
| **优先级** | **P1** — 平台稳定后做 token 优化 |

### G4: Per-Agent 工具/Capability 过滤

| 维度 | 内容 |
|------|------|
| **描述** | Aperant 每个 Agent 类型只能访问其配置的工具列表。AITest CapabilityRouter 有映射但未强制执行 |
| **Aperant 为何有** | 安全：QA Agent 不应有写权限，Plan Agent 不应执行 Bash |
| **是否解决真实问题** | 是。Bug Analysis Agent 不应执行 Browser 操作，Arch Agent 不应生成测试脚本 |
| **对 AITest 是否有用** | 高 |
| **实现复杂度** | 低。CapabilityRouter 已有映射表，增加 `check_capability()` 调用即可 |
| **架构影响** | 低。纯增强已有模块 |
| **优先级** | **P0** — 安全加固 |

### G5: 收敛推动

| 维度 | 内容 |
|------|------|
| **描述** | Aperant 当 Agent 使用 75% step 预算时注入收敛提示，推动 Agent 产出结论。AITest 无此机制 |
| **Aperant 为何有** | 防 Agent 卡死在无限循环中 |
| **是否解决真实问题** | 是。长 SOP 运行可能卡在 Bug Analysis 循环 |
| **对 AITest 是否有用** | 中 |
| **实现复杂度** | 低。在 AgentLoop step counter 达到 75% max_steps 时注入收敛提示 |
| **架构影响** | 极低。纯 Prompt 注入 |
| **优先级** | **P2** — 优化性质 |

### G6: MCP 优雅降级

| 维度 | 内容 |
|------|------|
| **描述** | Aperant MCP 连接失败用 `Promise.allSettled` 模式——成功连接的继续，失败的 skip+log。AITest 无此处理 |
| **Aperant 为何有** | 避免单点 MCP 失败阻塞 Agent 启动 |
| **是否解决真实问题** | 是。ChromaDB/外部工具可能不可用 |
| **对 AITest 是否有用** | 中 |
| **实现复杂度** | 低。MCP connection 用 try/except + log，不抛异常 |
| **架构影响** | 极低 |
| **优先级** | **P2** |

---

## 4. Strength Analysis — AITest 强于 Aperant

### S1: 多项目隔离 + .tlo/ 目录

Aperant 是单项目桌面工具。AITest 通过 `.tlo/` 目录 + `project.yaml` 实现项目与平台的彻底分离。项目上下文跟随项目，平台降级为 Registry。这是企业多项目场景的核心优势。

**为何是优势:** 平台可承载 N 个项目而不膨胀。新项目接入只需创建 `.tlo/project.yaml`。

### S2: Governance Layer — 门禁 + 审计 + 合规

Aperant 无治理概念。AITest 有完整的治理栈：SOP Gate（不可跳 Phase）、Validator（文档完整性检查）、KPI Timeseries、Audit Log、Event Bus。这是企业合规必需的。

**为何是优势:** 测试证据链完整可追溯。每次 Agent 决策、每次工具调用、每次 Phase 转换可审计。

### S3: LangGraph 编排 > EventEmitter 编排

Aperant 用 EventEmitter 管理编排事件。AITest 用 LangGraph StateGraph——形式化状态图，持久化 checkpoint，HITL 断点。更强的编排原语。

**为何是优势:** 状态转换可验证，断点可续跑，并行 Send() API 天然支持多页面并发。

### S4: 独立 CLI + API 服务

Aperant 仅为 Electron 桌面应用。AITest 有独立 CLI（23 命令）+ FastAPI 服务（REST + SSE + WS）。可集成到 CI/CD 管道。

**为何是优势:** 非 GUI 场景可用。`aitest graph run --module=x --non-interactive` 输出 JSON 可被 CI 解析。

### S5: 测试领域深度

Aperant 通用代码生成。AITest 深度理解测试领域：Page Object、Locator、Fixture、SOP Phase、Element Plus 已知坑位、Allure 集成。这些领域知识无法从通用框架获得。

**为何是优势:** Agent 不需要从头学测试。Skill 库封装了 40+ 测试领域的可复用能力。

### S6: 企业可观测性栈

Aperant 用 Sentry 做错误追踪。AITest 有：OpenTelemetry 分布式追踪、Prometheus Metrics、Structured Logging (JSONL)、Health Check、Circuit Breaker 状态暴露。完整的企业级可观测性。

---

## 5. Evolution Roadmap

仅推荐有明确架构价值的改进。每项独立，不需要全部实施。

### R1: Phase-Aware Model Tier (P0)

| 维度 | 内容 |
|------|------|
| **解决的问题** | 所有 SOP Phase 用同一模型，简单 Phase 浪费成本 |
| **预期收益** | Token 成本降 ~40-60%，简单 Phase 延迟降 |
| **复杂度** | 低。`agent-definitions.yaml` 加字段 + ReliableProvider 按 tier 选模型 |
| **架构影响** | 无。配置增强 |
| **参考 Aperant** | `phase-config.ts` 的 per-phase model resolution |

### R2: Capability 强制执行 (P0)

| 维度 | 内容 |
|------|------|
| **解决的问题** | Agent 可调用任何 Capability，无权限门控 |
| **预期收益** | 安全加固。Bug Agent 不可操作 Browser |
| **复杂度** | 低。CapabilityRouter 已有映射表，增加 `enforce=True` |
| **架构影响** | 无。已有模块增强 |
| **参考 Aperant** | `agent-configs.ts` 的 Agent-type-aware tool filtering |

### R3: Memory Observer — 测试行为信号 (P1)

| 维度 | 内容 |
|------|------|
| **解决的问题** | Memory 依赖手动记录，无自动积累 |
| **预期收益** | 跨会话知识积累：定位器失败模式自动沉淀，El Plus 坑位自动发现 |
| **复杂度** | 高。需 Observer + Scratchpad + Trust Gate + Promotion |
| **架构影响** | 中。新增 `testing_memory/observer.py` |
| **参考 Aperant** | Memory V5 Observer-First 设计思想（非实现） |

### R4: Prompt 片段化 + Phase 动态组装 (P1)

| 维度 | 内容 |
|------|------|
| **解决的问题** | Skill .md 全量加载浪费 token |
| **预期收益** | Prompt token 降 ~50-70% |
| **复杂度** | 中。Skill 拆片 + 组装器 |
| **架构影响** | 低。Skill 文件重构 |
| **参考 Aperant** | Subtask-focused prompt generation |

### R5: 收敛推动 (P2)

| 维度 | 内容 |
|------|------|
| **解决的问题** | 长 SOP 运行可能卡死 |
| **预期收益** | 防 Agent 无限循环，提升 long-running 任务成功率 |
| **复杂度** | 极低。AgentLoop step counter 检查 + prompt 注入 |
| **架构影响** | 无 |
| **参考 Aperant** | Convergence nudge at 75% step budget |

### R6: MCP 优雅降级 (P2)

| 维度 | 内容 |
|------|------|
| **解决的问题** | 单点 MCP 失败可能阻塞 |
| **预期收益** | 韧性提升 |
| **复杂度** | 极低。try/except + log |
| **架构影响** | 无 |
| **参考 Aperant** | `Promise.allSettled` 模式 |

---

## 6. Final Assessment

### 6.1 Architecture Maturity

| | Aperant | AITest |
|---|---|---|
| **定位** | 开源桌面 AI 编码框架 | 企业 AI 测试自动化平台 |
| **成熟度** | 高 (v2.8.0, 社区验证) | 中高 (v0.3, 架构评审通过) |
| **核心优势** | Memory Observer + Agent 工程 | Governance + 多项目 + 测试领域深度 |
| **核心弱点** | 无治理、单项目、不可 SaaS 化 | Memory 弱、缺 Phase-aware model |
| **技术栈** | TypeScript + Vercel AI SDK + Electron | Python + LangGraph + FastAPI + Vue 3 |

### 6.2 Platform Completeness

| 维度 | Aperant | AITest |
|------|---------|--------|
| Agent 执行 | ⬛ 成熟 | ⬛ 成熟 |
| 编排 | ⬛ EventEmitter | ⬛⬛ LangGraph (更强) |
| Memory | ⬛⬛⬛ V5 Observer (领先) | ⬛ Partial |
| 治理 | ⬜ 无 | ⬛⬛⬛ 完整 (领先) |
| 多项目 | ⬜ 无 | ⬛⬛⬛ 完整 (领先) |
| 可观测性 | ⬛ Sentry | ⬛⬛⬛ OTel+Prometheus+Trace (领先) |
| API 化 | ⬜ 无 | ⬛⬛ REST+SSE+WS (领先) |
| 插件系统 | ⬜ MCP only | ⬛⬛ YAML manifest |
| 安全 | ⬛⬛ Bash validator | ⬛⬛ 三层+TLS+Auth |
| Provider | ⬛⬛⬛ 9+Provider+多账户 | ⬛ 3 Provider+Fallback |

### 6.3 Top Strengths

1. **Governance 体系** — SOP Gate + Validator + KPI + Audit。Aperant 完全没有，AITest 业界领先
2. **多项目隔离** — `.tlo/` + project.yaml。企业场景不可替代
3. **LangGraph 编排** — 形式化状态图优于 EventEmitter
4. **测试领域深度** — 40+ Skill + El Plus 已知坑位 + Page Object 模式
5. **企业可观测性** — OTel + Prometheus + JSONL Trace + Health Check

### 6.4 Top Weaknesses

1. **Memory 系统弱** — 缺 Observer 模式，无法自动积累测试行为知识
2. **无 Phase-Aware Model** — 所有 Phase 用同一模型，成本可优化
3. **Prompt 全量加载** — 无动态组装，Token 浪费
4. **Provider 数量少** — 3 Provider vs Aperant 9+（但企业场景够用）

### 6.5 Top Three Future Investments

| 优先级 | 投资 | 预期收益 | 参考 |
|--------|------|----------|------|
| **P0** | Phase-Aware Model Tier | 成本降 40-60% | Aperant phase-config.ts |
| **P0** | Capability 强制执行 | 安全加固 | Aperant agent-configs.ts |
| **P1** | Memory Observer | 跨会话知识自动积累 | Aperant Memory V5 设计思想 |

### 6.6 Overall Recommendation

**AITest 不需要成为 Aperant。**

两个平台解决不同问题、服务不同用户、有不同约束。AITest 在治理、多项目、SOP 编排、领域深度方面**已超越** Aperant。Aperant 在 Memory 系统和 Agent 工程精细化方面领先。

最值得借鉴的是 Aperant 的**三个设计原则**——不是其实现：

1. **Phase-Aware Model Selection** — 不同 Phase 不同模型，成本与能力平衡
2. **Observer-First Memory** — 最有价值的记忆来自行为观察，非显式记录
3. **Capability 门控** — Agent 只能调用声明的能力，声明即授权

这三个原则独立于技术栈，可直接映射到 AITest 的 Python 生态。

---

> **结论:** AITest 与 Aperant 是**互补**关系，非竞争关系。AITest 在企业测试自动化领域的深度（Governance、SOP、多项目、测试领域知识）是 Aperant 永远无法提供的。Aperant 在 Memory Observer 和 Agent 工程精细化方面的积累值得学习。建议取 Aperant 之精华（设计思想），融入 AITest 之特色（企业治理），而非模仿其实现。
