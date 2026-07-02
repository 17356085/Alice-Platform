# Platform Dependency Matrix

> 架构解耦分析 — 文档 2/7
> 目标: 识别 Engine 与 Platform 的所有耦合点，三层分类: Core / Extensions / Platform
> 注: 05 升级为四层 (Core/Runtime/Workflow/Adapter)，07 提供迁移地图

## 1. 依赖分类标准

| 分类 | 含义 | 处理方式 |
|------|------|----------|
| **Core (MUST)** | 串行必须，移除则无法完成一次 SOP 执行 | 保留在 Engine 中 |
| **Extensions (SHOULD)** | 可插拔子引擎，各自有独立执行逻辑，增强但不串入核心链路 | 接口抽象 + 可选注入 |
| **Platform (MUST NOT)** | 运维/商业逻辑，不属于引擎 | 从 Engine 依赖图中移除 |

## 2. 逐模块依赖分析

### 2.1 Core (MUST) — 串行必须

这些模块构成最小执行路径，移除任何一个则无法完成一次 SOP 执行。

**核心链路**: `SOPGraph → AgentLoop → SkillExecutor → LLMProvider → 产物写入`

| 模块 | 文件 | 被谁依赖 | 依赖原因 |
|------|------|----------|----------|
| **SOPGraph** | `graphs/sop_graph.py` | sop_runner.py | 顶层编排图，Engine 的核心 |
| **SOPRunner** | `graphs/sop_runner.py` | cli.py, server | CompiledGraph.invoke() 驱动 |
| **SOPState** | `graphs/state.py` | sop_graph.py, nodes.py | LangGraph State 定义 |
| **AgentNode** | `graphs/nodes.py` | sop_graph.py | make_agent_loop_node() 工厂 |
| **Checkpoint** | `graphs/checkpoint.py` | sop_graph.py, sop_runner.py | resume 能力 |
| **ExecutionGraph** | `graphs/execution_graph.py` | sop_graph.py | execution/report/knowledge 子图 |
| **BugAnalysisGraph** | `graphs/bug_analysis_graph.py` | sop_graph.py | bug 分析子图 |
| **AgentRunner** | `agents/agent_runner.py` | nodes.py | AgentLoop 执行引擎 |
| **SkillExecutor** | `agents/skill_executor.py` | agent_runner.py | Skill 加载+执行 |
| **TaskStateMachine** | `agents/task_state_machine.py` | agent_runner.py | Agent 状态管理 |
| **RunnerState** | `agents/runner_state.py` | agent_runner.py | 任务状态模型 |
| **LLMProvider** | `llm/provider.py` | agent_runner.py, skill_executor.py | LLM 调用接口 |
| **ReliableProvider** | `llm/reliable_provider.py` | provider.py | Retry + Fallback |
| **ContextWindow** | `llm/context_window.py` | agent_runner.py | Token 管理 + 续传 |
| **PromptAdapter** | `llm/prompt_adapter.py` | agent_runner.py | Provider 格式化 |
| **SkillLoader** | `llm/skill_loader.py` | skill_executor.py | .md Skill 文件读取 |
| **SkillYamlParser** | `llm/skill_yaml_parser.py` | skill_loader.py | Skill YAML 解析 |
| **GovernanceGate** | `llm/governance_gate.py` | agent_runner.py | 生成前检查 |
| **GovernanceConnector** | `llm/governance_connector.py` | agent_runner.py | Agent ↔ Governance |
| **SecureSubprocess** | `infra/secure_subprocess.py` | sop_graph.py (data_sanitization) | 安全执行外部命令 |
| **CommandValidator** | `infra/security/command_validator.py` | secure_subprocess.py | 命令白名单 |
| **PlatformPaths** | `platform/paths.py` | sop_graph.py, agent_runner.py | 路径解析 |
| **ProjectContext** | `platform/context.py` | paths.py, agent_runner.py | 活跃项目 |
| **Config** | `config.py` | 全局 | .env + YAML 配置 |
| **Governance** | `governance/` | skill_loader.py, skill_executor.py | agents/*.yaml, skills/*.md |

**Core 内部的 Mock 需求** (Standalone 模式下替换):

| 模块 | 用途 | Mock 方案 |
|------|------|-----------|
| **EventBus (audit)** | exit_node 中 emit(CycleEnd, StateDrift) | NoopEventBus: 空实现 |
| **ErrorLogger** | log_error() 错误记录 | 标准 logging |
| **ContextBuilder** | 构建 LLM 上下文 | 简化实现 |
| **CircuitBreaker** | LLM Provider 熔断 | 直通实现 |

### 2.2 Extensions (SHOULD) — 可插拔子引擎

这些模块各自有独立执行逻辑，是**子引擎**而非工具函数。它们增强 Engine 能力但不串入核心链路。当前代码中通过 try/except 或条件判断调用，失败不影响主流程。

| 子引擎 | 模块 | 独立职责 | 当前集成方式 | 增强能力 |
|--------|------|----------|-------------|----------|
| **Capability Router** | `platform/capability_router/` | Agent ↔ Provider 路由 | AgentRunner 直接 `get_llm_provider()`，未经过 Router | 自动选择最优 Provider (cost/latency/quality) |
| **Complexity Classifier** | `platform/complexity/` | SOP 流水线路由 | `resolve_sop_pipeline()` 可选调用 | 按复杂度选择 SIMPLE/STANDARD/COMPLEX 流水线 |
| **Knowledge + RAG** | `knowledge/` | 知识检索 + 沉淀 | knowledge_agent 写 .md，不调 RAG | 跨 Run 知识复用，减少重复 LLM 调用 |
| **Testing Memory** | `platform/testing_memory.py` | ChromaDB 向量记忆 | ObservationBus 自动同步，AgentLoop 不直接读写 | 跨 Run 记忆: 记住已知 Bug、已覆盖场景 |
| **Memory Observer** | `platform/memory_observer.py` | Memory 自动同步 | 随 Testing Memory 一起工作 | Memory 生命周期管理 |
| **Browser-Use** | `discovery/browser_use.py` | AI 浏览器探索 | `bu_heal` fixture，仅 dev 环境 | 自动探索页面结构，生成 Page Object |
| **BU Adapter** | `bu_adapter.py` | Browser-Use 适配 | 随 Browser-Use 一起工作 | Skill ↔ BrowserUseDriver 桥接 |
| **Audit Engine** | `audit_engine/` | 质量审计 (6 维) | `exit_node` 中 try/except 调用 | 状态漂移检测 + SOP 合规检查 |
| **Context Builder** | `llm/context_builder.py` | 上下文压缩 | AgentRunner 中可选使用 | 减少 Token 消耗 |

#### 为什么 Extensions 不在 Core 中

追踪 `sop_graph.py → nodes.py → agent_runner.py` 的实际 import 链:

| Extension | 核心链路是否 import | 证据 |
|-----------|---------------------|------|
| Capability Router | ❌ | AgentRunner 用 `get_llm_provider()` 直接获取 Provider |
| Complexity | ❌ | `resolve_sop_pipeline()` 存在但 `sop_runner.py` 不调用 |
| Knowledge + RAG | ❌ | knowledge_agent 写 .md，不调 RAG 检索 |
| Testing Memory | ❌ | AgentLoop 不直接读写 ChromaDB |
| Browser-Use | ❌ | 仅 `bu_heal` fixture，SOP 不调用 |
| Audit Engine | ⚠️ 部分 | exit_node 调了，但 try/except 包着，失败不影响执行 |

### 2.3 Platform (MUST NOT) — 不属于引擎

这些模块是纯 Platform 层功能，Engine 执行链路不直接依赖。

| 模块 | 文件 | 用途 | 为什么不属于 Engine |
|------|------|------|---------------------|
| **Web API** | `server/` 全部 | HTTP 接口 | Engine 直接调用 Python API |
| **Chat** | `chat/` | 意图解析 | Engine 接收结构化输入 |
| **Session Store** | `server/session_store.py` | 多用户会话 | Engine 单次执行 |
| **Auth** | `server/auth.py` | 认证授权 | Engine 无认证需求 |
| **ObservationBus** | `platform/observation_bus.py` | 事件广播+Memory同步 | Engine 用 EventBus 即可 |
| **RunStore** | `platform/run_store.py` | 执行历史 | Engine 不管理历史 |
| **Run** | `platform/run.py` | Run 对象模型 | Engine 用 dict 即可 |
| **ExecutionService** | `platform/execution_service.py` | 多 Run 并发 | Engine 单次执行 |
| **ExecutionRequest** | `platform/execution_request.py` | 请求验证 | Engine 直接接收参数 |
| **RunEvent** | `platform/run_event.py` | Run 生命周期事件 | Engine 无此需求 |
| **Lifecycle** | `platform/lifecycle/` | 资源生命周期 | Engine 无状态 |
| **Tenant** | `platform/tenant.py` | 多租户 | Engine 单租户 |
| **Organization** | `platform/organization.py` | 团队管理 | Engine 无此需求 |
| **Workspace** | `platform/workspace.py` | 工作区隔离 | Engine 无此需求 |
| **Ownership** | `platform/ownership.py` | 资源归属 | Engine 无此需求 |
| **PluginSystem** | `platform/plugin.py` | 动态扩展 | Engine 用内置 |
| **Artifacts** | `platform/artifacts.py` | 跨 Run 产物管理 | Engine 直接写文件 |
| **ArtifactLineage** | `platform/artifact_lineage.py` | 产物血缘 | Engine 无此需求 |
| **AuditLog** | `platform/audit_log.py` | 平台审计 | Engine 无此需求 |
| **Timeline** | `platform/timeline.py` | 时间线可视化 | Engine 无此需求 |
| **TTLSet** | `platform/ttl_set.py` | 缓存过期 | Engine 无缓存 |
| **Discovery** | `discovery/` | 页面发现 | Engine 接收 pages 参数 |
| **Hooks** | `platform/hooks/` | Billing/Metrics/Webhook | Engine 无此需求 |
| **Consumer** | `platform/consumer.py` | 事件消费者 | Engine 无此需求 |
| **EventBus (platform)** | `platform/event_bus.py` | 增强事件总线 | Engine 用 audit event_bus |
| **CostAdvisor** | `cost_advisor.py` | 成本建议 | Engine 无此需求 |
| **Testing** | `testing/` | 压测/回归/评估 | Engine 无此需求 |
| **MCP** | `mcp/` | Model Context Protocol | Engine 无此需求 |
| **IDE** | `ide/` | IDE 集成 | Engine 无此需求 |
| **Integrations** | `integrations/` | GitHub/Jira | Engine 无此需求 |
| **CLI** | `infra/cli/` | 命令行界面 | Engine 用 Python API |
| **Web Frontend** | `web/` | React Dashboard | Engine 无此需求 |

## 3. 依赖热力图

```
                     Core     Extensions  Platform
                     (MUST)   (SHOULD)    (MUST NOT)
graphs/              ████     ░░          ░░
agents/              ████     ░░          ░░
llm/                 ████     █░          ░░
infra/               ██░░     ░░          ░░
platform/paths       ██░░     ░░          ░░
platform/context     ██░░     ░░          ░░
platform/cap_router  ░░░░     ████        ░░
platform/complexity  ░░░░     ████        ░░
platform/memory      ░░░░     ████        ░░
platform/ (其他)     ░░░░     ░░          ████
audit_engine/        ░░░░     ████        ░░
knowledge/           ░░░░     ████        ░░
discovery/           ░░░░     ████        ░░
server/              ░░░░     ░░          ████
governance/          ████     ░░          ░░
config.py            ██░░     ░░          ░░
```

## 4. 关键耦合点详解

### 4.1 EventBus 耦合 → Core Mock

**位置**: `sop_graph.py` exit_node, `agent_runner.py`

**问题**: Engine 在 exit_node 中调用 `emit("CycleEnd", ...)`, `emit("StateDrift", ...)` 等事件。这些事件被 Platform 层的 ObservationBus、Hooks、Metrics 消费。

**解耦方案**:

```python
# Engine 内部接口
class EventBus(Protocol):
    def emit(self, event_type: str, **kwargs) -> None: ...

# Standalone 实现
class NoopEventBus:
    def emit(self, event_type: str, **kwargs) -> None:
        pass  # 静默丢弃

# Platform 实现
class PlatformEventBus:
    def emit(self, event_type: str, **kwargs) -> None:
        # → ObservationBus → Hooks → Metrics → Webhooks
        ...
```

### 4.2 Audit Engine → Extension

**位置**: `sop_graph.py` exit_node

**问题**: exit_node 中调用 StateAuditor + SOPAuditor，这两个模块依赖 Platform 的产物路径和配置。

**当前状态**: try/except 包着，失败不影响执行。**这是 Extension 的典型特征**。

**解耦方案**: 将审计注册为可选 Extension:

```python
class Engine:
    def __init__(self, extensions=None):
        self.extensions = extensions or []

    def run(self, module, pages, mode, run_id):
        result = self._execute_sop(module, pages, mode, run_id)
        # Extensions 在核心执行完成后运行
        for ext in self.extensions:
            ext.on_cycle_end(module, result)
        return result
```

### 4.3 Capability Router → Extension

**位置**: `platform/capability_router/`

**当前状态**: AgentRunner 直接 `get_llm_provider()`，不经过 Router。

**增强能力**: 自动选择最优 Provider (cost/latency/quality)。

**解耦方案**: 注入 Provider 选择策略:

```python
class Engine:
    def __init__(self, provider_selector=None):
        self.provider_selector = provider_selector  # CapabilityRouter

    def _get_provider(self, agent_name, task_type):
        if self.provider_selector:
            return self.provider_selector.select(agent_name, task_type)
        return get_llm_provider()  # 默认行为
```

### 4.4 Complexity Classifier → Extension

**位置**: `platform/complexity/`

**当前状态**: `resolve_sop_pipeline()` 存在但 `sop_runner.py` 不调用。

**增强能力**: 按复杂度选择 SIMPLE/STANDARD/COMPLEX 流水线。

**解耦方案**: 注入流水线选择策略:

```python
class Engine:
    def __init__(self, pipeline_selector=None):
        self.pipeline_selector = pipeline_selector  # ComplexityClassifier

    def run(self, module, pages, mode, run_id):
        if self.pipeline_selector:
            pipeline = self.pipeline_selector.resolve(module, pages)
            # 使用推荐的 pipeline
        # ... 默认行为
```

### 4.5 Knowledge + RAG → Extension

**位置**: `knowledge/`

**当前状态**: knowledge_agent 写 .md，不调 RAG 检索。

**增强能力**: 跨 Run 知识复用，减少重复 LLM 调用。

**解耦方案**: 注入知识检索:

```python
class Engine:
    def __init__(self, knowledge_store=None):
        self.knowledge_store = knowledge_store  # RAGEngine

    def _build_context(self, module, page):
        context = build_default_context(module, page)
        if self.knowledge_store:
            relevant = self.knowledge_store.search(module, page)
            context["knowledge"] = relevant
        return context
```

### 4.6 Testing Memory → Extension

**位置**: `platform/testing_memory.py`, `platform/memory_observer.py`

**当前状态**: ObservationBus 自动同步，AgentLoop 不直接读写。

**增强能力**: 跨 Run 记忆: 记住已知 Bug、已覆盖场景。

**解耦方案**: 注入记忆层:

```python
class Engine:
    def __init__(self, memory=None):
        self.memory = memory  # TestingMemory

    def run(self, module, pages, mode, run_id):
        if self.memory:
            # 注入历史记忆到 AgentLoop 上下文
            past_runs = self.memory.query(module)
            initial_state["memory"] = past_runs
        # ... 执行
```

### 4.7 Browser-Use → Extension

**位置**: `discovery/browser_use.py`, `bu_adapter.py`

**当前状态**: `bu_heal` fixture，仅 dev 环境。

**增强能力**: 自动探索页面结构，生成 Page Object。

**解耦方案**: 注入页面发现:

```python
class Engine:
    def __init__(self, page_discovery=None):
        self.page_discovery = page_discovery  # BrowserUseDiscovery

    def run(self, module, pages, mode, run_id):
        if not pages and self.page_discovery:
            pages = self.page_discovery.discover(module)
        # ... 执行
```

### 4.8 LLM Provider 耦合 → Core

**位置**: `llm/provider.py`, `llm/reliable_provider.py`

**问题**: LLM Provider 是 Engine 的核心依赖，但它依赖 API Key (.env) 和网络。

**解耦方案**: 保持 Core，但提供 Mock Provider 用于测试:

```python
class MockLLMProvider:
    def chat(self, messages, **kwargs):
        return {"content": "[Mock] 测试输出", "usage": {...}}
```

### 4.9 Platform Paths 耦合 → Core

**位置**: `platform/paths.py`, `platform/context.py`

**问题**: 路径解析依赖 ProjectContext 和 .tlo/ 目录结构。

**解耦方案**: 保持 Core，但简化配置:

```python
# Standalone 模式: 直接指定路径
ENGINE_WORKSTUDY = os.environ.get("ENGINE_WORKSTUDY", ".")
ENGINE_GOVERNANCE = os.environ.get("ENGINE_GOVERNANCE", "./governance")
```

## 5. 依赖统计

| 分类 | 模块数 | 占比 |
|------|--------|------|
| **Core (MUST)** | 24 | 22% |
| **Extensions (SHOULD)** | 9 | 8% |
| **Platform (MUST NOT)** | 77 | 70% |
| **总计** | 110 | 100% |

**结论**: Engine Core 仅需 22% 的模块完成一次完整执行。Extensions 提供 8 个可插拔子引擎增强能力。
