# Phase 4: Component Design（组件设计）

## 概述

- **编号**: 4 / 10
- **目标**: 将架构设计细化为组件级的规格说明、Props 接口和数据流设计
- **执行 Agent**: `design-agent`（组件设计 Agent）
- **阶段分组**: 设计阶段

## 输入条件

- Phase 3 Architecture 完成：COMPONENT_TREE.md 已生成
- [待补充：需定义 design-agent 从 arch-agent 的 `agent_outputs` 中读取哪些字段]

## 执行步骤

由 Agent Loop 驱动，`design-agent` 按以下 Skill 链执行：

1. `component-design/component-spec` — 组件结构分析（依赖 COMPONENT_TREE.md）
2. `component-design/props-interface` — Props 接口定义（依赖 component-spec）
3. `component-design/layout-mockup` — 页面布局 mockup（依赖 component-spec）
4. `component-design/data-flow` — 数据流设计（依赖 props-interface）

## 涉及 Skills

| Skill ID | 文件路径 | 描述 | 依赖 |
|----------|---------|------|------|
| `component-design/component-spec` | `governance/skills-dev/component-design/component-spec.md` | 组件结构分析 | `architecture/component-tree-designer` |
| `component-design/props-interface` | `governance/skills-dev/component-design/props-interface.md` | Props 接口定义 | `component-spec` |
| `component-design/data-flow` | `governance/skills-dev/component-design/data-flow.md` | 数据流设计 | `props-interface` |
| `component-design/layout-mockup` | `governance/skills-dev/component-design/layout-mockup.md` | 页面布局 mockup | `component-spec` |

## 产出物规范

| 产出物 | 路径模板 | 验证规则 |
|--------|---------|----------|
| COMPONENT_SPEC.md | `{module}/COMPONENT_SPEC.md` | [待补充：需定义组件规格的最小结构] |
| PROPS_INTERFACE.yaml | `{module}/PROPS_INTERFACE.yaml` | [待补充：需定义 Props 接口的必填字段（name/type/required/default）] |
| DATA_FLOW.md | `{module}/DATA_FLOW.md` | [待补充：需定义数据流描述的最小规范] |

## 门禁条件

进入 Phase 5 (Frontend Impl) 前必须满足：

- [ ] **COMPONENT_SPEC.md** 存在且：
  - 覆盖 COMPONENT_TREE.md 中所有组件
  - 每个组件有功能描述、Props 清单、Events 清单、Slots 清单
- [ ] **PROPS_INTERFACE.yaml** 存在且：
  - 每个组件定义了 Props（字段: name, type, required, default）
  - ≥1 个组件通过 JSON Schema 校验
- [ ] **DATA_FLOW.md** 存在且：
  - 描述 ≥2 条组件间数据传递路径
  - 标注状态管理方式（props/emit/provide-inject/Pinia）

`check_sop_gate_dev.py --agent design-agent` 检查项:
- COMPONENT_SPEC.md, PROPS_INTERFACE.yaml, DATA_FLOW.md 存在于 artifacts 目录

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

- **Agent ID**: `design-agent`
- **System Prompt Role**: 资深 UI/UX 架构师
- **模型层级**: [待补充：agent-definitions-dev.yaml 中未指定 model_tier]
- **上下文文件**: `shared-language` [待补充：是否还需要其他上下文文件]
- **边界**: 不编写业务代码、不生成 API

## 常见问题 / 故障排除

- [待补充：根据实践经验积累]

## 相关文档

- Phase 定义: [../CANONICAL_PHASES.md](../CANONICAL_PHASES.md)
- Agent 映射: [../AGENT_PHASE_MAP.md](../AGENT_PHASE_MAP.md)
- Agent 定义: `governance/agents/agent-definitions-dev.yaml` → `design-agent`
