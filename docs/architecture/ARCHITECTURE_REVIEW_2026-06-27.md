# Architecture Review Report — AITest Platform v2.5

> **评审类型:** Delta Re-Audit (2-day gap)
> **评审日期:** 2026-06-27
> **上次评审:** 2026-06-25 (6.3/10)
> **评审范围:** aitest/ 240 .py files (~60,800 lines) + web/ 53 files (~6,900 lines)

---

## 1. Delta since 2026-06-25

| 维度 | 06-25 | 06-27 | Δ |
|------|-------|-------|---|
| `server/main.py` | 2,137 lines | **333 lines** | -1,804 (-84%) ✅ |
| 提取模块 | 0 | 8 (health/sweep/audit_scheduler/subscribers + 4 API routes) | ✅ |
| 测试文件 | 11 | 14 | +3 |
| `print()` 调用 | 50 | 0 (已替换 logging) | ✅ |
| 路径重复 `get_workstudy()` | 70+ | 0 (config.get_env) | ✅ |
| Redis 组件 | 0 | 5 (cache/session/lock/ratelimit/pubsub) | 新增 |
| 任务队列后端 | SQLite only | SQLite + Redis/RQ (auto-detect) | 新增 |
| 前端框架 | React 18 | React 18 + shadcn/ui 18 components | 渐进迁移 |
| Tauri 桌面壳 | — | scaffolded (未构建) | 新增 |
| 架构冻结违规 | 0 | 0 | ✅ |

---

## 2. 评分总览 (1-10)

| 维度 | 06-25 | 06-27 | 说明 |
|------|-------|-------|------|
| Modularity | 7 | **8** | main.py God Module 已拆。platform/ 膨胀需关注 |
| Maintainability | 5 | **7** | print() 清零。路径计算统一。43 文件仍 >400 行 |
| Scalability | 6 | **7** | Redis 队列/缓存/锁/限流。多 worker 就绪 |
| Testability | 5 | **5** | 14 测试文件 (2,077 行)。覆盖率 ~3.4%，仍不足 |
| Extensibility | 8 | **8** | 稳定。RunEvent 消费者模式工作良好 |
| Governance | 8 | **8** | 架构冻结零违规。审计引擎全链路覆盖 |
| Platformization | 7 | **7** | ZJSN 解耦完成。.tlo/ 隔离完整 |
| Observability | 6 | **7** | event_bus + timeline + metrics + Redis pubsub |
| Production Readiness | 5 | **6** | 限流/锁/重试/超时就位。缺集成测试 |
| **综合** | **6.3** | **7.0** | +0.7 — 工程卫生大幅改善，基础设施硬化 |

---

## 3. 核心判断

### 3.1 已完成 (P0-P4 执行清单)

main.py God Module 拆分 (P0-2) 是最大单次改进。从 2,137 行拆到 333 行，提取 8 个子模块。lifespan handler (70 行) 仍是瓶颈但不再阻塞开发。

Redis 生态 (P2-P5) 引入 5 个基础设施组件，全部有 graceful fallback。RQ 队列在 Windows 上通过 SimpleWorker 可用。

### 3.2 五个结构问题

#### 问题 1: event_bus 泛滥 — 30+ 文件延迟导入

`audit_engine/event_bus.py` 被 30+ 个文件通过函数内 `from aitest.audit_engine.event_bus import emit` 引用。这是反模式：

```
sop_graph.py:483:    from aitest.audit_engine.event_bus import emit
sop_graph.py:496:    from aitest.audit_engine.event_bus import emit as _emit2
sop_graph.py:518:    from aitest.audit_engine.event_bus import emit as _emit3
review_graph.py:342: from aitest.audit_engine.event_bus import emit
cost_auditor.py:116: from aitest.audit_engine.event_bus import emit
security.py:326:     from aitest.audit_engine.event_bus import emit
state_auditor.py:239: from aitest.audit_engine.event_bus import emit
...
```

根源: `event_bus.py:511` 反向引用 `from aitest.graphs.review_graph import run_review`，造成循环依赖。所有消费者被迫用延迟导入规避。

**修复路径**: 将 `review_graph` 引用从 event_bus 中提取为注册回调 (`bus.on("review", run_review)`)，消除循环，所有调用方可直接顶层导入。

#### 问题 2: platform/ 膨胀 — 50 文件, 9,759 行

最大的模块，包含: capabilities, complexity, lifecycle, capability_router, 运行时组件 (execution_service, run, event_bus, consumer) + 业务 hooks (billing, quota, webhook, metrics) + 存储 (run_store, testing_memory, artifact_lineage) + 组织模型 (organization, workspace, tenant, ownership)。

混合了 3 种不同的关注点：能力路由、执行编排、业务策略。应该考虑拆分子包边界。

#### 问题 3: 43 文件超过 400 行

| 行数 | 文件 | 拆分建议 |
|------|------|---------|
| 1,598 | `infra/cli/__init__.py` | 按子命令拆分 (server/graph/project/...) |
| 1,449 | `graphs/sop_graph.py` | 按 phase 拆 node 函数 |
| 1,213 | `audit_engine/state_auditor.py` | 按检查维度拆分 |
| 1,190 | `agents/agent_runner.py` | Plan/Act/Observe 阶段分离 |
| 1,021 | `llm/provider.py` | 按 provider 拆分 (Claude/DeepSeek/OpenAI) |
| 784 | `knowledge/rag_engine.py` | 索引/查询/维护 分离 |

#### 问题 4: 测试覆盖率不足

14 测试文件 (2,077 行) vs 60,800 行生产代码 → ~3.4% 行覆盖率估算。架构冻结测试 (31 tests) 提供关键路径保护，但 agent runner、SOP graph、audit engine、task queue 缺少集成测试。

#### 问题 5: 5 个循环导入对

```
audit_engine.event_bus ⇄ graphs.review_graph     ← 跨层循环 (最严重)
graphs.checkpoint ⇄ graphs.sop_graph              ← 模块内循环
mcp.mcp_client ⇄ mcp.registry                     ← 模块内循环
platform.context ⇄ platform.paths                  ← 模块内循环
platform.memory_observer ⇄ platform.observation_bus ← 模块内循环
```

---

## 4. 前端评估

结构健康: 16 视图 / 12 组件 / 18 UI 基元 / 6 stores / 5 hooks / 2 API。shadcn/ui 渐进替换手写组件。Zustand 状态管理清晰。

问题:
- `stores/chat.ts` (326 行) — 最大 store，混了消息/会话/WS 状态
- `views/DashboardView.tsx` (270 行) — 可拆子组件
- vite.config.ts 稳定 (OOM 修复, vendor chunking, CSS code split)

---

## 5. 基础设施层评估

| 组件 | 后端 | 状态 | 备注 |
|------|------|------|------|
| Task Queue | Redis/SQLite auto-detect | ✅ | 重试/超时/恢复/健康 |
| LLM Cache | Redis + memory fallback | ✅ | 1h TTL, cross-worker |
| Session Store | Redis + SQLite fallback | ✅ | 7-day TTL, ZSet 索引 |
| Distributed Lock | Redis SETNX + Lua | ✅ | 互斥验证通过 |
| Rate Limiting | Redis Lua sliding window | ✅ | 61st req 429 拦截 |
| Pub/Sub | Redis channels | ✅ | 4 事件类型 |
| Vector Search | Redis Stack (skipped) | — | ChromaDB 主力 |

---

## 6. 架构冻结合规

v2.0-v2.4 冻结层零违规。RunEvent 字段无变化。EventBus API 稳定。消费者无序、幂等。

---

## 7. 下一步建议 (优先级)

### P0 — 消除 event_bus 循环依赖
- 从 event_bus 中提取 `review_graph` 回调为注册模式
- 代价: ~20 行改动。收益: 30+ 文件可顶层导入

### P1 — 拆分超大文件
- `infra/cli/__init__.py` (1,598 行) — 按子命令拆分
- `graphs/sop_graph.py` (1,449 行) — 按 phase 拆分
- `audit_engine/state_auditor.py` (1,213 行) — 按维度拆分

### P2 — 测试覆盖率
- `agent_runner.py` 集成测试 (mock LLM)
- `sop_graph.py` 关键路径测试
- `task_queue.py` 端到端测试 (重试/超时/恢复)

### P3 — platform/ 边界整理
- 拆分业务 hooks (billing/quota/webhook) 从运行时组件
- 能力路由独立子包

### P4 — 前端
- Tauri 构建 (`rustup` + `cargo tauri build`)
- chat store 拆分 (messages/sessions/ws)
- pnpm install + vitest 运行

---

## 8. 评分走势

```
v0.5   ████████░░░░░░░░░░  4.2  (2026-06-20, 初始评审)
v1.0   ██████████░░░░░░░░  5.0  (2026-06-23, platform/ 引入)
v2.0   ███████████░░░░░░░  5.7  (2026-06-23, 架构冻结)
v2.5   ████████████░░░░░░  6.3  (2026-06-25, P0-P3 修复)
v2.5+  ██████████████░░░░  7.0  (2026-06-27, Redis 生态 + 工程卫生)
----   ──────────────────  ----
v3.0   ██████████████████  8.5+ (目标: 循环消除 + 测试 + 拆分)
```
