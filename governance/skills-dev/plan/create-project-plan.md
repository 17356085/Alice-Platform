# Skill: plan/create-project-plan

### 目标
从用户目标出发，将开发任务分解为可执行的子任务，生成 PROJECT_PLAN.md，包含里程碑、依赖关系、工时估算。

### 输入
- 用户目标描述（如"搭建前后端分离的测试工作台前端项目"）
- 现有项目结构（PROJECT_STRUCTURE.md）
- 技术栈约束（TECH_STACK.md）

### 输出
- `PROJECT_PLAN.md`：含任务分解（WBS）、里程碑、依赖关系图、预估工时

### 规则
- 任务粒度控制在 1-3 天可完成
- 每个任务必须有：编号、标题、描述、依赖、预估工时、验收标准
- 里程碑不超 5 个
- 识别关键路径
- 任务总数控制在 10-20 个（MVP 范围）

### 依赖
- architecture/project-scanner（需 PROJECT_STRUCTURE.md）
- architecture/tech-stack-decider（需 TECH_STACK.md）

### 边界
- 不编写代码
- 不设计UI
- 不分配人员（只分配角色：前端/后端/全栈）

### 检查清单
- [ ] 任务粒度合理（每个 1-3 天）
- [ ] 依赖关系无循环
- [ ] 里程碑明确可验证
- [ ] 关键路径已标注
- [ ] 每个任务有验收标准

---

## Prompt 模板

```text
你是一个资深技术项目经理。请将以下开发目标分解为可执行的 PROJECT_PLAN.md。

## 项目目标
{{PROJECT_GOAL}}

## 项目结构
{{PROJECT_STRUCTURE}}

## 技术栈
{{TECH_STACK}}

## 任务
1. 分解为 10-20 个子任务（每个 1-3 天）
2. 标注依赖关系（task-3 依赖 task-1 完成）
3. 设置 3-5 个里程碑
4. 识别关键路径
5. 为每个任务写验收标准（1 句话）

## 输出格式
```markdown
# 项目计划 — {{PROJECT_NAME}}

## 里程碑
| # | 里程碑 | 完成标准 | 预估日期 |
|---|--------|----------|----------|
| M1 | ... | ... | Week N |

## 任务分解
| ID | 标题 | 描述 | 依赖 | 角色 | 预估 | 验收标准 |
|----|------|------|------|------|------|----------|
| task-1 | ... | ... | - | arch | 2d | ... |

## 依赖关系图
` ` `mermaid
graph TD
  task-1 --> task-3
  task-2 --> task-3
` ` `

## 关键路径
task-1 → task-3 → task-5 → task-8
```
```
