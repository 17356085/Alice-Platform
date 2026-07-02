# Engine Boundary

> 架构解耦分析 — 文档 1/7
> 目标: 定义 Engine 的职责边界，三层分类: Core / Extensions / Platform
> 注: 05 升级为四层 (Core/Runtime/Workflow/Adapter)，07 提供迁移地图

## 1. Engine 定义

**Engine** 是负责"接收任务 → 编排 Agent → 执行 Skill 链 → 输出产物"的可运行核心。

一次完整的 Engine 执行链路:
```
输入(module, pages, mode)
  → SOP 图编排 (LangGraph StateGraph)
    → Preflight 扫描
    → Phase 路由 (条件边)
      → AgentLoop 执行 Skill 链
        → LLM 调用 (Skill 提示 → 产出)
      → 产物写入 (.md / .py)
    → 状态更新 (completed_phases)
  → 退出 (写 SOP_STATUS.json)
```

## 2. 三层分类

```
┌─────────────────────────────────────────────────────────────────────┐
│  Layer 1: Engine Core (MUST)                                        │
│  "怎么跑" — 串行必须，移除则无法执行                                  │
│  SOP 编排 → Agent 执行 → LLM 调用 → 产物输出                         │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 2: Engine Extensions (SHOULD)                                │
│  "跑得更好" — 可插拔子引擎，各自有独立执行逻辑                         │
│  能力路由 / 复杂度评估 / 知识检索 / 记忆管理 / 浏览器探索 / 质量审计   │
├─────────────────────────────────────────────────────────────────────┤
│  Layer 3: Platform Services (MUST NOT)                              │
│  "谁在跑" — 运维/商业逻辑，不属于引擎                                │
│  Web API / Dashboard / Auth / Tenant / Billing / Metrics           │
└─────────────────────────────────────────────────────────────────────┘
```

## 3. Layer 1: Engine Core (MUST)

串行必须 — 这些模块构成最小执行路径，移除任何一个则无法完成一次 SOP 执行。

| 职责 | 模块 | 说明 |
|------|------|------|
| **SOP 图编排** | `graphs/sop_graph.py` | LangGraph StateGraph 构建 + 条件路由 |
| **图执行引擎** | `graphs/sop_runner.py` | CompiledGraph.invoke() 驱动 |
| **执行子图** | `graphs/execution_graph.py` | execution/report/knowledge 子图 |
| **Bug 分析子图** | `graphs/bug_analysis_graph.py` | HITL + 自动修复循环 |
| **Agent 状态定义** | `graphs/state.py` | TypedDict SOPState |
| **Agent 节点工厂** | `graphs/nodes.py` | make_agent_loop_node() |
| **Checkpoint** | `graphs/checkpoint.py` | SQLite 持久化 + resume |
| **AgentLoop 执行** | `agents/agent_runner.py` | Skill 链执行引擎 |
| **Skill 调度** | `agents/skill_executor.py` | Skill 加载 + 执行 + HITL |
| **Runner 状态** | `agents/runner_state.py` | 任务状态机 |
| **Task 状态机** | `agents/task_state_machine.py` | Agent 状态机 (9 种状态) |
| **LLM 调用** | `llm/provider.py` | 统一 LLM 接口 |
| **LLM 可靠层** | `llm/reliable_provider.py` | 3x Retry + 3 Provider Fallback |
| **上下文窗口** | `llm/context_window.py` | Token 监控 + 续传 + DeepSeek 摘要 |
| **Prompt 适配** | `llm/prompt_adapter.py` | Provider-specific 格式化 |
| **Skill 加载** | `llm/skill_loader.py` | .md Skill 文件读取 |
| **Skill YAML** | `llm/skill_yaml_parser.py` | Skill 元数据解析 |
| **Governance Gate** | `llm/governance_gate.py` | 生成前 Governance 检查 |
| **Governance 连接器** | `llm/governance_connector.py` | Agent ↔ Governance 桥接 |
| **安全子进程** | `infra/secure_subprocess.py` | subprocess 安全 wrapper |
| **命令校验** | `infra/security/command_validator.py` | 命令白名单 + 路径校验 |
| **路径解析** | `platform/paths.py` | 项目路径统一解析 |
| **项目上下文** | `platform/context.py` | 活跃项目 + .tlo/ |
| **配置** | `config.py` | .env + YAML 配置 |
| **Governance 文件** | `governance/` | agents/*.yaml, skills/*.md, shared-language.md |

**核心链路**:
```
SOPGraph → AgentLoop → SkillExecutor → LLMProvider → 产物写入
```

## 4. Layer 2: Engine Extensions (SHOULD)

可插拔子引擎 — 各自有独立执行逻辑，增强 Engine 能力但不串入核心链路。当前代码中它们是**旁路增强**，通过 try/except 或条件判断调用，失败不影响主流程。

| 子引擎 | 模块 | 独立职责 | 当前集成方式 | 增强能力 |
|--------|------|----------|-------------|----------|
| **Capability Router** | `platform/capability_router/` | Agent ↔ Provider 路由 | AgentRunner 中直接 `get_llm_provider()`，未经过 Router | 自动选择最优 Provider (cost/latency/quality) |
| **Complexity Classifier** | `platform/complexity/` | SOP 流水线路由 | `resolve_sop_pipeline()` 可选调用 | 按复杂度选择 SIMPLE/STANDARD/COMPLEX 流水线 |
| **Knowledge + RAG** | `knowledge/` | 知识检索 + 沉淀 | knowledge_agent 节点写 .md，不调 RAG | 跨 Run 知识复用，减少重复 LLM 调用 |
| **Testing Memory** | `platform/testing_memory.py` | ChromaDB 向量记忆 | ObservationBus 自动同步，AgentLoop 不直接读写 | 跨 Run 记忆: 记住已知 Bug、已覆盖场景 |
| **Memory Observer** | `platform/memory_observer.py` | Memory 自动同步 | 随 Testing Memory 一起工作 | Memory 生命周期管理 |
| **Browser-Use** | `discovery/browser_use.py` | AI 浏览器探索 | `bu_heal` fixture，仅 dev 环境 | 自动探索页面结构，生成 Page Object |
| **BU Adapter** | `bu_adapter.py` | Browser-Use 适配 | 随 Browser-Use 一起工作 | Skill ↔ BrowserUseDriver 桥接 |
| **Audit Engine** | `audit_engine/` | 质量审计 (6 维) | `exit_node` 中 try/except 调用 StateAuditor + SOPAuditor | 状态漂移检测 + SOP 合规检查 |
| **Context Builder** | `llm/context_builder.py` | 上下文压缩 | AgentRunner 中可选使用 | 减少 Token 消耗 |

### 4.1 为什么它们是"引擎"

每个 Extension 都有:
- **独立的执行逻辑** — 不是简单的工具函数，是有状态、有决策的子系统
- **明确的输入/输出** — 有清晰的接口契约
- **可独立运行** — 理论上可以脱离 SOP 流水线单独调用

### 4.2 为什么它们不在 Core 中

追踪 `sop_graph.py → nodes.py → agent_runner.py` 的实际 import 链:

| Extension | 核心链路是否 import | 证据 |
|-----------|---------------------|------|
| Capability Router | ❌ | AgentRunner 用 `get_llm_provider()` 直接获取 Provider |
| Complexity | ❌ | `resolve_sop_pipeline()` 存在但 `sop_runner.py` 不调用 |
| Knowledge + RAG | ❌ | knowledge_agent 写 .md，不调 RAG 检索 |
| Testing Memory | ❌ | AgentLoop 不直接读写 ChromaDB |
| Browser-Use | ❌ | 仅 `bu_heal` fixture，SOP 不调用 |
| Audit Engine | ⚠️ | exit_node 调了，但 try/except 包着，失败不影响执行 |

## 5. Layer 3: Platform Services (MUST NOT)

运维/商业逻辑 — 不属于引擎，是平台层的用户管理、监控、计费等能力。

| 职责 | 模块 | 为什么不属于 Engine |
|------|------|---------------------|
| **Web API** | `server/` | 用户交互层，Engine 无需 HTTP |
| **Chat UI** | `server/api/chat.py` | Dashboard 功能 |
| **Session 管理** | `server/session_store.py` | 多用户会话，Engine 单次执行 |
| **认证** | `server/auth.py` | 平台安全，非执行安全 |
| **Dashboard** | `infra/cli/dashboard_cmds.py` | 可视化监控 |
| **Observation Bus** | `platform/observation_bus.py` | 事件广播，Engine 用 EventBus 即可 |
| **Operational Metrics** | `platform/operational_metrics.py` | Prometheus 指标 |
| **Run Store** | `platform/run_store.py` | 执行历史管理 |
| **Execution Service** | `platform/execution_service.py` | 多 Run 并发编排 |
| **Execution Request** | `platform/execution_request.py` | 请求验证 + TTL |
| **Run Event** | `platform/run_event.py` | Run 生命周期事件广播 |
| **Lifecycle Registry** | `platform/lifecycle/` | 资源生命周期管理 |
| **Tenant** | `platform/tenant.py` | 多租户隔离 |
| **Organization** | `platform/organization.py` | 团队管理 |
| **Workspace** | `platform/workspace.py` | 用户工作区隔离 |
| **Ownership** | `platform/ownership.py` | 资源归属 |
| **Plugin System** | `platform/plugin.py` | 动态扩展，Engine 用内置 Provider |
| **Artifacts** | `platform/artifacts.py` | 跨 Run 产物管理 |
| **Artifact Lineage** | `platform/artifact_lineage.py` | 产物血缘 |
| **Audit Log** | `platform/audit_log.py` | 平台审计日志 |
| **Timeline** | `platform/timeline.py` | 执行时间线可视化 |
| **TTL Set** | `platform/ttl_set.py` | 缓存过期管理 |
| **Discovery** | `discovery/` | 页面自动发现 |
| **Hooks** | `platform/hooks/` | Billing, Metrics, Webhook |
| **Consumer** | `platform/consumer.py` | 事件消费者基类 |
| **Event Bus (Platform)** | `platform/event_bus.py` | 增强事件总线 |
| **Error Logger** | `infra/error_logger.py` | 增强错误日志 |
| **All CLI** | `infra/cli/` | 命令行界面 |
| **Web Frontend** | `web/` | React Dashboard |
| **MCP** | `mcp/` | Model Context Protocol |
| **IDE Integration** | `ide/` | IDE 插件 |
| **Integrations** | `integrations/` | GitHub, Jira 等 |
| **Chat** | `chat/` | 意图解析 |
| **Cost Advisor** | `cost_advisor.py` | 成本建议 |
| **Testing Tools** | `testing/` | 压测、回归、评估 |

## 6. 边界图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     Platform Services (MUST NOT)                        │
│                                                                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌─────────────┐  │
│  │ Web API  │ │Dashboard │ │  Hooks   │ │  Tenant  │ │  Metrics    │  │
│  │ server/  │ │ CLI/     │ │billing/  │ │ Auth/    │ │ Prometheus  │  │
│  │          │ │dashboard │ │webhook/  │ │ Session  │ │             │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └─────────────┘  │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                     Engine Extensions (SHOULD)                          │
│                                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │
│  │ Capability  │ │ Complexity  │ │ Knowledge   │ │ Testing Memory  │  │
│  │ Router      │ │ Classifier  │ │ + RAG       │ │ + Observer      │  │
│  │             │ │             │ │             │ │                 │  │
│  │ 自动选择    │ │ 自动选择    │ │ 知识检索    │ │ 跨 Run 记忆     │  │
│  │ 最优Provider│ │ SOP流水线   │ │ +沉淀       │ │                 │  │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘  │
│                                                                         │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐                      │
│  │ Browser-Use │ │ Audit       │ │ Context     │                      │
│  │ + BU Adapter│ │ Engine      │ │ Builder     │                      │
│  │             │ │             │ │             │                      │
│  │ AI 浏览器   │ │ 6 维质量    │ │ 上下文压缩  │                      │
│  │ 页面探索    │ │ 审计        │ │             │                      │
│  └─────────────┘ └─────────────┘ └─────────────┘                      │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                     Engine Core (MUST)                                  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ SOP Graph (LangGraph)                                             │  │
│  │  entry → preflight → route ─┬→ project_agent ─→ route            │  │
│  │                              ├→ requirement_agent ─→ route        │  │
│  │                              ├→ test_design_agent ─→ qgate        │  │
│  │                              ├→ automation ─→ hitl ─→ page_iter   │  │
│  │                              ├→ execution_agent ─→ route          │  │
│  │                              ├→ bug_analysis ─→ qa_loop           │  │
│  │                              ├→ report_agent ─→ route             │  │
│  │                              └→ knowledge_agent ─→ route          │  │
│  │                              └→ exit → END                        │  │
│  └───────────────────────┬───────────────────────────────────────────┘  │
│                          │                                              │
│  ┌───────────────────────▼───────────────────────────────────────────┐  │
│  │ AgentLoop (Skill 链执行)                                           │  │
│  │  SkillLoader → SkillExecutor → LLM Provider                       │  │
│  └───────────────────────┬───────────────────────────────────────────┘  │
│                          │                                              │
│  ┌───────────────────────▼───────────────────────────────────────────┐  │
│  │ LLM Layer                                                          │  │
│  │  Provider → Retry/Fallback → Context Window                       │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Infrastructure                                                      │  │
│  │  secure_subprocess, command_validator, paths, config               │  │
│  └───────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │ Governance (静态文件)                                               │  │
│  │  agents/*.yaml, skills/*.md, shared-language.md                   │  │
│  └───────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

## 7. Engine 接口契约

Engine 对外暴露的最小接口:

```python
class Engine:
    """最小可运行 Engine 接口。"""

    def run(self, project: str, module: str = None, pages: list[str] = None,
            mode: str = "full", run_id: str = None) -> dict:
        """
        执行一次完整的 SOP 流水线。

        Args:
            project: 项目 ID (对应 .tlo/project.yaml)
            module: 模块名 (可选，如 "equipment", "tank"，None=自动发现)
            pages: 页面列表 (可选，None=自动发现)
            mode: 执行模式 (full/resume/from-automation/status)
            run_id: 运行 ID (可选，None=自动生成)

        Returns:
            {
                "status": "completed" | "completed_with_issues" | "failed",
                "run_id": str,
                "completed_phases": list[str],
                "failed_phases": list[str],
                "pages": list[str],
                "agent_outputs": dict[str, AgentResult],
            }
        """
        ...
```

## 8. 设计原则

1. **单次执行**: Engine 无状态，每次 run() 独立，不管理并发
2. **同步阻塞**: run() 阻塞直到完成，不提供异步/流式接口
3. **文件 I/O**: 产物直接写文件系统，不经过抽象层
4. **最小依赖**: Core 只依赖 LangGraph + LLM Provider + Governance 文件
5. **可测试**: 所有外部依赖 (LLM, subprocess) 可 Mock
6. **可插拔**: Extensions 通过接口注入，不硬编码到 Core
