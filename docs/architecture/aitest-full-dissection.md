# aitest 全量目录解剖报告

> 日期: 2026-07-01
> 总代码: ~70,000 行

---

## 总览

```
目录                行数      文件数   定位
──────────────────────────────────────────────────
tests/              11701     60       测试 (不属于SDK)
platform/           9911      52       平台层 (Web/Dashboard/Multi-tenant)
infra/              6313      30       基础设施 (Redis/Queue/Trace)
server/             6012      29       Web API (FastAPI)
audit_engine/       4867      15       审计引擎 (质量门禁)
graphs/             4754      11       Workflow 编排 ⭐ 可进SDK
agents/             3913      18       Agent 框架 ⭐ 部分可进SDK
testing/            3842      9        测试工具
discovery/          3709      15       页面发现 (Selenium/BrowserUse)
engine/             3297      14       Engine 核心 ⭐ 已部分进SDK
adapters/           3176      13       适配器层
llm/                3157      18       LLM 抽象层 ⭐ 部分可进SDK
cli/                2915      19       CLI 入口
mcp/                2432      24       MCP 集成
runtime/            1987      10       Runtime 能力 ⭐ 可进SDK
knowledge/          1653      5        知识管理 (RAG)
integrations/       1295      3        外部集成
tools/              1049      4        工具脚本
knowledge_model/    895       3        知识模型
onboarding/         848       2        引导流程
graphs_dev/         317       3        开发SOP图
chat/               196       2        聊天接口
```

---

## 按归属分类

### 🔴 Engine Core (应进 SDK) — ~13000 行

```
模块              文件              行数    状态
────────────────────────────────────────────────
Workflow          graphs/sop_graph   1509   待迁移
Workflow          graphs/state       550    待迁移
Workflow          graphs/nodes       361    待迁移
Workflow          graphs/sop_runner  434    待迁移
Workflow          graphs/parallel    271    待迁移
Workflow          graphs/review      461    待迁移
Workflow          graphs/execution   335    待迁移
Workflow          graphs/lifecycle   312    待迁移
Runtime           runtime/retry      392    待迁移
Runtime           runtime/ctx_window 317    待迁移
Runtime           runtime/checkpoint 259    待迁移
Runtime           runtime/config     243    待迁移
Runtime           runtime/paths      174    待抽象
Engine            engine/executor    1401   已解剖
Engine            engine/skill_exec  282    待迁移
Engine            engine/planner     307    已在SDK
Engine            engine/task        216    已在SDK
Engine            engine/state_mach  203    已在SDK
Engine            engine/skill_load  452    已在SDK
LLM               llm/ctx_injector   662    待迁移
LLM               llm/skill_registry 439    待迁移
LLM               llm/ctx_builder    395    待迁移
LLM               llm/circuit_break  177    待迁移
Agent             agents/core        731    待迁移
Agent             agents/ctx_agent   497    待迁移
```

### 🟢 Runtime Audit (应进 SDK) — ~4867 行

```
模块              文件                  行数    说明
────────────────────────────────────────────────────────
Audit             cost_auditor          749    成本审计
Audit             safety_auditor        733    安全检查 ⭐
Audit             online_monitor        533    在线监控 ⭐
Audit             governance_kpi        533    治理KPI
Audit             qa_loop               503    QA循环
Audit             failure_attributor    378    失败归因 ⭐
Audit             step_efficiency       353    步骤效率
Audit             diff_extractor        317    Diff提取
Audit             review_trigger        311    审查触发
Audit             diff_first_review     265    Diff审查适配器
Audit             scheduled_audit       168    定时审计
```

> 决策: audit_engine 进 SDK，作为 Runtime Audit 能力。
> 质量门禁、安全检查、失败归因是 Engine 核心能力，不是可选插件。
> 依赖 `aitest.platform.paths` 需要通过 PathResolver 接口解耦。

### 🟡 Extension (可选增强) — ~2000 行

```
模块              文件              行数    说明
────────────────────────────────────────────────
Agent Ext         agents/human_feed  416    人工反馈
Agent Ext         agents/scheduler   416    Agent调度
Agent Ext         agents/benchmark   327    Agent基准测试
Agent Ext         agents/ab_test     273    A/B测试
Agent Ext         agents/prompt_bench 375   Prompt基准
```

### 🔵 Platform (平台特有) — ~25000 行

```
模块              行数    说明
────────────────────────────────────────────────
platform/         9911    Web Dashboard, Multi-tenant, RBAC
infra/            6313    Redis, Queue, Trace, Telemetry
server/           6012    FastAPI Web API
cli/              2915    CLI 入口 (Typer)
adapters/         3176    适配器层
discovery/        3709    Selenium/BrowserUse 页面发现
mcp/              2432    MCP 集成
knowledge/        1653    RAG 引擎
integrations/     1295    外部集成
tools/            1049    工具脚本
onboarding/       848     引导流程
```

### 🟣 LLM 层 (部分进 SDK) — ~3157 行

```
模块                  行数    平台依赖   归属
────────────────────────────────────────────────
context_injector       662    paths      SDK (需解耦)
skill_registry         439    无         SDK ⭐
context_builder        395    无         SDK ⭐
circuit_breaker        177    无         SDK ⭐
prompt_adapter          2    adapters   SDK (re-export)
provider                6    adapters   SDK (re-export)
context_window          6    runtime    SDK (re-export)
skill_loader            5    engine     SDK (re-export)
reliable_provider       7    runtime    SDK (re-export)
```

### 🟤 Agents 层 (部分进 SDK) — ~3913 行

```
模块                  行数    平台依赖   归属
────────────────────────────────────────────────
core                   731    无         SDK ⭐
context_agent          497    paths      SDK (需解耦)
interactive_runner     128    无         SDK ⭐
output_persistence     199    event_bus  SDK (需解耦)
consistency_checks     161    provider   SDK (需解耦)
human_feedback         416    logging    Extension
agent_scheduler        416    event_bus  Extension
prompt_benchmark       375    logging    Extension
agent_benchmark        327    logging    Extension
ab_test                273    paths      Extension
pipeline_router        357    graphs_dev Extension
```

### 🔵 Adapters 层 (部分进 SDK) — ~3176 行

```
模块                  行数    平台依赖   归属
────────────────────────────────────────────────
audit.state           1224    graphs     SDK (需解耦)
audit.sop              883    paths      SDK (需解耦)
event.interface        694    paths      SDK (需解耦)
llm.prompt             151    无         SDK ⭐
llm.provider_base      142    无         SDK ⭐
llm.interface           82    providers  SDK ⭐
```

### ⚪ Platform / 工具 (不进 SDK) — ~30000 行

```
模块              行数    说明
────────────────────────────────────────────────
server/           6012    FastAPI Web API
infra/            6313    Redis/Queue/Trace/Telemetry
platform/         9911    Dashboard/Multi-tenant/RBAC
cli/              2915    CLI 入口 (Typer)
discovery/        3709    Selenium/BrowserUse 页面发现
mcp/              2432    MCP 集成
knowledge/        1653    RAG 引擎
integrations/     1295    外部集成 (BrowserUse/GitHub)
tools/            1049    工具脚本
testing/          3842    测试工具
onboarding/       848     引导流程
knowledge_model/  895     知识模型
chat/             196     聊天接口
tests/            11701   测试代码
```

---

## SDK 迁移路线图

```
Phase A: 解剖完成 ✅
Phase B: 定义接口 ✅ (5个接口已定义)
Phase C: runtime/ 迁移 (~1400行, 零依赖)
Phase D: llm/ 迁移 (~1600行, 大部分零依赖)
Phase E: graphs/ 迁移 (~4200行, 低依赖)
Phase F: engine/ 迁移 (~2400行, 中依赖)
Phase G: audit_engine/ 迁移 (~4867行, 需解耦paths)
Phase H: agents/ 核心迁移 (~1500行, 需解耦)
Phase I: adapters/ 迁移 (~3176行, 需解耦)
Phase J: aitest 改为 import

总计: ~21000 行可进SDK
```

## 零依赖文件 (可直接移入 SDK)

| 文件 | 行数 | 说明 |
|------|------|------|
| llm/skill_registry.py | 439 | Skill 注册表 |
| llm/context_builder.py | 395 | 上下文构建器 |
| llm/circuit_breaker.py | 177 | 熔断器 |
| runtime/context_window.py | 317 | 上下文窗口监控 |
| runtime/config.py | 243 | 运行时配置 |
| agents/core.py | 731 | Agent 核心框架 |
| agents/interactive_runner.py | 128 | 交互式执行器 |
| adapters/llm/prompt.py | 151 | Prompt 适配器 |
| adapters/llm/provider_base.py | 142 | Provider 基类 |
| adapters/llm/interface.py | 82 | LLM 接口 |
| **合计** | **2805** | **可直接移入** |

---

## 关键洞察

1. **Engine Core 占 23%** — ~16000 行可进 SDK
2. **graphs/ 几乎全是 Core** — LangGraph 编排是通用的
3. **runtime/ 一半零依赖** — 可以直接移
4. **audit_engine/ 进 SDK** — 质量门禁、安全检查、失败归因是核心能力
5. **platform/ 完全不进 SDK** — Web/Dashboard/Multi-tenant
6. **infra/ 完全不进 SDK** — Redis/Queue/Trace 是运维基础设施
7. **executor.py 直接 import audit_engine** — 违反分层，需改为 Hook
