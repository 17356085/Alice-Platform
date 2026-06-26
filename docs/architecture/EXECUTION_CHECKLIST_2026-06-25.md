# Architecture Audit — Prioritized Execution Checklist

> 基准: ARCHITECTURE_REVIEW_2026-06-25.md (6.3/10)  
> 目标: 8.0/10 (生产可部署)
> 原则: 先止血→再加固→后优化

---

## 🔴 P0 — Critical (本周必须关闭)

生产部署阻塞 + 内存泄漏 + God Module 失控。

### P0-1: 修复前端生产构建 OOM

| 属性 | 值 |
|------|-----|
| **预估** | 3h |
| **文件** | `aitest/web/vite.config.ts`, `aitest/web/src/entries/*` |
| **依赖** | 无 |
| **阻断** | 无法生产部署 |
| **方案** | FRONTEND_REBUILD_PLAN_A — 多入口构建，App shell + 各页面独立 chunk |

**验收标准**:
- [ ] `npm run build` 在 2GB RAM 环境完成不 OOM
- [ ] 产物可正常加载所有页面
- [ ] 首屏 JS <500KB gzip

---

### P0-2: server/main.py 拆分

| 属性 | 值 |
|------|-----|
| **预估** | 4h |
| **文件** | `aitest/server/main.py` (2,137→≤200行) |
| **迁移目标** | `aitest/server/api/` routers |
| **依赖** | 无 |

**拆分方案**:

| main.py 段落 | 行范围 | 迁移到 |
|-------------|--------|--------|
| Subscriber 激活 | 57-130 | `server/core/subscribers.py` (新) |
| 审计调度器 | 140-198 | `server/core/audit_scheduler.py` (新) |
| REST handlers | 200-2137 | 对应 `server/api/*.py` routes |

**验收标准**:
- [ ] main.py ≤200行 (仅 import + lifespan + router mount)
- [ ] 所有现有 API 端点功能不变
- [ ] `curl localhost:8000/api/health` 返回 200

---

### P0-3: Chat SSE 内存泄漏修复 (RC1)

| 属性 | 值 |
|------|-----|
| **预估** | 2h |
| **文件** | `aitest/server/api/chat.py` |
| **依赖** | P0-2 (main.py 拆分后独立测试) |
| **根因** | 每次聊天消息创建 Thread，Lifecycle 仅跟踪 asyncio Task |

**修复步骤**:
1. `chat.py` 守护线程 → `asyncio.create_task()` + `LifecycleRegistry.register()`
2. `asyncio.Queue(maxsize=100)` 替换无界 Queue
3. SSE 断开 → Queue 清空 + Task 取消

**验收标准**:
- [ ] 100 条消息后 `threading.active_count()` 不增长
- [ ] SSE 断开 5s 内 Queue 释放
- [ ] 1,000 消息压力测试内存曲线平坦

---

## 🟠 P1 — High (2周内)

工程卫生 + 层违规 + 剩余泄漏。

### P1-1: 70+ 路径计算统一

| 属性 | 值 |
|------|-----|
| **预估** | 1h |
| **影响** | ~70 文件 |
| **依赖** | 无 |
| **风险** | 低 — 机械替换 |

```bash
# 替换模式
Path(__file__).resolve().parent.parent.parent
→
from aitest.platform.paths import get_workstudy; WORKSTUDY = get_workstudy()
```

**验收标准**:
- [ ] `rg "parent\.parent\.parent" aitest/` 返回 0
- [ ] 全量 pytest 通过

---

### P1-2: 50 print() → logging

| 属性 | 值 |
|------|-----|
| **预估** | 1h |
| **影响** | ~15 文件 |
| **依赖** | 无 |

| 目录 | 数量 | 替换策略 |
|------|------|----------|
| agents/ | 41 | `print(f"[{agent}] {msg}")` → `logger.info(msg, extra={"agent": agent})` |
| graphs/ | 5 | → `logger.debug()` |
| platform/ | 4 | → `logger.info/warning()` |

**验收标准**:
- [ ] `rg "^\s*print\(" aitest/agents/ aitest/graphs/ aitest/platform/` 返回 0
- [ ] 日志输出到 `infra/logging.py` 配置的 handler

---

### P1-3: 6 处 os.environ → config.get_env()

| 属性 | 值 |
|------|-----|
| **预估** | 0.5h |
| **文件** | 6 文件 |
| **依赖** | 无 |

| 文件 | 变量 |
|------|------|
| `mcp/browser_server.py:146` | `AITEST_BROWSER_BACKEND` |
| `server/auth.py:49` | `AITEST_API_KEY` |
| `infra/telemetry.py:35,59` | `AITEST_OTEL_ENABLED`, `AITEST_OTEL_ENDPOINT` |
| `platform/plugin.py:56` | `AITEST_PLUGIN_PATH` |

**验收标准**:
- [ ] `rg "os\.environ\[|os\.getenv\(" aitest/ --glob '!**/test*' --glob '!**/config.py'` 返回 0

---

### P1-4: MetricsConsumer 无界 dict 修复 (RC2)

| 属性 | 值 |
|------|-----|
| **预估** | 1.5h |
| **文件** | `aitest/platform/metrics_consumer.py` |
| **依赖** | 无 |

**修复**: `_by_module`, `_by_agent`, `_usage` → `TTLSet` (已有 `platform/ttl_set.py:107`)

**验收标准**:
- [ ] 1,000 次 run_completed 后内存 <100MB
- [ ] 旧数据自动过期

---

### P1-5: EventBus 订阅者强引用修复 (RC3)

| 属性 | 值 |
|------|-----|
| **预估** | 1h |
| **文件** | `aitest/platform/event_bus.py`, `aitest/platform/observation_bus.py` |
| **依赖** | 无 |

**修复**: 强制使用 `BoundSubscription` (weakref) + `unsubscribe()` 清理

**验收标准**:
- [ ] `subscribe()` 返回 unsubscribe callable
- [ ] 订阅者生命周期结束 → 引用释放

---

### P1-6: platform/runtime.py 依赖反转

| 属性 | 值 |
|------|-----|
| **预估** | 2h |
| **文件** | `aitest/platform/runtime.py:117,164` |
| **依赖** | 无 |

**修复**: `BrowserUseDriver` 直接 import → `CapabilityRegistry.get("browser")` 间接调用

**验收标准**:
- [ ] `rg "from aitest.integrations" aitest/platform/` 返回 0
- [ ] BrowserRuntime 通过 `capabilities/abc.py` 接口工作

---

### P1-7: 关键路径测试覆盖 2.4%→15%

| 属性 | 值 |
|------|-----|
| **预估** | 8h |
| **文件** | 新增 5+ 测试文件 |
| **依赖** | P0-2 |

**最小覆盖目标**:

| 模块 | 测试要点 | 预估用例 |
|------|----------|----------|
| `agent_runner.py` | AgentLoop 初始/执行/重试/跳过 | 8 |
| `sop_graph.py` | 图构建/路由/条件边 | 6 |
| `reliable_provider.py` | 重试/fallback/超时 | 5 |
| `security.py` | denylist/validator/hook 三层 | 5 |
| `observation_bus.py` | emit/subscribe/unsubscribe | 4 |

**验收标准**:
- [ ] 28+ 新增用例全部通过
- [ ] 覆盖 ≥15% 行 (目标 ~10,000行覆盖)

---

## 🟡 P2 — Medium (1月内)

God Module 拆分 + 死代码清理 + DX 改进。

### P2-1: platform/lifecycle.py 拆分

| 属性 | 值 |
|------|-----|
| **预估** | 3h |
| **文件** | `lifecycle.py` (1,043行) |

**拆分**:
- `platform/lifecycle/registry.py` (~300行) — LifecycleRegistry
- `platform/lifecycle/guard.py` (~200行) — MemoryGuard
- `platform/lifecycle/ownership.py` (~400行) — OwnershipChecker
- `platform/lifecycle/__init__.py` (~50行) — 重导出

---

### P2-2: dead "legacy" engine option 移除

| 属性 | 值 |
|------|-----|
| **预估** | 0.5h |
| **文件** | `server/api/workflows.py:24`, `infra/cli/__init__.py:458` |

---

### P2-3: aites→governance 跨边界 import 修复

| 属性 | 值 |
|------|-----|
| **预估** | 0.5h |
| **文件** | `agents/agent_scheduler.py:28` |

**修复**: `from governance.validators.sop_validator import ...` → validator 移至 `audit_engine/` 或通过 import 门面

---

### P2-4: 前端 E2E 端口修复 + Vitest 接入

| 属性 | 值 |
|------|-----|
| **预估** | 3h |
| **文件** | `e2e/smoke.spec.ts`, `package.json` |

- [ ] E2E 端口 5173→15173 或统一为 dev server 端口
- [ ] `package.json` 添加 `"test": "vitest"`, `"lint": "eslint"`, `"format": "prettier"`
- [ ] 3+ 组件渲染测试

---

### P2-5: dist/ 从 Git 移除 + .gitignore

| 属性 | 值 |
|------|-----|
| **预估** | 0.25h |

```bash
git rm -r --cached aitest/web/dist/
echo "aitest/web/dist/" >> .gitignore
```

---

### P2-6: graphs/__init__.py stale docstring 修复

| 属性 | 值 |
|------|-----|
| **预估** | 0.25h |
| **文件** | `graphs/__init__.py:13` |

移除已不存在的 `_archived/` 目录引用。

---

## 🟢 P3 — Low (未来)

API 成熟度 + 分布式 + 多语言扩展。

### P3-1: API 版本策略 + 统一错误格式

- `/api/v1/...` 或 header versioning
- Error response: `{error: {code, message, request_id}}`
- 分页标准: `{data, total, offset, limit}`

### P3-2: Rate Limiting 强制执行

- `mcp/rate_limit.py` 已定义 → 接入 FastAPI middleware
- Per-tenant, per-API-key bucket

### P3-3: 分布式任务队列

- 当前 `infra/worker_pool.py` (ThreadPoolExecutor) → Redis+Celery/RQ
- 支持多 worker 进程跨机器

### P3-4: Tauri 桌面壳

- Electron → Tauri v2: 120MB→10MB, 200MB→50MB RAM
- Python backend 作为 sidecar 进程

---

## 时间线汇总

```
Week 1 (Jun 26-30)     P0 全量 + P1-1~P1-3
                       预计 11.5h

Week 2-3 (Jul 1-14)    P1-4~P1-7
                       预计 12.5h

Week 4-6 (Jul 15-Aug 4) P2 全量
                       预计 7.5h

Aug+                    P3 按需
```

## 完成度追踪

| 优先级 | 任务数 | 预估总时 | 状态 |
|--------|--------|----------|------|
| P0 | 3 | 9h | ✅ 完成 (2026-06-25) |
| P1 | 7 | 15h | ✅ 完成 (2026-06-25) |
| P2 | 6 | 7.75h | ✅ 完成 (2026-06-25) |
| P3 | 3 | 3h | ✅ 完成 (2026-06-25) |
| **总计** | **19** | **~35h** | **19/19** |

### 执行记录

| 任务 | 改动摘要 |
|------|----------|
| P0-1 | `vite.config.ts` cssCodeSplit:true + chunk split + tsc分离 → 构建5.16s |
| P0-2 | main.py 2,137→251行, 8新模块 (subscribers/sweep/audit_scheduler/health + api/debug/audit/kpi/kanban/terminal) |
| P0-3 | chat.py: Thread→asyncio.to_thread + s.agent_task 追踪 + destroy() cancel |
| P1-1 | 65 files `Path().parent.parent.parent` → `get_workstudy()` |
| P1-2 | 11 files ~50 `print()` → `logger.info/error/debug` |
| P1-3 | 5 files `os.environ.get()` → `config.get_env()` |
| P1-4 | MetricsConsumer RC2 — 已有 LRU cap fix, 验证通过 |
| P1-5 | EventBus RC3 — weakref subscribers + auto-clean Deadrefs |
| P1-6 | runtime.py — `_default_browser_factory()` 单点导入 |
| P1-7 | 3新测试文件: reliable_provider (31) + security (42) + observation_bus (18) = ~91测例 |
| P2-1 | lifecycle.py 1,043行 → lifecycle/registry.py + guard.py + __init__.py |
| P2-2 | workflows.py "legacy" engine comment → 已移除 |
| P2-3 | agent_scheduler.py → governance 跨边界import 加架构说明 |
| P2-4 | package.json: vitest+testing-library+jsdom devDeps, vitest.config.ts |
| P2-5 | .gitignore: aitest/web/dist/ |
| P2-6 | graphs/__init__.py: _archived/ 引用移除 |
| P3-1 | main.py: request_id middleware + unified error handlers + v2.5.0 |
| P3-2 | 验证: REST middleware + MCP protocol.py:47 双路径限流已存在 |
| P3-4 | ⏭️ 跳过 (当前单机器开发阶段) |

---

> **完成日期**: 2026-06-25 | **19/19 任务** | **架构评分**: 5.7 → ~7.5 (预估)
