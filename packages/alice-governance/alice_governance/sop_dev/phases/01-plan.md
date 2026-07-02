# Phase 1: Plan（项目规划）

## 概述

- **编号**: 1 / 10
- **目标**: 将项目目标转化为可执行的任务分解、里程碑规划和风险评估
- **执行 Agent**: `pm-agent`（项目管理 Agent）
- **阶段分组**: 规划阶段

## 输入条件

- 项目目标和范围描述 [待补充：需从用户输入或项目上下文中获取具体格式]
- Phase 0（无前置 Phase）：作为 Dev SOP 的第一个 Phase，无上游依赖

## 执行步骤

由 Agent Loop 驱动，`pm-agent` 按以下 Skill 链执行：

1. `plan/create-project-plan` — 任务分解、里程碑规划、依赖关系图
2. `plan/sprint-planner` — Sprint 规划、任务优先级排序、工时估算
3. `plan/risk-analyzer` — 风险矩阵分析（依赖 `create-project-plan` 输出）
4. `plan/progress-tracker` — 生成初始进度基线（依赖 `create-project-plan` 输出）

## 涉及 Skills

| Skill ID | 文件路径 | 描述 | 依赖 |
|----------|---------|------|------|
| `plan/create-project-plan` | `governance/skills-dev/plan/create-project-plan.md` | 任务分解、里程碑规划、依赖关系图 | `architecture/project-scanner` |
| `plan/progress-tracker` | `governance/skills-dev/plan/progress-tracker.md` | 对比计划 vs 实际产物，输出进度报告 | `plan/create-project-plan` |
| `plan/risk-analyzer` | `governance/skills-dev/plan/risk-analyzer.md` | 风险矩阵分析，标注高等级风险缓解措施 | `plan/create-project-plan` |
| `plan/sprint-planner` | `governance/skills-dev/plan/sprint-planner.md` | Sprint 规划，任务优先级排序，工时估算 | `plan/create-project-plan` |

## 产出物规范

| 产出物 | 路径模板 | 验证规则 |
|--------|---------|----------|
| PROJECT_PLAN.md | `{module}/PROJECT_PLAN.md` | [待补充：需定义 Milestone/任务分解的最小结构] |
| PROGRESS_REPORT.md | `{module}/PROGRESS_REPORT.md` | [待补充：需定义进度指标格式] |
| RISK_ANALYSIS.md | `{module}/RISK_ANALYSIS.md` | [待补充：需定义风险矩阵最小字段] |

## 门禁条件

进入 Phase 2 (Requirements) 前必须满足：

- [ ] **PROJECT_PLAN.md** 存在且非空，包含：
  - ≥1 个里程碑 (Milestone)，每个有截止日期
  - 任务分解 (WBS)，粒度 ≤3 天/任务
  - 依赖关系图 (Mermaid 或文字描述)
- [ ] **RISK_ANALYSIS.md** 存在且：
  - 列出 ≥3 个风险项
  - 每个风险有 概率×影响 评分 + 缓解措施
- [ ] **PROGRESS_REPORT.md** 存在（初始基线）
- [ ] `agent_outputs["pm-agent"]` 存在且 artifacts 字段非空

`check_sop_gate_dev.py --agent pm-agent` 检查项:
- PROJECT_PLAN.md, PROGRESS_REPORT.md, RISK_ANALYSIS.md 存在于 artifacts 目录

## 跳过条件

此 Phase 在以下模式中被跳过：

| Mode | 跳过? | 说明 |
|------|-------|------|
| `full` | 否 | — |
| `resume` | 否* | 若已完成则跳过 |
| `status` | 是 | entry 后直接 exit |
| `from-architecture` | **是** | 跳过 Plan + Requirements |
| `from-frontend` | **是** | 跳过 Plan + Requirements + Architecture + Component Design |
| `from-backend` | **是** | 跳过前 5 Phase |
| `review-only` | **是** | 跳过前 6 Phase |

## Agent 详情

- **Agent ID**: `pm-agent`
- **System Prompt Role**: 资深技术项目经理
- **模型层级**: balanced
- **上下文文件**: `shared-language`, `project-context`, `tech-stack`
- **边界**: 不编写代码、不修改代码、不部署

## 常见问题 / 故障排除

- [待补充：根据实践经验积累]

## 相关文档

- Phase 定义: [../CANONICAL_PHASES.md](../CANONICAL_PHASES.md)
- Agent 映射: [../AGENT_PHASE_MAP.md](../AGENT_PHASE_MAP.md)
- Agent 定义: `governance/agents/agent-definitions-dev.yaml` → `pm-agent`
