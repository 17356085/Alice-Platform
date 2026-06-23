# Architecture Review Report — AITest Platform

> **评审类型:** Enterprise Architecture Review  
> **评审日期:** 2026-06-23  
> **评审范围:** 全仓库 (aitest/ + governance/ + docs/ + 所有子目录)  
> **评审人:** Enterprise Software Architect (Claude)  

---

## 1. Executive Summary

AITest Platform 是一个从**单一测试项目工作台**向**测试自动化 Agent Native 平台**演进中的系统。当前处于 v0.6 → v1.0 过渡期。

### 1.1 核心判断

| 维度 | 结论 |
|------|------|
| 架构类型 | **Modular Monolith + Layered Architecture**，正向 Platform-Oriented Clean Architecture 演进 |
| 成熟度 | **C+ / B-** — 可运行、可交付，但平台独立性尚未完成 |
| 最大风险 | 平台与测试项目耦合残留 (ZJSN 硬编码)、配置漂移、依赖声明缺失 |
| 最大资产 | Agent/Skill/Workflow 治理体系、ADR 决策过程、LangGraph 编排引擎、声明式 Agent 定义 |
| 演进方向 | ✅ 正确 — 从项目专属工具 → 多项目平台 → SaaS 化 API |

### 1.2 评分总览 (1-10)

| 维度 | 评分 | 说明 |
|------|------|------|
| Modularity | 7 | 分层清晰，15 子包，无循环依赖 |
| Maintainability | 6 | 大文件多 (25 >500行)，但结构清晰 |
| Scalability | 5 | 单进程，无水平扩展 |
| Testability | 4 | 仅 1 个测试文件，E2E 端口不匹配 |
| Extensibility | 7 | Agent/Skill 声明式注册，新 Agent 低成本 |
| Governance | 8 | YAML 单一事实源 + 门禁 + 审计 + ADR |
| Platformization | 5 | .tlo/ 解耦进行中，~6 处残留硬编码 |
| Observability | 5 | Trace + Event Bus + KPI + 审计，但无 Metrics/Health Check |
| Production Readiness | 4 | 缺 Circuit Breaker、Rate Limiting、Proper Logging |

**综合: 5.7/10** — "可运行的内部工具，正演进为企业平台"。

---

## 2. Current Architecture

### 2.1 架构类型判定

**Modular Monolith + Layered Architecture (4-Tier)，带有 Hexagonal 倾向。**

不完全是 Clean Architecture（缺乏明确的 Use Case/Interactor 层），但有清晰的依赖方向：外层依赖内层，内层不依赖外层。

### 2.2 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRESENTATION LAYER                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │
│  │ Vue 3 Web UI │  │ Electron Shell│  │ MCP Protocol (JSON)  │   │
│  │ (aitest/web/) │  │ (web/electron)│  │ (aitest/mcp/)        │   │
│  └──────┬───────┘  └──────┬───────┘  └──────────┬───────────┘   │
│         │                 │                      │               │
├─────────┼─────────────────┼──────────────────────┼───────────────┤
│         ▼                 ▼                      ▼               │
│                        API LAYER                                 │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  FastAPI Server (aitest/server/)                          │   │
│  │  ├─ REST: /api/agents, /api/chat, /api/sop-status, ...    │   │
│  │  ├─ SSE:  /api/chat/{id}/stream                           │   │
│  │  ├─ WS:   /ws/kanban, /ws/onboarding                      │   │
│  │  └─ SessionStore (SQLite)                                  │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│                              ▼                                   │
│                     ORCHESTRATION LAYER                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LangGraph SOP Engine (aitest/graphs/)                    │   │
│  │  ├─ sop_graph.py — 主编排器 (8-Agent StateGraph)          │   │
│  │  ├─ parallel_sop.py — Send() 多页面并行                    │   │
│  │  ├─ review_graph.py — Review 子图                         │   │
│  │  ├─ bug_analysis_graph.py — Bug 分析子图                  │   │
│  │  └─ checkpoint.py — SqliteSaver 断点续跑                  │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│                              ▼                                   │
│                      EXECUTION LAYER                             │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  AgentLoop (aitest/agents/agent_runner.py)                │   │
│  │  Perceive → Plan → Act → Observe → Update                 │   │
│  │  ├─ Skill Executor (skill_executor.py)                    │   │
│  │  ├─ Runner State (runner_state.py)                        │   │
│  │  ├─ Output Persistence (output_persistence.py)            │   │
│  │  └─ Consistency Checks (consistency_checks.py)            │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│                              ▼                                   │
│                    DOMAIN / CAPABILITY LAYER                     │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ Discovery│ │Governance│ │ Testing  │ │  Knowledge (RAG) │   │
│  │ (discov) │ │(govern)  │ │(testing) │ │  (knowledge/)    │   │
│  ├──────────┤ ├──────────┤ ├──────────┤ ├──────────────────┤   │
│  │ Source   │ │ KPI      │ │ Eval     │ │ RagEngine        │   │
│  │ Analysis │ │ Audit    │ │Regress   │ │ KnowledgeServer  │   │
│  │ Browser  │ │ QA Loop  │ │Consist   │ │ KnowledgeExtract │   │
│  │  Use     │ │ Monitor  │ │Export    │ │                  │   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────────┬─────────┘   │
│       │            │            │                 │              │
├───────┼────────────┼────────────┼─────────────────┼──────────────┤
│       ▼            ▼            ▼                 ▼              │
│                      PLATFORM LAYER                              │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  aitest/platform/                                         │   │
│  │  ├─ paths.py — 路径解析 (单一入口，fallback chain)         │   │
│  │  ├─ context.py — 项目上下文 (project.yaml 读取)           │   │
│  │  ├─ runtime.py — 执行运行时抽象 (BrowserRuntime)          │   │
│  │  ├─ testing_memory.py — 8 种测试记忆类型                  │   │
│  │  ├─ testing_memory_store.py — ChromaDB CRUD               │   │
│  │  ├─ observation_bus.py — 事件总线                         │   │
│  │  ├─ capability_router/ — Agent×Capability 路由            │   │
│  │  └─ complexity/ — 18因子评分 + 3档路由                    │   │
│  └──────────────────────────┬───────────────────────────────┘   │
│                              │                                   │
├──────────────────────────────┼───────────────────────────────────┤
│                              ▼                                   │
│                    INFRASTRUCTURE LAYER                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐   │
│  │ LLM      │ │ Security │ │ Trace    │ │ Task / Parallel  │   │
│  │ Provider │ │ Denylist │ │ Event    │ │ Queue / Runner   │   │
│  │ Reliable │ │ Validator│ │ Context  │ │ Worktree Manager │   │
│  │ Context  │ │ Subproc  │ │          │ │ Webhook Server   │   │
│  │ Window   │ │          │ │          │ │ Error Logger     │   │
│  └──────────┘ └──────────┘ └──────────┘ └──────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  External: ChromaDB │ LangGraph │ FastAPI │ browser-use  │   │
│  │            Selenium │ Playwright│ pytest   │ Allure       │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

                     ║  Governance (独立层) ║
  ┌──────────────────────────────────────────────────────────┐
  │  governance/ (YAML + Markdown, 98% 配置)                  │
  │  ├─ agents/agent-definitions.yaml — Agent 单一事实源      │
  │  ├─ skills/skill-registry.yaml — Skill 注册表             │
  │  ├─ skills-dev/skill-registry-dev.yaml — Dev Skill 注册表 │
  │  ├─ workflows/workflow-registry.yaml — 工作流注册表       │
  │  ├─ context/shared-language.md — 170+ 领域术语            │
  │  ├─ validators/ — Python 门禁验证器                       │
  │  └─ kpi/timeseries/ — 35 JSONL 时序指标                   │
  └──────────────────────────────────────────────────────────┘
```

### 2.3 层级依赖规则 (已验证)

```
Presentation  ──imports──▶  API  ──imports──▶  Orchestration
                                                   │
                                                   ▼
                                            Execution (AgentLoop)
                                                   │
                                                   ▼
                                            Domain / Capability
                                                   │
                                                   ▼
                                            Platform
                                                   │
                                                   ▼
                                            Infrastructure (LLM, Security, Trace)
```

**验证结果: 零循环依赖。** 依赖方向严格从上到下。`platform.paths` 是唯一被广泛依赖的横切模块，自身零内部依赖。

---

## 3. Module Analysis

### 3.1 模块职责矩阵

| 模块 | 行数 | 职责 | 单一职责 | 问题 |
|------|------|------|----------|------|
| `aitest/agents/` | ~4,500 | Agent 执行引擎 | ✅ | agent_runner.py 1014行，可拆分 |
| `aitest/graphs/` | ~6,500 | LangGraph 编排 | ✅ | sop_graph.py 1446行，含预检缓存 |
| `aitest/llm/` | ~3,400 | LLM Provider 抽象 | ✅ | provider.py 1021行 |
| `aitest/platform/` | ~3,100 | 平台抽象层 | ⚠️ | 6 个子模块，职责分散 |
| `aitest/server/` | ~2,800 | FastAPI 服务 | ✅ | main.py 含初始化逻辑过多 |
| `aitest/infra/` | ~4,900 | 基础设施 | ⚠️ | cli.py 2191行 — God Module |
| `aitest/governance/` | ~7,400 | 治理审计 | ✅ | state_auditor 1213行 |
| `aitest/mcp/` | ~2,300 | MCP 协议 | ✅ | 清晰 |
| `aitest/discovery/` | ~2,800 | 项目结构发现 | ✅ | 含 Vue 专用提取器 |
| `aitest/testing/` | ~3,100 | 测试工具 | ✅ | evaluator 937行 |
| `aitest/knowledge/` | ~1,700 | RAG 引擎 | ✅ | rag_engine 671行 |
| `aitest/integrations/` | ~1,000 | 外部集成 | ✅ | GitHub + BrowserUse |
| `aitest/web/` | ~15,000 | Vue 3 前端 | ✅ | 14 视图 + 5 Store |

### 3.2 God Module 识别

| 文件 | 行数 | 严重度 | 建议 |
|------|------|--------|------|
| `infra/cli.py` | 2,191 | **Critical** | 拆分为 subcommands/*.py |
| `graphs/sop_graph.py` | 1,446 | **High** | 节点工厂 + 预检模块独立 |
| `governance/state_auditor.py` | 1,213 | **High** | 按审计类型拆分 |
| `llm/provider.py` | 1,021 | **Medium** | 按 Provider 拆分 (claude.py, openai.py) |
| `agents/agent_runner.py` | 1,014 | **Medium** | Observer 和 Planner 独立 |

---

## 4. Domain Boundary Analysis

### 4.1 三边界定义

```
┌─────────────────────────────────────────────────────┐
│                 PLATFORM                            │
│  (多项目复用、与业务无关的通用能力)                    │
│  aitest/platform/   aitest/llm/   aitest/infra/     │
│  aitest/mcp/        aitest/knowledge_model/         │
├─────────────────────────────────────────────────────┤
│                 AI AGENT RUNTIME                     │
│  (Agent 生命周期管理，不绑定测试领域)                  │
│  aitest/agents/     aitest/graphs/                  │
│  aitest/graphs_dev/ governance/agents/              │
│  governance/skills-dev/                             │
├─────────────────────────────────────────────────────┤
│                 TESTING DOMAIN                       │
│  (测试业务专属：SOP、Skill、Validator、Exporter)      │
│  governance/skills/   aitest/testing/               │
│  governance/validators/  aitest/discovery/          │
│  governance/context/projects/ (legacy)              │
│  governance/workflows/                              │
└─────────────────────────────────────────────────────┘
```

### 4.2 Boundary Leakage (边界泄漏)

| # | 问题 | 位置 | 严重度 | 说明 |
|---|------|------|--------|------|
| 1 | **ZJSN 硬编码泄漏到平台** | `platform/paths.py:181` | High | `Path("D:/Desktop/WorkStudy2/ZJSN_Test-master526")` 硬编码 |
| 2 | **ZJSN 路径残留** | `knowledge/rag_engine.py:409` | Medium | `WORKSTUDY / "ZJSN_Test-master526" / "page"` |
| 3 | **ZJSN 路径残留** | `testing/testcase_exporter.py:23-24` | Medium | allure-results / script 默认路径 |
| 4 | **qa_loop.py ZJSN 硬编码** | `governance/qa_loop.py:117,240,404` | Medium | 3 处 ZJSN_Test-master526 fallback |
| 5 | **BrowserRuntime ↭ BrowserUseDriver** | `platform/runtime.py:145` | Medium | 平台运行时直接依赖具体 BrowserUse 实现 |
| 6 | **aitest/governance/ vs governance/** | 两处 | Low | 同名包可能混淆 — `aitest/governance/` 是 Python, `governance/` 是配置 |
| 7 | **workflow_engine.py 过期未删** | `workflow_engine.py` | Low | DEPRECATED 标记 30 天已过 (2026-07-13)，仍 626 行 |
| 8 | **_archived 仍含可执行代码** | `graphs/_archived/` | Low | 含 6 处 ZJSN 硬编码，可能被误导入 |

### 4.3 建议解耦方案

| 问题 | 推荐方案 | 优先级 |
|------|----------|--------|
| ZJSN 硬编码 | 全部改为 `get_test_project_root()` + 无 fallback 时抛明确异常 | P0 |
| BrowserRuntime 耦合 | 通过 `capabilities/abc.py` 的 `CapabilityRegistry` 依赖注入，而非直接 import | P1 |
| qa_loop.py | 使用 `platform.paths.get_test_project_root()` | P1 |
| 同名包 | 将 `aitest/governance/` 重命名为 `aitest/audit_engine/` 区分 | P2 |
| 过期模块 | 删除 `workflow_engine.py`，清理所有 `_archived/` | P2 |

---

## 5. Dependency Analysis

### 5.1 依赖方向图

```
server/main.py ──────imports──────▶ 全部 (合法: API 聚合层)
      │
      ▼
graphs/sop_graph.py ──imports──▶ agents/agent_runner.py
      │                                │
      │                                ▼
      │                         llm/provider.py
      │                         platform/paths.py  ← ★ 核心依赖枢纽
      │                         platform/observation_bus.py
      │
      ▼
platform/paths.py ──── ZERO 内部依赖 (纯函数)
platform/context.py ── imports ──▶ platform/paths.py
platform/runtime.py ── imports ──▶ integrations/bu_driver.py (⚠️)
```

### 5.2 依赖问题清单

| # | 问题 | 路径 | 影响 |
|---|------|------|------|
| 1 | **无循环依赖** | — | ✅ 零发现 |
| 2 | `platform.paths` 被 20+ 模块依赖 | 全局 | ⚠️ 变更影响面大，但模块稳定 |
| 3 | `governance/safety_auditor.py` → `graphs/state.py` | 审核→编排 | ⚠️ 轻微层违规 |
| 4 | `platform/runtime.py` → `integrations/bu_driver.py` | 平台→集成 | ⚠️ 平台不应依赖具体实现 |
| 5 | `workflow_engine.py` → `governance.validators` | 顶层→治理 | ⚠️ 但该文件已 DEPRECATED |
| 6 | 6 个文件有 `ZJSN_Test-master526` 字符串 | 分散 | ❌ 平台-项目耦合 |

### 5.3 Shared Utils 分析

`platform/paths.py` — 唯一真正共享的工具模块。**健康**: 185 行，纯路径计算，零副作用，有 fallback chain。

`aitest/__init__.py` — 重导出 14 个顶级符号。**干净**: 无逻辑，纯聚合。

---

## 6. Runtime Flow

### 6.1 完整执行链

```
User (Web UI / CLI / MCP Client)
  │
  ▼
┌─ API Layer ─────────────────────────────────────────┐
│ POST /api/chat/message  →  SSE Stream               │
│ POST /api/sop/start     →  Background Task           │
│ MCP tools/run_sop       →  Direct AgentLoop          │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─ Orchestration (LangGraph) ─────────────────────────┐
│ SOPGraph.preflight()                                 │
│   ├─ Load PROJECT_CONTEXT, MODULE_CONTEXT            │
│   ├─ Validate SOP gate (validators/sop_validator.py) │
│   └─ Complexity classify (SIMPLE/STANDARD/COMPLEX)   │
│                                                      │
│ SOPGraph.route() → Agent Node (×8 phases)            │
│   Phase 0: project-agent                             │
│   Phase 1: requirement-agent                         │
│   Phase 2: test-design-agent                         │
│   Phase 4: automation-agent                          │
│   Phase 6: execution-agent                           │
│   Phase 7: bug-analysis-agent                        │
│   Phase 8: report-agent                              │
│   (transverse): knowledge-agent                      │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─ AgentLoop (Perceive→Plan→Act→Observe) ────────────┐
│                                                      │
│ Perceive:                                            │
│   ├─ ContextInjector → RAG search (ChromaDB)         │
│   ├─ ContextWindowMonitor → 85%/90% threshold        │
│   └─ SkillLoader → Prompt template + context merge   │
│                                                      │
│ Plan:                                                │
│   ├─ AGENT_SKILL_MAP[agent] → skill sequence         │
│   └─ Failure → retry/skip/abort decision             │
│                                                      │
│ Act:                                                 │
│   ├─ ReliableProvider.complete()                     │
│   │   ├─ RetryManager (3x)                           │
│   │   └─ FallbackChain (claude→deepseek→openai)      │
│   ├─ Skill Executor → LLM call                       │
│   └─ Stream events → SSE → Web UI                    │
│                                                      │
│ Observe:                                             │
│   ├─ Mechanical Checks (file existence, code format) │
│   ├─ LLM Consistency Review                          │
│   ├─ Output Persistence (save to disk)               │
│   └─ ObservationBus.emit()                           │
│                                                      │
│ Update:                                              │
│   ├─ AgentState.step += 1                            │
│   ├─ Store observation result                        │
│   └─ Emit PhaseChangeEvent                           │
└──────────────────────────┬──────────────────────────┘
                           │
                           ▼
┌─ Post-Execution ───────────────────────────────────┐
│ Testing Memory — auto-store observations             │
│ Audit Log — tool-calls.jsonl                         │
│ KPI Timeseries — state-{page}.jsonl                  │
│ SOP_STATUS — per-project runtime state               │
│ Governance Event → KnowledgeAgentSubscriber          │
└─────────────────────────────────────────────────────┘
```

### 6.2 耦合点分析

| 步骤 | 当前耦合 | 理想解耦 |
|------|----------|----------|
| API → Graph | 直接 `import sop_graph` | 通过 Workflow Registry 间接调用 |
| Graph → Agent | 直接 `make_agent_loop_node()` | 通过 Agent Registry |
| Agent → LLM | ReliableProvider 抽象 | ✅ 已解耦 |
| Agent → Browser | 通过 `runtime.py` 抽象 | ⚠️ 但 runtime 直接 import BrowserUseDriver |
| Agent → Memory | ObservationBus 事件 | ✅ 事件驱动，已解耦 |
| Agent → File | output_persistence + platform.paths | ✅ |

---

## 7. Agent Architecture

### 7.1 当前模式判定

**Hybrid: State Machine + Pipeline + Agent Loop**

```
SOP Graph (State Machine)
  │
  ├─ Phase 0 ──▶ Phase 1 ──▶ Phase 2 ──▶ ...
  │    │            │            │
  │    ▼            ▼            ▼
  │  AgentLoop   AgentLoop   AgentLoop   ← Pipeline (顺序执行)
  │    │            │            │
  │    ▼            ▼            ▼
  │  Skill 1..N  Skill 1..N  Skill 1..N  ← Agent Loop (Plan-Act-Observe)
```

**不是真正的自治 Agent。** 每个 Agent 仍按预定义 Skill 序列执行，虽有重试和跳过逻辑，但不做自主目标分解。这是合理的工程选择 — 测试 SOP 场景不需要开放式 Agent。

### 7.2 Agent 扩展性

| 扩展点 | 难度 | 说明 |
|--------|------|------|
| 新 Agent (测试) | **低** | `agent-definitions.yaml` 加配置 + `AGENT_SKILL_MAP` 注册 |
| 新 Agent (开发) | **低** | `agent-definitions-dev.yaml` + `DEV_AGENT_SKILL_MAP` |
| 新 Skill | **低** | `.md` 文件 + `skill-registry.yaml` 注册 |
| 新 Planner 策略 | **中** | 需改 `agent_runner.py`，无策略接口 |
| 新 Observer | **中** | Observer 硬编码在 AgentLoop 中 |
| 新 Memory 类型 | **低** | `testing_memory.py` 定义新类型 |
| 新 Capability Provider | **低** | `capability_router/providers/` 添加 |

### 7.3 Agent vs Workflow 对比

| | Agent (agent_runner.py) | Workflow (workflow_engine.py) |
|---|---|---|
| 状态 | ✅ Active | ❌ DEPRECATED |
| 编排 | LangGraph StateGraph | YAML DAG |
| 断点 | SqliteSaver checkpoint | JSON checkpoint |
| Agent Loop | ✅ Perceive-Plan-Act-Observe | ❌ 顺序执行 |
| 推荐 | **唯一定位** | **应删除** |

---

## 8. Browser Layer

### 8.1 当前状态

```
Browser Abstraction:
  platform/runtime.py::Runtime (ABC)
    └── BrowserRuntime
          └── integrations/bu_driver.py::BrowserUseDriver
                └── browser-use (Playwright Chromium)

Selenium (独立线):
  ZJSN_Test-master526/base/ (BasePage, 定位器)
    └── aitest/bu_adapter.py (Skill → BrowserUse 桥接)
```

### 8.2 判定

**当前: Browser Automation + 部分 Runtime 抽象。非真正的 Agent Browser Runtime。**

| 维度 | 现状 |
|------|------|
| 浏览器驱动 | BrowserUse (AI-driven) + Selenium (deterministic) |
| 抽象层 | `Runtime` ABC + `BrowserRuntime` 实现 |
| 能力注册 | `capabilities/abc.py` — Navigator/Observer/Clicker/Inputter |
| 多浏览器 | ❌ 仅 Playwright Chromium |
| Remote Browser | ❌ 不支持 |
| Mobile/Desktop | ❌ 不支持 |
| MCP Browser | ❌ 无 MCP Browser Server |

### 8.3 扩展就绪度

| 未来需求 | 当前支持 | 需改动 |
|----------|----------|--------|
| Playwright 直连 | ❌ | 需实现 `PlaywrightRuntime(Runtime)` |
| Browser-Use v2 | ⚠️ | 适配 `BrowserUseDriver`，接口稳定 |
| Remote Browser | ❌ | 需 WebSocket/CDP 代理 |
| Cloud Browser (Browserbase) | ❌ | 需新 Provider |
| Mobile (Appium) | ❌ | 需 `AppiumRuntime(Runtime)` |
| MCP Browser Server | ❌ | 需 MCP Server 包装 Runtime |

---

## 9. Platform Layer

### 9.1 独立性评估

**当前状态: 半独立。** `aitest/platform/` 已建立抽象层，但仍有泄漏。

| 组件 | 独立性 | 问题 |
|------|--------|------|
| `paths.py` | ⚠️ 80% | fallback 含 ZJSN 硬编码 |
| `context.py` | ✅ 95% | 读取 project.yaml，项目无关 |
| `runtime.py` | ⚠️ 70% | `BrowserRuntime` 直接 import BrowserUseDriver |
| `testing_memory.py` | ✅ 100% | 纯数据结构，无外部依赖 |
| `observation_bus.py` | ✅ 100% | 事件总线，项目无关 |
| `capability_router/` | ✅ 95% | 声明式路由 |
| `complexity/` | ✅ 90% | 18 因子通用 |

### 9.2 多项目支持

| 能力 | 状态 |
|------|------|
| 项目注册 | ✅ `aitest project register` |
| 项目切换 | ✅ `aitest project set --id=X` |
| 项目上下文隔离 | ✅ project.yaml + .tlo/ |
| 多租户 | ❌ 无租户概念 |
| 项目间 Skill 共享 | ✅ governance/skills/ |
| 项目间 Agent 共享 | ✅ governance/agents/ |
| 插件扩展 | ❌ 无插件系统 |
| SaaS 化 | ❌ 单实例，无 API Key 管理 |

---

## 10. Prompt Governance

### 10.1 Prompt 存放位置

| 位置 | 内容 | 格式 |
|------|------|------|
| `governance/skills/*.md` | 测试 Skill Prompt 模板 | Markdown + `{{ }}` 占位符 |
| `governance/skills-dev/*.md` | 开发 Skill Prompt 模板 | Markdown + 规则说明 |
| `governance/agents/agent-definitions.yaml` | Agent system_prompt_role | YAML 字段 |
| `aitest/llm/skill_loader.py` | Prompt 加载 + 渲染引擎 | Python |
| `aitest/mcp/prompts/templates.py` | MCP Prompt 模板 | Python 常量 |
| `aitest/llm/prompt_adapter.py` | 跨 Provider Prompt 适配 | Python |

### 10.2 治理成熟度

| 维度 | 状态 | 说明 |
|------|------|------|
| Versioning | ✅ | skill-registry.yaml 记录版本历史 |
| Registry | ✅ | skill-registry.yaml + skill-registry-dev.yaml |
| Template | ✅ | `{{ }}` 占位符，skill_loader 渲染 |
| Dynamic Prompt | ⚠️ | context_injector 注入运行时上下文，但非结构化 |
| Role Prompt | ✅ | agent-definitions.yaml 的 system_prompt_role |
| 易于治理 | ✅ | 新增 Skill = 写 .md + 注册 |
| A/B 测试 | ❌ | prompt_benchmark.py 存在但未集成 |
| Prompt 版本回滚 | ⚠️ | 注册表记录版本但无自动回滚 |

---

## 11. Context Management

### 11.1 Context 流动

```
Project Context (.tlo/ or governance/context/projects/<id>/)
  │
  ├─ manifest.yaml / project.yaml
  ├─ knowledge/modules/<module>/
  │   ├─ MODULE_CONTEXT.md
  │   ├─ PROJECT_CONTEXT.md
  │   └─ pages/<page>/
  │       ├─ PAGE_CONTEXT.md
  │       ├─ TECH_ANALYSIS.md
  │       ├─ RISK_MODEL.md
  │       ├─ TEST_CASES.md
  │       └─ AUTO_STRATEGY.md
  │
  ▼
ContextInjector (aitest/llm/context_injector.py)
  │
  ├─ Load project profile
  ├─ Load module context
  ├─ Load page context (if focused)
  ├─ Load shared-language.md (always)
  ├─ RAG search (ChromaDB — known issues)
  ├─ Skill-specific context (from skill_loader)
  └─ Merge → System Prompt
  │
  ▼
AgentLoop.system_prompt (assembled)
```

### 11.2 Context 类型边界

| Context 类型 | 来源 | 生命周期 | 边界清晰? |
|-------------|------|----------|-----------|
| Runtime Context | `platform/context.py` | 每次调用 | ✅ |
| User Context | chat message / CLI args | 单次会话 | ✅ |
| Project Context | `.tlo/` / governance/context/ | 跨会话 | ⚠️ 迁移中 |
| Agent Context | AgentState.memory | 单次 SOP run | ⚠️ 与 TestingMemory 重叠 |
| Memory | `platform/testing_memory.py` | 跨 SOP run | ⚠️ 定义清晰但使用分散 |

**问题: AgentState.memory (dict) 和 TestingMemory (类型化) 两套 Memory 并存。** v1.0 计划用 TestingMemory 替代 AgentState.memory，当前处于过渡期。

---

## 12. Configuration

### 12.1 配置体系

| 方式 | 位置 | 用途 |
|------|------|------|
| `.env` | 项目根目录 | API Keys (ANTHROPIC, GOOGLE, MIMO) |
| `pyproject.toml` | 项目根目录 | 包元数据 (无依赖声明) |
| `project.yaml` | .tlo/ 或 governance/context/ | 项目配置 |
| `environments.yaml` | governance/context/ | 环境配置 |
| YAML 注册表 | governance/agents/, skills/, workflows/ | Agent/Skill/Workflow 定义 |
| 硬编码 `os.environ` | 10 个文件 | 运行时配置 |
| `localStorage` | 前端 | UI 偏好 (theme, lang) |
| `vite.config.ts` | aitest/web/ | 构建配置 |

### 12.2 配置漂移

| 问题 | 影响 |
|------|------|
| **`pyproject.toml` 无运行时依赖** | 无法 `pip install` 复现环境 |
| **10 个文件各自读 `os.environ`** | 配置分散，无统一入口 |
| **ENV 变量无文档** | AITEST_AUDIT_INTERVAL 等隐藏配置 |
| **前端 port 硬编码不一致** | vite.config 15173 vs e2e test 5173 |
| **`dist/` 提交到 Git** | 构建产物污染源码 |

### 12.3 建议

- 添加 `pyproject.toml` 的 `dependencies` 声明
- 创建 `aitest/config.py` 统一配置入口 (读 ENV + YAML)
- 文档化所有 ENV 变量
- 统一前端端口配置
- `.gitignore` 添加 `dist/`

---

## 13. Extensibility

### 13.1 扩展成本评估

| 扩展场景 | 成本 | 涉及文件 | 风险 |
|----------|------|----------|------|
| 新 LLM Provider | **低** | `llm/provider.py` 新类 + 注册 | 低 — 有 ABC 接口 |
| 新 Browser Driver | **中** | `platform/runtime.py` 新 Runtime | 中 — 需实现 Runtime ABC |
| 新 Agent (测试) | **低** | YAML + `AGENT_SKILL_MAP` 注册 | 低 — 声明式 |
| 新 MCP Tool | **低** | `mcp/tools/__init__.py` 加 ToolDef | 低 |
| 新 Workflow | **低** | `governance/workflows/` 新 YAML | 低 |
| 新项目接入 | **中** | project.yaml + .tlo/ + onboarding | 中 — 需项目知识 |
| 新前端页面 | **低** | Vue 组件 + 路由注册 | 低 |
| 新 Runtime 类型 | **中** | `platform/runtime.py` 新子类 | 中 |
| 水平扩展 | **高** | 需引入消息队列、分布式状态 | 高 — 当前单进程 |

---

## 14. Technical Debt

### 14.1 Architecture Smells

#### Critical (阻塞演进)

| # | Smell | 位置 | 说明 |
|---|-------|------|------|
| C1 | **God Module** | `infra/cli.py` (2,191行) | CLI 单文件过大，难以维护 |
| C2 | **Hardcoded Path** | 6 个 Python 文件 | ZJSN_Test-master526 硬编码 |
| C3 | **Missing Dependencies** | `pyproject.toml` | 无运行时依赖声明 |
| C4 | **Duplicate Memory** | AgentState.memory + TestingMemory | 两套 Memory 并存 |

#### High (影响可维护性)

| # | Smell | 位置 | 说明 |
|---|-------|------|------|
| H1 | **God Class** | `graphs/sop_graph.py` (1,446行) | 预检逻辑与图定义混合 |
| H2 | **God Class** | `governance/state_auditor.py` (1,213行) | 单一文件含多种审计 |
| H3 | **Layer Violation** | `platform/runtime.py` → `integrations/bu_driver.py` | 平台层依赖集成层 |
| H4 | **Config Drift** | 10 个文件各读 `os.environ` | 无统一配置 |
| H5 | **Dead Code** | `workflow_engine.py` (626行) | DEPRECATED 已超期 |
| H6 | **Dead Code** | `graphs/_archived/` (~2,000行) | 含 6 处硬编码，可能被误导入 |

#### Medium (影响代码质量)

| # | Smell | 位置 | 说明 |
|---|-------|------|------|
| M1 | **Hardcoded Chinese** | 多个 Vue 组件 | 虽有 i18n，仍硬编码中文 |
| M2 | **Port Mismatch** | `e2e/smoke.spec.ts` | 5173 vs 15173 |
| M3 | **dist/ in Git** | `aitest/web/dist/` | 构建产物不应提交 |
| M4 | **Missing Tests** | 全仓库仅 1 个 pytest 文件 | test_sop_routing.py 仅 220 行 |
| M5 | **Module-level State** | `useKanbanWS.ts`, `useGapScanner.ts` | Vue composable 使用单例模式 |
| M6 | **Named Package Conflict** | `aitest/governance/` vs `governance/` | 同名包容易混淆 |

#### Low (改善项)

| # | Smell | 位置 | 说明 |
|---|-------|------|------|
| L1 | **Raw fetch() 绕过 ApiClient** | KnowledgeView, ReportsView | 错误处理不一致 |
| L2 | **Empty directories** | `docs/archive/`, `governance/docs/` | 已创建但空的目录 |
| L3 | **node_modules 在 Python 包内** | `aitest/node_modules/` | Electron 依赖混入 Python 包 |

### 14.2 重复逻辑

| 模式 | 出现次数 |
|------|----------|
| `Path(__file__).resolve().parent.parent.parent` 找项目根 | 5+ |
| `load_dotenv()` | 3+ (provider.py, bu_driver.py, context.py) |
| ZJSN_Test-master526 fallback | 6 |
| WORKSTUDY 路径拼接 | 10+ |

---

## 15. Production Readiness

### 15.1 Checklist

| 能力 | 状态 | 说明 |
|------|------|------|
| **Logging** | ⚠️ | `print()` 为主，`infra/error_logger.py` 存在但未广泛使用 |
| **Metrics** | ❌ | 无 Prometheus/OpenTelemetry 集成 |
| **Tracing** | ⚠️ | `infra/trace.py` 有 TraceEvent/TraceContext，但未集成 OpenTelemetry |
| **Health Check** | ❌ | 无 `/health` 端点 (KnowledgeView 调用它但不存在) |
| **Retry** | ✅ | `ReliableProvider` 含 RetryManager (3x) |
| **Circuit Breaker** | ❌ | 无熔断器 |
| **Timeout** | ⚠️ | LLM 调用有 max_tokens，但无全局超时 |
| **Error Recovery** | ⚠️ | AgentLoop 有重试/跳过/中止，但无自动恢复 |
| **Audit** | ⚠️ | `governance/audit/tool-calls.jsonl` 仅 32 条 |
| **Governance** | ✅ | SOP Gate + Validator + KPI + ADR |
| **Observability** | ⚠️ | Event Bus + KPI Timeseries，但无 Dashboard |
| **Rate Limiting** | ❌ | `mcp/rate_limit.py` 定义但未强制执行 |
| **Auth** | ❌ | 无 API 认证 |
| **CORS** | ✅ | FastAPI CORSMiddleware |

---

## 16. Architecture Maturity Scores

| 维度 | 评分 | 原因 |
|------|------|------|
| **Modularity** | 7/10 | 15 子包，分层清晰，零循环依赖。扣分: 部分模块过大 |
| **Maintainability** | 6/10 | 代码风格统一，注释充分。扣分: 25 文件 >500 行，God Module |
| **Scalability** | 5/10 | 单进程架构，无消息队列，无水平扩展路径 |
| **Testability** | 4/10 | 仅 1 个测试文件。E2E 端口不匹配。大量逻辑未测试 |
| **Extensibility** | 7/10 | Agent/Skill 声明式注册。扣分: 抽象接口不完整 |
| **Governance** | 8/10 | YAML 单一事实源，SOP Gate，ADR 流程。业界领先水平 |
| **Platformization** | 5/10 | .tlo/ 解耦进行中。扣分: 6 处硬编码残留，1 个过期模块 |
| **Observability** | 5/10 | Trace + Event Bus + KPI。缺 Metrics 和 Dashboard |
| **Production Readiness** | 4/10 | 缺 Auth/Health/CircuitBreaker/RateLimiting |
| **综合** | **5.7/10** | 可运行的内部工具，正演进为企业平台 |

---

## 17. Risk Assessment

| # | 风险 | 可能性 | 影响 | 等级 |
|---|------|--------|------|------|
| R1 | **ZJSN 硬编码导致新项目接入失败** | 高 | 高 | 🔴 Critical |
| R2 | **pyproject.toml 无依赖 → 环境不可复现** | 高 | 中 | 🟠 High |
| R3 | **单进程架构 → 无法承载多项目并发** | 中 | 高 | 🟠 High |
| R4 | **workflow_engine.py 被误用** | 低 | 中 | 🟡 Medium |
| R5 | **BrowserRuntime 耦合 BrowserUseDriver → 换驱动成本高** | 中 | 中 | 🟡 Medium |
| R6 | **无 API Auth → 生产部署风险** | 中 | 高 | 🟠 High |
| R7 | **配置漂移 → 多环境不一致** | 高 | 低 | 🟡 Medium |

---

## 18. Roadmap

### Phase 1: 平台解耦完成 (1-2 周)

**目标:** 消除所有硬编码，使平台可独立部署

| 任务 | 优先级 |
|------|--------|
| 消除所有 ZJSN_Test-master526 硬编码 | P0 |
| `pyproject.toml` 添加完整依赖声明 | P0 |
| 删除 `workflow_engine.py` + `_archived/` | P0 |
| `platform/runtime.py` 解除对 BrowserUseDriver 的直接依赖 | P1 |
| 统一配置入口 `aitest/config.py` | P1 |
| `platform/paths.py` 移除 Windows 绝对路径 fallback | P1 |

**收益:** 平台可在任意机器 `pip install aitest` 运行  
**风险:** 低 — 纯代码清理，不改业务逻辑

### Phase 2: 生产加固 (2-4 周)

**目标:** 使平台可安全对外暴露

| 任务 | 优先级 |
|------|--------|
| API 认证 (API Key / JWT) | P0 |
| Health Check 端点 + Readiness Probe | P0 |
| Structured Logging (替代 print) | P1 |
| Prometheus Metrics 端点 | P1 |
| Circuit Breaker for LLM calls | P1 |
| Rate Limiting 强制执行 | P1 |
| 单元测试覆盖核心模块 | P1 |
| `dist/` 从 Git 移除 | P1 |

**收益:** 可部署到生产环境  
**风险:** 中 — API 认证需前端配合

### Phase 3: 平台化扩展 (4-8 周)

**目标:** 支持多项目、多租户、插件化

| 任务 | 优先级 |
|------|--------|
| 多租户隔离 (per-tenant ChromaDB, per-tenant session) | P2 |
| Plugin 系统 (Capability Provider 动态加载) | P2 |
| Remote Browser 支持 (WebSocket/CDP) | P2 |
| MCP Browser Server | P2 |
| OpenTelemetry 分布式追踪 | P2 |
| `aitest/governance/` 重命名为 `aitest/audit_engine/` | P3 |
| 前端 E2E 测试修复 + 扩展 | P3 |

**收益:** 可作为 SaaS 平台对外提供服务  
**风险:** 中 — 架构变更需设计评审

---

## 19. Final Recommendations

### 19.1 立即行动 (本周)

1. **消除所有硬编码路径** — 这是平台化的最大障碍
2. **声明运行时依赖** — 使环境可复现
3. **删除过期代码** — `workflow_engine.py` + `_archived/`

### 19.2 短期 (2 周内)

4. **统一配置管理** — 创建 `config.py`，消除分散的 `os.environ` 读取
5. **BrowserRuntime 依赖反转** — 通过 CapabilityRegistry 注入，不直接 import
6. **添加 Health Check** — 最基本的生产就绪要求

### 19.3 中期 (1-2 月)

7. **API 认证** — 任何对外暴露的前提
8. **Structured Logging + Metrics** — 可观测性基础
9. **增加测试覆盖** — 当前 4/10 的 Testability 评分不可接受
10. **God Module 拆分** — `infra/cli.py`, `graphs/sop_graph.py`

### 19.4 架构原则建议

1. **Platform 不 import 任何业务模块** — 当前 `platform/runtime.py` 违规
2. **Governance 配置层保持 Python-free** — governance/ 98% YAML/MD 是正确的设计
3. **Agent 定义继续声明式** — 不退回代码硬编码
4. **每个新模块问: "这个能用于另一个项目吗?"** — 如果不能，放在 Testing Domain 而非 Platform

---

## Appendix A: 文件统计

| 指标 | 数值 |
|------|------|
| Python 文件总数 | 114 |
| Python 总行数 | ~46,000 |
| 最大文件 | `infra/cli.py` (2,191行) |
| 子包数量 | 15 |
| 前端 Vue 组件 | 26 |
| Pinia Store | 5 |
| Agent 定义 (测试) | 12 |
| Agent 定义 (开发) | 11 |
| Skill (测试) | 40 |
| Skill (开发) | 54 |
| MCP Tools | 13 |
| Workflow | 10 |
| ADR 文档 | 4 |
| 架构文档 | 8 |
| ChromaDB 集合 | 5 (235 文档) |
| KPI 时序文件 | 35 |

## Appendix B: 关键文件索引

| 文件 | 角色 |
|------|------|
| `docs/architecture/00-ARCHITECTURE_OVERVIEW.md` | v1.0 架构总览 |
| `docs/adr/ADR_001_TLO_DIRECTORY.md` | .tlo/ 目录决策 |
| `governance/agents/agent-definitions.yaml` | Agent 单一事实源 |
| `governance/context/shared-language.md` | 领域术语表 |
| `aitest/agents/agent_runner.py` | Agent 执行引擎核心 |
| `aitest/graphs/sop_graph.py` | LangGraph 编排器 |
| `aitest/platform/paths.py` | 路径解析中枢 |
| `aitest/platform/runtime.py` | 浏览器运行时抽象 |
| `aitest/llm/provider.py` | LLM Provider 抽象 |
| `aitest/server/main.py` | FastAPI 服务入口 |
| `aitest/infra/cli.py` | CLI 工具 |

---

> **评审结论:** AITest Platform 在治理体系和 Agent 工程方面已达到较高成熟度 (8/10)，但在平台独立性 (5/10) 和生产就绪度 (4/10) 方面仍有显著差距。核心问题不是架构设计 — 设计方向正确 — 而是**执行层面的耦合残留**和**运维基础设施缺失**。建议优先完成 Phase 1 平台解耦，再投入 Phase 2 生产加固。
