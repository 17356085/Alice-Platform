# ADR-002: Engine 职责边界

> 状态: 已决议 | 日期: 2026-07-01 | 更新: 2026-07-01 (Runtime 三层拆分)

---

## 背景

alice-engine SDK 从 aitest 平台中独立出来。需要明确 Engine 的职责边界，防止 Engine 退化为"什么都做"的大杂烩。

## 决策

**Engine 只负责四件事:**

```
Task Intake → Workflow → Runtime → RunResult
```

| 职责 | 说明 | 对应模块 |
|------|------|---------|
| Task Intake | 接收任务输入 (module, pages, mode) | `engine.py` |
| Workflow | SOP 编排 + Agent 调度 | `workflow/` |
| Runtime | 状态管理 + 检查点 + 事件总线 | `runtime/` |
| RunResult | 返回结构化执行结果 | `engine.py` |

## 五层架构

```
Engine
  ↓
Workflow (Orchestration) — 只依赖 Runtime 接口
  ↓
Runtime (Services) — 拆为 3 个子层
  ├── Core Runtime
  ├── Intelligence Runtime
  └── Observability Runtime
  ↓
Adapter (Ports) — 只有接口定义
  ↓
Extension (Hooks) — 被动监听
  ↓
Platform (Business) — 业务特有
```

### 判断标准

> **Engine 是否应该知道它?**

| 类型 | 判断 | 说明 |
|------|------|------|
| Runtime | ✅ Engine 主动依赖 | 参与控制流和执行过程 |
| Workflow | ✅ Engine 用它组织流程 | 编排和调度 |
| Adapter | ⚠️ Engine 只通过接口调用 | 不关心具体协议 |
| Extension | ❌ Engine 不依赖 | 被动通知，不影响执行 |
| Platform | ❌ 只有业务才需要 | AI Test 特有 |

### 依赖方向 (单向)

```
Engine → Workflow → Runtime → Adapter
                ↓
            Extension (被动)
                ↓
            Platform (业务)
```

**Workflow 只依赖 Runtime 接口，不依赖具体实现。**

---

## Runtime (三层拆分)

### Core Runtime — 执行基础

| 能力 | 说明 | 更新频率 |
|------|------|---------|
| Retry | 失败重试 | 稳定 |
| Checkpoint | 断点续跑 | 稳定 |
| Security | 安全防护 | 稳定 |
| ContextWindow | 上下文窗口管理 | 稳定 |
| CircuitBreaker | 熔断器 | 稳定 |

### Intelligence Runtime — 智能能力

| 能力 | 说明 | 更新频率 |
|------|------|---------|
| MemoryStore | 记住历史执行结果 | 可插拔 |
| KnowledgeStore | 执行前检索、执行后沉淀 | 可插拔 |
| DiffExtractor | 代码变更提取 | 可插拔 |

### Observability Runtime — 可观测性

| 能力 | 说明 | 更新频率 |
|------|------|---------|
| Tracing | Runtime Trace | 外部系统 |
| CostAuditor | 成本审计 | 外部系统 |
| OnlineMonitor | 执行在线监控 | 外部系统 |
| SafetyAuditor | 运行时安全检查 | 外部系统 |
| FailureAttributor | 失败归因分析 | 外部系统 |

---

## Workflow (Orchestration)

| 能力 | 说明 |
|------|------|
| SOPGraph | LangGraph SOP 编排 |
| SOPRunner | SOP 执行器 |
| ParallelSOP | 并行 SOP |
| Planner | 规划引擎 |
| AgentLoop | Agent 执行循环 |

**Workflow 只依赖 Runtime 接口，不依赖具体实现。**

---

## Adapter (Ports — 接口定义)

| 接口 | 说明 | 包 |
|------|------|-----|
| LLMProvider | LLM 调用 | alice-engine |
| ToolProvider | 工具调用 | alice-engine |

**SDK 只定义接口，不关心具体协议 (MCP/HTTP/Browser)。**

适配器实现按需安装:
- `alice-engine-mcp` — MCP 协议实现
- `alice-engine-http` — HTTP 传输实现
- `alice-engine-browser` — 浏览器自动化实现

---

## Extension (Hooks — 被动监听)

| 扩展 | 说明 |
|------|------|
| TestComplexity | 业务复杂度 |
| KnowledgeReporter | 知识报告 |
| SlackNotify | 通知 |
| MetricsExporter | 指标导出 |

---

## Platform (Business — 业务特有)

| 模块 | 说明 |
|------|------|
| Web Dashboard | Web UI |
| Auth | 认证授权 |
| Multi-tenant | 多租户 |
| Report | 测试报告 |
| Governance | 治理规则 |

---

## 包结构

```
alice-engine (核心 SDK)
├── Engine, Project, RunResult
├── Core Runtime: Retry, Checkpoint, Security, ContextWindow
├── Intelligence Runtime: Memory, Knowledge, DiffExtractor
├── Observability Runtime: Tracing, CostAudit, Monitor, Safety
├── Workflow: SOPGraph, Planner, AgentLoop
├── Adapter 接口: LLMProvider, ToolProvider
└── 不依赖 MCP, HTTP, Browser

alice-engine-mcp (独立适配器包 — 按需安装)
├── 实现 ToolProvider
├── 实现 MCP Client/Server
├── 依赖 mcp 库
└── 通用生态协议，其他 Agent 也能用

aitest (平台)
├── 使用 alice-engine
├── 按需安装 alice-engine-mcp
├── 注册测试相关工具
├── 管理 governance/skills/报告
└── AI Test 业务特有
```

---

## Engine 公开 API (v0.3)

```python
class Engine:
    def __init__(
        project: Project,
        llm_provider: str,
        event_bus: EventBus,               # Core Runtime
        knowledge: KnowledgeStore,         # Intelligence Runtime
        memory: MemoryStore,               # Intelligence Runtime
        tool_provider: ToolProvider,       # Adapter (可选)
        extensions: list[Extension],       # Extensions
    )
    def run(module, pages, mode) -> RunResult
    def run_async(module, pages, mode) -> RunResult
    def validate() -> ValidationResult
    def list_modules() -> list[str]
    def add_extension(ext) -> None
```

---

## 演进规则

| Engine 行数 | 动作 |
|------------|------|
| < 300 | 保持单文件 |
| 300-800 | 拆 `api/engine.py` + `core/` |
| 800+ | 拆 `workflow/` + `runtime/` |

**按演进拆，不按想象拆。**

---

## 关联

- [[ADR_001_TLO_DIRECTORY]] — .tlo/ 项目目录设计
- `packages/alice-engine/` — SDK 包实现
