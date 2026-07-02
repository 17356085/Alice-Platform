# Engine 架构解耦

> 分层解耦设计 — 从单体到四层架构
> 详细设计见 `archive/` 目录，本文档是统一视图

## 1. 问题

当前 Engine 代码中，"引擎本质"与"运行时增强"、"外部系统连接"、"平台服务"混在一起。`agent_runner.py` 1370 行，`sop_graph.py` 1500 行，Core、Runtime、Adapter 逻辑交织，无法独立测试、独立部署、独立替换。

**目标**: 把 Engine 拆成四层，每层有明确职责、清晰接口、单向依赖。

## 2. 四层架构

```text
┌─────────────────────────────────────────────────────────────────┐
│  Layer 0: Core — Engine 的本质                                   │
│  "一个任务怎么从输入变成输出"                                      │
│  Task Intake → Planner → Executor → StateMachine → Result       │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Runtime — 让 Core 可靠运行                              │
│  "怎么跑得稳"                                                    │
│  Retry / Fallback / Checkpoint / Resume / Context Window        │
│  Governance / Security / Error Handling / Config / Paths        │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Workflow — 让 Core 理解业务                             │
│  "跑什么流程"                                                    │
│  SOP Graph / Phase 定义 / 路由规则 / 门禁逻辑                    │
│  当前: LangGraph 实现                                            │
│  未来: Workflow Interface 抽象 (暂缓，等有第二个引擎需求)          │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Adapter — 让 Core 连接外部世界                          │
│  "怎么和外面打交道"                                               │
│  LLM Adapter / Browser Adapter / Knowledge Adapter              │
│  Memory Adapter / Audit Adapter / Event Adapter                 │
└─────────────────────────────────────────────────────────────────┘
```

### 2.1 依赖规则

```text
允许:
  Core (L0)      ──依赖──→  Workflow (L2)     定义"跑什么流程"
  Core (L0)      ──依赖──→  LLM Adapter (L3)  调用 LLM
  Core (L0)      ──依赖──→  Event Adapter (L3) 发射事件
  Runtime (L1)   ──包装──→  Core (L0) 的 Executor/Planner
  Workflow (L2)  ──调用──→  Core (L0) 的 Executor (通过节点工厂)

禁止:
  Core      ──✗──→  Runtime    (Core 不知道 Runtime 的存在)
  Core      ──✗──→  Platform   (Core 不依赖平台)
  Workflow  ──✗──→  Runtime    (Workflow 不直接包装)
  Adapter   ──✗──→  Core       (Adapter 是独立实现，只实现接口)
```

### 2.2 每层职责

| 层 | 职责 | 文件数 | 关键设计 |
| --- | --- | --- | --- |
| **Core** | 接收任务 → 规划步骤 → 执行步骤 → 返回结果 | 4 | 最小接口，无外部依赖 |
| **Runtime** | 让 Core 可靠运行 (Retry/Checkpoint/Security) | 7 | 装饰器模式，包装 Core 的 Executor/Planner |
| **Workflow** | 定义"跑什么流程" (SOP Graph) | 6 | 当前直接用 LangGraph，暂不抽象接口 |
| **Adapter** | 连接外部系统 (LLM/Browser/DB/Event) | 8 | Protocol 接口，实现可替换 |

## 3. Layer 0: Core — Engine 的本质

**只有一个问题**: 一个任务怎么从输入变成输出?

```text
Task
  ↓
Plan (拆解为步骤)
  ↓
Execute (逐步执行)
  ↓
Result (返回结果)
```

### 3.1 四个模块

| 模块 | 职责 | 当前对应 |
|------|------|----------|
| **task.py** | Task / Context / Result 模型，AgentState | `agents/runner_state.py`, `agents/agent_runner.py` 基础属性 |
| **planner.py** | 将任务拆解为可执行步骤，Skill 加载 | `agents/plan_engine.py`, `llm/skill_loader.py` |
| **executor.py** | 执行单个步骤，Skill 链执行 | `agents/agent_runner.py` 核心循环, `agents/skill_executor.py` |
| **state_machine.py** | 管理执行状态，决定下一步 | `agents/task_state_machine.py`, `agents/state_updater.py` |

### 3.2 Core 接口

```python
class Engine:
    """Engine 的本质: 任务 → 结果。"""

    def run(self, task: Task, context: Context = None) -> Result:
        plan = self.planner.plan(task, context)
        state = StateMachine(plan)

        while state.has_next():
            step = state.next()
            result = self.executor.execute(step, context)
            state.update(result)

        return state.to_result()
```

### 3.3 Core 不关心的事

| 不关心 | 由谁负责 |
|--------|----------|
| 用什么 LLM | Adapter (LLM) |
| 失败了要不要重试 | Runtime (Retry) |
| 用什么图引擎 | Workflow (LangGraph) |
| 怎么持久化状态 | Runtime (Checkpoint) |
| 怎么做合规检查 | Runtime (Governance) |
| 怎么连接浏览器 | Adapter (Browser) |

## 4. Layer 1: Runtime — 让 Core 可靠运行

**一个问题**: 怎么跑得稳?

| 模块 | 职责 | 当前对应 |
|------|------|----------|
| **retry.py** | Retry/Fallback + Provider 降级 | `llm/reliable_provider.py` |
| **checkpoint.py** | 状态持久化 + 断点恢复 | `graphs/checkpoint.py` |
| **context_window.py** | Token 监控 + 续传 + 摘要 | `llm/context_window.py` |
| **governance.py** | 合规检查 + 门禁 | `llm/governance_gate.py`, `llm/governance_connector.py` |
| **security.py** | 命令白名单 + 路径校验 | `infra/secure_subprocess.py`, `infra/security/command_validator.py` |
| **error_handling.py** | 错误记录 + 分类 | `infra/error_logger.py` |
| **config.py** + **paths.py** + **context.py** | 配置 + 路径 + 项目上下文 | `config.py`, `platform/paths.py`, `platform/context.py` |

### 4.1 Runtime 的关键设计: 装饰器模式

Core 不知道 Runtime 的存在。Runtime 通过包装 Core 的 Executor/Planner 来增强能力:

```python
class Runtime:
    def wrap_executor(self, executor: Executor) -> Executor:
        """包装 Executor，加入 Retry/Checkpoint/Security 等增强。"""
        reliable = ReliableProvider(...)
        window = ContextWindowMonitor(...)

        class EnhancedExecutor:
            def execute(self, skill_id, context):
                window.check()
                result = reliable.complete(...)
                window.add_usage(...)
                return result

        return EnhancedExecutor()
```

## 5. Layer 2: Workflow — 让 Core 理解业务

**一个问题**: 跑什么流程?

| 模块 | 职责 | 当前对应 |
|------|------|----------|
| **langgraph/sop_graph.py** | SOP 编排图 + 路由 | `graphs/sop_graph.py` |
| **langgraph/runner.py** | CompiledGraph.invoke() 驱动 | `graphs/sop_runner.py` |
| **langgraph/state.py** | SOPState TypedDict | `graphs/state.py` |
| **langgraph/nodes.py** | Agent 节点工厂 | `graphs/nodes.py` |
| **langgraph/execution.py** | execution/report/knowledge 子图 | `graphs/execution_graph.py` |
| **langgraph/bug_analysis.py** | Bug 分析子图 | `graphs/bug_analysis_graph.py` |

### 5.1 Workflow 抽象 (暂缓)

当前 LangGraph 是唯一实现，抽象层增加间接性但没有收益。**只做物理隔离**（`workflow/langgraph/` 目录），接口提取等有第二个引擎需求时再做。

## 6. Layer 3: Adapter — 让 Core 连接外部世界

**一个问题**: 怎么和外面打交道?

| Adapter | 职责 | 当前对应 | 未来可替换为 |
|---------|------|----------|-------------|
| **LLM** | 统一 LLM 调用接口 | `llm/provider.py` | OpenAI SDK / 自建 Gateway |
| **Browser** | 浏览器操作 | `discovery/browser_use.py` | Playwright / Puppeteer / CDP |
| **Knowledge** | 知识检索 + 沉淀 | `knowledge/rag_engine.py` | ChromaDB / Pinecone / 自建 |
| **Memory** | 跨 Run 记忆 | `platform/testing_memory.py` | ChromaDB / Redis / 文件 |
| **Audit** | 质量审计 | `audit_engine/` | 自建 / 外部 QA 平台 |
| **Event** | 事件广播 | `audit_engine/event_bus.py` | 内部 EventBus / Kafka / Webhook |

### 6.1 Adapter 接口 (Protocol)

```python
class LLMAdapter(Protocol):
    def chat(self, messages: list, model: str = None, **kwargs) -> dict: ...
    def chat_stream(self, messages: list, model: str = None, **kwargs): ...

class BrowserAdapter(Protocol):
    def navigate(self, url: str) -> None: ...
    def click(self, selector: str) -> None: ...
    def fill(self, selector: str, value: str) -> None: ...
    def screenshot(self) -> bytes: ...

class KnowledgeAdapter(Protocol):
    def search(self, query: str, limit: int = 5) -> list: ...
    def ingest(self, content: dict) -> None: ...

class EventBus(Protocol):
    def emit(self, event_type: str, **kwargs) -> None: ...
```

### 6.2 Adapter vs Extension

| 维度 | Adapter | Extension |
| --- | --- | --- |
| **关系** | Core 的**依赖** | Core 的**可选增强** |
| **何时用** | 执行链路必须调用 | 增强能力但不串入核心链路 |
| **例子** | LLM, Event | Audit, Complexity, Knowledge |

## 7. 目标目录结构

```text
aitest/
├── engine/                          ← Layer 0: Core
│   ├── __init__.py                  ← Engine 类 (Task → Result)
│   ├── task.py                      ← Task / Context / Result / AgentState
│   ├── planner.py                   ← Planner + Skill 加载
│   ├── executor.py                  ← Executor + Skill 链执行
│   └── state_machine.py             ← StateMachine + 状态转换
│
├── runtime/                         ← Layer 1: Runtime
│   ├── retry.py                     ← Retry/Fallback (ReliableProvider)
│   ├── checkpoint.py                ← Checkpoint/Resume (SQLite)
│   ├── context_window.py            ← Token 管理 + 续传
│   ├── governance.py                ← 合规检查 + 门禁
│   ├── security.py                  ← 命令白名单 + 路径校验
│   ├── error_handling.py            ← 错误记录
│   ├── config.py                    ← .env + YAML 配置
│   ├── paths.py                     ← 路径解析
│   └── context.py                   ← 项目上下文 (ProjectContext)
│
├── workflow/                        ← Layer 2: Workflow
│   └── langgraph/                   ← LangGraph 实现
│       ├── sop_graph.py             ← SOP 编排图
│       ├── runner.py                ← CompiledGraph.invoke()
│       ├── state.py                 ← SOPState
│       ├── nodes.py                 ← Agent 节点工厂
│       ├── execution.py             ← execution/report/knowledge 子图
│       └── bug_analysis.py          ← Bug 分析子图
│
├── adapters/                        ← Layer 3: Adapters
│   ├── llm/
│   │   ├── interface.py             ← LLMAdapter Protocol
│   │   ├── anthropic.py             ← Anthropic 实现
│   │   ├── deepseek.py              ← DeepSeek 实现
│   │   └── openai.py                ← OpenAI 实现
│   ├── event/
│   │   ├── interface.py             ← EventBus Protocol + NoopEventBus
│   │   └── platform.py              ← PlatformEventBus
│   ├── audit/
│   │   ├── state.py                 ← StateAuditor
│   │   └── sop.py                   ← SOPAuditor
│   ├── browser/
│   │   ├── interface.py             ← BrowserAdapter Protocol
│   │   └── playwright.py            ← Playwright 实现
│   ├── knowledge/
│   │   ├── interface.py             ← KnowledgeAdapter Protocol
│   │   └── chromadb.py              ← ChromaDB 实现
│   └── memory/
│       ├── interface.py             ← MemoryAdapter Protocol
│       └── chromadb.py              ← ChromaDB 实现
│
├── extensions/                      ← 可插拔子引擎 (原 Layer 2 Extensions)
│   ├── audit.py                     ← Audit Engine Extension
│   ├── complexity.py                ← Complexity Classifier
│   ├── knowledge.py                 ← Knowledge + RAG
│   └── memory.py                    ← Testing Memory
│
├── governance/                      ← 静态文件 (不属于任何层)
│   ├── agents/                      ← Agent 定义 YAML
│   ├── skills/                      ← Skill 提示 .md
│   └── context/                     ← shared-language.md
│
├── server/                          ← Platform (不属于 Engine)
├── web/                             ← Platform
├── chat/                            ← Platform
└── config.py                        ← 全局配置入口
```

## 8. 模块归属总览

### 8.1 当前代码 → 目标层映射

| 当前文件 | 目标层 | 目标位置 |
|----------|--------|----------|
| `agents/agent_runner.py` | Core | `engine/executor.py` (核心循环) + `engine/task.py` (属性) + `engine/planner.py` (规划) + `engine/state_machine.py` (状态判定) |
| `agents/runner_state.py` | Core | `engine/task.py` |
| `agents/task_state_machine.py` | Core | `engine/state_machine.py` |
| `agents/plan_engine.py` | Core | `engine/planner.py` |
| `agents/state_updater.py` | Core | `engine/state_machine.py` |
| `agents/skill_executor.py` | Core | `engine/executor.py` |
| `llm/skill_loader.py` | Core | `engine/planner.py` |
| `llm/reliable_provider.py` | Runtime | `runtime/retry.py` |
| `llm/context_window.py` | Runtime | `runtime/context_window.py` |
| `graphs/checkpoint.py` | Runtime | `runtime/checkpoint.py` |
| `llm/governance_gate.py` | Runtime | `runtime/governance.py` |
| `llm/governance_connector.py` | Runtime | `runtime/governance.py` |
| `infra/secure_subprocess.py` | Runtime | `runtime/security.py` |
| `infra/security/command_validator.py` | Runtime | `runtime/security.py` |
| `infra/error_logger.py` | Runtime | `runtime/error_handling.py` |
| `platform/paths.py` | Runtime | `runtime/paths.py` |
| `platform/context.py` | Runtime | `runtime/context.py` |
| `config.py` | Runtime | `runtime/config.py` |
| `graphs/sop_graph.py` | Workflow | `workflow/langgraph/sop_graph.py` |
| `graphs/sop_runner.py` | Workflow | `workflow/langgraph/runner.py` |
| `graphs/state.py` | Core + Workflow | `engine/task.py` (AgentResult) + `workflow/langgraph/state.py` (SOPState) |
| `graphs/nodes.py` | Workflow | `workflow/langgraph/nodes.py` |
| `graphs/execution_graph.py` | Workflow | `workflow/langgraph/execution.py` |
| `graphs/bug_analysis_graph.py` | Workflow | `workflow/langgraph/bug_analysis.py` |
| `llm/provider.py` | Adapter | `adapters/llm/interface.py` |
| `llm/prompt_adapter.py` | Adapter | `adapters/llm/prompt.py` |
| `audit_engine/event_bus.py` | Adapter | `adapters/event/interface.py` |
| `audit_engine/state_auditor.py` | Adapter | `adapters/audit/state.py` |
| `audit_engine/sop_auditor.py` | Adapter | `adapters/audit/sop.py` |
| `discovery/browser_use.py` | Adapter | `adapters/browser/playwright.py` |
| `knowledge/rag_engine.py` | Adapter | `adapters/knowledge/chromadb.py` |
| `platform/testing_memory.py` | Adapter | `adapters/memory/chromadb.py` |

### 8.2 统计

| 分类 | 当前文件数 | 目标文件数 | 占比 |
|------|-----------|-----------|------|
| Core (L0) | 8 (分散) | 4 (集中) | 15% |
| Runtime (L1) | 11 (分散) | 9 (集中) | 35% |
| Workflow (L2) | 6 | 6 | 23% |
| Adapter (L3) | 7 (分散) | 8 (集中) | 31% |
| Extensions | 9 | 4 | — |
| Platform | 77 | 77 (不动) | — |

## 9. 迁移路径

**核心原则**: 先剥离"不改变执行逻辑"的模块（Runtime），再剥离"有独立接口"的模块（Adapter），最后拆分"代码最复杂"的模块（Core）。

```text
Phase 0 (2.5天)  热力图标注 + 目录创建 + 依赖检查脚本
Phase 1 (5天)    Runtime 层剥离 (最安全，收益最大)
Phase 2 (3天)    LLM/Event Adapter 接口提取
Phase 3 (3天)    Core 提纯 (agent_runner.py 拆分)
Phase 4 (暂缓)   Workflow 抽象 (等有第二个引擎需求)
```

### 9.1 Phase 0: 准备 (2.5 天)

| 步骤 | 产出 | 时间 |
|------|------|------|
| 热力图标注 | 每个函数有 `[LAYER:...]` 归属注释 | 1 天 |
| 文件搬迁表 Review | 团队签字确认 | 0.5 天 |
| 创建目标目录结构 | `engine/`, `runtime/`, `workflow/`, `adapters/` + `__init__.py` | 0.5 天 |
| 依赖检查脚本 | `tools/check_layer_deps.py`，CI 把关 | 0.5 天 |

### 9.2 Phase 1: Runtime 剥离 (5 天)

按搬迁表把 Runtime 相关文件从原位置搬到 `runtime/`，原位置留 re-export 保证零破坏:

**搬迁顺序** (先搬被依赖少的):
1. `runtime/config.py` ← `config.py`
2. `runtime/paths.py` ← `platform/paths.py`
3. `runtime/context.py` ← `platform/context.py`
4. `runtime/security.py` ← `infra/secure_subprocess.py` + `infra/security/command_validator.py`
5. `runtime/error_handling.py` ← `infra/error_logger.py`
6. `runtime/retry.py` ← `llm/reliable_provider.py`
7. `runtime/context_window.py` ← `llm/context_window.py`
8. `runtime/checkpoint.py` ← `graphs/checkpoint.py`
9. `runtime/governance.py` ← `llm/governance_gate.py` + `llm/governance_connector.py`

每搬一个文件，跑一次 `pytest` 确认无回归。

### 9.3 Phase 2: Adapter 接口提取 (3 天)

1. `adapters/llm/interface.py` ← `llm/provider.py` (仅接口定义)
2. `adapters/llm/prompt.py` ← `llm/prompt_adapter.py`
3. `adapters/event/interface.py` ← `audit_engine/event_bus.py`
4. `adapters/audit/state.py` ← `audit_engine/state_auditor.py`
5. `adapters/audit/sop.py` ← `audit_engine/sop_auditor.py`

Browser/Knowledge/Memory 是 Extension，暂不搬迁。

### 9.4 Phase 3: Core 提纯 (3 天)

最复杂，需要拆分 `agent_runner.py`（1370 行）:

**拆分策略**: 先搬后拆。

1. 先把 `agent_runner.py` 整体搬到 `engine/executor.py`
2. 把 `runner_state.py` 搬到 `engine/task.py`
3. 把 `task_state_machine.py` + `state_updater.py` 搬到 `engine/state_machine.py`
4. 把 `plan_engine.py` + `skill_loader.py` 搬到 `engine/planner.py`
5. 从 `engine/executor.py` 中逐步提取:
   - Task 相关代码 → `engine/task.py`
   - Planner 相关代码 → `engine/planner.py`
   - StateMachine 相关代码 → `engine/state_machine.py`

### 9.5 Phase 4: Workflow 抽象 (暂缓)

条件: 当有第二个 Workflow 引擎需求时才做。当前只做物理隔离（`workflow/langgraph/` 目录）。

### 9.6 验收标准

| Phase | 验收条件 |
|-------|----------|
| Phase 0 | 所有函数有 `[LAYER:...]` 归属注释；搬迁表签字确认；目录创建完成；依赖检查脚本 CI 通过 |
| Phase 1 | 所有文件搬到目标目录；原位置 re-export 正常；全量 pytest 通过；`python demo.py --module equipment --mock-llm` 正常运行 |
| Phase 2 | Core 代码不直接 import Runtime 模块；Core 代码不直接 import 具体 Adapter 实现；LLM/Event 接口提取完成 |
| Phase 3 | Core 只剩 4 个文件 (task/planner/executor/state_machine)；Core 不 import Runtime/Adapter 的具体实现 |

## 10. 与 Platform 的关系

```text
完整 Platform:
  Engine Core + All Extensions + Web API + Dashboard + Auth + Tenant + ...

Standalone Engine (Core only):
  Engine Core + NoopEventBus + Mocks

Standalone Engine (with Extensions):
  Engine Core + AuditExtension + ComplexityExtension + KnowledgeExtension + ...

切换方式:
  1. 完整 Platform:     python -m aitest.server.main
  2. Standalone Core:   python demo.py --module equipment
  3. Standalone + Ext:  python demo.py --module equipment --extensions audit,complexity
```

**设计原则**:

1. Engine Core 不修改任何现有代码
2. Extensions 通过接口注入，不硬编码到 Core
3. Extensions 可独立测试和演示
4. 完整 Platform 仍然正常工作

## 11. 最小启动清单

```text
必须有:
  1. Python 3.10+
  2. .env (至少一个 LLM API Key)
  3. .tlo/project.yaml (项目配置: URL, 技术, 框架)
  4. governance/ (Agent 定义 + Skill 提示)
  5. .tlo/knowledge/modules/ (模块+页面目录)

不需要:
  ✗ Web API (server/)
  ✗ Dashboard (web/)
  ✗ Database
  ✗ Redis
  ✗ ChromaDB
  ✗ Docker
  ✗ 任何 Platform 模块
```

## 12. 详细设计文档

本文档是统一视图。详细设计见 `archive/` 目录:

| 文档 | 内容 |
|------|------|
| `archive/01-ENGINE_BOUNDARY.md` | 三层分类详解 (Core/Extensions/Platform) |
| `archive/02-PLATFORM_DEPENDENCY_MATRIX.md` | 110 模块依赖矩阵 + 耦合点详解 |
| `archive/03-STANDALONE_ENGINE_ARCHITECTURE.md` | Engine 类设计 + Extension 实现示例 |
| `archive/04-DEMO_EXECUTION_FLOW.md` | demo.py 执行流程 + 使用示例 |
| `archive/05-REFINED_ARCHITECTURE.md` | 四层架构详解 (Core/Runtime/Workflow/Adapter) |
| `archive/06-ENGINE_DEMO_GUIDE.md` | 最小启动指南 + project.yaml 说明 |
| `archive/07-MIGRATION_MAP.md` | agent_runner.py 热力图 + 全量搬迁表 + 时间线 |
| `archive/07-CLI_INTERRUPT_HANDLER_DESIGN.md` | CLI 中断处理器设计 (9 个暂停点) |
| `archive/08-PHASE0_PROJECT_SETUP.md` | Phase 0 交互式配置设计 |
