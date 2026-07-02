# Phase 索引

> Dev SOP 10 Phase 快速导航。

## 按阶段分组

### 规划阶段（Phase 1-2）

| # | Phase | Agent | 一句话描述 | 文档 |
|---|-------|-------|-----------|------|
| 1 | Plan | pm-agent | 项目规划：任务分解、里程碑、风险评估 | [01-plan.md](01-plan.md) |
| 2 | Requirements | req-agent | 需求分析：功能规格、用户故事、验收标准 | [02-requirements.md](02-requirements.md) |

### 设计阶段（Phase 3-4）

| # | Phase | Agent | 一句话描述 | 文档 |
|---|-------|-------|-----------|------|
| 3 | Architecture | arch-agent | 架构设计：技术栈、组件树、API 契约 | [03-architecture.md](03-architecture.md) |
| 4 | Component Design | design-agent | 组件设计：Props 接口、数据流、布局 | [04-component-design.md](04-component-design.md) |

### 实现阶段（Phase 5-6）

| # | Phase | Agent | 一句话描述 | 文档 |
|---|-------|-------|-----------|------|
| 5 | Frontend Impl | frontend-agent | 前端实现：Vue 3 组件、Pinia store、路由 | [05-frontend-impl.md](05-frontend-impl.md) |
| 6 | Backend Impl | backend-agent | 后端实现：FastAPI 路由、Schema、模型 | [06-backend-impl.md](06-backend-impl.md) |

### 验证阶段（Phase 7-8）

| # | Phase | Agent | 一句话描述 | 文档 |
|---|-------|-------|-----------|------|
| 7 | Code Review | review-agent | 代码审查：质量、性能、安全、一致性 | [07-code-review.md](07-code-review.md) |
| 8 | Dev Test | dev-test-agent | 开发测试：单元测试、集成测试、覆盖率 | [08-dev-test.md](08-dev-test.md) |

### 修复阶段（Phase 9）

| # | Phase | Agent | 一句话描述 | 文档 |
|---|-------|-------|-----------|------|
| 9 | Debug & Fix | debug-agent | 调试修复：错误定位、修复建议、回归验证 ⚠️ 条件触发 | [09-debug-fix.md](09-debug-fix.md) |

### 交付阶段（Phase 10）

| # | Phase | Agent | 一句话描述 | 文档 |
|---|-------|-------|-----------|------|
| 10 | Build | build-agent | 构建部署：类型检查、Lint、测试运行、打包 | [10-build.md](10-build.md) |

## Phase 流水线

```
  规划          设计              实现              验证          修复      交付
┌──────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────┐    ┌─────┐
│ Plan │───→│ Req      │───→│ Arch     │───→│ Design   │    │      │    │     │
│  (1) │    │  (2)     │    │  (3)     │    │  (4)     │    │      │    │     │
└──────┘    └──────────┘    └──────────┘    └──────────┘    │      │    │     │
                                               ↓            │      │    │     │
                                        ┌────────────┐      │      │    │     │
                                     ┌──│ Frontend(5)│──┐   │      │    │     │
                                     │  └────────────┘  │   │      │    │     │
                                     │  ┌────────────┐  │   │      │    │     │
                                     └──│ Backend (6)│──┘   │      │    │     │
                                        └────────────┘      │      │    │     │
                                               ↓            ↓      │    │     │
                                        ┌──────────┐    ┌────────┐ │    │     │
                                        │ Review(7)│───→│Test (8)│─┤    │     │
                                        └──────────┘    └────────┘ │    │     │
                                               │              ↓    │    │     │
                                               │  issues?  ┌──────────┐ │     │
                                               └──────────→│Debug (9) │ │     │
                                               无 issues   └──────────┘ │     │
                                                    ↓              ↓    ↓     ↓
                                               ┌──────────────────────────────┐
                                               │         Build (10)           │
                                               └──────────────────────────────┘
```

> Phase 9 (Debug & Fix) 为条件触发：仅当 Phase 7 (Code Review) 发现 issues 时进入。

## 相关文档

- Phase 完整定义: [../CANONICAL_PHASES.md](../CANONICAL_PHASES.md)
- Agent 映射: [../AGENT_PHASE_MAP.md](../AGENT_PHASE_MAP.md)
- 模式跳过: [../MODE_SKIP_MAP.md](../MODE_SKIP_MAP.md)
