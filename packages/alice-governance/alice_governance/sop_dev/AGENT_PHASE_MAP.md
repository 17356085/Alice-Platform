# AGENT_PHASE_MAP — Agent ↔ Phase 映射表

> 来源: `aitest/graphs_dev/state_dev.py` → `DEV_AGENT_PHASE_MAP` + `DEV_PHASE_TO_NODE`
> Agent 信息: `governance/agents/agent-definitions-dev.yaml`

## Agent → Phase 映射

| Agent ID | Agent 名称 | 负责 Phase | Node 名称 | Skills 数 |
|----------|-----------|-----------|-----------|----------|
| pm-agent | 项目管理 Agent | Plan | pm_agent | 4 |
| req-agent | 需求分析 Agent | Requirements | req_agent | 5 |
| arch-agent | 架构 Agent | Architecture | arch_agent | 4 |
| design-agent | 组件设计 Agent | Component Design | design_agent | 4 |
| frontend-agent | 前端开发 Agent | Frontend Impl | frontend_agent | 5 |
| backend-agent | 后端开发 Agent | Backend Impl | backend_agent | 6 |
| review-agent | 代码审查 Agent | Code Review | review_agent | 5 |
| dev-test-agent | 测试 Agent | Dev Test | dev_test_agent | 3 |
| debug-agent | 调试 Agent | Debug & Fix | debug_agent | 5 |
| build-agent | 构建 Agent | Build | build_agent | 4 |

## Phase → Agent 映射

| Phase 编号 | Phase 名称 | 执行 Agent | 输入来源 | 输出产物 |
|-----------|-----------|-----------|---------|---------|
| 1 | Plan | pm-agent | 用户输入 + 项目上下文 | PROJECT_PLAN.md, PROGRESS_REPORT.md, RISK_ANALYSIS.md |
| 2 | Requirements | req-agent | Phase 1 输出 | FEATURE_SPEC.md, USER_STORIES.md, ACCEPTANCE_CRITERIA.md, DATA_MODEL.md |
| 3 | Architecture | arch-agent | Phase 2 输出 | PROJECT_STRUCTURE.md, TECH_STACK.md, COMPONENT_TREE.md, API_CONTRACTS.md |
| 4 | Component Design | design-agent | Phase 3 输出 | COMPONENT_SPEC.md, PROPS_INTERFACE.yaml, DATA_FLOW.md |
| 5 | Frontend Impl | frontend-agent | Phase 4 输出 | `src/components/*.vue`, `src/pages/*.vue`, `src/stores/*.ts` |
| 6 | Backend Impl | backend-agent | Phase 3-4 输出 + API_CONTRACTS.md | `routers/*.py`, `schemas/*.py`, `models/*.py` |
| 7 | Code Review | review-agent | Phase 5-6 输出 | CODE_REVIEW.md, PERFORMANCE_REPORT.md, SECURITY_REPORT.md, CONSISTENCY_REPORT.md |
| 8 | Dev Test | dev-test-agent | Phase 5-7 输出 | `tests/test_*.py`, COVERAGE_REPORT.md |
| 9 | Debug & Fix | debug-agent | Phase 7 输出（条件触发） | ERROR_DIAGNOSIS.md, STACK_ANALYSIS.md, FIX_PROPOSAL.md, REGRESSION_REPORT.md |
| 10 | Build | build-agent | Phase 5-9 输出 | BUILD_REPORT.md, TEST_RESULTS.md |

## Agent 职责简述

### pm-agent — 项目管理 Agent

**职责**: 任务分解、里程碑规划、进度跟踪、风险分析。作为 Dev SOP 的入口 Phase，输出项目整体蓝图。

**类别**: plan  
**边界**: 不编写代码、不修改代码、不部署

### req-agent — 需求分析 Agent

**职责**: 功能规格、用户故事、验收标准、数据模型。将需求转化为可执行的开发规格。

**类别**: requirements-dev  
**边界**: 不设计 UI、不编写代码、不部署

### arch-agent — 架构 Agent

**职责**: 项目扫描、技术栈分析、组件树设计、API 契约定义。确定技术方案和系统骨架。

**类别**: architecture  
**边界**: 不编写业务代码、不生成 UI 组件、不部署

### design-agent — 组件设计 Agent

**职责**: 组件结构分析、Props 接口、数据流、页面布局。细化架构到组件级别。

**类别**: component-design  
**边界**: 不编写业务代码、不生成 API

### frontend-agent — 前端开发 Agent

**职责**: Vue 3 组件/页面实现、Pinia store、路由、Lint 检查。将设计转化为可运行的前端代码。

**类别**: frontend  
**核心规则**: Composition API (`<script setup lang="ts">`) 优先、TypeScript 严格模式（`any` 禁止）、生成后自检 (ESLint + `tsc --noEmit`)  
**边界**: 不生成后端 API、不设计数据库

### backend-agent — 后端开发 Agent

**职责**: FastAPI router/schema/model/CRUD/test 生成。将 API 契约转化为可运行的后端代码。

**类别**: backend  
**核心规则**: SQLAlchemy 2.0 `mapped_column()`、Pydantic v2 `ConfigDict`、`async def` 所有端点  
**边界**: 不生成前端代码、不部署

### review-agent — 代码审查 Agent

**职责**: 代码审查、性能分析、安全扫描、前后端一致性检查。质量保障的第一道关口。

**类别**: code-review  
**关键作用**: 此 Agent 的审查结果决定 Debug & Fix Phase 是否触发  
**边界**: 不修改代码（只报告）、不执行构建

### dev-test-agent — 测试 Agent

**职责**: 单元测试生成、集成测试生成、覆盖率检查。验证代码正确性。

**类别**: test-dev  
**边界**: 不修改源文件、不部署

### debug-agent — 调试 Agent

**职责**: 错误定位、堆栈分析、修复建议、回归验证。质量保障的闭环修复环节。

**类别**: debug  
**模式**: `diagnose`（仅诊断）、`fix`（完整诊断→修复→验证，≤3 轮）  
**边界**: 不直接修改文件（只建议修复）、修复需人工确认、最多 3 轮修复

### build-agent — 构建 Agent

**职责**: 类型检查、Lint 执行、测试运行、打包构建。交付前的最后验证。

**类别**: build  
**边界**: 不修改源代码、不部署到生产

## 编排器: dev-full-sop

`dev-full-sop` 是开发流水线的编排器定义，非独立 Agent。它在 `agent-definitions-dev.yaml` 中定义了完整的 10 Phase 流水线：

```
Plan → Requirements → Architecture → Component Design
  → Frontend Impl → Backend Impl → Code Review
  → Dev Test → Debug & Fix → Build
```

编排器负责：
- Phase 顺序调度
- 条件路由（`review_has_issues` → Debug & Fix）
- 模式跳过逻辑（`DEV_MODE_SKIP_MAP`）
- 并行控制（Frontend Impl `per_component`、Backend Impl `per_api_group`）

## Agent 分层

| 层级 | Agent | Phase 覆盖 |
|------|-------|-----------|
| **流程管控层** | pm-agent, req-agent | Plan, Requirements |
| **代码生成层** | arch-agent, design-agent, frontend-agent, backend-agent | Architecture, Component Design, Frontend Impl, Backend Impl |
| **质量保障层** | review-agent, dev-test-agent, debug-agent | Code Review, Dev Test, Debug & Fix |
| **交付层** | build-agent | Build |

## 相关文档

- Phase 定义: [CANONICAL_PHASES.md](CANONICAL_PHASES.md)
- Agent 定义源文件: `governance/agents/agent-definitions-dev.yaml`
- Skill 注册: `governance/skills-dev/skill-registry-dev.yaml`
