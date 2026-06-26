# Phase 5: Frontend Impl（前端实现）

## 概述

- **编号**: 5 / 10
- **目标**: 基于组件设计，生成 Vue 3 前端代码——组件、页面、状态管理和路由配置
- **执行 Agent**: `frontend-agent`（前端开发 Agent）
- **阶段分组**: 实现阶段

## 输入条件

- Phase 4 Component Design 完成：COMPONENT_SPEC.md + PROPS_INTERFACE.yaml + DATA_FLOW.md 已生成
- [待补充：需定义 frontend-agent 从 design-agent 的 `agent_outputs` 中读取哪些字段]

## 执行步骤

由 Agent Loop 驱动，`frontend-agent` 按以下 Skill 链执行：

1. `frontend/vue-component-generator` — 基于 COMPONENT_SPEC.md 生成 Vue 3 组件
2. `frontend/vuex-pinia-store` — 基于 DATA_FLOW.md 生成 Pinia Store
3. `frontend/router-config` — 配置路由
4. `frontend/page-implementer` — 组装页面
5. `frontend/frontend-lint-checker` — Lint 检查（ESLint + tsc --noEmit）

> **特殊规则**: `per_component: true` — 每个组件可按组件拆分独立执行。

## 涉及 Skills

| Skill ID | 文件路径 | 描述 | 依赖 |
|----------|---------|------|------|
| `frontend/vue-component-generator` | `governance/skills-dev/frontend/vue-component-generator.md` | Vue 3 组件生成 | — |
| `frontend/page-implementer` | `governance/skills-dev/frontend/page-implementer.md` | 页面实现 | — |
| `frontend/vuex-pinia-store` | `governance/skills-dev/frontend/vuex-pinia-store.md` | Pinia Store 生成 | — |
| `frontend/router-config` | `governance/skills-dev/frontend/router-config.md` | 路由配置 | — |
| `frontend/frontend-lint-checker` | `governance/skills-dev/frontend/frontend-lint-checker.md` | Lint 检查 | — |

## 产出物规范

| 产出物 | 路径模板 | 验证规则 |
|--------|---------|----------|
| Vue 组件 | `src/components/*.vue` | Composition API (`<script setup lang="ts">`) |
| 页面组件 | `src/pages/*.vue` | 完整页面，引用子组件 |
| Pinia Store | `src/stores/*.ts` | TypeScript 严格模式 |

### 代码规则

- **必须**: Composition API (`<script setup lang="ts">`) 优先
- **必须**: TypeScript 严格模式，`any` 禁止
- **必须**: 生成后自检：ESLint + `tsc --noEmit`
- **禁止**: 使用 Options API、忽略类型错误

## 门禁条件

进入 Phase 6 (Backend Impl) 前必须满足：

- [ ] 所有 COMPONENT_SPEC.md 定义的组件已生成（检查 `agent_outputs["design-agent"]` 中的组件清单）
- [ ] **ESLint 通过**: 0 error（warning 允许）
- [ ] **tsc --noEmit 通过**: 0 type error
- [ ] **Router 配置完整**: `router/index.ts` 中所有页面路由已注册
- [ ] 所有 `.vue` 文件使用 Composition API (`<script setup lang="ts">`)
- [ ] 无 `: any` 类型标注（grep 检查通过）

`check_sop_gate_dev.py --agent frontend-agent` 检查项:
- 前端产物路径可变，不执行静态文件检查（参见 check_sop_gate_dev.py AGENT_ARTIFACTS 注释）

## 跳过条件

此 Phase 在以下模式中被跳过：

| Mode | 跳过? | 说明 |
|------|-------|------|
| `full` | 否 | — |
| `resume` | 否* | 若已完成则跳过 |
| `status` | 是 | entry 后直接 exit |
| `from-architecture` | 否 | 从 Architecture 开始 |
| `from-frontend` | 否 | 从 Frontend Impl 开始 |
| `from-backend` | **是** | 跳过 Frontend Impl |
| `review-only` | **是** | 跳过实现 Phase |

## Agent 详情

- **Agent ID**: `frontend-agent`
- **System Prompt Role**: 资深 Vue 3 + TypeScript 前端开发专家
- **模型层级**: [待补充：agent-definitions-dev.yaml 中未指定 model_tier]
- **上下文文件**: `shared-language`, `coding-standards`
- **边界**: 不生成后端 API、不设计数据库

## 常见问题 / 故障排除

- [待补充：根据实践经验积累]

## 相关文档

- Phase 定义: [../CANONICAL_PHASES.md](../CANONICAL_PHASES.md)
- Agent 映射: [../AGENT_PHASE_MAP.md](../AGENT_PHASE_MAP.md)
- Agent 定义: `governance/agents/agent-definitions-dev.yaml` → `frontend-agent`
- 后端实现: [06-backend-impl.md](06-backend-impl.md)
