# CANONICAL_PHASES — 开发 SOP Phase 定义

> 来源: `aitest/graphs_dev/state_dev.py` → `DEV_CANONICAL_PHASES`
> 互补: `AGENT_PHASE_MAP.md`（Agent 映射）, `MODE_SKIP_MAP.md`（跳过规则）

## Phase 完整列表

| # | Phase 名称 | 执行 Agent | Node 名称 | 输出产物 |
|---|-----------|-----------|-----------|---------|
| 1 | Plan | pm-agent | pm_agent | PROJECT_PLAN.md, PROGRESS_REPORT.md, RISK_ANALYSIS.md |
| 2 | Requirements | req-agent | req_agent | FEATURE_SPEC.md, USER_STORIES.md, ACCEPTANCE_CRITERIA.md, DATA_MODEL.md |
| 3 | Architecture | arch-agent | arch_agent | PROJECT_STRUCTURE.md, TECH_STACK.md, COMPONENT_TREE.md, API_CONTRACTS.md |
| 4 | Component Design | design-agent | design_agent | COMPONENT_SPEC.md, PROPS_INTERFACE.yaml, DATA_FLOW.md |
| 5 | Frontend Impl | frontend-agent | frontend_agent | `src/components/*.vue`, `src/pages/*.vue`, `src/stores/*.ts` |
| 6 | Backend Impl | backend-agent | backend_agent | `routers/*.py`, `schemas/*.py`, `models/*.py` |
| 7 | Code Review | review-agent | review_agent | CODE_REVIEW.md, PERFORMANCE_REPORT.md, SECURITY_REPORT.md, CONSISTENCY_REPORT.md |
| 8 | Dev Test | dev-test-agent | dev_test_agent | `tests/test_*.py`, COVERAGE_REPORT.md |
| 9 | Debug & Fix | debug-agent | debug_agent | ERROR_DIAGNOSIS.md, STACK_ANALYSIS.md, FIX_PROPOSAL.md, REGRESSION_REPORT.md |
| 10 | Build | build-agent | build_agent | BUILD_REPORT.md, TEST_RESULTS.md |

## Phase 详解

### Phase 1: Plan（项目管理）

- **编号**: 1 / 10
- **Agent**: pm-agent（项目管理 Agent）
- **输入条件**: 项目目标 + 范围描述 [待补充：需从用户输入或项目上下文中获取]
- **输出产物**:
  - `PROJECT_PLAN.md` — 任务分解 + 里程碑规划
  - `PROGRESS_REPORT.md` — 进度跟踪
  - `RISK_ANALYSIS.md` — 风险评估矩阵
- **Skills**:
  - `plan/create-project-plan` — 任务分解、里程碑规划、依赖关系图
  - `plan/progress-tracker` — 对比计划 vs 实际产物
  - `plan/risk-analyzer` — 风险矩阵分析
  - `plan/sprint-planner` — Sprint 规划、任务优先级、工时估算

### Phase 2: Requirements（需求分析）

- **编号**: 2 / 10
- **Agent**: req-agent（需求分析 Agent）
- **输入条件**: Phase 1 Plan 完成（PROJECT_PLAN.md 已生成）
- **输出产物**:
  - `FEATURE_SPEC.md` — 结构化功能规格
  - `USER_STORIES.md` — As a/I want/So that 格式
  - `ACCEPTANCE_CRITERIA.md` — Given/When/Then 验收标准
  - `DATA_MODEL.md` — ERD 图 + 实体字段定义
- **Skills**:
  - `requirements-dev/feature-spec` — 结构化功能规格，优先级分类
  - `requirements-dev/user-story-writer` — 用户故事
  - `requirements-dev/acceptance-criteria` — 验收标准（含边界和异常）
  - `requirements-dev/data-model-spec` — 数据模型规格
  - `automation/prompt-engineering-expert` — Prompt 自优化

### Phase 3: Architecture（架构设计）

- **编号**: 3 / 10
- **Agent**: arch-agent（架构 Agent）
- **输入条件**: Phase 2 Requirements 完成（FEATURE_SPEC.md 已生成）
- **输出产物**:
  - `PROJECT_STRUCTURE.md` — 项目目录结构扫描
  - `TECH_STACK.md` — 技术栈选型
  - `COMPONENT_TREE.md` — 组件树设计
  - `API_CONTRACTS.md` — API 契约定义
- **Skills**:
  - `architecture/project-scanner` — 项目扫描
  - `architecture/tech-stack-decider` — 技术栈选型
  - `architecture/component-tree-designer` — 组件树设计
  - `architecture/api-contract-designer` — API 契约设计

### Phase 4: Component Design（组件设计）

- **编号**: 4 / 10
- **Agent**: design-agent（组件设计 Agent）
- **输入条件**: Phase 3 Architecture 完成（COMPONENT_TREE.md 已生成）
- **输出产物**:
  - `COMPONENT_SPEC.md` — 组件规格说明
  - `PROPS_INTERFACE.yaml` — Props 接口定义
  - `DATA_FLOW.md` — 数据流设计
- **Skills**:
  - `component-design/component-spec` — 组件结构分析
  - `component-design/props-interface` — Props 接口定义
  - `component-design/data-flow` — 数据流设计
  - `component-design/layout-mockup` — 页面布局 mockup

### Phase 5: Frontend Impl（前端实现）

- **编号**: 5 / 10
- **Agent**: frontend-agent（前端开发 Agent）
- **输入条件**: Phase 4 Component Design 完成（COMPONENT_SPEC.md 已生成）
- **输出产物**:
  - `src/components/*.vue` — Vue 3 组件
  - `src/pages/*.vue` — 页面组件
  - `src/stores/*.ts` — Pinia 状态管理
- **Skills**:
  - `frontend/vue-component-generator` — Vue 3 组件生成
  - `frontend/page-implementer` — 页面实现
  - `frontend/vuex-pinia-store` — Pinia Store 生成
  - `frontend/router-config` — 路由配置
  - `frontend/frontend-lint-checker` — Lint 检查
- **特殊规则**: `per_component: true` — 按组件并行执行

### Phase 6: Backend Impl（后端实现）

- **编号**: 6 / 10
- **Agent**: backend-agent（后端开发 Agent）
- **输入条件**: Phase 4 Component Design 完成 + API_CONTRACTS.md 可用
- **输出产物**:
  - `routers/*.py` — FastAPI 路由
  - `schemas/*.py` — Pydantic Schema
  - `models/*.py` — SQLAlchemy 模型
- **Skills**:
  - `backend/fastapi-router-generator` — FastAPI 路由生成
  - `backend/pydantic-schema-generator` — Pydantic Schema 生成
  - `backend/sqlalchemy-model-generator` — SQLAlchemy 模型生成
  - `backend/crud-generator` — CRUD 生成
  - `backend/unit-test-generator` — 后端单元测试
  - `backend/backend-consistency-checker` — 一致性检查
- **特殊规则**: `per_api_group: true` — 按 API 组并行执行

### Phase 7: Code Review（代码评审）

- **编号**: 7 / 10
- **Agent**: review-agent（代码审查 Agent）
- **输入条件**: Phase 5 Frontend Impl + Phase 6 Backend Impl 均完成
- **输出产物**:
  - `CODE_REVIEW.md` — 代码审查报告
  - `PERFORMANCE_REPORT.md` — 性能分析报告
  - `SECURITY_REPORT.md` — 安全扫描报告
  - `CONSISTENCY_REPORT.md` — 前后端一致性报告
- **Skills**:
  - `code-review/source-code-reviewer` — 源代码审查
  - `code-review/performance-analyzer` — 性能分析
  - `code-review/security-scanner` — 安全扫描
  - `code-review/consistency-enforcer` — 一致性检查
  - `automation/prompt-engineering-expert` — Prompt 自优化
- **关键作用**: 此 Phase 的结果决定 Phase 9 Debug & Fix 是否触发

### Phase 8: Dev Test（开发测试）

- **编号**: 8 / 10
- **Agent**: dev-test-agent（测试 Agent）
- **输入条件**: Phase 7 Code Review 完成（代码已审查）
- **输出产物**:
  - `tests/test_*.py` — 单元测试
  - `tests/integration/test_*.py` — 集成测试
  - `COVERAGE_REPORT.md` — 覆盖率报告
- **Skills**:
  - `test-dev/unit-test-generator` — 单元测试生成
  - `test-dev/integration-test-generator` — 集成测试生成
  - `test-dev/coverage-checker` — 覆盖率检查

### Phase 9: Debug & Fix（调试修复）⚠️ 条件触发

- **编号**: 9 / 10
- **Agent**: debug-agent（调试 Agent）
- **输入条件**: **Phase 7 Code Review 发现 issues**（`review_has_issues == true`）
- **条件逻辑**: 若 Code Review 未发现问题，自动跳过此 Phase，进入 Phase 10 Build
- **最大轮次**: 3 轮
- **输出产物**:
  - `ERROR_DIAGNOSIS.md` — 错误诊断
  - `STACK_ANALYSIS.md` — 堆栈分析
  - `FIX_PROPOSAL.md` — 修复建议
  - `REGRESSION_REPORT.md` — 回归验证
- **Skills**:
  - `debug/error-locator` — 错误定位
  - `debug/stack-trace-analyzer` — 堆栈分析
  - `debug/fix-suggester` — 修复建议
  - `debug/regression-verifier` — 回归验证
  - `automation/prompt-engineering-expert` — Prompt 自优化
- **模式**: `diagnose`（仅诊断）、`fix`（完整诊断→修复→验证，≤3轮）

### Phase 10: Build（构建部署）

- **编号**: 10 / 10
- **Agent**: build-agent（构建 Agent）
- **输入条件**: Phase 8 Dev Test 完成 + Phase 9 Debug & Fix 完成/跳过
- **输出产物**:
  - `BUILD_REPORT.md` — 构建报告
  - `TEST_RESULTS.md` — 测试结果汇总
- **Skills**:
  - `build/type-checker` — 类型检查
  - `build/lint-executor` — Lint 执行
  - `build/test-runner` — 测试执行
  - `build/package-bundler` — 打包构建

## Phase 间依赖关系

### 顺序依赖

```
Phase 1 (Plan)
    ↓
Phase 2 (Requirements)
    ↓
Phase 3 (Architecture)
    ↓
Phase 4 (Component Design)
    ↓
Phase 5 (Frontend Impl) ──┐
                          ├──→ Phase 7 (Code Review)
Phase 6 (Backend Impl) ──┘         ↓
                              Phase 8 (Dev Test)
                                    ↓
                              Phase 9 (Debug & Fix) ← 条件触发
                              （仅当 Code Review 发现 issues）
                                    ↓
                              Phase 10 (Build)
```

### 条件依赖

| 条件 | 触发逻辑 | 涉及 Phase |
|------|---------|-----------|
| `review_has_issues == true` | 进入 Debug & Fix | Phase 9 |
| `review_has_issues == false` | 跳过 Debug & Fix，直接 Build | Phase 9 |
| `mode == "status"` | entry 后直接 exit | 全部 |

### 并行执行说明

- Phase 5 (Frontend Impl) 和 Phase 6 (Backend Impl) 在设计上可并行（均依赖 Phase 4），但在当前顺序流水线中按 Phase 5 → Phase 6 顺序执行
- Phase 5 内部支持 `per_component` 并行（按组件拆分）
- Phase 6 内部支持 `per_api_group` 并行（按 API 组拆分）

> 注意：源文件 `state_dev.py` 中的 `DEV_AGENT_PHASE_MAP` 和 `DEV_CANONICAL_PHASES` 定义了 1:1 的 Agent↔Phase 映射。Phase 间输入/输出数据流由 `agent_outputs` dict 承载，具体字段 [待补充：需定义每个 Phase 的输入/输出 Schema]。

## 相关文档

- Agent→Phase 映射: [AGENT_PHASE_MAP.md](AGENT_PHASE_MAP.md)
- 模式跳过规则: [MODE_SKIP_MAP.md](MODE_SKIP_MAP.md)
- Phase 详细文档: [phases/](phases/)
