# Aperant Architecture Analysis → AITest Platform Evolution

> 分析: Aperant v2.8.0-beta.6 + Memory V5 Design
> 目标: 提取设计思想，映射到 AITest v1.0 企业级测试平台
> 原则: 分析设计而非复制实现 | 企业平台视角而非开源项目视角
> 日期: 2026-06-23

---

## 0. 两个项目的本质差异

分析架构前，先确认两者定位差异——这决定哪些设计可借鉴、哪些不可：

| 维度 | Aperant | AITest Platform |
|------|---------|-----------------|
| **定位** | 开源桌面端 AI 编码框架 | 企业级 AI 测试自动化平台 |
| **用户** | 独立开发者、小团队 | 企业 QA 团队，多项目并行 |
| **核心流程** | NL Task → Plan → Code → QA → Merge | Module → Strategy → Design → Analyze → Execute → Validate → Report → Knowledge |
| **第一公民** | Code, Diff, PR, Git | Browser, Page, SOP, Evidence, Knowledge |
| **Agent 产出** | 代码文件 + Git commit | 测试脚本 + 执行报告 + Evidence |
| **工具系统** | Read/Write/Edit/Bash (文件操作) | Browser/RAG/PageAnalysis/Codegen/Execute/Report (测试能力) |
| **并行单元** | 子任务 (subtask) | 页面 (page) |
| **记忆类型** | 代码模式 + Gotcha + 决策 | UI Pattern + Locator History + Business Rule + Known Bug |
| **合规需求** | 低 | 高（审计追踪、治理门禁、不可跳 Phase） |
| **部署模式** | Electron 桌面应用 | Python 后端 + Web 前端，支持多项目 |
| **技术栈** | TypeScript + Vercel AI SDK v6 | Python + LangGraph + FastAPI |

---

## 1. 子系统设计分析

### 1.1 Memory System (V5 Design)

**为什么这样设计？**

Aperant 将 Memory 定位为"技术护城河"（Technical Moat）。核心洞察：每次会话启动时，Agent 从零开始探索代码库——重读相同文件、重试相同失败方法、重踩相同坑。Memory 积累的价值随时间复利增长：Session 1-5 冷启动 → Session 30+ 如资深开发者般导航。

**解决的核心问题：**
- **上下文成本**：每次都从头读代码库，token 浪费巨大
- **重复失败**：同样的错误跨会话重演，无学习机制
- **知识断层**：Agent A 发现的 Gotcha，Agent B 不知道

**为什么不用其他方案？**

| 替代方案 | 弃用原因 |
|---------|---------|
| 纯向量数据库 (Pinecone/Qdrant) | 只解决语义相似，不解决结构化关系（依赖图、共访问模式） |
| 纯图数据库 (Neo4j) | 运维复杂，不适合桌面端嵌入部署 |
| 纯 FTS (Elasticsearch) | 无语义理解，代码搜索召回率低 |
| LLM 上下文注入（无检索） | Token 成本不可控，上下文窗口浪费 |
| RAG 框架 (LangChain/LlamaIndex) | 通用框架，无 Agent 行为观察能力 |

**核心 Trade-off：**

- **libSQL over better-sqlite3**：统一本地/云端查询语法，代价是依赖 Turso 生态
- **应用端 RRF 融合 over SQL JOIN**：libSQL 不支持 FULL OUTER JOIN，在应用层做，略慢但可移植
- **3 层知识图谱 (结构/语义/知识)**：功能强大但存储膨胀，闭表层深度限制在 5 防止 O(n²)
- **Observer-first over Explicit**：被动观察最准确但延迟高（需积累足够信号）；主动记录即时但可能噪声多
- **ONNX 回退 at <100MB**：零配置但精度不如 Qwen3 嵌入；加载时间 vs 使用便利性

**企业平台视角的补充考量：**

Aperant 的 Memory 设计针对"单一项目、长期使用"场景优化。企业测试平台需要额外考虑：
- **多项目 Memory 隔离**：A 项目的 Gotcha 不可污染 B 项目
- **团队 Memory 共享**：Alice 发现的定位器模式，Bob 应该受益
- **Memory 审计**：谁记录了这条 Memory？为什么？何时过期？
- **合规归档**：测试证据链需要 Memory 来源可追溯

---

### 1.2 Session Runner (Agent Runtime)

**为什么这样设计？**

`runAgentSession()` 是所有 Agent 的统一执行环境。它包装 Vercel AI SDK `streamText()`，提供：
- 多 provider 账户切换（rate limit 时自动换号）
- 上下文窗口守卫（85% 警告 / 90% 硬中断）
- 步骤追踪和收敛推动
- 错误分类和重试

**解决的核心问题：**
- **Provider 可靠性**：单 provider 不可靠，需多账户 + 多 provider fallback
- **上下文耗尽**：长任务会超出上下文窗口，需检测 + continuation
- **Agent 卡死**：某些 provider 不发送 finishReason，需超时检测

**为什么不用其他方案？**

| 替代方案 | 弃用原因 |
|---------|---------|
| 直接调用 Anthropic API | 无 provider 切换、无 rate limit 处理 |
| LangChain AgentExecutor | 重量级抽象，不可控的 prompt 注入 |
| 自建 Agent Loop | 需自行处理 tool calling、streaming、error recovery |
| CrewAI/AutoGen | 多 Agent 框架，单 Agent 执行过重 |

**核心 Trade-off：**

- **AI SDK v6 锁定**：获得 tool calling + streaming + provider registry，但被 Vercel 生态绑定
- **Worker Thread 执行**：避免阻塞 Electron 主进程，但增加 IPC 复杂度
- **File-based 状态 over 内存**：crash 可恢复，但读写延迟

**企业平台视角：**

AITest 已有 `agent_runner.py` AgentLoop，基于 LangGraph StateGraph。Aperant 的 Session Runner 设计中最值得借鉴的是**上下文窗口守卫 + continuation** 和**错误分类重试**两个模式——AITest 当前缺少这些。

---

### 1.3 Tool Registry (工具系统)

**为什么这样设计？**

`ToolRegistry` 是工具定义、注册、权限执行的唯一入口。核心设计：
- `Tool.define()` 包装 AI SDK `tool()`，注入安全检查
- Agent-type-aware 工具过滤：每个 Agent 类型只能访问其配置的工具
- 文件路径 sanitization（某些模型漏 JSON 字符到字符串参数）
- 写路径 containment

**解决的核心问题：**
- **工具治理**：不同 Agent 能力不同，不可让 QA Agent 执行写操作
- **安全隔离**：Bash 命令须验证，文件写入须限制路径
- **模型容错**：不同 provider 的 tool calling 实现有 bug，需容错处理

**为什么不用其他方案？**

| 替代方案 | 弃用原因 |
|---------|---------|
| 全局工具集 | 无 Agent 级别的能力门控 |
| MCP-only 工具 | 增加外部依赖，本地工具更可控 |
| 动态工具生成 | 不可审计，不可治理 |

**核心 Trade-off：**

- **声明式注册 over 动态发现**：可审计、可预测，但新增工具需改配置
- **Zod Schema over JSON Schema**：TypeScript 原生类型检查，但无法跨语言共享

**企业平台视角：**

这是 AITest **最应该借鉴的模块**。AITest 已有 MCP `ToolDef` 注册表雏形，但缺少：
- Agent 类型 → 工具权限的声明式映射
- 工具执行的沙箱化（路径 containment、Bash validation）
- 工具调用的审计日志

AITest Capability Router 应以此模式为蓝本，但用 Capability 抽象替代 Tool 抽象——Agent 调用 `browser.navigate()` 而非 `tool('browse')`。

---

### 1.4 Provider System (多 Provider 抽象)

**为什么这样设计？**

Aperant 支持 10+ AI provider（Anthropic, OpenAI, Google, Bedrock, Azure, Mistral, Groq, xAI, OpenRouter, Ollama），通过 Vercel AI SDK 的 `createProviderRegistry()` 统一访问。

**解决的核心问题：**
- **Provider 锁定**：不依赖单一 provider
- **成本优化**：简单任务用 Haiku/GPT-4o-mini，复杂任务用 Opus
- **Rate Limit 容忍**：多账户自动切换

**为什么不用其他方案？**

| 替代方案 | 弃用原因 |
|---------|---------|
| 单一 provider | 不可靠，rate limit 后全停 |
| 自建 provider 抽象 | 重复造轮子，AI SDK 已有成熟抽象 |
| LiteLLM proxy | 增加外部依赖，不适合桌面端 |

**核心 Trade-off：**

- **AI SDK 封装 over 直接 API**：简化多 provider 切换，但受 SDK 版本影响
- **Provider-specific 适配**：Codex 需 Responses API，Gemini 需不同 thinking 处理

**企业平台视角：**

AITest 已有 `reliable_provider.py`（Retry 3x + Fallback claude→deepseek→openai），基本满足需求。Aperant 的多账户轮换和 OAuth token 刷新不适用（企业用 API Key）。但 **phase-aware model selection**（不同 Phase 用不同模型）值得采纳——AITest 应在 SOP 配置中声明每个 Phase 的推荐 model tier。

---

### 1.5 Configuration System (Agent 配置)

**为什么这样设计？**

`AGENT_CONFIGS` 是一个包含 30+ Agent 类型的声明式配置注册表。每个条目定义：
- 允许的工具列表
- 需要的 MCP 服务器
- 默认思考级别
- 模型偏好

**解决的核心问题：**
- **Agent 能力宣言**：每个人都清楚 Agent X 能做什么、不能做什么
- **中心化治理**：修改 Agent 能力只改一处
- **自文档化**：配置即文档

**为什么不用其他方案？**

| 替代方案 | 弃用原因 |
|---------|---------|
| 代码中的 if/else | 分散、不可审计、难以新增 |
| 外部配置文件 (YAML/JSON) | 缺少类型安全，需额外解析层 |
| 数据库存储 | 过度设计，配置不常变 |

**核心 Trade-off：**

- **单体配置表 over 分布式配置**：简单、可 grep，但随 Agent 数量增长可能膨胀
- **TypeScript 对象 over YAML**：类型安全，但非技术人员不可编辑

**企业平台视角：**

AITest 的 Agent 定义在 `governance/agents/*.yaml`，配置模型合理但缺少 **Agent → Capability 映射** 和 **Phase → Model tier 映射**。Aperant 的设计思路可直接映射：
- `AGENT_CONFIGS` → `governance/agents/` YAML（已有，增强 capability + model tier 字段）
- `phase-config.ts` → `governance/sop/phase_config.yaml`（新增）

---

### 1.6 Worktree (工作区隔离)

**为什么这样设计？**

每个 Task 在独立 git worktree 中执行。分支名 `auto-claude/{specId}`，工作区路径 `.auto-claude/worktrees/tasks/{specId}/`。

**解决的核心问题：**
- **主分支安全**：Agent 的任何修改不污染主分支
- **并行隔离**：多个 Task 并行执行不互相干扰
- **可丢弃**：失败的 Task 直接删除 worktree，零影响
- **可审计**：每个 Task 的修改在独立分支，清晰可追溯

**为什么不用其他方案？**

| 替代方案 | 弃用原因 |
|---------|---------|
| Docker 容器隔离 | 过重，不适合桌面端 |
| 文件系统快照 | 非 git 原生，无法 diff/merge |
| 分支 + stash | stash 不可靠，并行 Task 时 stash 栈冲突 |
| VM 快照 | 极重，启动慢 |

**核心 Trade-off：**

- **git 依赖**：项目必须是 git 仓库，非 git 项目不可用
- **磁盘开销**：每个 worktree 是完整 checkout（但有 shared objects）
- **跨 worktree 状态复制**：`.auto-claude/specs/` 需显式从主项目复制

**企业平台视角：**

AITest 的测试项目通常是 git 仓库但不需要 worktree 隔离——测试执行不修改源码。但有一个**高度相关的场景**：**测试脚本生成后的沙箱验证**。Agent 生成的测试脚本应先在不影响现有测试套件的情况下验证。Aperant 的 worktree 模式可改造为 **Test Sandbox** 机制：

```
TestSandbox
→ 在临时目录运行生成的测试脚本
→ 验证通过后合并到 script/module/
→ 失败则丢弃，Agent 重试
```

---

### 1.7 Prompt System (提示管理)

**为什么这样设计？**

- **File-based**: 所有 Agent 提示为 `.md` 文件，非代码内嵌
- **Subtask-focused**: 每个子任务生成 ~100 行定制提示，非单一 900 行巨型提示
- **Context injection**: 在 base prompt 前动态注入项目指令、恢复上下文、人类反馈

**解决的核心问题：**
- **提示可编辑**：非开发者可通过编辑 .md 文件调整 Agent 行为
- **Token 效率**：按需注入上下文，省 ~80% token
- **版本控制**：提示变化可追溯

**为什么不用其他方案？**

| 替代方案 | 弃用原因 |
|---------|---------|
| 代码内嵌字符串 | 不可维护，不可审计 |
| 数据库存储 | 版本控制困难 |
| LangChain PromptTemplate | 增加依赖，简单的字符串替换即可 |

**核心 Trade-off：**

- **File-based over Code-based**：可编辑但需路径解析逻辑（dev vs production）
- **Subtask-focused over Monolithic**：省 token 但增加生成复杂度

**企业平台视角：**

AITest 已有 24 个测试 Skill + 32 个开发 Skill，全部为 `.md` 文件，已是 file-based。Aperant 的 subtask-focused 生成策略可改造为 **Phase-focused prompt generation**：根据当前 Phase 和 Page 复杂度动态组装提示，而非加载完整 Skill 全文。

---

### 1.8 Context Builder (上下文构建)

**为什么这样设计？**

`buildContext()` 搜索项目结构、分类文件角色（修改 vs 参考）、检测代码模式、匹配服务目录。

**解决的核心问题：**
- **上下文精度**：Agent 只看到相关文件，非整个项目
- **模式识别**：自动检测框架、库、代码风格
- **减少 token 浪费**：80% token 削减

**为什么不用其他方案？**

| 替代方案 | 弃用原因 |
|---------|---------|
| 完整项目索引 | 太重，不适合快速上下文构建 |
| 无上下文（Agent 自探索） | 浪费 token 和时间 |
| RAG over 代码库 | 适合"查找"但不适合"理解项目结构" |

**企业平台视角：**

AITest 的测试上下文构建与 Aperant 的代码上下文构建有本质差异。AITest 需要的是 **Page Context**：
- 页面 DOM 结构摘要
- Element Plus / 自定义 UI 框架检测
- 已知定位器列表
- 页面间导航关系

这应该作为 Capability Router 的 `page-analysis` capability 而非独立的 Context Builder。

---

### 1.9 MCP Integration

**为什么这样设计？**

通过 MCP 协议连接外部工具服务器：Context7（文档）、Linear（项目管理）、Puppeteer/Electron（浏览器）、Graphiti（记忆）。

**解决的核心问题：**
- **工具扩展性**：不把所有工具内置，按需连接外部服务器
- **标准协议**：MCP 是开放标准，生态工具可复用
- **优雅降级**：MCP 服务器连接失败不阻塞 Agent

**为什么不用其他方案？**

| 替代方案 | 弃用原因 |
|---------|---------|
| 所有工具内置 | 膨胀、不可扩展 |
| REST API 集成 | 无标准，每个工具接口不同 |
| Plugin 系统 | 需自建协议 |

**核心 Trade-off：**

- **MCP stdio/HTTP over Plugin SDK**：标准但有进程管理开销
- **Graceful degradation over Fail-fast**：灵活但可能隐藏配置错误

**企业平台视角：**

AITest 已有 MCP 集成（`aitest/mcp/`），这是正确的方向。Aperant 的 per-agent MCP 覆盖机制（`AGENT_MCP_<agent>_ADD`/`_REMOVE`）值得借鉴——在 AITest 中应体现为 per-Agent Skill 声明其需要的 MCP 服务器。

---

### 1.10 Orchestration (编排层)

**为什么这样设计？**

`BuildOrchestrator` 驱动完整的 build 生命周期：planning → coding → qa_review → qa_fixing。EventEmitter 模式解耦编排逻辑与 UI。

**解决的核心问题：**
- **阶段转换管理**：Phase A 完成 → Phase B 开始的逻辑集中管理
- **失败恢复**：Phase 失败不丢弃所有进度，从断点恢复
- **可观察性**：每个阶段的事件可被 UI/日志/监控消费

**核心 Trade-off：**

- **EventEmitter over State Machine**：简单灵活但缺少形式化状态转换验证
- **File-based 进度 over In-memory**：crash 可恢复但增加 I/O

**企业平台视角：**

AITest 已用 LangGraph StateGraph 做编排——这是比 EventEmitter 更强的选择（形式化状态图 + 持久化 checkpoint）。不需要借鉴 Aperant 的编排模式。但 **恢复机制**（扫描 stuck subtask → reset to pending）值得在 AITest 的 SOP 重跑中实现。

---

### 1.11 Agent 生命周期管理

**为什么这样设计？**

`AgentManager` 是 Agent 进程的完整生命周期管理器：spawn、monitor、cleanup、auth 解析。

**解决的核心问题：**
- **进程管理**：Agent 作为子进程运行，需生命周期管理
- **Rate limit 自动恢复**：检测 rate limit → 自动切换账户 → 重启任务
- **启动恢复**：应用重启后扫描 stuck task → reset to pending

**企业平台视角：**

AITest 当前 Agent 作为 LangGraph node 内的 async 函数运行，非独立进程。这种模式对测试场景更合适——测试 Agent 生命周期短，不需要进程级隔离。但 **Rate limit 自动恢复**和**启动恢复**两个模式值得在 AITest 的 Agent Runner 中实现。

---

## 2. 设计借鉴分类

### 可直接借鉴

| Aperant 设计 | 借鉴内容 | AITest 映射 |
|-------------|---------|------------|
| Agent Config 声明式注册 | Agent → Capability 映射、Phase → Model tier 映射 | `governance/agents/*.yaml` 增强 |
| Context Window 守卫 + Continuation | 85%/90% 阈值、Haiku 摘要、max continuation | `aitest/llm/context_window.py` |
| 错误分类 + 重试 | 区分可重试/不可重试、指数退避 | `aitest/llm/reliable_provider.py` 增强 |
| Tool 执行沙箱 | 路径 containment、Bash validation、denylist | `aitest/infra/security.py` |
| Per-Agent Tool 过滤 | Agent 类型 → 可用工具集的声明式映射 | Capability Router |

### 可改造借鉴

| Aperant 设计 | 改造方向 | AITest 映射 |
|-------------|---------|------------|
| Memory Observer | 代码行为信号 → 测试行为信号 | `aitest/platform/testing_memory.py` |
| Memory 三档注入 | 保留分层但内容改为测试领域 | Testing Memory 注入层 |
| Memory 检索融合 | BM25 + 向量 → ChromaDB + BM25 | Testing Memory 检索 |
| Worktree 隔离 | 代码隔离 → 测试沙箱 | Test Sandbox |
| Subtask-focused Prompt | 子任务提示 → Phase-focused 提示 | `governance/skills/` 动态组装 |
| MCP graceful degradation | 连接失败非致命 | `aitest/mcp/` 增强 |
| 启动恢复扫描 | 扫描 stuck SOP → reset | `aitest/agents/agent_runner.py` |

### 不建议借鉴

| Aperant 设计 | 原因 |
|-------------|------|
| Worker Thread 执行 | Python asyncio 天然适合 IO 密集，不需要线程隔离 |
| Vercel AI SDK 全栈 | 技术栈不可迁移（TypeScript SDK vs Python） |
| Electron 桌面应用 | AITest 是 Web 平台 + CLI，不需要桌面壳 |
| Graphiti MCP sidecar | Aperant 自身标记为可选，且 Python 侧 ChromaDB 更简单 |
| Planner/Coder/QA 流水线 | Coding 流程完全不适用于 Testing 流程 |
| 18-agent PR Review engine | AITest 无 PR Review 场景 |
| tree-sitter AST chunking | 对测试场景（DOM/定位器）价值有限 |
| libSQL/Turso 嵌入 | Python 生态用 ChromaDB + SQLite 更成熟 |

### 完全不适合

| Aperant 设计 | 原因 |
|-------------|------|
| AGPL-3.0 商业许可模式 | AITest 是企业内部平台，非开源项目 |
| 多账户 OAuth 轮换 | 企业用 API Key，不需要 consumer auth |
| Claude Code CLI 子进程 | AITest 直接调 API，不通过 CLI |
| Linear/Jira 集成 | 测试平台不涉及项目管理 |
| 自更新桌面应用 | AITest 是服务端应用，CI/CD 部署 |

---

## 3. Aperant → AITest 核心映射

```
Aperant                              AITest Platform
───────                              ──────────────

Workspace (git worktree)         →  Project Workspace (.tlo/ + project dir)
Runtime (runAgentSession)        →  Agent Runtime (AgentLoop + LangGraph)
Session (streamText loop)        →  Test Session (SOP Session)
Memory (libSQL + Graphiti)       →  Execution Memory (ChromaDB + SQLite)
Context (buildContext)           →  Project Context (Page Context + Module Profile)
Prompt (.md files + injection)   →  Prompt Registry (Skill .md + Phase assembly)
Agent Config (AGENT_CONFIGS)     →  Agent Registry (governance/agents/*.yaml)
Tool Registry (Tool.define)      →  Capability Router (Capability Registry)
Provider Factory (10 providers)  →  Provider Chain (ReliableProvider)
Orchestrator (BuildOrchestrator) →  SOP Engine (sop_graph.py + parallel_sop.py)
Spec Pipeline (spec-orchestrator)→  Strategy Pipeline (complexity → strategy → design)
QA Loop (qa-loop.ts)            →  Validate Loop (execute → assert → evidence)
MCP Client (stdio/HTTP)         →  MCP Bridge (aitest/mcp/)
Agent Manager (lifecycle)       →  Agent Supervisor (agent_runner.py)
Event Emitter (AgentEvents)     →  Observation Bus (observation_bus.py)
Continuation (context window)   →  Context Window Guard (context_window.py)
Security (bash-validator)       →  Security Layer (security.py)
```

---

## 4. ADR — Architecture Decision Records

### ADR-010: 声明式 Agent 能力注册

**Context**:
AITest 当前 Agent 定义在 `governance/agents/*.yaml`，但缺少正式的能力映射——Agent 能调用哪些 Capability、使用哪些模型、默认 thinking 级别未在配置中声明。

**Decision**:
在 Agent YAML 中增加 `capabilities`、`model_tier`、`thinking_budget` 字段，形成完整的 Agent 能力声明。

**Pros**:
- 能力可审计：任何 Agent 的能力范围一目了然
- 安全：Capability Router 按声明授权，未声明能力不可调用
- 新增 Agent 只需 YAML 声明，不改路由逻辑

**Cons**:
- 增加 YAML 字段复杂度
- 需维护映射一致性

**Alternative**:
- 代码中硬编码：简单但不可治理
- 数据库存储：过度设计

**Impact**: 低风险，纯增强现有 YAML 结构

**建议采用**: **Yes** — 立即采用

---

### ADR-011: Phase-Aware Model Tier Selection

**Context**:
当前所有 SOP Phase 使用相同模型。实际场景：Page Analysis 需要强推理（Opus），Execute 只需执行（Haiku），Report 需要结构化输出。

**Decision**:
在 SOP Phase 配置中增加 `model_tier` 字段。`SIMPLE` Phase 使用 econ 模型（Haiku/DeepSeek），`STANDARD` 使用 balance（Sonnet），`COMPLEX` 使用 max（Opus）。

**Pros**:
- 成本优化：不需要全用 Opus
- 延迟优化：简单 Phase 用更快模型
- 可配置：项目可按预算调整

**Cons**:
- 配置错误可能导致质量下降
- 需要 Phase 复杂度的预判

**Alternative**:
- 统一模型：简单但浪费
- 动态切换：不可预测

**Impact**: 中等，需修改 `phase-config` 和 `provider.py`

**建议采用**: **Yes** — 后续采用（依赖 Complexity Router 先落地）

---

### ADR-012: Context Window Guard + Continuation

**Context**:
长 SOP 运行（如 warehouse 12 页）可能超出 LLM 上下文窗口。当前无检测、无自动处理。

**Decision**:
实现两层守卫：85% 使用量发出警告，90% 触发自动 continuation——用轻量模型摘要已完成步骤，在新会话中继续。

**Pros**:
- 防止静默截断：Agent 不会在上下文耗尽时丢失信息
- 自动恢复：不需要人工干预
- 可配置阈值

**Cons**:
- 摘要可能丢失细节
- 需要可靠的 token 计数

**Alternative**:
- 不处理：静默失败
- 手动分片：操作负担

**Impact**: 中等，`aitest/llm/context_window.py` 新增

**建议采用**: **Yes** — 后续采用（依赖 ReliableProvider 稳定后）

---

### ADR-013: Capability Router — Agent-to-Capability 映射

**Context**:
当前 Agent 可调用任何 Skill，无能力门控。Arch Agent 不应执行 Browser 操作，Script Agent 不应做页面分析。

**Decision**:
Capability Router 维护 `Agent → Capability[ ]` 映射表。Agent 调用能力时，Router 检查声明、审计、执行、记录结果。

**Pros**:
- 能力隔离：Agent 只能执行声明过的能力
- 审计追踪：每次能力调用被记录
- 安全：恶意 prompt 无法越权调用

**Cons**:
- 增加调用开销（检查 + 审计）
- 初始配置工作量大

**Alternative**:
- 自由调用：不可治理
- MCP-only：限制工具生态

**Impact**: 高，核心架构模块

**建议采用**: **Yes** — 立即采用（已在 v1.0 架构中规划）

---

### ADR-014: Testing Memory — 行为信号观察

**Context**:
AITest 当前 Memory 为简单的 `dict`。需要结构化测试记忆系统，记录定位器历史、UI 模式、已知缺陷、业务规则。

**Decision**:
实现 Observer 模式的 Testing Memory：被动收集 6 种测试行为信号（定位器失败、页面加载异常、断言模式、测试脚本撤回、元素等待超时、数据依赖），经 Trust Gate 后提升为结构化 Memory。

**Pros**:
- 跨会话知识积累：Agent 不重复踩坑
- 自动化：不需要人工标注
- 可衰减：过时 Memory 自动降低权重

**Cons**:
- 冷启动问题：初始无 Memory 积累
- 实现复杂度：Observer + Trust Gate + Promotion Pipeline

**Alternative**:
- 纯向量数据库：丢失结构化关系
- 纯人工标注：不可扩展
- 不做 Memory：每次从头来

**Impact**: 高，但可分阶段交付（P2 优先级）

**建议采用**: **Yes** — 长期规划（先完成 Capability Router + Provider Chain）

---

### ADR-015: 工具执行安全沙箱

**Context**:
AITest Agent 可执行 bash 命令、写文件、访问网络。当前无细粒度安全控制。

**Decision**:
实现三层安全模型：
1. **Denylist**: 禁止命令列表（rm -rf /, curl | sh, etc.）
2. **Per-Command Validator**: 命令参数白名单（pytest 只能跑指定目录）
3. **Pre-exec Hook**: 执行前最终检查（路径 containment、网络限制）

**Pros**:
- 防误操作：Agent 不会意外删除文件
- 可审计：所有命令执行记录
- 分层防御：单层失效不导致整体失效

**Cons**:
- 可能误拦合法命令
- 维护 denylist 需要持续投入

**Alternative**:
- 不做安全：企业环境不可接受
- 容器隔离：过重

**Impact**: 中等

**建议采用**: **Yes** — 立即采用（已在 v1.0 架构中规划）

---

### ADR-016: Prompt 动态组装 — Phase-Focused

**Context**:
当前 Skill 文件是完整加载的。对于简单 Page/Phase 组合，许多内容不相关，浪费 token。

**Decision**:
实现 Phase-focused prompt assembly：根据当前 Phase 类型、Page 复杂度、已知上下文动态选择 Skill 片段，生成 ~150 行定制提示而非加载 500 行完整 Skill。

**Pros**:
- Token 节省：~70% prompt token 削减
- 聚焦：Agent 只看到相关信息
- 可复用：Skill 片段可跨 Phase 组合

**Cons**:
- 组装逻辑复杂
- 片段切割需要人工设计

**Alternative**:
- 完整 Skill 加载：简单但浪费
- LLM 摘要 Skill：不可靠

**Impact**: 低-中，优化性质

**建议采用**: **Yes** — 长期规划（token 优化在平台稳定后进行）

---

### ADR-017: MCP 优雅降级 + Per-Agent 服务器覆盖

**Context**:
当前 MCP 服务器连接失败可能影响 Agent 启动。需要优雅降级和 per-Agent 配置。

**Decision**:
1. MCP 连接失败 → `Promise.allSettled` 模式，成功连接的继续用，失败的 skip + log
2. Per-Agent MCP 覆盖：`AGENT_MCP_<name>_ADD` / `_REMOVE` 环境变量允许细粒度控制

**Pros**:
- 韧性：单点 MCP 失败不影响整体
- 灵活性：不同 Agent 连接不同 MCP 服务器
- 可调试：日志记录失败原因

**Cons**:
- 可能隐藏配置错误
- Per-Agent 配置增加运维复杂度（企业环境）

**Alternative**:
- Fail-fast：简单但脆弱
- 全局 MCP：简单但不灵活

**Impact**: 低，增强现有 MCP 层

**建议采用**: **Yes** — 后续采用

---

### ADR-018: SOP 启动恢复扫描

**Context**:
AITest 平台重启后，正在运行的 SOP 可能处于"卡住"状态（in_progress 但无活跃执行）。

**Decision**:
启动时扫描所有 SOP Session，发现 in_progress 但无运行进程的 → 标记状态 + 提供恢复选项（从最后 checkpoint 继续或 reset）。

**Pros**:
- 不丢进度：意外宕机可从 checkpoint 恢复
- 自动发现：不需要人工排查
- LangGraph checkpoint 天然支持

**Cons**:
- 恢复可能引入不一致（checkpoint 不是事务性的）
- 需仔细处理边界情况

**Alternative**:
- 不做恢复：丢失进度
- 自动重跑：可能浪费资源

**Impact**: 低-中

**建议采用**: **Yes** — 后续采用

---

## 5. 最终架构建议

### 5.1 推荐架构全景

```
                        AITest Platform v1.0+
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        Project Workspace  Agent Registry  SOP Engine
         (.tlo/ + dir)    (YAML declarative) (LangGraph)
              │               │               │
              │               ▼               │
              │        Capability Router      │
              │     (Agent→Cap mapping)       │
              │               │               │
              ▼               ▼               ▼
        ┌─────────────────────────────────────────┐
        │          Capability Providers            │
        │  Browser │ RAG │ Codegen │ Execute       │
        │  Report  │ Validate │ Observe            │
        └─────────────────────────────────────────┘
              │               │               │
              ▼               ▼               ▼
        Context Guard   Security Layer   Provider Chain
        (85%/90% thresh) (3-layer sandbox) (retry+fallback)
              │               │               │
              ▼               ▼               ▼
        ┌─────────────────────────────────────────┐
        │          Testing Memory                  │
        │  Observer → Scratchpad → Trust Gate      │
        │  → Promotion → Structured Memory         │
        │  → Retrieval (ChromaDB + BM25)           │
        └─────────────────────────────────────────┘
              │
              ▼
        Observation Bus (Event Stream → Audit + UI SSE)
```

### 5.2 优先级路线图

#### 立即采用（已在 v1.0 架构中规划，立即实施）

| 模块 | AITest 实现 | 参考 Aperant |
|------|------------|-------------|
| **Capability Router** | `aitest/platform/capability_router/` | Agent Config 声明式映射 |
| **Provider Chain** | `aitest/llm/reliable_provider.py` | factory.ts + continuation.ts |
| **Security Layer** | `aitest/infra/security.py` | bash-validator + denylist |
| **Agent Capability 声明** | `governance/agents/*.yaml` 增强 | agent-configs.ts |

**为什么先做这些？**
基础能力层。没有 Capability Router，上层 Agent 无法安全调用能力。没有 Provider Chain，长 SOP 不可靠。没有 Security，企业不可用。

#### 后续采用（v1.0 后期或 v1.1，已有基础后增强）

| 模块 | AITest 实现 | 参考 Aperant |
|------|------------|-------------|
| **Context Window Guard** | `aitest/llm/context_window.py` | continuation.ts |
| **Complexity Router** | `aitest/platform/complexity/` | spec-orchestrator.ts |
| **Phase-Aware Model Selection** | `governance/sop/phase_config.yaml` | phase-config.ts |
| **MCP 优雅降级** | `aitest/mcp/` 增强 | mcp/client.ts |
| **SOP 恢复扫描** | `aitest/agents/agent_runner.py` | agent-manager.ts |

**为什么放后续？**
依赖基础层稳定。Context Window Guard 需要 Provider Chain 先可靠。Complexity Router 需要足够 SOP 数据才能校准 18 因子评分。

#### 长期规划（v1.2+，平台成熟后）

| 模块 | AITest 实现 | 参考 Aperant |
|------|------------|-------------|
| **Testing Memory (Observer)** | `aitest/platform/testing_memory.py` | Memory V5 observer |
| **Testing Memory (Retrieval)** | `aitest/platform/testing_memory_store.py` | retrieval pipeline |
| **Prompt 动态组装** | `governance/skills/` 增强 | subtask-prompt-generator |
| **Test Sandbox** | `aitest/platform/test_sandbox.py` | worktree manager |

**为什么放长期？**
Testing Memory 是差异化能力但实现复杂，需要先在真实运行中积累数据。Prompt 组装是优化，平台稳定后做。

#### 暂不采用

| Aperant 设计 | 原因 |
|-------------|------|
| Electron 桌面应用 | AITest 是 Web + CLI 平台 |
| Vercel AI SDK v6 | 技术栈不可迁移 |
| Worker Thread 执行 | Python asyncio 更自然 |
| Planner/Coder/QA 流水线 | Coding 流程 ≠ Testing 流程 |
| PR Review engine (18 agents) | 无此场景 |
| tree-sitter AST chunking | 测试场景无价值 |
| Graphiti MCP sidecar | ChromaDB 更简单 |
| libSQL/Turso | Python 生态用 ChromaDB + SQLite |
| 多账户 OAuth 轮换 | 企业用 API Key |
| Linear/Jira 集成 | 不涉及项目管理 |
| AGPL-3.0 开源模式 | 企业内部平台 |

---

## 6. 企业平台特有考量

Aperant 是面向独立开发者的开源桌面工具。AITest 是面向企业 QA 团队的内部平台。以下考量与具体设计无关，但影响架构决策：

### 6.1 可治理性 > 灵活性

开源工具允许用户任意修改配置、添加自定义 Agent、绕过限制。企业平台需要：
- **不可跳 Phase**：SOP Gate 是硬约束，Agent 不可跳过
- **审计追踪**：每次 Agent 决策、每次工具调用、每次 Memory 变更可追溯
- **配置变更审批**：Agent 能力声明变更需记录

### 6.2 多项目隔离 > 单项目优化

Aperant 优化单项目长期使用。AITest 需支持多项目并行：
- **Memory 按项目隔离**：`.tlo/memory/` 跟随项目，不走全局
- **SOP 配置按项目区分**：不同项目可能有不同 complexity 阈值
- **Provider 配额按项目预算**：重点项目可用 Opus，次要项目用 Haiku

### 6.3 团队协作 > 个人使用

Aperant 单人使用。AITest 需要：
- **Memory 共享**：Alice 发现的定位器模式，Bob 应受益
- **Skill 版本管理**：Skill 更新后不影响进行中的 SOP
- **角色权限**：不同角色可配置的 Agent 参数不同

### 6.4 稳定性 > 前沿性

企业平台不能因依赖不稳定而频繁故障：
- **减少外部依赖**：不依赖 MCP 服务器作为必须组件（全部 graceful degradation）
- **Provider 不锁定单一**：至少保留 2 个可用 provider
- **LangGraph 保持为主线**：不做无谓的技术栈切换

### 6.5 合规审计 > 功能迭代速度

- **测试证据链完整**：每个测试结果的产生过程可追溯
- **Memory 来源标记**：每条 Memory 记录来源（自动观察 / LLM 推断 / 人工标注）
- **不可篡改的执行日志**：Observation Bus 事件流为只追加

---

## 7. 总结

Aperant 最值得借鉴的**不是具体实现**，而是三个设计原则：

1. **声明式配置作为治理工具**：Agent 能力、工具权限、模型选择全部声明式注册，新增不改逻辑
2. **Observer-First Memory**：最有价值的记忆来自行为观察，非主动记录——这在测试领域同样成立（哪个定位器容易失败 = 观察重试模式）
3. **多层防御**：Provider 有重试+切换、上下文有守卫+continuation、工具有 denylist+validator+pre-exec hook——每层独立可 fail，整体可靠

AITest 应该借鉴这些原则，在测试领域重新实现——不照搬代码，不迁移实现，只提取设计思想。
