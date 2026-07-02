# Phase 3: Architecture（架构设计）

## 概述

- **编号**: 3 / 10
- **目标**: 确定项目的技术栈、目录结构、组件树和 API 契约，形成系统骨架设计
- **执行 Agent**: `arch-agent`（架构 Agent）
- **阶段分组**: 设计阶段

## 输入条件

- Phase 2 Requirements 完成：FEATURE_SPEC.md 已生成
- [待补充：需定义 arch-agent 从 req-agent 的 `agent_outputs` 中读取哪些字段]

## 执行步骤

由 Agent Loop 驱动，`arch-agent` 按以下 Skill 链执行：

1. `architecture/project-scanner` — 扫描现有项目结构
2. `architecture/tech-stack-decider` — 基于需求和数据模型确定技术栈（依赖 project-scanner）
3. `architecture/component-tree-designer` — 设计组件树（依赖 tech-stack-decider）
4. `architecture/api-contract-designer` — 定义 API 契约（依赖 component-tree-designer）

## 涉及 Skills

| Skill ID | 文件路径 | 描述 | 依赖 |
|----------|---------|------|------|
| `architecture/project-scanner` | `governance/skills-dev/architecture/project-scanner.md` | 项目扫描 | — |
| `architecture/tech-stack-decider` | `governance/skills-dev/architecture/tech-stack-decider.md` | 技术栈选型 | `project-scanner` |
| `architecture/component-tree-designer` | `governance/skills-dev/architecture/component-tree-designer.md` | 组件树设计 | `tech-stack-decider` |
| `architecture/api-contract-designer` | `governance/skills-dev/architecture/api-contract-designer.md` | API 契约设计 | `component-tree-designer` |

## 产出物规范

| 产出物 | 路径模板 | 验证规则 |
|--------|---------|----------|
| PROJECT_STRUCTURE.md | `{module}/PROJECT_STRUCTURE.md` | [待补充：需定义目录结构描述的最小规范] |
| TECH_STACK.md | `{module}/TECH_STACK.md` | [待补充：需定义技术栈声明的必填字段] |
| COMPONENT_TREE.md | `{module}/COMPONENT_TREE.md` | [待补充：需定义组件树描述的最小结构] |
| API_CONTRACTS.md | `{module}/API_CONTRACTS.md` | [待补充：需定义 API 契约的最小字段（method/path/request/response）] |

## 门禁条件

进入 Phase 4 (Component Design) 前必须满足：

- [ ] **PROJECT_STRUCTURE.md** 存在且：
  - 覆盖所有计划目录（前端 src/、后端 routers/models/schemas/）
  - 每个目录有用途说明
- [ ] **TECH_STACK.md** 存在且：
  - 列出前端技术栈（框架、UI 库、状态管理、构建工具）
  - 列出后端技术栈（框架、ORM、数据库、缓存）
  - 每个选型附理由（≥1 句）
- [ ] **COMPONENT_TREE.md** 存在且：
  - 树形结构覆盖 FEATURE_SPEC.md 所有功能
  - 每个组件标注类型（page/component/layout）
- [ ] **API_CONTRACTS.md** 存在且：
  - 每个端点包含 method, path, request schema, response schema
  - ≥1 个端点定义

`check_sop_gate_dev.py --agent arch-agent` 检查项:
- PROJECT_STRUCTURE.md, TECH_STACK.md, COMPONENT_TREE.md, API_CONTRACTS.md 存在于 artifacts 目录

## 跳过条件

此 Phase 在以下模式中被跳过：

| Mode | 跳过? | 说明 |
|------|-------|------|
| `full` | 否 | — |
| `resume` | 否* | 若已完成则跳过 |
| `status` | 是 | entry 后直接 exit |
| `from-architecture` | 否 | 从 Architecture 开始 |
| `from-frontend` | **是** | 跳过前 4 Phase |
| `from-backend` | **是** | 跳过前 5 Phase |
| `review-only` | **是** | 跳过前 6 Phase |

## Agent 详情

- **Agent ID**: `arch-agent`
- **System Prompt Role**: 资深全栈架构师
- **模型层级**: [待补充：agent-definitions-dev.yaml 中未指定 model_tier，默认使用 balanced]
- **上下文文件**: `shared-language`, `coding-standards`
- **边界**: 不编写业务代码、不生成 UI 组件、不部署

## 常见问题 / 故障排除

- [待补充：根据实践经验积累]

## 相关文档

- Phase 定义: [../CANONICAL_PHASES.md](../CANONICAL_PHASES.md)
- Agent 映射: [../AGENT_PHASE_MAP.md](../AGENT_PHASE_MAP.md)
- Agent 定义: `governance/agents/agent-definitions-dev.yaml` → `arch-agent`
