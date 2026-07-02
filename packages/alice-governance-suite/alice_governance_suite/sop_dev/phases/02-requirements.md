# Phase 2: Requirements（需求分析）

## 概述

- **编号**: 2 / 10
- **目标**: 将项目计划转化为结构化的功能规格、用户故事、验收标准和数据模型
- **执行 Agent**: `req-agent`（需求分析 Agent）
- **阶段分组**: 规划阶段

## 输入条件

- Phase 1 Plan 完成：PROJECT_PLAN.md 已生成
- [待补充：需定义 req-agent 从 pm-agent 的 `agent_outputs` 中读取哪些字段]

## 执行步骤

由 Agent Loop 驱动，`req-agent` 按以下 Skill 链执行：

1. `requirements-dev/feature-spec` — 结构化功能规格，优先级分类，MVP 边界
2. `requirements-dev/user-story-writer` — As a/I want/So that 格式用户故事（依赖 feature-spec）
3. `requirements-dev/data-model-spec` — ERD 图 + 实体字段定义（依赖 feature-spec）
4. `requirements-dev/acceptance-criteria` — Given/When/Then 验收标准（依赖 user-story-writer）
5. `automation/prompt-engineering-expert` — 主动优化 Skill Prompt（事件驱动）

## 涉及 Skills

| Skill ID | 文件路径 | 描述 | 依赖 |
|----------|---------|------|------|
| `requirements-dev/feature-spec` | `governance/skills-dev/requirements-dev/feature-spec.md` | 结构化功能规格，优先级分类 | — |
| `requirements-dev/user-story-writer` | `governance/skills-dev/requirements-dev/user-story-writer.md` | As a/I want/So that 用户故事 | `feature-spec` |
| `requirements-dev/acceptance-criteria` | `governance/skills-dev/requirements-dev/acceptance-criteria.md` | Given/When/Then 验收标准 | `user-story-writer` |
| `requirements-dev/data-model-spec` | `governance/skills-dev/requirements-dev/data-model-spec.md` | ERD 图 + 实体字段定义 | `feature-spec` |
| `automation/prompt-engineering-expert` | `governance/skills-dev/automation/prompt-engineering-expert.md` | PE 技术应用（17 种技术，≤3 叠加） | `review/prompt-engineering` |

## 产出物规范

| 产出物 | 路径模板 | 验证规则 |
|--------|---------|----------|
| FEATURE_SPEC.md | `{module}/FEATURE_SPEC.md` | [待补充：需定义功能规格的最小结构] |
| USER_STORIES.md | `{module}/USER_STORIES.md` | [待补充：需定义 User Story 最小格式] |
| ACCEPTANCE_CRITERIA.md | `{module}/ACCEPTANCE_CRITERIA.md` | [待补充：需定义 AC 最小格式] |
| DATA_MODEL.md | `{module}/DATA_MODEL.md` | [待补充：需定义 ERD 和字段定义格式] |

## 门禁条件

进入 Phase 3 (Architecture) 前必须满足：

- [ ] **FEATURE_SPEC.md** 存在且包含：
  - 功能描述 + 优先级分类 (P0/P1/P2)
  - 用户场景 ≥3 个，覆盖正常/边界/异常
  - 非功能需求（性能、安全）明确标注
- [ ] **USER_STORIES.md** 存在且：
  - ≥3 个 User Story，使用 "As a/I want/So that" 格式
  - 每个 Story 有验收标准
- [ ] **ACCEPTANCE_CRITERIA.md** 存在且覆盖：
  - 正常流程 (happy path) ≥2 条
  - 边界条件 ≥2 条，异常处理 ≥1 条
- [ ] **DATA_MODEL.md** 存在且包含：
  - 实体关系描述 (ERD 或文字)
  - 每个实体的字段定义 (字段名、类型、约束)

`check_sop_gate_dev.py --agent req-agent` 检查项:
- FEATURE_SPEC.md, USER_STORIES.md, ACCEPTANCE_CRITERIA.md, DATA_MODEL.md 存在于 artifacts 目录

## 跳过条件

此 Phase 在以下模式中被跳过：

| Mode | 跳过? | 说明 |
|------|-------|------|
| `full` | 否 | — |
| `resume` | 否* | 若已完成则跳过 |
| `status` | 是 | entry 后直接 exit |
| `from-architecture` | **是** | 跳过 Plan + Requirements |
| `from-frontend` | **是** | 跳过前 4 Phase |
| `from-backend` | **是** | 跳过前 5 Phase |
| `review-only` | **是** | 跳过前 6 Phase |

## Agent 详情

- **Agent ID**: `req-agent`
- **System Prompt Role**: 资深产品经理 + 需求分析师
- **模型层级**: balanced
- **上下文文件**: `shared-language`, `project-context`, `tech-stack`
- **边界**: 不设计 UI、不编写代码、不部署

## 常见问题 / 故障排除

- [待补充：根据实践经验积累]

## 相关文档

- Phase 定义: [../CANONICAL_PHASES.md](../CANONICAL_PHASES.md)
- Agent 映射: [../AGENT_PHASE_MAP.md](../AGENT_PHASE_MAP.md)
- Agent 定义: `governance/agents/agent-definitions-dev.yaml` → `req-agent`
