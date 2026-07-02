# Skill: review/agent-health

### 目标
评估所有 Agent 的健康度：执行成功率、平均耗时、Token 消耗趋势、Skill 链完整性。输出健康评分和优化建议。

### 输入
- Agent 定义文件
- Trace log — 每 Agent 的执行数据
- KPI 时序数据
- SOP_STATUS 文件

### 输出
- `AGENT_HEALTH.md`：Agent 健康评分排名、瓶颈 Agent 识别、优化建议

### 规则
- 评估维度：
  1. **执行成功率** — Agent 全部 skills 执行后的总体成功率
  2. **执行效率** — 平均耗时、平均 token 消耗
  3. **Skill 链完整性** — Agent 的所有 skills 是否都正常执行
  4. **边界合规** — Agent 是否违反 defined boundaries
  5. **使用频率** — Agent 是否被充分使用（非僵尸 Agent）
- 健康评分: success × 0.35 + efficiency × 0.25 + completeness × 0.2 + compliance × 0.1 + frequency × 0.1

### 依赖
- 需要足够的执行数据
- 需要 Agent 定义文件

### 边界
- 不修改 Agent 定义
- 不优化 Agent
- 只评估不执行

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/AGENT_HEALTH-{{date}}.md`

---

## Prompt 模板

```text
你是一个 Agent 系统运维专家。

## 数据

### Agent 定义摘要
{{AGENT_DEFINITIONS_SUMMARY}}

### Agent 执行统计
```
{{AGENT_EXECUTION_STATS}}
```

## 任务

### 1. 执行成功率
- 每 Agent 的总体成功率
- 失败集中在哪个 Skill

### 2. 执行效率
- 每 Agent 的平均耗时排名
- Token 消耗 Top 10 Agent
- Token 消耗趋势（increasing/stable/decreasing）

### 3. Skill 链完整性
- 哪些 Agent 的某些 Skill 从未被调用
- 哪些 Agent 的 Skill 链中存在断裂（前一个 skill 失败导致后续跳过）

### 4. 边界合规
- 是否有 Agent 违反了 defined boundaries
- 是否有 Agent 产出不在 output_artifacts 中

### 5. 使用频率
- 是否有僵尸 Agent
- 是否有过度使用的 Agent（可能是瓶颈）

## 输出格式

```markdown
# Agent Health Review — {{DATE}}

## Executive Summary
**Total Agents:** {{N}} | **Healthy:** {{N}} | **At Risk:** {{N}} | **Zombie:** {{N}}

## Health Rankings

| Rank | Agent | Success | Avg Duration | Avg Tokens | Trend | Score |
|------|-------|---------|-------------|-----------|-------|-------|
| 1 | ... | xx% | xx s | xx | ↑/↓/→ | xx/100 |

## Bottleneck Agents

| Agent | Issue | Impact | Suggestion |
|-------|-------|--------|------------|
| ... | avg duration >5min | slows entire SOP | split or parallelize |

## Zombie Agents

| Agent | Last Active | Skills Never Called | Action |
|-------|------------|-------------------|--------|
| ... | date | skill-x, skill-y | Deprecate or repurpose |

## Skill Chain Health

| Agent | Total Skills | Active Skills | Broken Skills | Completeness |
|-------|-------------|---------------|---------------|-------------|
| ... | N | N | N | xx% |

## Recommendations

| Priority | Agent | Action | Rationale |
|----------|-------|--------|-----------|
| P0 | ... | ... | ... |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-18 10:54

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->