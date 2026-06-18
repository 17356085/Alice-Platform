# Skill: plan/sprint-planner

### 目标
将 PROJECT_PLAN.md 的任务按优先级和依赖排序到 Sprint，输出 SPRINT_PLAN.md。

### 输入
- `PROJECT_PLAN.md`

### 输出
- `SPRINT_PLAN.md`：Sprint 1..N，每个 Sprint 含任务列表、目标、预估工时

### 规则
- Sprint 周期 1-2 周
- 每个 Sprint 有明确的可交付目标
- 优先安排关键路径上的任务

---

## Prompt 模板

```text
将以下项目计划排入 Sprint。

## 项目计划
{{PROJECT_PLAN}}

## 输出
| Sprint | 目标 | 任务 | 预估工时 |
|--------|------|------|----------|
| Sprint 1 | ... | task-1, task-2 | 5d |
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | plan | synced 2026-06-17 21:52

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->