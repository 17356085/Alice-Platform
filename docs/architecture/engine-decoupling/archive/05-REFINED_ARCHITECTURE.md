# Refined Standalone Engine Architecture

> 架构解耦分析 — 文档 5/7
> 起因: 对 01-04 的评审反馈，核心问题是"Core 还是太胖"
> 目标: 四层拆解 — Core / Runtime / Workflow / Adapter
> 后续: 07-MIGRATION_MAP.md 提供从当前代码到此目标态的迁移路径

## 1. 问题诊断

上一版的三层分类:

```
Core (MUST)       — 24 个文件，串行必须
Extensions (SHOULD) — 9 个子引擎
Platform (MUST NOT) — 77 个模块
```

**问题**: Core 里塞了太多"不是 Engine 本质"的东西。

| 模块 | 为什么不该在 Core |
|------|-------------------|
| `reliable_provider.py` | 3x Retry + Fallback — 这是**弹性策略**，不是执行本质 |
| `context_window.py` | Token 监控 + 续传 — 这是**资源管理**，不是执行本质 |
| `checkpoint.py` | SQLite 持久化 — 这是**状态持久化**，不是执行本质 |
| `governance_gate.py` | 生成前检查 — 这是**合规策略**，不是执行本质 |
| `governance_connector.py` | Agent ↔ Governance — 这是**治理集成**，不是执行本质 |
| `secure_subprocess.py` | 安全 subprocess — 这是**安全策略**，不是执行本质 |
| `command_validator.py` | 命令白名单 — 这是**安全策略**，不是执行本质 |

**真正 Core 的只有**:

```
接收任务 → 规划步骤 → 执行步骤 → 返回结果
```

## 2. 四层架构

```
┌─────────────────────────────────────────────────────────────────┐
│  Layer 0: Core — Engine 的本质                                   │
│  "一个任务怎么从输入变成输出"                                      │
│                                                                  │
│  Engine.run(task) → Plan → Execute → Result                     │
│                                                                  │
│  只有 4 个职责:                                                  │
│    1. 接收任务 (Task Intake)                                     │
│    2. 规划步骤 (Planner)                                         │
│    3. 执行步骤 (Executor)                                        │
│    4. 管理状态 (StateMachine)                                    │
├─────────────────────────────────────────────────────────────────┤
│  Layer 1: Runtime — 让 Core 可靠运行                              │
│  "怎么跑得稳"                                                    │
│                                                                  │
│  Retry / Fallback / Checkpoint / Resume / Context Window        │
│  Governance / Security / Error Handling                          │
├─────────────────────────────────────────────────────────────────┤
│  Layer 2: Workflow — 让 Core 理解业务                             │
│  "跑什么流程"                                                    │
│                                                                  │
│  SOP Graph / Phase 定义 / 路由规则 / 门禁逻辑                    │
│  当前: LangGraph 实现                                            │
│  未来: Workflow Interface 抽象 → LangGraph / Temporal / 自研 DAG │
├─────────────────────────────────────────────────────────────────┤
│  Layer 3: Adapter — 让 Core 连接外部世界                          │
│  "怎么和外面打交道"                                               │
│                                                                  │
│  LLM Adapter / Browser Adapter / Knowledge Adapter              │
│  Audit Adapter / Memory Adapter / Event Adapter                 │
└─────────────────────────────────────────────────────────────────┘
```

## 3. 每层详解

### 3.1 Layer 0: Core — Engine 的本质

**只有一个问题**: 一个任务怎么从输入变成输出?

```
Task
  ↓
Plan (拆解为步骤)
  ↓
Execute (逐步执行)
  ↓
Result (返回结果)
```

**4 个模块**:

| 模块 | 职责 | 当前对应 |
|------|------|----------|
| **Task Intake** | 接收任务，验证输入，创建执行上下文 | `create_initial_state()` |
| **Planner** | 将任务拆解为可执行步骤 | `sop_graph.py` 的图结构 |
| **Executor** | 执行单个步骤 | `agent_runner.py` 的 `_execute_skill()` |
| **StateMachine** | 管理执行状态，决定下一步 | `task_state_machine.py` + `runner_state.py` |

**Core 的接口**:

```python
class Engine:
    """Engine 的本质: 任务 → 结果。"""

    def run(self, task: Task, context: Context = None) -> Result:
        """
        Args:
            task:   要执行的任务 (结构化描述)
            context: 执行上下文 (可选)

        Returns:
            Result: 执行结果
        """
        plan = self.planner.plan(task, context)
        state = StateMachine(plan)

        while state.has_next():
            step = state.next()
            result = self.executor.execute(step, context)
            state.update(result)

        return state.to_result()
```

**Core 不关心的事**:

- 用什么 LLM → Adapter
- 失败了要不要重试 → Runtime
- 用什么图引擎 → Workflow
- 怎么持久化状态 → Runtime
- 怎么做合规检查 → Runtime
- 怎么连接浏览器 → Adapter

### 3.2 Layer 1: Runtime — 让 Core 可靠运行

**一个问题**: 怎么跑得稳?

| 模块 | 职责 | 当前对应 |
|------|------|----------|
| **Retry/Fallback** | 失败重试 + Provider 降级 | `reliable_provider.py` |
| **Checkpoint/Resume** | 状态持久化 + 断点恢复 | `checkpoint.py` |
| **Context Window** | Token 监控 + 续传 + 摘要 | `context_window.py` |
| **Governance** | 合规检查 + 门禁 | `governance_gate.py`, `governance_connector.py` |
| **Security** | 命令白名单 + 路径校验 | `secure_subprocess.py`, `command_validator.py` |
| **Error Handling** | 错误记录 + 分类 | `error_logger.py` |

**Runtime 的接口**:

```python
class Runtime:
    """Runtime 增强: 让 Core 可靠运行。"""

    def wrap_executor(self, executor: Executor) -> Executor:
        """包装 Executor，加入 Retry/Checkpoint/Security 等增强。"""
        ...

    def wrap_planner(self, planner: Planner) -> Planner:
        """包装 Planner，加入 Governance 检查。"""
        ...
```

**Runtime 的关键设计**: 装饰器模式。Core 不知道 Runtime 的存在，Runtime 通过包装 Core 的 Executor/Planner 来增强能力。

### 3.3 Layer 2: Workflow — 让 Core 理解业务

**一个问题**: 跑什么流程?

| 模块 | 职责 | 当前对应 |
|------|------|----------|
| **Workflow Interface** | 流程引擎抽象 | 新增 |
| **LangGraph Adapter** | LangGraph 实现 | `sop_graph.py`, `sop_runner.py` |
| **SOP Definition** | Phase 定义 + 路由规则 | `state.py`, `nodes.py` |
| **Gate Logic** | 质量门禁 | `testcase_quality_gate_node` |

**Workflow Interface**:

```python
class WorkflowEngine(Protocol):
    """流程引擎抽象 — 不绑定具体实现。"""

    def build(self, definition: WorkflowDefinition) -> CompiledWorkflow:
        """构建流程。"""
        ...

    def execute(self, workflow: CompiledWorkflow, initial_state: dict) -> dict:
        """执行流程。"""
        ...


class LangGraphEngine:
    """LangGraph 实现。"""

    def build(self, definition):
        # → StateGraph(definition.state_schema)
        # → 添加节点和边
        # → compile()
        ...

    def execute(self, workflow, initial_state):
        # → workflow.invoke(initial_state)
        ...


class TemporalEngine:
    """未来: Temporal 实现。"""

    def build(self, definition):
        # → Temporal workflow definition
        ...

    def execute(self, workflow, initial_state):
        # → temporal_client.execute_workflow(...)
        ...
```

**为什么要抽象**: 当前 Engine 和 LangGraph 绑死了。`sop_graph.py` 直接使用 `StateGraph`, `add_node`, `add_conditional_edges` 等 LangGraph API。如果未来要换 Temporal 或自研 DAG，需要重写整个图层。

**抽象的好处**:

- 今天: `LangGraphEngine` 包装现有 `sop_graph.py`
- 明天: `TemporalEngine` 替换实现
- 后天: `SimpleDagEngine` 轻量级 DAG 引擎

### 3.4 Layer 3: Adapter — 让 Core 连接外部世界

**一个问题**: 怎么和外面打交道?

| Adapter | 职责 | 当前对应 | 未来可替换为 |
|---------|------|----------|-------------|
| **LLM Adapter** | 统一 LLM 调用接口 | `llm/provider.py` | OpenAI SDK / 自建 Gateway |
| **Browser Adapter** | 浏览器操作 | `discovery/browser_use.py` | Playwright / Puppeteer / CDP |
| **Knowledge Adapter** | 知识检索 + 沉淀 | `knowledge/rag_engine.py` | ChromaDB / Pinecone / 自建 |
| **Memory Adapter** | 跨 Run 记忆 | `platform/testing_memory.py` | ChromaDB / Redis / 文件 |
| **Audit Adapter** | 质量审计 | `audit_engine/` | 自建 / 外部 QA 平台 |
| **Event Adapter** | 事件广播 | `audit_engine/event_bus.py` | 内部 EventBus / Kafka / Webhook |
| **Filesystem Adapter** | 文件读写 | 直接 Path 操作 | 本地 / S3 / OSS |

**Adapter 的接口**:

```python
class LLMAdapter(Protocol):
    """LLM 调用抽象。"""

    def chat(self, messages: list, model: str = None, **kwargs) -> dict:
        """同步调用。"""
        ...

    def chat_stream(self, messages: list, model: str = None, **kwargs):
        """流式调用。"""
        ...


class BrowserAdapter(Protocol):
    """浏览器操作抽象。"""

    def navigate(self, url: str) -> None: ...
    def click(self, selector: str) -> None: ...
    def fill(self, selector: str, value: str) -> None: ...
    def screenshot(self) -> bytes: ...


class KnowledgeAdapter(Protocol):
    """知识检索抽象。"""

    def search(self, query: str, limit: int = 5) -> list: ...
    def ingest(self, content: dict) -> None: ...
```

**Adapter vs Extension 的区别**:

- **Adapter**: 连接外部系统 (LLM, Browser, DB)，是 Core 的**依赖**
- **Extension**: 增强 Engine 能力 (Audit, Complexity)，是 Core 的**可选增强**

Browser-Use 是 Adapter 不是 Extension，因为 Core 需要通过它来操作浏览器，它是执行链路的一部分。

## 4. 依赖关系图

```
Core (Layer 0)
  │
  │ 依赖 (必须)
  ├──→ Workflow (Layer 2)    ← 定义"跑什么流程"
  │     └──→ LangGraphAdapter
  │
  │ 依赖 (必须)
  ├──→ LLM Adapter (Layer 3) ← 调用 LLM
  │
  │ 增强 (可选)
  ├──→ Runtime (Layer 1)     ← 让执行更可靠
  │     ├──→ Retry/Fallback
  │     ├──→ Checkpoint
  │     ├──→ Context Window
  │     ├──→ Governance
  │     └──→ Security
  │
  │ 增强 (可选)
  ├──→ Adapters (Layer 3)    ← 连接外部系统
  │     ├──→ Browser Adapter
  │     ├──→ Knowledge Adapter
  │     ├──→ Memory Adapter
  │     └──→ Audit Adapter
  │
  └──→ Extensions (原 Layer 2) ← 增强能力
        ├──→ Complexity
        └──→ (其他)
```

## 5. 目录结构 (目标)

```
aitest/
├── engine/                          ← Layer 0: Core
│   ├── __init__.py                  ← Engine 类 (Task → Result)
│   ├── task.py                      ← Task / Context / Result 模型
│   ├── planner.py                   ← Planner 接口
│   ├── executor.py                  ← Executor 接口
│   └── state_machine.py             ← StateMachine
│
├── runtime/                         ← Layer 1: Runtime
│   ├── retry.py                     ← Retry/Fallback
│   ├── checkpoint.py                ← Checkpoint/Resume
│   ├── context_window.py            ← Token 管理
│   ├── governance.py                ← 合规检查
│   ├── security.py                  ← 安全策略
│   └── error_handling.py            ← 错误处理
│
├── workflow/                        ← Layer 2: Workflow
│   ├── interface.py                 ← WorkflowEngine 接口
│   ├── langgraph/                   ← LangGraph 实现
│   │   ├── engine.py                ← LangGraphEngine
│   │   ├── sop_graph.py             ← SOP 编排图
│   │   ├── state.py                 ← SOPState
│   │   └── nodes.py                 ← Agent 节点
│   └── definition/                  ← 流程定义 (数据)
│       └── test_sop.yaml            ← 测试 SOP 定义
│
├── adapters/                        ← Layer 3: Adapters
│   ├── llm/                         ← LLM Adapter
│   │   ├── interface.py             ← LLMAdapter 接口
│   │   ├── anthropic.py             ← Anthropic 实现
│   │   ├── deepseek.py              ← DeepSeek 实现
│   │   └── openai.py                ← OpenAI 实现
│   ├── browser/                     ← Browser Adapter
│   │   ├── interface.py             ← BrowserAdapter 接口
│   │   └── playwright.py            ← Playwright 实现
│   ├── knowledge/                   ← Knowledge Adapter
│   │   ├── interface.py             ← KnowledgeAdapter 接口
│   │   └── chromadb.py              ← ChromaDB 实现
│   ├── memory/                      ← Memory Adapter
│   │   ├── interface.py             ← MemoryAdapter 接口
│   │   └── chromadb.py              ← ChromaDB 实现
│   └── event/                       ← Event Adapter
│       ├── interface.py             ← EventAdapter 接口
│       ├── noop.py                  ← Noop 实现
│       └── platform.py              ← Platform 实现
│
├── governance/                      ← 静态文件 (不属于任何层)
│   ├── agents/
│   ├── skills/
│   └── context/
│
├── platform/                        ← Platform Services (不属于 Engine)
│   ├── server/
│   ├── dashboard/
│   ├── tenant/
│   ├── billing/
│   └── ...
│
└── demo.py                          ← 入口
```

## 6. 与当前代码的映射

| 当前文件 | 目标层 | 目标位置 |
|----------|--------|----------|
| `graphs/sop_graph.py` | Layer 2 | `workflow/langgraph/sop_graph.py` |
| `graphs/sop_runner.py` | Layer 2 | `workflow/langgraph/engine.py` |
| `graphs/state.py` | Layer 2 | `workflow/langgraph/state.py` |
| `graphs/nodes.py` | Layer 2 | `workflow/langgraph/nodes.py` |
| `graphs/checkpoint.py` | Layer 1 | `runtime/checkpoint.py` |
| `graphs/execution_graph.py` | Layer 2 | `workflow/langgraph/execution.py` |
| `graphs/bug_analysis_graph.py` | Layer 2 | `workflow/langgraph/bug_analysis.py` |
| `agents/agent_runner.py` | Layer 0 | `engine/executor.py` |
| `agents/skill_executor.py` | Layer 0 | `engine/executor.py` |
| `agents/task_state_machine.py` | Layer 0 | `engine/state_machine.py` |
| `agents/runner_state.py` | Layer 0 | `engine/task.py` |
| `llm/provider.py` | Layer 3 | `adapters/llm/interface.py` |
| `llm/reliable_provider.py` | Layer 1 | `runtime/retry.py` |
| `llm/context_window.py` | Layer 1 | `runtime/context_window.py` |
| `llm/prompt_adapter.py` | Layer 3 | `adapters/llm/prompt.py` |
| `llm/skill_loader.py` | Layer 0 | `engine/planner.py` |
| `llm/governance_gate.py` | Layer 1 | `runtime/governance.py` |
| `infra/secure_subprocess.py` | Layer 1 | `runtime/security.py` |
| `platform/paths.py` | Layer 1 | `runtime/paths.py` |
| `platform/context.py` | Layer 1 | `runtime/context.py` |
| `config.py` | Layer 1 | `runtime/config.py` |
| `audit_engine/event_bus.py` | Layer 3 | `adapters/event/interface.py` |
| `audit_engine/state_auditor.py` | Layer 3 | `adapters/audit/state.py` |
| `discovery/browser_use.py` | Layer 3 | `adapters/browser/playwright.py` |
| `knowledge/rag_engine.py` | Layer 3 | `adapters/knowledge/chromadb.py` |
| `platform/testing_memory.py` | Layer 3 | `adapters/memory/chromadb.py` |

## 7. 演进路线

不要一步到位。按层逐步剥离。

### Phase 1: 现在 (已完成)

```
Engine (当前)
  ├── engine/__init__.py    ← Engine 类
  ├── engine/mocks.py       ← Mock 模块
  └── engine/extensions/    ← Extensions
```

### Phase 2: 抽离 Workflow Interface

```
引擎不直接依赖 LangGraph，而是通过接口调用。

workflow/
  ├── interface.py          ← WorkflowEngine 协议
  └── langgraph/
      └── engine.py         ← 包装现有 sop_graph.py
```

### Phase 3: 抽离 Runtime

```
将 Retry/Checkpoint/Governance 从 agent_runner.py 中拆出。

runtime/
  ├── retry.py
  ├── checkpoint.py
  ├── governance.py
  └── security.py
```

### Phase 4: 抽离 Adapters

```
将 LLM/Browser/Knowledge 从核心链路中解耦。

adapters/
  ├── llm/
  ├── browser/
  ├── knowledge/
  └── memory/
```

### Phase 5: Core 提纯

```
最终 Core 只剩 4 个文件:

engine/
  ├── task.py          ← Task / Context / Result
  ├── planner.py       ← Planner
  ├── executor.py      ← Executor
  └── state_machine.py ← StateMachine
```

## 8. 与上一版的关系

```
上一版 (01-04):
  Core (MUST)     = 24 个文件
  Extensions       = 9 个文件
  Platform         = 77 个文件

本版 (05):
  Layer 0: Core    = 4 个文件 (task, planner, executor, state_machine)
  Layer 1: Runtime = 7 个文件 (retry, checkpoint, context, governance, security, error, config)
  Layer 2: Workflow = 6 个文件 (interface + langgraph/*)
  Layer 3: Adapter = 8 个文件 (llm, browser, knowledge, memory, event, audit, filesystem)
  Extensions       = 2 个文件 (complexity, ...)
  Platform         = 77 个文件

变化:
  - Core 从 24 → 4 (减 83%)
  - 新增 Runtime (7) + Workflow (6) + Adapter (8) = 21 个文件
  - 总文件数不变，但分层更清晰
```
