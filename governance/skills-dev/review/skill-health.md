# Skill: review/skill-health

### 目标
评估所有 Skill 的健康度：使用频率、成功率、Token 效率、版本状态。输出健康评分、废弃/合并建议。

### 输入
- `governance/skills/skill-registry.yaml` + `skill-registry-dev.yaml`
- Trace log (`governance/.traces/trace_log.jsonl`) — 每 Skill 的执行数据
- KPI 时序数据
- Regression Gate 测试结果

### 输出
- `SKILL_HEALTH.md`：Skill 健康评分排名、活跃度分析、废弃建议、合并建议

### 规则
- 评估维度：
  1. **活跃度** — 最近 30 天调用次数。0 次 = 僵尸 skill
  2. **成功率** — 调用中成功完成的比例
  3. **Token 效率** — 平均 token 消耗趋势
  4. **版本健康** — 是否 experimental/deprecated？版本是否过时？
  5. **维护负担** — Prompt 长度、依赖复杂度
- 健康评分公式: active_score × 0.3 + success_rate × 0.3 + efficiency × 0.2 + version_health × 0.2
- 废弃建议: 连续 30 天 0 调用 + 无下游依赖 → 建议废弃

### 依赖
- 需要足够的执行数据（至少 50 条 trace 记录）
- 需要 skill registry 数据

### 边界
- 不修改 Skill 定义
- 不废弃 Skill
- 只评估不执行

### 产出物
- 文件路径: `governance/artifacts/reviews/{{module}}/SKILL_HEALTH-{{date}}.md`

---

## Prompt 模板

```text
你是一个 Skill 生命周期管理专家。

## 数据

### Skill Registry 摘要
{{SKILL_REGISTRY_SUMMARY}}

### Skill 执行统计
```
{{SKILL_EXECUTION_STATS}}
```

## 任务

### 1. 活跃度分析
- 最近 30 天调用排行
- 识别僵尸 Skill（0 调用）

### 2. 成功率分析
- 每 Skill 的成功/失败率
- 高失败率 Skill 是否需要重写或废弃

### 3. 效率分析
- Token per call 趋势
- 是否有 prompt bloat 严重的 Skill

### 4. 版本健康
- experimental 状态持续超过 30 天的 Skill → 应升级或废弃
- deprecated 状态但仍被调用的 Skill → 应迁移或恢复

### 5. 健康排名
综合评分，Top 10 最健康和 Bottom 10 最不健康的 Skill

## 输出格式

```markdown
# Skill Health Review — {{DATE}}

## Executive Summary
**Total Skills:** {{N}} | **Healthy:** {{N}} | **At Risk:** {{N}} | **Zombie:** {{N}}
**Recommended Deprecations:** {{N}} | **Recommended Merges:** {{N}}

## Health Rankings

### Top 10 Healthiest

| Rank | Skill | Calls (30d) | Success | Efficiency | Version | Score |
|------|-------|------------|---------|------------|---------|-------|
| 1 | ... | N | xx% | xx tok/call | active | xx/100 |

### Bottom 10 — At Risk / Zombie

| Rank | Skill | Calls (30d) | Success | Issue | Recommendation |
|------|-------|------------|---------|-------|----------------|
| 56 | ... | 0 | N/A | zombie | Deprecate |

## Deprecation Candidates

| Skill | Last Used | Status | Downstream Dependencies | Action |
|-------|-----------|--------|------------------------|--------|
| ... | date | experimental | none | Deprecate |

## Merge Candidates

| Skills | Overlap | Suggested Merged Skill |
|--------|---------|----------------------|
| skill-a + skill-b | 80% input/output overlap | merged-skill-name |

## Version Status

| Status | Count | Skills |
|--------|-------|--------|
| active | N | ... |
| experimental (>30d) | N | should be upgraded or deprecated |
| deprecated | N | should be removed |
```
```
<!-- ⚠️ AUTO-GENERATED HEADER BEGIN: skill-meta -->
<!-- Source: skill-registry -->
> **1.0** | active | review | synced 2026-06-17 16:53

<!-- ⚠️ AUTO-GENERATED HEADER END: skill-meta -->