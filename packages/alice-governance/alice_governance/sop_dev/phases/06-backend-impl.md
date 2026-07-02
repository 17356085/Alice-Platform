# Phase 6: Backend Impl（后端实现）

## 概述

- **编号**: 6 / 10
- **目标**: 基于 API 契约和组件设计，生成 FastAPI 后端代码——路由、Schema、模型和 CRUD
- **执行 Agent**: `backend-agent`（后端开发 Agent）
- **阶段分组**: 实现阶段

## 输入条件

- Phase 3 Architecture 完成：API_CONTRACTS.md 已生成
- Phase 4 Component Design 完成：COMPONENT_SPEC.md 已生成
- [待补充：需定义 backend-agent 从 arch-agent/design-agent 的 `agent_outputs` 中读取哪些字段]

## 执行步骤

由 Agent Loop 驱动，`backend-agent` 按以下 Skill 链执行：

1. `backend/pydantic-schema-generator` — 基于 API_CONTRACTS.md 生成 Pydantic Schema
2. `backend/sqlalchemy-model-generator` — 基于 DATA_MODEL.md 生成 SQLAlchemy 模型
3. `backend/fastapi-router-generator` — 基于 API 契约生成 FastAPI 路由
4. `backend/crud-generator` — 生成标准 CRUD 操作
5. `backend/unit-test-generator` — 生成后端单元测试
6. `backend/backend-consistency-checker` — 检查 Schema/Model/Router 一致性

> **特殊规则**: `per_api_group: true` — 可按 API 组拆分独立执行。

## 涉及 Skills

| Skill ID | 文件路径 | 描述 | 依赖 |
|----------|---------|------|------|
| `backend/fastapi-router-generator` | `governance/skills-dev/backend/fastapi-router-generator.md` | FastAPI 路由生成 | — |
| `backend/pydantic-schema-generator` | `governance/skills-dev/backend/pydantic-schema-generator.md` | Pydantic Schema 生成 | — |
| `backend/sqlalchemy-model-generator` | `governance/skills-dev/backend/sqlalchemy-model-generator.md` | SQLAlchemy 模型生成 | — |
| `backend/crud-generator` | `governance/skills-dev/backend/crud-generator.md` | CRUD 生成（需人工确认） | — |
| `backend/unit-test-generator` | `governance/skills-dev/backend/unit-test-generator.md` | 后端单元测试 | — |
| `backend/backend-consistency-checker` | `governance/skills-dev/backend/backend-consistency-checker.md` | 一致性检查 | — |

## 产出物规范

| 产出物 | 路径模板 | 验证规则 |
|--------|---------|----------|
| FastAPI 路由 | `routers/*.py` | `async def` 所有端点 |
| Pydantic Schema | `schemas/*.py` | Pydantic v2 `ConfigDict` |
| SQLAlchemy 模型 | `models/*.py` | SQLAlchemy 2.0 `mapped_column()` |

### 代码规则

- **必须**: SQLAlchemy 2.0 `mapped_column()`
- **必须**: Pydantic v2 `ConfigDict`
- **必须**: `async def` 所有端点
- **禁止**: 同步端点、旧版 Pydantic `class Config`、SQLAlchemy 1.x `Column()`

## 门禁条件

进入 Phase 7 (Code Review) 前必须满足：

- [ ] 所有 API_CONTRACTS.md 定义的端点已实现（检查 `agent_outputs["arch-agent"]` 中的契约清单）
- [ ] **所有端点 `async def`**（grep 检查: 无 `def ` 在路由文件中）
- [ ] **SQLAlchemy 2.0**: `mapped_column()` 使用（grep 检查: 无 `Column()` 导入）
- [ ] **Pydantic v2**: `model_config = ConfigDict(...)` 使用（grep 检查: 无 `class Config` 旧版用法）
- [ ] **backend-consistency-checker 通过**: 前后端 API 契约匹配

`check_sop_gate_dev.py --agent backend-agent` 检查项:
- 后端产物路径可变，不执行静态文件检查
- 建议包含：
  - [ ] 所有 API_CONTRACTS.md 中定义的端点已实现
  - [ ] Schema/Model/Router 一致性检查通过
  - [ ] 后端单元测试可运行
  - [ ] CRUD 操作完整（Create/Read/Update/Delete）

## 跳过条件

此 Phase 在以下模式中被跳过：

| Mode | 跳过? | 说明 |
|------|-------|------|
| `full` | 否 | — |
| `resume` | 否* | 若已完成则跳过 |
| `status` | 是 | entry 后直接 exit |
| `from-architecture` | 否 | 从 Architecture 开始 |
| `from-frontend` | 否 | 从 Frontend Impl 开始 |
| `from-backend` | 否 | 从 Backend Impl 开始 |
| `review-only` | **是** | 跳过实现 Phase |

## Agent 详情

- **Agent ID**: `backend-agent`
- **System Prompt Role**: 资深 FastAPI + SQLAlchemy 后端开发专家
- **模型层级**: [待补充：agent-definitions-dev.yaml 中未指定 model_tier]
- **上下文文件**: `shared-language`, `coding-standards`
- **边界**: 不生成前端代码、不部署

## 常见问题 / 故障排除

- [待补充：根据实践经验积累]

## 相关文档

- Phase 定义: [../CANONICAL_PHASES.md](../CANONICAL_PHASES.md)
- Agent 映射: [../AGENT_PHASE_MAP.md](../AGENT_PHASE_MAP.md)
- Agent 定义: `governance/agents/agent-definitions-dev.yaml` → `backend-agent`
- 前端实现: [05-frontend-impl.md](05-frontend-impl.md)
