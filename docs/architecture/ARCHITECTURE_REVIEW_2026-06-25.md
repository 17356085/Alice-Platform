# Architecture Review Report — AITest Platform v2

> **评审类型:** Full Architecture Re-Audit  
> **评审日期:** 2026-06-25  
> **评审范围:** 全仓库 (aitest/ 242 .py files + governance/ 1,071 files + docs/)  
> **上次评审:** 2026-06-23 (5.7/10)  
> **评审人:** Enterprise Architect (Claude)

---

## 1. Executive Summary

### 1.1 Delta since 2026-06-23

| 维度 | 06-23 | 06-25 | Δ |
|------|-------|-------|---|
| Python 文件数 | 114 | 242 | +128 (+112%) |
| Python 总行数 | ~46,000 | ~66,500 | +20,500 (+45%) |
| 前端框架 | Vue 3 | React 18 + Zustand | 全量迁移 |
| 前端源文件 | 26 | 53 | +27 |
| 测试文件 | 1 | 11 | +10 |
| `platform/` 行数 | ~3,100 | 9,587 | +6,487 (+209%) |
| `server/main.py` | ~199 | 2,137 | +1,938 |
| `workflow_engine.py` | 626行 (deprecated) | 已删除 | ✅ |
| 硬编码 ZJSN | 6处 | 1处 (paths.py:17) | -5 |
| `print()` 调用 | 未统计 | 50处 | 新识别 |
| 架构冻结 | 无 | v2.0-v2.4 FROZEN | 新 |

### 1.2 评分总览 (1-10)

| 维度 | 06-23 | 06-25 | 说明 |
|------|-------|-------|------|
| Modularity | 7 | **7** | 分层仍清晰。platform/ 膨胀需关注 |
| Maintainability | 6 | **5** | server/main.py 2,137行。50 print()。25文件>500行 |
| Scalability | 5 | **6** | WorkerPool/ExecutionService 引入并发原语 |
| Testability | 4 | **5** | 11测试文件 1,476行。仍缺关键路径覆盖 |
| Extensibility | 7 | **8** | Plugin系统+RunEvent消费者。Capability注册改进 |
| Governance | 8 | **8** | 稳定。YAML+MCP+Audit全链路 |
| Platformization | 5 | **7** | ZJSN从6处→1处。.tlo/解耦接近完成 |
| Observability | 5 | **6** | EventBus+Timeline+MetricsConsumer+Otel |
| Production Readiness | 4 | **5** | Auth中间件+RateLimit定义。缺强制执行 |
| **综合** | **5.7** | **6.3** | +0.6 — 平台化进展显著，工程卫生退步 |

**核心判断**: 架构设计质量提升 (v2.0-v2.4 冻结层稳定)。工程卫生退步 (`main.py` 2,137行, 50 `print()`, 70+ 路径计算重复)。前端迁移 React 带来构建-OOM 风险。

---

## 2. Current Architecture Topology

### 2.1 架构层级 (已验证最新)

```
Presentation   React 18 + Zustand + Tailwind (aitest/web/src/)   ← Vue→React
               Electron Shell (web/electron/)
               MCP Protocol JSON-RPC (aitest/mcp/)
    │
API Layer      FastAPI (server/main.py: 2,137行 ⚠️)
               REST+SSE+WS. Auth中间件 (server/auth.py: 179行)
    │
Orchestration  LangGraph StateGraph (graphs/: 4,731行)
               SOP Graph + Parallel SOP + Review Graph + Bug Graph
               Dev SOP Graph (graphs_dev/: 307行)
    │
Execution      AgentLoop (agents/agent_runner.py: 1,190行)
               Perceive→Plan→Act→Observe→Update
               SkillExecutor + PipelineRouter + PlanEngine
    │
Platform       platform/: 9,587行 (3x growth)
  v2.0-v2.4    ExecutionService + Run + RunEvent + EventBus
  FROZEN        Lifecycle + Consumer + Timeline + Workspace
               CapabilityRouter + ComplexityClassifier
    │
Infrastructure infra/: 5,709行
               LLM Provider/Reliable/ContextWindow/CircuitBreaker
               Security + WorkerPool + TaskQueue + Telemetry
    │
Domain         audit_engine/: 8,521行 (15 auditors)
               knowledge/: 1,435行 (RAG+ChromaDB)
               testing/: 3,082行 (Evaluator+Regression+Exporter)
               discovery/: 3,244行 (Source+VueExtractor+FrameworkDetector)
```

### 2.2 依赖方向验证

```
Presentation → API → Orchestration → Execution → Platform → Infrastructure
                                                         → Domain (audit_engine/testing/discovery)

❌ 违规: platform/runtime.py → integrations/bu_driver.py (平台→集成)
⚠️ 违规: agents/agent_scheduler.py → governance.validators (aitest→governance/)
⚠️ 扩散: 70+文件各自计算 WORKSTUDY root (Path(__file__).resolve().parent.parent.parent)
```

**零循环依赖仍然成立。** 但 platform/runtime.py 的层违规未修复 (06-23 评审已标记)。

---

## 3. Module Deep-Dive

### 3.1 God Module 演变

| 文件 | 06-23 行数 | 06-25 行数 | Δ | 状态 |
|------|-----------|-----------|-----|------|
| `server/main.py` | 199 | **2,137** | +1,938 | ❌ CRITICAL |
| `infra/cli.py` | 2,191 | 1,597 (cli/__init__.py) | -594 | ⚠️ IMPROVED |
| `graphs/sop_graph.py` | 1,446 | 1,449 | +3 | 持平 |
| `agents/agent_runner.py` | 1,014 | 1,190 | +176 | ⚠️ |
| `llm/provider.py` | 1,021 | 1,021 | 0 | 持平 |
| `audit_engine/state_auditor.py` | 1,213 | 1,213 | 0 | 持平 |
| `platform/lifecycle.py` | — | **1,043** | 新 | ⚠️ NEW |
| `platform/ownership.py` | — | **746** | 新 | 新 |
| `testing/evaluator.py` | 937 | 937 | 0 | 持平 |
| `audit_engine/sop_auditor.py` | — | **877** | 新 | 新 |

### 3.2 server/main.py — Critical Expansion

2,137行入口文件是新架构最大风险。拆解其内容:

| 段落 | 行范围 | 行数 | 职责 |
|------|--------|------|------|
| Import + 模块导入 | 1-38 | 38 | 合法聚合 |
| Lifespan + DB Init | 40-55 | 16 | Startup |
| Subscriber 激活 | 57-130 | 74 | KnowledgeAgent + Audit + Webhook + Metrics + Billing + Quota |
| LifecycleRegistry | 113-124 | 12 | 注册 |
| 路由挂载 | 126-138 | 13 | API routers |
| 审计调度器 | 140-198 | 59 | 定时全量审计 |
| REST endpoints | 200-2137 | **1,937** | 🔴 业务逻辑嵌入 main.py |

**诊断**: 大量业务逻辑 (REST handlers) 直接写在 `main.py` 而非 router 文件。`server/api/` 下仅 13 个 router 文件合计 2,360 行，而 `main.py` 自身 2,137 行。

**修复**: main.py 应为薄壳 (≤200行) — 仅 lifespan + router 挂载。业务 handlers 全部移入 `server/api/`。

### 3.3 platform/lifecycle.py — New God Module

1,043 行单文件管理全平台生命周期。职责过载:
- LifecycleRegistry (注册/注销/心跳)
- LifecycleObject 协议
- MemoryGuard (内存守卫)
- OwnershipChecker (所有权检查)
- guarded_create_task (安全任务创建)

**建议**: 拆分为 `lifecycle/registry.py`, `lifecycle/guard.py`, `lifecycle/ownership.py`。

---

## 4. Boundary Analysis (Re-verified)

### 4.1 三层边界

```
PLATFORM (多项目复用)  →  platform/ + llm/ + infra/ + mcp/
AI AGENT RUNTIME       →  agents/ + graphs/ + graphs_dev/ + governance/agents/
TESTING DOMAIN         →  audit_engine/ + testing/ + discovery/ + governance/skills/
```

### 4.2 Boundary Leakage (Updated)

| # | 问题 | 06-23 | 06-25 | 严重度 |
|---|------|-------|-------|--------|
| 1 | **ZJSN 硬编码** | 6处 | **1处** (paths.py:17) | ✅ DOWN |
| 2 | **platform→integrations** | runtime.py:145 | runtime.py:117,164 | 未修复 |
| 3 | **aitest→governance** | — | agent_scheduler.py:28 | 新发现 |
| 4 | **70+ Path(__file__).parent...** | 10+ | **70+** | ❌ WORSE |
| 5 | **server/main.py 业务逻辑** | 199行 | 2,137行 | ❌ WORSE |
| 6 | **workflow_engine legacy option** | 626行文件 | workflows.py:24 (dead path) | ✅ CLEANED |
| 7 | **50 print() calls** | 未统计 | 50处 | 新识别 |

### 4.3 70+ 路径计算重复 — 详细分析

模式 `Path(__file__).resolve().parent.parent.parent` 出现于 ~70 个文件。分布:

| 目录 | 出现次数 |
|------|----------|
| agents/ | 10 |
| knowledge/ | 3 |
| graphs/ | 6 |
| infra/ | 8 |
| audit_engine/ | 12 |
| platform/ | 3 |
| llm/ | 2 |
| testing/ | 5 |
| server/ | 2 |
| integrations/ | 1 |
| graphs_dev/ | 1 |
| tools/ | 1 |
| governance/validators/ | 2 |
| 其他 | ~14 |

**根因**: `platform/paths.py` 已有 `get_workstudy()` 和 `get_project_root()`，但 ~70 个文件选择各自计算。

**修复**: 全局替换为 `from aitest.platform.paths import get_workstudy`，一次改 ~70 文件。风险低 (纯机械替换)。

---

## 5. Platform v2.0-v2.4 FROZEN Audit

### 5.1 冻结模块稳定性检查

| 冻结模块 | 行数 | 06-23以来变更 | 状态 |
|----------|------|--------------|------|
| `platform/runtime.py` | 499 | 未知 | 需验证 |
| `platform/execution_service.py` | 289 | 新模块 | ✅ STABLE |
| `platform/run.py` | 150 | 新模块 | ✅ STABLE |
| `platform/run_event.py` | 96 | 新模块 | ✅ STABLE |
| `platform/event_bus.py` | 90 | 新模块 | ✅ STABLE |
| `platform/consumer.py` | 28 | 新模块 | ✅ STABLE |

### 5.2 冻结违规检查

| 违规类型 | 位置 | 说明 |
|----------|------|------|
| runtime.py import integrations | runtime.py:117 | 冻结模块依赖非冻结集成层 |
| consumer.py print() | consumer.py:12 | CONSTITUTION 禁止生产代码 print() |

---

## 6. Frontend Architecture (Vue → React Migration)

### 6.1 Migration Status

**Vue 3 组件全部删除，React 18 替代。** 53 源文件，5,930 行。

| 层 | 技术 | 文件数 |
|----|------|--------|
| 视图 | React 18 + React Router 6 | 14 views |
| 状态 | Zustand 4.5 | 5 stores |
| UI | Tailwind 3.4 + Radix UI | — |
| 终端 | @xterm/xterm 5.5 | 嵌入式终端 |
| 国际化 | i18next 23 + react-i18next | 2 locale files |
| 桌面 | Electron (含 Tauri 评估) | electron/main.js |

### 6.2 Known Issues

| 问题 | 文档 | 严重度 |
|------|------|--------|
| **生产构建 OOM** | FRONTEND_REBUILD_PLAN_A.md | 🔴 CRITICAL |
| 内存泄漏 RC1-Chat 线程 | MEMORY_LEAK_RCA_2026-06-24.md | 🔴 CRITICAL |
| 内存泄漏 RC2-MetricsConsumer | 同上 | 🟠 HIGH |
| E2E 测试端口不匹配 | e2e/smoke.spec.ts | 🟡 MEDIUM |
| 无 Vitest/Testing Library | package.json | 🟡 MEDIUM |
| dist/ 提交到 Git | git status | 🟡 MEDIUM |

### 6.3 Build OOM Root Cause

开发模式不OOM (ESM模块隔离)。生产构建 Rollup 合并所有模块 → 闭包合并 → 完整响应式循环。

**修复计划** (FRONTEND_REBUILD_PLAN_A): 多入口构建 — App shell 和各页面独立 chunk，破坏闭合循环。预计 3 小时。

---

## 7. Memory Leak Analysis (2026-06-24 RCA)

### 7.1 Three Root Causes

| RC | 组件 | 机制 | 逃逸原因 |
|----|------|------|----------|
| RC1 | Chat SSE | 守护线程+无界Queue | Lifecycle仅跟踪asyncio Task |
| RC2 | MetricsConsumer | 模块级无界dict | 单例未注册为LifecycleObject |
| RC3 | EventBus | 订阅者强引用 | BoundSubscription存在但未使用 |

### 7.2 Fix Status

| 修复 | 状态 |
|------|------|
| Chat SSE 线程→asyncio | 待实现 |
| MetricsConsumer dict→TTL cap | 待实现 |
| BoundSubscription 强制使用 | 待实现 |
| Observed增长点监控 | lifecycle.py 已有，需接入 |

---

## 8. Test Coverage Assessment

| 目录 | 文件数 | 行数 | 覆盖模块 |
|------|--------|------|----------|
| tests/ | 6 | 1,075 | circuit_breaker, config, platform_freeze, sop_routing, tenant |
| tests/integration/ | 5 | 508 | agent_loop, capability_enforcement, plugin_system, sop_graph |
| **总计** | **11** | **1,583** | |

### 8.1 Missing Coverage (Critical Paths)

| 未覆盖模块 | 影响 |
|------------|------|
| `agent_runner.py` (1,190行) | 核心Agent执行 |
| `sop_graph.py` (1,449行) | 主编排器 |
| `reliable_provider.py` (390行) | LLM可靠性链 |
| `capability_router/router.py` (279行) | 能力路由 |
| `security.py` (340行) | 安全层 |
| `audit_engine/*` (8,521行) | 全审计引擎 |
| `observation_bus.py` (250行) | 事件总线 |

**综合**: 1,583行测试覆盖~66,500行代码 = **2.4%** 行覆盖。Alpha Validation (06-24) 报告 94 单元测试，当前仅 11 文件 — 测试文件数与测试用例数不匹配 (可能是参数化测试)。

---

## 9. Dependency & Configuration Health

### 9.1 os.environ Direct Access (CONSTITUTION Violation)

CONSTITUTION §禁止清单: "禁止在 config.py 外使用 os.environ"

| 文件 | 行 | 变量 |
|------|-----|------|
| `mcp/browser_server.py` | 146 | `AITEST_BROWSER_BACKEND` |
| `server/auth.py` | 49 | `AITEST_API_KEY` |
| `infra/telemetry.py` | 35,59 | `AITEST_OTEL_ENABLED/ENDPOINT` |
| `platform/plugin.py` | 56 | `AITEST_PLUGIN_PATH` |

**共6处违规。** 应替换为 `config.get_env()`。

### 9.2 load_dotenv() Calls

仅 2 处: `config.py:26` + `infra/cli/__init__.py:733`。✅ 已收敛。

### 9.3 print() vs Logging

50 个 `print()` 调用分布在 15 个文件中:

| 目录 | print() 数 |
|------|-----------|
| agents/ | 41 |
| graphs/ | 5 |
| platform/ | 4 |

`infra/logging.py` (136行) 存在但被绕过。CONSTITUTION 明确禁止生产代码 print()。

---

## 10. Technical Debt Assessment

### 10.1 Critical (阻塞架构演进)

| # | 债务 | 位置 | 影响 |
|---|------|------|------|
| C1 | **server/main.py God Module** | 2,137行 | 所有API变更需触碰巨型文件 |
| C2 | **70+ 路径计算重复** | ~70文件 | 目录结构变更需改70处 |
| C3 | **前端构建OOM** | vite build | 生产部署阻塞 |
| C4 | **内存泄漏 RC1** | Chat SSE线程 | 长期运行OOM |

### 10.2 High (影响可维护性)

| # | 债务 | 位置 |
|---|------|------|
| H1 | platform/runtime.py 层违规 | runtime.py:117,164 |
| H2 | 50 print() 替代 logging | ~15文件 |
| H3 | 6处 os.environ 直接读取 | 6文件 |
| H4 | platform/lifecycle.py 1,043行 | lifecycle.py |
| H5 | dead "legacy" engine option | server/api/workflows.py:24 |
| H6 | 测试覆盖 2.4% | 全局 |

### 10.3 Medium

| # | 债务 | 位置 |
|---|------|------|
| M1 | aites→governance 跨边界 import | agents/agent_scheduler.py:28 |
| M2 | E2E 端口不一致 | e2e/smoke.spec.ts |
| M3 | dist/ 提交到 Git | aitest/web/dist/ |
| M4 | graphs/__init__.py stale docstring | 引用已删除的 _archived/ |
| M5 | 前端无 lint/format/test 脚本 | package.json |

---

## 11. Risk Assessment (Updated)

| # | 风险 | 可能性 | 影响 | 等级 | 06-23状态 |
|---|------|--------|------|------|-----------|
| R1 | **前端构建OOM阻断部署** | 高 | 高 | 🔴 CRITICAL | 新 |
| R2 | **server/main.py 膨胀→合并冲突+回归** | 高 | 中 | 🟠 HIGH | 新 |
| R3 | **Chat SSE内存泄漏→长期运行OOM** | 高 | 高 | 🔴 CRITICAL | 新 |
| R4 | 70+路径重复→重构成本高 | 中 | 中 | 🟡 MEDIUM | 新 |
| R5 | ZJSN硬编码→新项目接入失败 | 低 | 高 | 🟡 MEDIUM | 曾CRITICAL |
| R6 | pyproject.toml 无依赖→环境不可复现 | 高 | 中 | 🟠 HIGH | 未变 |
| R7 | 单进程架构→多项目并发瓶颈 | 中 | 高 | 🟠 HIGH | 未变 |
| R8 | platform→integrations 耦合→换驱动成本 | 中 | 中 | 🟡 MEDIUM | 未变 |
| R9 | 测试覆盖2.4%→回归检测失效 | 中 | 高 | 🟠 HIGH | 恶化 |

---

## 12. Recommendations (Prioritized)

### Phase 1: 止损 (本周)

| # | 行动 | 优先级 | 预估 |
|---|------|--------|------|
| 1 | **修复前端构建OOM** — 多入口构建 (FRONTEND_REBUILD_PLAN_A) | P0 | 3h |
| 2 | **server/main.py 拆分** — handlers 移入 api/ routers | P0 | 4h |
| 3 | **修复Chat SSE内存泄漏 (RC1)** — asyncio Task替代Thread | P0 | 2h |
| 4 | **全局替换70+路径计算** — `Path(__file__).parent...` → `get_workstudy()` | P1 | 1h |
| 5 | **50 print()→logging** — 批量替换 | P1 | 1h |
| 6 | **6处 os.environ→config.get_env()** | P1 | 0.5h |

### Phase 2: 加固 (2周)

| # | 行动 | 优先级 |
|---|------|--------|
| 7 | MetricsConsumer 无界dict→TTL cap (RC2) | P1 |
| 8 | BoundSubscription 强制使用 (RC3) | P1 |
| 9 | platform/runtime.py 依赖反转 | P1 |
| 10 | platform/lifecycle.py 拆分 | P2 |
| 11 | dead "legacy" engine option 移除 | P2 |
| 12 | 前端添加 Vitest + Testing Library | P2 |

### Phase 3: 平台成熟 (1月)

| # | 行动 | 优先级 |
|---|------|--------|
| 13 | 测试覆盖从2.4%→15% (agent_runner+sop_graph+security) | P1 |
| 14 | API 版本策略 + 统一错误格式 | P2 |
| 15 | Rate Limiting 强制执行 | P2 |
| 16 | 前端 E2E 端口修复 | P3 |
| 17 | dist/ 从 Git 移除 | P3 |

---

## 13. Architecture Maturity Scores (Final)

| 维度 | 06-23 | 06-25 | 评语 |
|------|-------|-------|------|
| **Modularity** | 7 | 7 | 分层干净。platform/膨胀+main.py需拆分 |
| **Maintainability** | 6 | **5** | 退步。God Module 更严重。print()泛滥 |
| **Scalability** | 5 | **6** | WorkerPool+ExecutionService 改善并发 |
| **Testability** | 4 | **5** | 10x测试文件增长。2.4%覆盖仍不足 |
| **Extensibility** | 7 | **8** | Plugin+RunEvent消费者。架构冻结清晰 |
| **Governance** | 8 | **8** | 稳定。YAML+ADR+MCP+Audit |
| **Platformization** | 5 | **7** | 最大进展。ZJSN 6→1, .tlo/成熟 |
| **Observability** | 5 | **6** | EventBus+Timeline+Otel端点 |
| **Production Readiness** | 4 | **5** | Auth中间件存在，缺强制执行 |
| **综合** | **5.7** | **6.3** | +0.6 — 架构方向正确，执行卫生退步 |

---

> **评审结论:** AITest Platform v2 取得了显著的架构进步 (+0.6) — 平台解耦接近完成、v2.0-v2.4 冻结层稳定、前端完成 Vue→React 现代化迁移。但快速迭代带来了工程卫生问题：God Module 膨胀 (main.py 2,137行)、70+ 路径计算重复、50 print() 泛滥、关键内存泄漏未修复、测试覆盖仅 2.4%。建议立即执行 Phase 1 止损 (3天)，然后 Phase 2 加固 (2周)，再进入后续 feature 开发。
>
> **与 06-23 评审对比**: 平台解耦从最大风险降为可控。新最大风险是前端构建 OOM + server/main.py 膨胀 + Chat 内存泄漏。这三个问题应在本周内关闭。

---

## Appendix A: 文件统计

| 指标 | 06-23 | 06-25 | Δ |
|------|-------|-------|-----|
| Python 文件 | 114 | 242 | +128 |
| Python 总行数 | ~46,000 | ~66,500 | +20,500 |
| 最大文件 | infra/cli.py (2,191) | server/main.py (2,137) |
| >1,000 行文件数 | 3 | 5 |
| >500 行文件数 | 12 | 25 |
| 前端源文件 | 26 (.vue) | 53 (.tsx/.ts) | +27 |
| 测试文件 | 1 | 11 | +10 |
| 测试行数 | ~220 | 1,583 | +1,363 |
| Agent 定义 | 12+11 | 12+11 | 0 |
| Skill | 40+54 | 37+66 | -3+12 |
| MCP Tools | 13 | 13 | 0 |
| Workflow | 10 | 11 | +1 |
| ADR | 4 | 4 | 0 |
| 架构文档 | 8 | 23+9(reviews) | +24 |

## Appendix B: 关键文件索引 (Updated)

| 文件 | 角色 | 行数 |
|------|------|------|
| `docs/architecture/00-ARCHITECTURE_OVERVIEW.md` | v1.0 架构总览 | 162 |
| `docs/architecture/CONSTITUTION.md` | 架构宪章 | 330 |
| `docs/architecture/ARCHITECTURE_FREEZE_V1.md` | v2.0-2.4 冻结声明 | 84 |
| `docs/architecture/DESIGN_DECISIONS.md` | 12项不可逆设计决策 | 199 |
| `docs/adr/ADR_001_TLO_DIRECTORY.md` | .tlo/ 目录决策 | — |
| `governance/agents/agent-definitions.yaml` | Agent 单一事实源 | 524 |
| `governance/context/shared-language.md` | 170+ 领域术语 | 231 |
| `aitest/agents/agent_runner.py` | Agent 执行引擎 | 1,190 |
| `aitest/graphs/sop_graph.py` | LangGraph 编排器 | 1,449 |
| `aitest/platform/paths.py` | 路径解析中枢 | 184 |
| `aitest/platform/runtime.py` | 浏览器运行时 | 499 |
| `aitest/platform/execution_service.py` | 执行编排 (v2.2) | 289 |
| `aitest/platform/lifecycle.py` | 生命周期+内存守卫 | 1,043 |
| `aitest/llm/provider.py` | LLM Provider 抽象 | 1,021 |
| `aitest/llm/reliable_provider.py` | 可靠性链 | 390 |
| `aitest/server/main.py` | FastAPI 入口 **CRITICAL** | 2,137 |
| `aitest/infra/cli/__init__.py` | CLI 工具 | 1,597 |
| `aitest/infra/security.py` | 3层安全模型 | 340 |
| `aitest/infra/worker_pool.py` | 并发执行池 | 201 |
| `aitest/audit_engine/state_auditor.py` | 状态审计 | 1,213 |
| `aitest/audit_engine/qa_loop.py` | 质量保证循环 | 491 |
