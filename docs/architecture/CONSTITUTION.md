# AITest Platform 1.0 — Architecture Constitution

> **地位:** 平台架构最高准则。所有 PR、重构、新功能均须对照本文。  
> **版本:** 1.0  
> **日期:** 2026-06-23  
> **前身:** Architecture Review + Aperant Benchmark → Design Freeze  

---

## 0. 平台定义

**AITest Platform 是一个企业级 AI 测试自动化平台。**

核心命题：

> 用 AI Agent 自主执行测试 SOP，从需求分析到报告生成全流程覆盖。平台与项目解耦，可承载多项目并行。

三个永远不变：

1. **Platform ≠ Project** — 平台是承载层，项目是被测对象
2. **Governance is mandatory** — 不可跳过、不可绕过
3. **Capability over Tool** — Agent 调用能力，不调用工具

---

## 1. 架构层级与冻结状态

```
┌──────────────────────────────────────────────────────────────┐
│                      DOMAIN LAYER                            │
│  governance/skills/   aitest/testing/   aitest/discovery/   │
│  Status: EXTENSIBLE — 新测试能力在此添加                       │
├──────────────────────────────────────────────────────────────┤
│                    AGENT RUNTIME                             │
│  aitest/agents/   aitest/graphs/   governance/agents/       │
│  Status: STABLE — 接口不变，实现可优化                          │
├──────────────────────────────────────────────────────────────┤
│                      PLATFORM CORE                           │
│  aitest/platform/   aitest/llm/   aitest/server/            │
│  Status: FROZEN — 除非架构评审通过，不得变更                      │
├──────────────────────────────────────────────────────────────┤
│                    INFRASTRUCTURE                            │
│  aitest/infra/   aitest/mcp/   aitest/config.py             │
│  Status: STABLE — 可增强，不可推翻                              │
├──────────────────────────────────────────────────────────────┤
│                    EXPERIMENTAL                              │
│  (任何新子系统在进入 Core 前须在此验证)                            │
│  Status: FLUID — 随时可改、可删                                 │
└──────────────────────────────────────────────────────────────┘
```

### 1.1 各层定义

| 层级 | 目录 | 冻结状态 | 变更规则 |
|------|------|----------|----------|
| **Platform Core** | `aitest/platform/`, `aitest/llm/`, `aitest/server/` | ❄️ FROZEN | 需 Architecture Review 批准 |
| **Agent Runtime** | `aitest/agents/`, `aitest/graphs/`, `governance/agents/` | 🔒 STABLE | 接口不变，实现可优化 |
| **Infrastructure** | `aitest/infra/`, `aitest/mcp/`, `aitest/config.py` | 🔒 STABLE | 可增不可删 |
| **Domain** | `governance/skills/`, `aitest/testing/`, `aitest/discovery/` | 🔓 EXTENSIBLE | 按需扩展 |
| **Experimental** | 新子系统 | 🔓 FLUID | 自由 |

### 1.2 Frozen 清单 — 永不变更

以下模块已冻结。任何变更须：

1. 提交 Architecture Review Request
2. 说明为什么现有接口不够
3. 说明为什么 Extension Point 不可用
4. 获得批准后方可实施

| 模块 | 冻结范围 |
|------|----------|
| `aitest/platform/paths.py` | 路径解析逻辑、公开函数签名 |
| `aitest/platform/context.py` | ProjectContext 接口 |
| `aitest/platform/runtime.py` | Runtime ABC（抽象方法签名不可变） |
| `aitest/llm/reliable_provider.py` | `ReliableProvider.complete()` 签名 |
| `aitest/agents/agent_runner.py` | `AgentLoop.run()` 签名 + AgentState 结构 |
| `aitest/graphs/sop_graph.py` | SOP Phase 枚举 + Phase 间转换逻辑 |
| `aitest/server/main.py` | REST API 端点路径（/health, /metrics, /api/*） |
| `aitest/config.py` | `Config` 类公开属性名 |
| `governance/agents/agent-definitions.yaml` | Agent 定义 Schema |

---

## 2. 平台核心设计原则

### P1: Platform 不 import 业务模块

```
允许: aitest.platform → aitest.llm → aitest.infra
禁止: aitest.platform → governance.skills
禁止: aitest.platform → ZJSN_Test-master526 (任何形式)
```

**检查方法:** 将 `aitest/platform/` 拷贝到新项目，`import` 不报错 → 合格。

### P2: Governance 配置层保持 Python-free

`governance/` 目录下的配置（Agent 定义、Skill 注册表、Workflow）必须是 YAML/Markdown。不嵌入 Python 逻辑。

**原因:** 非开发者可编辑。版本可追溯。配置即文档。

### P3: Agent 定义声明式

Agent 的能力、Skill、边界全部通过 `agent-definitions.yaml` 声明。不在代码中硬编码 Agent 行为。

```
正确: agent-definitions.yaml 中声明 capabilities: [browser, codegen]
错误: if agent_name == "automation-agent": allow_browser()
```

### P4: Capability 抽象高于 Tool 实现

Agent 调用 `browser.navigate()`，不调用 `tool('browser_use__navigate')`。

Capability Router 负责将 Capability 名称路由到具体实现。更换底层工具不影响 Agent。

### P5: 每个新模块回答三个问题

新增任何模块前：

1. **这个能力能用于另一个项目吗？** → Yes → Platform / No → Domain
2. **这是企业测试需要吗？** → Yes → 继续 / No → 不加入 Core
3. **这三年后还会存在吗？** → Yes → Core / No → Experimental

三个全部 Yes → Platform Core  
两个 Yes → Domain  
其他 → Experimental 或不加入

### P6: Extension Point 优先

新能力优先通过以下方式加入：

1. **Plugin** (`aitest/platform/plugin.py`) — Capability Provider 动态加载
2. **Skill** (`governance/skills/`) — Prompt 模板 + 注册
3. **MCP Server** (`aitest/mcp/`) — 外部工具协议
4. **Config** (`aitest/config.py`) — 配置驱动

只有以上四种方式都无法满足时，才考虑修改 Core。

---

## 3. Extension Points

### EP1: Capability Provider Plugin

```
入口: aitest/platform/plugin.py → PluginManager
方式: 创建插件目录，含 aitest_plugin.yaml + Python 模块
示例: my-playwright-plugin/ → 注册 PlaywrightBrowserProvider
```

### EP2: Skill Registry

```
入口: governance/skills/skill-registry.yaml
方式: 写 .md Skill 文件 + 在 registry 中注册
示例: page-analysis-v1.1.md → 注册为 test-design/page-analysis
```

### EP3: MCP Server

```
入口: aitest/mcp/ → ToolDef 注册
方式: 在 tools/__init__.py 的 _build_registry() 中添加 ToolDef
示例: 新增 browser MCP Server → 8 个 Tool 注册
```

### EP4: Agent Definition

```
入口: governance/agents/agent-definitions.yaml
方式: 添加 Agent 条目（name, skills, capabilities, boundaries）
示例: 新增 security-audit-agent → Phase 9.5
```

### EP5: Configuration

```
入口: aitest/config.py Config 类
方式: 添加 @property
示例: config.new_feature_enabled
```

---

## 4. 变更审批流程

### 4.1 免审批 (直接改)

- Experimental 层任何变更
- Domain 层 Skill 新增/修改
- Infrastructure 层 bug fix
- 配置文件新增属性
- 测试文件

### 4.2 轻审批 (PR 中说明即可)

- Agent Runtime 层实现优化
- Infrastructure 层新增模块
- Domain 层新增测试工具
- MCP Server 新增 Tool

### 4.3 架构评审 (需 Architecture Review)

- Platform Core 任何变更
- Frozen 清单中的接口变更
- Agent 定义 Schema 变更
- SOP Phase 增删改
- REST API 端点变更（/health 除外）
- 新增顶层架构层级

---

## 5. 技术栈基线

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | ≥0.110 |
| AI 编排 | LangGraph | ≥0.2 |
| LLM Provider | Anthropic + OpenAI + DeepSeek | — |
| 向量数据库 | ChromaDB | ≥0.4 |
| 关系数据库 | SQLite (via SQLAlchemy) | — |
| 前端框架 | Vue 3 + Pinia | ≥3.5 |
| UI 组件 | Radix Vue + Tailwind CSS | — |
| 观测 | OpenTelemetry + Prometheus | — |
| 测试 | pytest + Playwright | ≥8.0 |
| 配置 | YAML + python-dotenv | — |
| Python | ≥3.10 | — |

**原则:** 不引入新技术栈除非现有栈无法满足且 Extension Point 不可用。

---

## 6. 禁止清单

以下行为在 Platform Core 层禁止：

- ❌ 硬编码项目名、路径、配置
- ❌ `os.environ.get()` 在 `aitest/config.py` 之外
- ❌ 跨层 import（Domain → Platform, Agent Runtime → Platform Core 内部实现）
- ❌ `print()` 在生产代码中（用 `aitest.infra.logging`）
- ❌ 裸 `except: pass`（至少 `log_error`）
- ❌ 在 `governance/` 目录写 Python 业务逻辑
- ❌ 在 Platform 层 import 测试项目代码

---

## 7. 版本演进策略

```
v0.3 — Architecture Complete (当前)
  │
  ├── v0.4 — Capability Enforcement (P0)
  │
  ├── v0.5 — Phase-Aware Model Tier (P0)
  │
  ├── v1.0 — Design Freeze + Stable API
  │
  └── v1.1+ — Memory Observer, Prompt Assembly, ...
```

**v1.0 之前的每次 Release，对照本宪章检查。**

---

## 8. 决策框架

每次面对架构决策时，按以下顺序回答：

```
Q1: 这能通过 Extension Point 实现吗？
    │
    ├── Yes → 用 Extension Point。不改 Core。
    │
    └── No → Q2

Q2: 这必须进 Platform Core 吗？
    │
    ├── No → 放 Domain 或 Experimental。
    │
    └── Yes → Q3

Q3: 三个问题全部 Yes？
    │  · 能用于另一个项目？
    │  · 企业测试需要？
    │  · 三年后还存在？
    │
    ├── Yes → 提 Architecture Review Request。
    │
    └── No → 放 Experimental。等到三个 Yes 再进 Core。
```

---

## 9. 相关文档

| 文档 | 作用 |
|------|------|
| [ARCHITECTURE_REVIEW_2026-06-23.md](ARCHITECTURE_REVIEW_2026-06-23.md) | 当前架构完整评审 |
| [BENCHMARK_APERANT_2026-06-23.md](BENCHMARK_APERANT_2026-06-23.md) | 与 Aperant 的能力对标 |
| [ADR_001_TLO_DIRECTORY.md](adr/ADR_001_TLO_DIRECTORY.md) | .tlo/ 目录决策 |
| [00-ARCHITECTURE_OVERVIEW.md](00-ARCHITECTURE_OVERVIEW.md) | v1.0 架构总览 |

---

> **本宪章自 2026-06-23 起生效。**  
> **所有后续 PR、重构、新功能均须对照本宪章。**  
> **宪章的修改须通过 Architecture Review 并更新版本号。**
