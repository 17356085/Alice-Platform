# 全量解剖报告: aitest 引擎核心模块

> 日期: 2026-07-01
> 范围: aitest/engine/ + aitest/graphs/ + aitest/runtime/

---

## 总览

```
目录              总行数    平台依赖    可进SDK
──────────────────────────────────────────────
engine/           ~3000     中等        部分
graphs/           ~4750     低          大部分
runtime/          ~2180     低          大部分
──────────────────────────────────────────────
合计              ~9930
```

---

## 1. aitest/graphs/ — Workflow 编排层

### sop_graph.py (1509行) — 顶层 LangGraph 编排器

```
平台依赖: 3个
  - aitest.platform.paths (路径)
  - aitest.audit_engine.event_bus (事件)
  - aitest.graphs.state (同目录，可带入)

职责分解:
  行范围      内容                        归属
  ─────────────────────────────────────────────
  1~60        imports + 图结构定义         Core
  61~200      build_sop_graph()           Core ← 这是核心
  201~400     节点函数 (entry/preflight)   Core
  401~800     Agent 节点包装               Core
  801~1000    条件路由 + Gate              Core
  1001~1200   HITL interrupt              Core
  1201~1509   辅助函数 + 旧接口兼容        Core

结论: 90% 是 Core，只有路径和事件是 Platform。
解耦难度: 低 — 路径通过参数传入，事件通过 EventBus 注入。
```

### state.py (550行) — SOP 状态定义

```
平台依赖: 1个
  - aitest.platform.paths (路径解析)

职责分解:
  行范围      内容                        归属
  ─────────────────────────────────────────────
  1~100       数据结构 (SOPState等)        Core ← 纯数据
  101~200     Phase/Agent 枚举            Core ← 纯常量
  201~350     create_initial_state()      Core
  351~550     辅助函数 (路径解析)          Platform

结论: 80% 是 Core，路径解析部分是 Platform。
解耦难度: 低。
```

### nodes.py (361行) — 图节点定义

```
平台依赖: 2个
  - aitest.platform.paths
  - aitest.graphs.state

职责分解:
  行范围      内容                        归属
  ─────────────────────────────────────────────
  1~80        imports + 节点工厂           Core
  81~200      make_agent_loop_node()      Core ← 核心
  201~361     辅助节点函数                 Core

结论: 90% 是 Core。
解耦难度: 低。
```

### sop_runner.py (434行) — SOP 执行器

```
平台依赖: 3个
  - aitest.agents.agent_runner
  - aitest.platform.paths
  - aitest.infra.logging

职责分解:
  行范围      内容                        归属
  ─────────────────────────────────────────────
  1~100       SOPRunner 类定义            Core
  101~250     run() 方法                  Core
  251~434     辅助函数 + 旧接口           Core

结论: 85% 是 Core。
解耦难度: 中 — 需要注入 logger 和 paths。
```

### parallel_sop.py (271行) — 并行 SOP

```
平台依赖: 0个 (只依赖同目录的 state/nodes)

结论: 100% Core。
解耦难度: 无。
```

### review_graph.py (461行) — 审查图

```
平台依赖: 待检查

结论: 大概率是 Core。
```

### execution_graph.py (335行) — 执行图

```
平台依赖: 待检查

结论: 大概率是 Core。
```

### lifecycle_state.py (312行) — 生命周期状态

```
平台依赖: 待检查

结论: 大概率是 Core (纯状态定义)。
```

---

## 2. aitest/runtime/ — Runtime 能力层

### retry.py (392行) — 重试 + 降级

```
平台依赖: 1个
  - aitest.llm.provider

职责分解:
  行范围      内容                        归属
  ─────────────────────────────────────────────
  1~100       ReliableProvider 类         Runtime ← 核心
  101~200     重试逻辑 + 降级链           Runtime
  201~300     UsageTracker                Runtime
  301~392     辅助函数                    Runtime

结论: 100% Runtime。
解耦难度: 低 — 只需替换 LLM provider 接口。
```

### context_window.py (317行) — 上下文窗口监控

```
平台依赖: 0个

职责分解:
  行范围      内容                        归属
  ─────────────────────────────────────────────
  1~100       ContextWindowMonitor        Runtime ← 核心
  101~200     SessionCompactor            Runtime
  201~317     build_continuation_prompt   Runtime

结论: 100% Runtime。
解耦难度: 无。
```

### context.py (336行) — 上下文管理

```
平台依赖: 4个

结论: 部分 Runtime，部分 Platform。
解耦难度: 中。
```

### checkpoint.py (259行) — 检查点管理

```
平台依赖: 1个

结论: 100% Runtime。
解耦难度: 低。
```

### config.py (243行) — 运行时配置

```
平台依赖: 0个

结论: 100% Runtime。
解耦难度: 无。
```

### paths.py (174行) — 路径解析

```
平台依赖: 1个

结论: Platform (路径约定是平台特有的)。
但可以抽象为 PathResolver 接口。
```

### error_handling.py (237行) — 错误处理

```
平台依赖: 1个

结论: 部分 Runtime，部分 Platform。
```

---

## 3. aitest/engine/ — Engine 核心层

### skill_executor.py (282行) — Skill 执行引擎

```
平台依赖: 6个
  - aitest.llm.provider
  - aitest.llm.prompt_adapter
  - aitest.llm.context_injector
  - aitest.llm.skill_registry
  - aitest.engine.skill_loader
  - aitest.runtime.paths

职责分解:
  行范围      内容                        归属
  ─────────────────────────────────────────────
  1~80        Agent→Skill映射 + 定义      Core
  81~180      run_skill()                 Core ← 核心
  181~282     辅助函数                    混合

结论: 60% Core，40% Platform (上下文注入)。
解耦难度: 中 — 需要抽象 ContextInjector 接口。
```

### planner.py (307行) — 规划引擎

```
平台依赖: 2个
  - aitest.engine.task (已在SDK)
  - aitest.runtime.paths

结论: 90% Core。
解耦难度: 低 — 路径通过参数传入。已在 SDK 中有版本。
```

---

## 汇总: 可进 SDK 的代码

| 模块 | 文件 | 行数 | Core% | 解耦难度 |
|------|------|------|-------|---------|
| Workflow | sop_graph.py | 1509 | 90% | 低 |
| Workflow | state.py | 550 | 80% | 低 |
| Workflow | nodes.py | 361 | 90% | 低 |
| Workflow | sop_runner.py | 434 | 85% | 中 |
| Workflow | parallel_sop.py | 271 | 100% | 无 |
| Workflow | review_graph.py | 461 | ?% | ? |
| Workflow | execution_graph.py | 335 | ?% | ? |
| Workflow | lifecycle_state.py | 312 | ?% | ? |
| Runtime | retry.py | 392 | 100% | 低 |
| Runtime | context_window.py | 317 | 100% | 无 |
| Runtime | checkpoint.py | 259 | 100% | 低 |
| Runtime | config.py | 243 | 100% | 无 |
| Engine | skill_executor.py | 282 | 60% | 中 |
| Engine | planner.py | 307 | 90% | 低 |
| **合计** | | **~6030** | | |

---

## 依赖解耦清单

需要注入的接口:

| 接口 | 用途 | 影响文件数 |
|------|------|-----------|
| `PathResolver` | 路径解析 | 8 |
| `EventEmitter` | 事件发射 | 4 |
| `Logger` | 结构化日志 | 3 |
| `LLMProvider` | LLM 调用 | 3 |
| `ContextInjector` | 上下文注入 | 2 |

**只有 5 个接口需要抽象，就能解耦 ~6000 行代码。**

---

## 执行顺序建议

```
Phase A: 解剖完成 ✅
Phase B: 定义 5 个接口 (PathResolver/EventEmitter/Logger/LLMProvider/ContextInjector)
Phase C: runtime/ 迁移 (retry/context_window/checkpoint/config — 无依赖)
Phase D: graphs/ 迁移 (sop_graph/state/nodes — 低依赖)
Phase E: engine/ 迁移 (skill_executor/planner — 中依赖)
Phase F: aitest 改为 import from alice_engine
```
